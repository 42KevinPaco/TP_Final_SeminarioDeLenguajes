"""CSV implementation of the product repository."""

from dataclasses import replace
from pathlib import Path

from app.models.producto import Producto
from app.repository.csv_base import CsvTable
from app.repository.interfaces import IProductoRepository
from app.utils.config import DATA_DIR

FIELDNAMES = ["id_producto", "nombre", "descripcion", "precio", "marca", "imagen"]


class CsvProductoRepository(IProductoRepository):
    """Persists products in `data/productos.csv`."""

    def __init__(self, path: Path | None = None) -> None:
        self._table = CsvTable(Path(path) if path else DATA_DIR / "productos.csv", FIELDNAMES)
        self._table.ensure()

    def listar(self) -> list[Producto]:
        return [self._to_model(row) for row in self._table.read_rows()]

    def obtener_por_id(self, id_producto: int) -> Producto | None:
        for row in self._table.read_rows():
            if int(row["id_producto"]) == id_producto:
                return self._to_model(row)
        return None

    def crear(self, producto: Producto) -> Producto:
        creado = replace(producto, id_producto=self._table.next_id("id_producto"))
        self._table.append_row(self._to_row(creado))
        return creado

    def actualizar(self, producto: Producto) -> Producto:
        rows = self._table.read_rows()
        for index, row in enumerate(rows):
            if int(row["id_producto"]) == producto.id_producto:
                rows[index] = self._to_row(producto)
                self._table.write_rows(rows)
                return producto
        raise ValueError(f"No existe el producto con id {producto.id_producto}")

    def eliminar(self, id_producto: int) -> None:
        rows = self._table.read_rows()
        self._table.write_rows([row for row in rows if int(row["id_producto"]) != id_producto])

    # ---------- mapping ----------
    def _to_model(self, row: dict[str, str]) -> Producto:
        return Producto(
            id_producto=int(row["id_producto"]),
            nombre=row.get("nombre", ""),
            descripcion=row.get("descripcion", ""),
            precio=float(row.get("precio") or 0),
            marca=row.get("marca", ""),
            imagen=row.get("imagen", ""),
        )

    def _to_row(self, producto: Producto) -> dict[str, str]:
        return {
            "id_producto": str(producto.id_producto),
            "nombre": producto.nombre,
            "descripcion": producto.descripcion,
            "precio": f"{producto.precio:.2f}",
            "marca": producto.marca,
            "imagen": producto.imagen,
        }
