"""Purchase use case: confirm the cart, charge, discount stock and persist."""

from app.models.compra import Compra
from app.models.pago import Pago
from app.repository.interfaces import ICompraRepository
from app.services.carrito_service import CarritoService
from app.services.stock_service import StockService
from app.utils.exceptions import DatosInvalidosError, StockInsuficienteError


class CompraService:
    """Turns a customer cart into a confirmed, persisted purchase."""

    def __init__(
        self,
        compra_repository: ICompraRepository,
        carrito_service: CarritoService,
        stock_service: StockService,
    ) -> None:
        self._compras = compra_repository
        self._carrito = carrito_service
        self._stock = stock_service

    def preparar(self, id_cliente: int) -> Compra | None:
        """Draft purchase for the checkout summary; None when the cart is empty."""
        carrito = self._carrito.obtener_carrito(id_cliente)
        if not carrito.items:
            return None
        return Compra.desde_carrito(0, id_cliente, 0, carrito)

    def confirmar(self, id_cliente: int, id_sucursal: int, pago: Pago) -> Compra:
        """Validate stock, charge, persist the purchase and empty the cart."""
        carrito = self._carrito.obtener_carrito(id_cliente)
        if not carrito.items:
            raise DatosInvalidosError("El carrito está vacío")

        self._validar_stock_de_la_sucursal(carrito, id_sucursal)

        resultado = pago.procesar_pago()
        if not resultado.aprobado:
            raise DatosInvalidosError(resultado.mensaje)

        compra = Compra.desde_carrito(0, id_cliente, id_sucursal, carrito, pago)
        compra.confirmar_compra()

        for detalle in compra.detalles:
            self._stock.descontar(detalle.id_producto, id_sucursal, detalle.cantidad)

        guardada = self._compras.crear(compra)
        self._carrito.vaciar(id_cliente)
        return guardada

    def listar_por_cliente(self, id_cliente: int) -> list[Compra]:
        return self._compras.listar_por_cliente(id_cliente)

    def _validar_stock_de_la_sucursal(self, carrito, id_sucursal: int) -> None:
        for item in carrito.items:
            if not self._stock.hay_disponibilidad(
                item.producto.id_producto, id_sucursal, item.cantidad
            ):
                raise StockInsuficienteError(
                    f"No hay stock suficiente de {item.producto.nombre} en esa sucursal"
                )
