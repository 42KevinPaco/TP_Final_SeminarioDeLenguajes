"""Domain models package (UML classes)."""

from app.models.carrito import CarritoCompra, ItemCarrito
from app.models.compra import Compra, DetalleCompra
from app.models.pago import (
    Pago,
    PagoCredito,
    PagoDebito,
    PagoEfectivo,
    ResultadoPago,
)
from app.models.producto import Producto
from app.models.sucursal import StockSucursal, Sucursal
from app.models.usuario import Administrador, Cliente, Usuario

__all__ = [
    "Administrador",
    "CarritoCompra",
    "Cliente",
    "Compra",
    "DetalleCompra",
    "ItemCarrito",
    "Pago",
    "PagoCredito",
    "PagoDebito",
    "PagoEfectivo",
    "Producto",
    "ResultadoPago",
    "StockSucursal",
    "Sucursal",
    "Usuario",
]
