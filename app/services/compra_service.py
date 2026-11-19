"""Purchase use case: confirm the cart, charge, discount stock and persist."""

from dataclasses import dataclass, field

from app.models.compra import Compra
from app.models.pago import Pago
from app.models.sucursal import Sucursal
from app.repository.interfaces import ICompraRepository
from app.services.carrito_service import CarritoService
from app.services.stock_service import StockService
from app.utils.concurrencia import LOCK_ALMACEN
from app.utils.exceptions import DatosInvalidosError, StockInsuficienteError


@dataclass
class OpcionSucursal:
    """A branch as offered at checkout: distance and whether it can serve the cart."""

    sucursal: Sucursal
    distancia_km: float | None = None
    faltantes: list[str] = field(default_factory=list)

    @property
    def completa(self) -> bool:
        return not self.faltantes


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

    def evaluar_sucursales(
        self,
        id_cliente: int,
        sucursales: list[tuple[Sucursal, float | None]],
    ) -> list[OpcionSucursal]:
        """Tell, for each branch, which cart products it cannot fully supply."""
        carrito = self._carrito.obtener_carrito(id_cliente)
        opciones: list[OpcionSucursal] = []
        for sucursal, distancia in sucursales:
            faltantes = [
                item.producto.nombre
                for item in carrito.items
                if not self._stock.hay_disponibilidad(
                    item.producto.id_producto, sucursal.id_sucursal, item.cantidad
                )
            ]
            opciones.append(OpcionSucursal(sucursal, distancia, faltantes))
        return opciones

    def confirmar(self, id_cliente: int, id_sucursal: int, pago: Pago) -> Compra:
        """Validate stock, charge, persist the purchase and empty the cart.

        All-or-nothing: stock is only given up together with a saved purchase;
        if saving fails the discounted units are put back.
        """
        with LOCK_ALMACEN:
            carrito = self._carrito.obtener_carrito(id_cliente)
            if not carrito.items:
                raise DatosInvalidosError("El carrito está vacío")

            self._validar_stock_de_la_sucursal(carrito, id_sucursal)

            resultado = pago.procesar_pago()
            if not resultado.aprobado:
                raise DatosInvalidosError(resultado.mensaje)

            compra = Compra.desde_carrito(0, id_cliente, id_sucursal, carrito, pago)
            compra.confirmar_compra()

            descontados: list[tuple[int, int]] = []
            try:
                for detalle in compra.detalles:
                    self._stock.descontar(detalle.id_producto, id_sucursal, detalle.cantidad)
                    descontados.append((detalle.id_producto, detalle.cantidad))
                guardada = self._compras.crear(compra)
            except Exception:
                for id_producto, cantidad in descontados:
                    self._stock.reponer(id_producto, id_sucursal, cantidad)
                raise

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
