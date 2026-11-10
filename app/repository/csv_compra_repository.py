"""CSV implementation of the purchase repository.

Two tables: one header row per purchase and one row per line. Card data is
never persisted; only the payment method discriminator is stored.
"""

from dataclasses import replace
from datetime import date
from pathlib import Path

from app.models.compra import Compra, DetalleCompra
from app.repository.csv_base import CsvTable
from app.repository.interfaces import ICompraRepository
from app.utils.config import DATA_DIR

COMPRA_FIELDNAMES = [
    "id_compra",
    "id_cliente",
    "id_sucursal",
    "fecha",
    "estado",
    "total",
    "metodo_pago",
]

DETALLE_FIELDNAMES = [
    "id_detalle",
    "id_compra",
    "id_producto",
    "nombre_producto",
    "cantidad",
    "precio_unitario",
]


class CsvCompraRepository(ICompraRepository):
    """Persists purchases in `data/compras.csv` and `data/compra_detalles.csv`."""

    def __init__(
        self,
        compras_path: Path | None = None,
        detalles_path: Path | None = None,
    ) -> None:
        self._compras = CsvTable(
            Path(compras_path) if compras_path else DATA_DIR / "compras.csv",
            COMPRA_FIELDNAMES,
        )
        self._detalles = CsvTable(
            Path(detalles_path) if detalles_path else DATA_DIR / "compra_detalles.csv",
            DETALLE_FIELDNAMES,
        )
        self._compras.ensure()
        self._detalles.ensure()

    # ---------- reads ----------
    def obtener_por_id(self, id_compra: int) -> Compra | None:
        for row in self._compras.read_rows():
            if int(row["id_compra"]) == id_compra:
                return self._to_compra(row)
        return None

    def listar_por_cliente(self, id_cliente: int) -> list[Compra]:
        return [
            self._to_compra(row)
            for row in self._compras.read_rows()
            if int(row["id_cliente"]) == id_cliente
        ]

    # ---------- writes ----------
    def crear(self, compra: Compra) -> Compra:
        id_compra = self._compras.next_id("id_compra")
        guardada = replace(compra, id_compra=id_compra)
        self._compras.append_row(self._to_row(guardada))
        for detalle in guardada.detalles:
            id_detalle = self._detalles.next_id("id_detalle")
            self._detalles.append_row(self._to_detalle_row(id_detalle, id_compra, detalle))
        return guardada

    # ---------- mapping ----------
    def _to_row(self, compra: Compra) -> dict[str, str]:
        return {
            "id_compra": str(compra.id_compra),
            "id_cliente": str(compra.id_cliente),
            "id_sucursal": str(compra.id_sucursal),
            "fecha": compra.fecha.isoformat(),
            "estado": compra.estado,
            "total": f"{compra.calcular_total():.2f}",
            "metodo_pago": compra.pago.metodo if compra.pago is not None else "",
        }

    def _to_detalle_row(
        self,
        id_detalle: int,
        id_compra: int,
        detalle: DetalleCompra,
    ) -> dict[str, str]:
        return {
            "id_detalle": str(id_detalle),
            "id_compra": str(id_compra),
            "id_producto": str(detalle.id_producto),
            "nombre_producto": detalle.nombre_producto,
            "cantidad": str(detalle.cantidad),
            "precio_unitario": f"{detalle.precio_unitario:.2f}",
        }

    def _to_compra(self, row: dict[str, str]) -> Compra:
        return Compra(
            id_compra=int(row["id_compra"]),
            id_cliente=int(row["id_cliente"]),
            id_sucursal=int(row["id_sucursal"]),
            fecha=date.fromisoformat(row["fecha"]) if row.get("fecha") else date.today(),
            estado=row.get("estado") or "confirmada",
            detalles=self._detalles_de(int(row["id_compra"])),
            pago=None,
        )

    def _detalles_de(self, id_compra: int) -> list[DetalleCompra]:
        return [
            DetalleCompra(
                id_producto=int(row["id_producto"]),
                nombre_producto=row.get("nombre_producto", ""),
                cantidad=int(row["cantidad"]),
                precio_unitario=float(row["precio_unitario"]),
            )
            for row in self._detalles.read_rows()
            if int(row["id_compra"]) == id_compra
        ]
