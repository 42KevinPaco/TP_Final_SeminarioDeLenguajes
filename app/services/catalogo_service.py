"""Catalog use case: what a customer is allowed to see.

Products with zero stock across every branch are hidden from the storefront.
The admin panel keeps listing every product, including sold-out ones.
"""

from app.models.producto import Producto
from app.services.producto_service import ProductoService
from app.services.stock_service import StockService


class CatalogoService:
    """Composes products and stock for the customer-facing catalog."""

    def __init__(
        self,
        producto_service: ProductoService,
        stock_service: StockService,
    ) -> None:
        self._productos = producto_service
        self._stock = stock_service

    def listar_disponibles(self) -> list[Producto]:
        """Return only products with at least one unit available somewhere."""
        totales = self._stock.cantidad_total_por_producto()
        return [
            producto
            for producto in self._productos.listar()
            if totales.get(producto.id_producto, 0) > 0
        ]
