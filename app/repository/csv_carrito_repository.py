"""CSV implementation of the cart repository.

Each row is one product line of one customer's cart. The profile price is kept
at insertion time, matching the ItemCarrito domain rule.
"""

from pathlib import Path

from app.models.carrito import ItemCarrito
from app.repository.csv_base import CsvTable
from app.repository.interfaces import ICarritoRepository, IProductoRepository
from app.utils.config import DATA_DIR

FIELDNAMES = ["id_linea", "id_usuario", "id_producto", "cantidad", "precio_unitario"]


class CsvCarritoRepository(ICarritoRepository):
    """Persists cart lines in `data/carrito.csv`."""

    def __init__(
        self,
        producto_repository: IProductoRepository,
        path: Path | None = None,
    ) -> None:
        self._productos = producto_repository
        self._table = CsvTable(Path(path) if path else DATA_DIR / "carrito.csv", FIELDNAMES)
        self._table.ensure()

    # ---------- reads ----------
    def listar_por_usuario(self, id_usuario: int) -> list[ItemCarrito]:
        items: list[ItemCarrito] = []
        for row in self._rows_for(id_usuario):
            item = self._to_item(row)
            if item is not None:
                items.append(item)
        return items

    def obtener_item(self, id_usuario: int, id_producto: int) -> ItemCarrito | None:
        for row in self._rows_for(id_usuario):
            if int(row["id_producto"]) == id_producto:
                return self._to_item(row)
        return None

    def contar_unidades(self, id_usuario: int) -> int:
        return sum(int(row["cantidad"]) for row in self._rows_for(id_usuario))

    # ---------- writes ----------
    def agregar(self, id_usuario: int, item: ItemCarrito) -> ItemCarrito:
        id_linea = self._table.next_id("id_linea")
        self._table.append_row(self._to_row(id_linea, id_usuario, item))
        return item

    def actualizar(self, id_usuario: int, item: ItemCarrito) -> ItemCarrito:
        rows = self._table.read_rows()
        for index, row in enumerate(rows):
            if (
                int(row["id_usuario"]) == id_usuario
                and int(row["id_producto"]) == item.producto.id_producto
            ):
                rows[index] = self._to_row(int(row["id_linea"]), id_usuario, item)
                self._table.write_rows(rows)
                return item
        raise ValueError(f"El producto {item.producto.id_producto} no está en el carrito")

    def eliminar(self, id_usuario: int, id_producto: int) -> None:
        rows = self._table.read_rows()
        restantes = [
            row
            for row in rows
            if not (
                int(row["id_usuario"]) == id_usuario
                and int(row["id_producto"]) == id_producto
            )
        ]
        if len(restantes) != len(rows):
            self._table.write_rows(restantes)

    def vaciar(self, id_usuario: int) -> None:
        rows = self._table.read_rows()
        restantes = [row for row in rows if int(row["id_usuario"]) != id_usuario]
        if len(restantes) != len(rows):
            self._table.write_rows(restantes)

    # ---------- mapping ----------
    def _rows_for(self, id_usuario: int) -> list[dict[str, str]]:
        return [
            row
            for row in self._table.read_rows()
            if int(row["id_usuario"]) == id_usuario
        ]

    def _to_item(self, row: dict[str, str]) -> ItemCarrito | None:
        producto = self._productos.obtener_por_id(int(row["id_producto"]))
        if producto is None:
            return None
        return ItemCarrito(
            producto=producto,
            cantidad=int(row["cantidad"]),
            precio_unitario=float(row["precio_unitario"]),
        )

    def _to_row(self, id_linea: int, id_usuario: int, item: ItemCarrito) -> dict[str, str]:
        return {
            "id_linea": str(id_linea),
            "id_usuario": str(id_usuario),
            "id_producto": str(item.producto.id_producto),
            "cantidad": str(item.cantidad),
            "precio_unitario": f"{item.precio_unitario:.2f}",
        }
