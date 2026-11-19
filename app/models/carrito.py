"""Shopping cart models.

UML composition: CarritoCompra owns its ItemCarrito instances. Deleting the
cart deletes its items; items never exist outside a cart.
"""

from dataclasses import dataclass, field
from datetime import date

from app.models.producto import Producto


@dataclass
class ItemCarrito:
    """One product line inside a cart. Keeps the unit price at insertion time."""

    producto: Producto
    cantidad: int
    precio_unitario: float

    def __post_init__(self) -> None:
        if self.cantidad < 1:
            raise ValueError("La cantidad debe ser un entero mayor o igual a 1")

    @classmethod
    def desde_producto(cls, producto: Producto, cantidad: int = 1) -> "ItemCarrito":
        return cls(producto=producto, cantidad=cantidad, precio_unitario=producto.precio)

    @property
    def subtotal(self) -> float:
        return round(self.precio_unitario * self.cantidad, 2)

    def calcular_subtotal(self) -> float:
        return self.subtotal

    def modificar_cantidad(self, cantidad: int) -> None:
        if cantidad < 1:
            raise ValueError("La cantidad debe ser un entero mayor o igual a 1")
        self.cantidad = cantidad


@dataclass
class CarritoCompra:
    """Active cart of a customer."""

    id_carrito: int
    fecha_creacion: date = field(default_factory=date.today)
    items: list[ItemCarrito] = field(default_factory=list)

    def agregar_producto(self, producto: Producto, cantidad: int = 1) -> ItemCarrito:
        if cantidad < 1:
            raise ValueError("La cantidad debe ser un entero mayor o igual a 1")
        existente = self.buscar_item(producto.id_producto)
        if existente is not None:
            existente.modificar_cantidad(existente.cantidad + cantidad)
            return existente
        item = ItemCarrito.desde_producto(producto, cantidad)
        self.items.append(item)
        return item

    def eliminar_producto(self, id_producto: int) -> None:
        self.items = [i for i in self.items if i.producto.id_producto != id_producto]

    def buscar_item(self, id_producto: int) -> ItemCarrito | None:
        for item in self.items:
            if item.producto.id_producto == id_producto:
                return item
        return None

    def calcular_total(self) -> float:
        return round(sum(item.subtotal for item in self.items), 2)

    def vaciar_carrito(self) -> None:
        self.items.clear()

    @property
    def cantidad_items(self) -> int:
        return sum(item.cantidad for item in self.items)
