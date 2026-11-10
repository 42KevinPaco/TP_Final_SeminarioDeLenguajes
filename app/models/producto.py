"""Product domain model."""

from dataclasses import dataclass


@dataclass
class Producto:
    """Catalog item. Prices are stored in ARS currency units."""

    id_producto: int
    nombre: str
    descripcion: str
    precio: float
    marca: str

    def __post_init__(self) -> None:
        if self.precio <= 0:
            raise ValueError("El precio del producto debe ser mayor a 0")
        if not self.nombre.strip():
            raise ValueError("El nombre del producto es obligatorio")

    def __str__(self) -> str:
        return f"{self.nombre} ({self.marca})"
