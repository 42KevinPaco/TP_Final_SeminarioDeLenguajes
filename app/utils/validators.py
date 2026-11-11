"""Server-side validation helpers.

These mirror the JavaScript validations: they check format and required
fields, never business availability.
"""

import re

from app.utils.exceptions import DatosInvalidosError

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PHONE_PATTERN = re.compile(r"^[0-9]{10}$")


def requerido(valor: str, campo: str) -> str:
    texto = (valor or "").strip()
    if not texto:
        raise DatosInvalidosError(f"El campo {campo} es obligatorio")
    return texto


def validar_email(email: str) -> str:
    texto = requerido(email, "email")
    if not EMAIL_PATTERN.match(texto):
        raise DatosInvalidosError("El email no tiene un formato válido")
    return texto.lower()


def validar_telefono(telefono: str) -> str:
    texto = requerido(telefono, "teléfono")
    if not PHONE_PATTERN.match(texto):
        raise DatosInvalidosError("El teléfono debe tener 10 dígitos")
    return texto


def validar_numero_positivo(valor, campo: str) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise DatosInvalidosError(f"El campo {campo} debe ser numérico") from exc
    if numero <= 0:
        raise DatosInvalidosError(f"El campo {campo} debe ser mayor a 0")
    return numero


def validar_entero_positivo(valor, campo: str) -> int:
    try:
        numero = int(valor)
    except (TypeError, ValueError) as exc:
        raise DatosInvalidosError(f"El campo {campo} debe ser un número entero") from exc
    if numero < 1:
        raise DatosInvalidosError(f"El campo {campo} debe ser mayor o igual a 1")
    return numero


def validar_entero_no_negativo(valor, campo: str) -> int:
    """Whole amount that may reach 0 (stock can legitimately sell out)."""
    try:
        numero = int(valor)
    except (TypeError, ValueError) as exc:
        raise DatosInvalidosError(f"El campo {campo} debe ser un número entero") from exc
    if numero < 0:
        raise DatosInvalidosError(f"El campo {campo} no puede ser negativo")
    return numero
