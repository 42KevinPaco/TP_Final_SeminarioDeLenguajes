"""Payment models.

UML: Pago is abstract; PagoEfectivo, PagoDebito and PagoCredito implement
procesarPago() with their own rules (polymorphism).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

ESTADO_PENDIENTE = "pendiente"
ESTADO_APROBADO = "aprobado"
ESTADO_RECHAZADO = "rechazado"


@dataclass
class ResultadoPago:
    """Outcome of processing a payment."""

    aprobado: bool
    mensaje: str
    vuelto: float = 0.0


@dataclass
class Pago(ABC):
    id_pago: int
    importe: float
    fecha: date = field(default_factory=date.today)
    estado: str = ESTADO_PENDIENTE

    def __post_init__(self) -> None:
        if self.importe <= 0:
            raise ValueError("El importe del pago debe ser mayor a 0")

    @abstractmethod
    def validar_pago(self) -> bool:
        """Return True when the payment data is well formed."""

    @abstractmethod
    def procesar_pago(self) -> ResultadoPago:
        """Apply the method-specific payment rules."""


@dataclass
class PagoEfectivo(Pago):
    """Cash payment: needs enough cash to cover the amount."""

    monto_recibido: float = 0.0

    def validar_pago(self) -> bool:
        return self.monto_recibido >= self.importe

    def procesar_pago(self) -> ResultadoPago:
        if not self.validar_pago():
            self.estado = ESTADO_RECHAZADO
            return ResultadoPago(False, "El monto recibido no alcanza para cubrir el total")
        self.estado = ESTADO_APROBADO
        return ResultadoPago(True, "Pago en efectivo registrado", round(self.monto_recibido - self.importe, 2))


@dataclass
class _PagoConTarjeta(Pago):
    """Shared card validation for debit and credit payments."""

    numero_tarjeta: str = ""
    titular: str = ""
    vencimiento: str = ""  # MM/AA
    cvv: str = ""

    def validar_pago(self) -> bool:
        numero = "".join(self.numero_tarjeta.split())
        if len(numero) != 16 or not numero.isdigit():
            return False
        if not self.titular.strip():
            return False
        if len(self.cvv) != 3 or not self.cvv.isdigit():
            return False
        return self._vencimiento_vigente()

    def _vencimiento_vigente(self) -> bool:
        if len(self.vencimiento) != 5 or self.vencimiento[2] != "/":
            return False
        mes_texto, anio_texto = self.vencimiento.split("/")
        if not (mes_texto.isdigit() and anio_texto.isdigit()):
            return False
        mes = int(mes_texto)
        if not 1 <= mes <= 12:
            return False
        anio = 2000 + int(anio_texto)
        hoy = date.today()
        return (anio, mes) >= (hoy.year, hoy.month)

    def _procesar_tarjeta(self, mensaje_ok: str) -> ResultadoPago:
        if not self.validar_pago():
            self.estado = ESTADO_RECHAZADO
            return ResultadoPago(False, "Datos de tarjeta inválidos")
        self.estado = ESTADO_APROBADO
        return ResultadoPago(True, mensaje_ok)


@dataclass
class PagoDebito(_PagoConTarjeta):
    """Debit card: charges the account immediately."""

    def procesar_pago(self) -> ResultadoPago:
        return self._procesar_tarjeta("Pago con tarjeta de débito aprobado")


@dataclass
class PagoCredito(_PagoConTarjeta):
    """Credit card: supports installments."""

    cuotas: int = 1

    def validar_pago(self) -> bool:
        return super().validar_pago() and self.cuotas >= 1

    def procesar_pago(self) -> ResultadoPago:
        return self._procesar_tarjeta(f"Pago con tarjeta de crédito aprobado en {self.cuotas} cuota(s)")
