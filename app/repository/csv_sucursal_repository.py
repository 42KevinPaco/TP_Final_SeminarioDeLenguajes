"""CSV implementation of the branch repository."""

from dataclasses import replace
from pathlib import Path

from app.models.sucursal import Sucursal
from app.repository.csv_base import CsvTable
from app.repository.interfaces import ISucursalRepository
from app.utils.config import DATA_DIR

FIELDNAMES = ["id_sucursal", "nombre", "direccion", "latitud", "longitud"]


class CsvSucursalRepository(ISucursalRepository):
    """Persists branches in `data/sucursales.csv`."""

    def __init__(self, path: Path | None = None) -> None:
        self._table = CsvTable(Path(path) if path else DATA_DIR / "sucursales.csv", FIELDNAMES)
        self._table.ensure()

    def listar(self) -> list[Sucursal]:
        return [self._to_model(row) for row in self._table.read_rows()]

    def obtener_por_id(self, id_sucursal: int) -> Sucursal | None:
        for row in self._table.read_rows():
            if int(row["id_sucursal"]) == id_sucursal:
                return self._to_model(row)
        return None

    def crear(self, sucursal: Sucursal) -> Sucursal:
        creada = replace(sucursal, id_sucursal=self._table.next_id("id_sucursal"))
        self._table.append_row(self._to_row(creada))
        return creada

    def actualizar(self, sucursal: Sucursal) -> Sucursal:
        rows = self._table.read_rows()
        for index, row in enumerate(rows):
            if int(row["id_sucursal"]) == sucursal.id_sucursal:
                rows[index] = self._to_row(sucursal)
                self._table.write_rows(rows)
                return sucursal
        raise ValueError(f"No existe la sucursal con id {sucursal.id_sucursal}")

    def eliminar(self, id_sucursal: int) -> None:
        rows = self._table.read_rows()
        restantes = [
            row for row in rows if int(row["id_sucursal"]) != id_sucursal
        ]
        if len(restantes) == len(rows):
            raise ValueError(f"No existe la sucursal con id {id_sucursal}")
        self._table.write_rows(restantes)

    # ---------- mapping ----------
    def _to_model(self, row: dict[str, str]) -> Sucursal:
        return Sucursal(
            id_sucursal=int(row["id_sucursal"]),
            nombre=row.get("nombre", ""),
            direccion=row.get("direccion", ""),
            latitud=float(row.get("latitud") or 0),
            longitud=float(row.get("longitud") or 0),
        )

    def _to_row(self, sucursal: Sucursal) -> dict[str, str]:
        return {
            "id_sucursal": str(sucursal.id_sucursal),
            "nombre": sucursal.nombre,
            "direccion": sucursal.direccion,
            "latitud": f"{sucursal.latitud:.6f}",
            "longitud": f"{sucursal.longitud:.6f}",
        }
