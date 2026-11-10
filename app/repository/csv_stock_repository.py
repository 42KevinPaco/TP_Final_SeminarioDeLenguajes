"""CSV implementation of the per-branch stock repository."""

from dataclasses import replace
from pathlib import Path

from app.models.sucursal import StockSucursal
from app.repository.csv_base import CsvTable
from app.repository.interfaces import IStockSucursalRepository
from app.utils.config import DATA_DIR

FIELDNAMES = ["id_stock", "id_producto", "id_sucursal", "cantidad_disponible"]


class CsvStockSucursalRepository(IStockSucursalRepository):
    """Persists stock rows in `data/stock.csv`."""

    def __init__(self, path: Path | None = None) -> None:
        self._table = CsvTable(Path(path) if path else DATA_DIR / "stock.csv", FIELDNAMES)
        self._table.ensure()

    def listar(self) -> list[StockSucursal]:
        return [self._to_model(row) for row in self._table.read_rows()]

    def listar_por_sucursal(self, id_sucursal: int) -> list[StockSucursal]:
        return [s for s in self.listar() if s.id_sucursal == id_sucursal]

    def listar_por_producto(self, id_producto: int) -> list[StockSucursal]:
        return [s for s in self.listar() if s.id_producto == id_producto]

    def obtener(self, id_producto: int, id_sucursal: int) -> StockSucursal | None:
        for stock in self.listar():
            if stock.id_producto == id_producto and stock.id_sucursal == id_sucursal:
                return stock
        return None

    def crear(self, stock: StockSucursal) -> StockSucursal:
        creado = replace(stock, id_stock=self._table.next_id("id_stock"))
        self._table.append_row(self._to_row(creado))
        return creado

    def actualizar(self, stock: StockSucursal) -> StockSucursal:
        rows = self._table.read_rows()
        for index, row in enumerate(rows):
            if int(row["id_stock"]) == stock.id_stock:
                rows[index] = self._to_row(stock)
                self._table.write_rows(rows)
                return stock
        raise ValueError(f"No existe el stock con id {stock.id_stock}")

    # ---------- mapping ----------
    def _to_model(self, row: dict[str, str]) -> StockSucursal:
        return StockSucursal(
            id_stock=int(row["id_stock"]),
            id_producto=int(row["id_producto"]),
            id_sucursal=int(row["id_sucursal"]),
            cantidad_disponible=int(row.get("cantidad_disponible") or 0),
        )

    def _to_row(self, stock: StockSucursal) -> dict[str, str]:
        return {
            "id_stock": str(stock.id_stock),
            "id_producto": str(stock.id_producto),
            "id_sucursal": str(stock.id_sucursal),
            "cantidad_disponible": str(stock.cantidad_disponible),
        }
