"""Purchase models.

UML composition: Compra owns its DetalleCompra instances, and keeps the unit
price recorded at confirmation time.
"""

from dataclasses import dataclass, field
from datetime import date

from app.models.carrito import CarritoCompra
from app.models.pago import Pago

ESTADO_PENDIENTE = "pendiente"
ESTADO_CONFIRMADA = "confirmada"
ESTADO_CANCELADA = "cancelada"


@dataclass
class DetalleCompra:
    """One product line of a confirmed purchase (price snapshot)."""

    id_producto: int
    nombre_producto: str
    cantidad: int
    precio_unitario: float

    def __post_init__(self) -> None:
        if self.cantidad < 1:
            raise ValueError("La cantidad debe ser un entero mayor o igual a 1")

    @property
    def subtotal(self) -> float:
        return round(self.precio_unitario * self.cantidad, 2)

    def calcular_subtotal(self) -> float:
        return self.subtotal


@dataclass
class Compra:
    """Confirmed purchase associated to one customer, one branch and one payment."""

    id_compra: int
    id_cliente: int
    id_sucursal: int
    fecha: date = field(default_factory=date.today)
    estado: str = ESTADO_PENDIENTE
    detalles: list[DetalleCompra] = field(default_factory=list)
    pago: Pago | None = None

    @classmethod
    def desde_carrito(
        cls,
        id_compra: int,
        id_cliente: int,
        id_sucursal: int,
        carrito: CarritoCompra,
        pago: Pago | None = None,
    ) -> "Compra":
        if not carrito.items:
            raise ValueError("No se puede confirmar una compra con el carrito vacío")
        detalles = [
            DetalleCompra(
                id_producto=item.producto.id_producto,
                nombre_producto=item.producto.nombre,
                cantidad=item.cantidad,
                precio_unitario=item.precio_unitario,
            )
            for item in carrito.items
        ]
        return cls(
            id_compra=id_compra,
            id_cliente=id_cliente,
            id_sucursal=id_sucursal,
            detalles=detalles,
            pago=pago,
        )

    @property
    def total(self) -> float:
        return self.calcular_total()

    def calcular_total(self) -> float:
        return round(sum(detalle.subtotal for detalle in self.detalles), 2)

    def confirmar_compra(self) -> None:
        if not self.detalles:
            raise ValueError("La compra no tiene detalles")
        if self.pago is not None and not self.pago.validar_pago():
            raise ValueError("El pago no es válido")
        self.estado = ESTADO_CONFIRMADA

    def cancelar_compra(self) -> None:
        if self.estado == ESTADO_CONFIRMADA:
            raise ValueError("Una compra confirmada no se puede cancelar desde este flujo")
        self.estado = ESTADO_CANCELADA
