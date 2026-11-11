"""Per-branch stock use cases."""

from app.models.sucursal import StockSucursal
from app.repository.interfaces import IStockSucursalRepository
from app.utils import validators
from app.utils.exceptions import RecursoNoEncontradoError, StockInsuficienteError


class StockService:
    """Keeps available quantities consistent across branches."""

    def __init__(self, stock_repository: IStockSucursalRepository) -> None:
        self._stock = stock_repository

    def listar(self) -> list[StockSucursal]:
        return self._stock.listar()

    def listar_por_sucursal(self, id_sucursal: int) -> list[StockSucursal]:
        return self._stock.listar_por_sucursal(id_sucursal)

    def listar_por_producto(self, id_producto: int) -> list[StockSucursal]:
        return self._stock.listar_por_producto(id_producto)

    def obtener(self, id_producto: int, id_sucursal: int) -> StockSucursal:
        stock = self._stock.obtener(id_producto, id_sucursal)
        if stock is None:
            raise RecursoNoEncontradoError("No hay stock registrado para ese producto en esa sucursal")
        return stock

    def asignar(self, id_producto: int, id_sucursal: int, cantidad) -> StockSucursal:
        """Create the stock row, or update it when it already exists."""
        cantidad_limpia = validators.validar_entero_positivo(cantidad, "cantidad")
        existente = self._stock.obtener(id_producto, id_sucursal)
        if existente is not None:
            existente.actualizar_stock(cantidad_limpia)
            return self._stock.actualizar(existente)
        return self._stock.crear(
            StockSucursal(
                id_stock=0,
                id_producto=id_producto,
                id_sucursal=id_sucursal,
                cantidad_disponible=cantidad_limpia,
            )
        )

    def actualizar_cantidad(self, id_stock: int, cantidad) -> StockSucursal:
        cantidad_limpia = validators.validar_entero_no_negativo(cantidad, "cantidad")
        for stock in self._stock.listar():
            if stock.id_stock == id_stock:
                stock.actualizar_stock(cantidad_limpia)
                return self._stock.actualizar(stock)
        raise RecursoNoEncontradoError("El registro de stock no existe")

    def descontar(self, id_producto: int, id_sucursal: int, cantidad) -> StockSucursal:
        cantidad_limpia = validators.validar_entero_positivo(cantidad, "cantidad")
        stock = self.obtener(id_producto, id_sucursal)
        if not stock.verificar_cantidad(cantidad_limpia):
            raise StockInsuficienteError("Stock insuficiente en la sucursal seleccionada")
        stock.descontar_stock(cantidad_limpia)
        return self._stock.actualizar(stock)

    def eliminar_de_producto(self, id_producto: int) -> None:
        """Cascade helper for the admin product deletion flow."""
        self._stock.eliminar_por_producto(id_producto)

    def eliminar_de_sucursal(self, id_sucursal: int) -> None:
        """Cascade helper for the admin branch deletion flow."""
        self._stock.eliminar_por_sucursal(id_sucursal)

    def hay_disponibilidad(self, id_producto: int, id_sucursal: int, cantidad: int = 1) -> bool:
        stock = self._stock.obtener(id_producto, id_sucursal)
        return stock is not None and stock.verificar_cantidad(cantidad)

    def cantidad_total(self, id_producto: int) -> int:
        """Available units across every branch (catalog-level availability)."""
        return sum(
            stock.cantidad_disponible for stock in self._stock.listar_por_producto(id_producto)
        )

    def cantidad_total_por_producto(self) -> dict[int, int]:
        totales: dict[int, int] = {}
        for stock in self._stock.listar():
            totales[stock.id_producto] = totales.get(stock.id_producto, 0) + stock.cantidad_disponible
        return totales
