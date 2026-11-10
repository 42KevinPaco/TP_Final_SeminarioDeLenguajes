"""Branch and per-branch stock models.

StockSucursal resolves the many-to-many relationship between Producto and
Sucursal (UML), holding the available quantity for one product in one branch.
"""

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.0


@dataclass
class Sucursal:
    """Physical store location."""

    id_sucursal: int
    nombre: str
    direccion: str
    latitud: float
    longitud: float

    def distancia_km(self, latitud: float, longitud: float) -> float:
        """Great-circle distance (Haversine) to the given coordinates."""
        lat1, lon1 = radians(self.latitud), radians(self.longitud)
        lat2, lon2 = radians(latitud), radians(longitud)
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1
        a = sin(delta_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
        return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


@dataclass
class StockSucursal:
    """Available quantity of one product in one branch."""

    id_stock: int
    id_producto: int
    id_sucursal: int
    cantidad_disponible: int

    def __post_init__(self) -> None:
        if self.cantidad_disponible < 0:
            raise ValueError("La cantidad disponible no puede ser negativa")

    def verificar_cantidad(self, cantidad: int) -> bool:
        return self.cantidad_disponible >= cantidad

    def descontar_stock(self, cantidad: int) -> None:
        if cantidad <= 0:
            raise ValueError("La cantidad a descontar debe ser mayor a 0")
        if not self.verificar_cantidad(cantidad):
            raise ValueError("Stock insuficiente en la sucursal seleccionada")
        self.cantidad_disponible -= cantidad

    def actualizar_stock(self, cantidad: int) -> None:
        if cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa")
        self.cantidad_disponible = cantidad
