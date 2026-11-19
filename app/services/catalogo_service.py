"""Catalog use cases: what a customer can look up.

Every product stays visible, including sold-out ones, so a customer can learn
that an item exists and see its stock (total and per branch). Searching works
on name, brand and description, ignoring case and accents.
"""

import unicodedata
from dataclasses import dataclass, field

from app.models.producto import Producto
from app.models.sucursal import Sucursal
from app.services.producto_service import ProductoService
from app.services.stock_service import StockService
from app.services.sucursal_service import SucursalService


@dataclass
class ItemCatalogo:
    """A product together with its availability."""

    producto: Producto
    stock_total: int = 0
    por_sucursal: list[tuple[Sucursal, int]] = field(default_factory=list)

    @property
    def disponible(self) -> bool:
        return self.stock_total > 0


def _normalizar(texto: str) -> str:
    sin_acentos = unicodedata.normalize("NFD", texto or "")
    return "".join(c for c in sin_acentos if unicodedata.category(c) != "Mn").lower().strip()


class CatalogoService:
    """Composes products, branches and stock for the customer-facing catalog."""

    def __init__(
        self,
        producto_service: ProductoService,
        stock_service: StockService,
        sucursal_service: SucursalService | None = None,
    ) -> None:
        self._productos = producto_service
        self._stock = stock_service
        self._sucursales = sucursal_service

    def consultar(self, busqueda: str = "") -> list[ItemCatalogo]:
        """Every product matching the search, with total and per-branch stock."""
        termino = _normalizar(busqueda)
        sucursales = {s.id_sucursal: s for s in self._sucursales.listar()} if self._sucursales else {}
        stock_por_producto: dict[int, list[tuple[Sucursal, int]]] = {}
        for fila in self._stock.listar():
            sucursal = sucursales.get(fila.id_sucursal)
            if sucursal is not None:
                stock_por_producto.setdefault(fila.id_producto, []).append(
                    (sucursal, fila.cantidad_disponible)
                )

        items: list[ItemCatalogo] = []
        for producto in self._productos.listar():
            texto = _normalizar(f"{producto.nombre} {producto.marca} {producto.descripcion}")
            if termino and termino not in texto:
                continue
            filas = sorted(stock_por_producto.get(producto.id_producto, []), key=lambda f: f[0].nombre)
            items.append(
                ItemCatalogo(
                    producto=producto,
                    stock_total=sum(cantidad for _, cantidad in filas),
                    por_sucursal=filas,
                )
            )
        return items

    def listar_disponibles(self) -> list[Producto]:
        """Only products with at least one unit available somewhere."""
        totales = self._stock.cantidad_total_por_producto()
        return [
            producto
            for producto in self._productos.listar()
            if totales.get(producto.id_producto, 0) > 0
        ]
