"""Cart use cases for a logged-in customer.

Stock is validated against the total available across branches, because the
branch is only chosen at purchase time.
"""

from app.models.carrito import CarritoCompra, ItemCarrito
from app.repository.interfaces import ICarritoRepository, IProductoRepository
from app.services.stock_service import StockService
from app.utils import validators
from app.utils.exceptions import RecursoNoEncontradoError, StockInsuficienteError


class CarritoService:
    """Orchestrates the persistent cart of one customer."""

    def __init__(
        self,
        carrito_repository: ICarritoRepository,
        producto_repository: IProductoRepository,
        stock_service: StockService,
    ) -> None:
        self._carrito = carrito_repository
        self._productos = producto_repository
        self._stock = stock_service

    def obtener_carrito(self, id_usuario: int) -> CarritoCompra:
        carrito = CarritoCompra(id_carrito=id_usuario)
        carrito.items = self._carrito.listar_por_usuario(id_usuario)
        return carrito

    def contar_unidades(self, id_usuario: int) -> int:
        return self._carrito.contar_unidades(id_usuario)

    def agregar(self, id_usuario: int, id_producto: int, cantidad=1) -> CarritoCompra:
        cantidad_limpia = validators.validar_entero_positivo(cantidad, "cantidad")
        producto = self._productos.obtener_por_id(id_producto)
        if producto is None:
            raise RecursoNoEncontradoError("El producto no existe")

        existente = self._carrito.obtener_item(id_usuario, id_producto)
        cantidad_final = (existente.cantidad if existente else 0) + cantidad_limpia
        self._validar_stock(id_producto, cantidad_final)

        if existente is not None:
            existente.modificar_cantidad(cantidad_final)
            self._carrito.actualizar(id_usuario, existente)
        else:
            self._carrito.agregar(id_usuario, ItemCarrito.desde_producto(producto, cantidad_limpia))
        return self.obtener_carrito(id_usuario)

    def actualizar_cantidad(self, id_usuario: int, id_producto: int, cantidad) -> CarritoCompra:
        cantidad_limpia = validators.validar_entero_positivo(cantidad, "cantidad")
        item = self._carrito.obtener_item(id_usuario, id_producto)
        if item is None:
            raise RecursoNoEncontradoError("El producto no está en el carrito")

        self._validar_stock(id_producto, cantidad_limpia)
        item.modificar_cantidad(cantidad_limpia)
        self._carrito.actualizar(id_usuario, item)
        return self.obtener_carrito(id_usuario)

    def eliminar(self, id_usuario: int, id_producto: int) -> CarritoCompra:
        self._carrito.eliminar(id_usuario, id_producto)
        return self.obtener_carrito(id_usuario)

    def vaciar(self, id_usuario: int) -> None:
        self._carrito.vaciar(id_usuario)

    def _validar_stock(self, id_producto: int, cantidad: int) -> None:
        disponible = self._stock.cantidad_total(id_producto)
        if disponible <= 0:
            raise StockInsuficienteError("El producto no tiene stock disponible")
        if cantidad > disponible:
            raise StockInsuficienteError(
                f"Solo hay {disponible} unidad(es) disponibles de ese producto"
            )
