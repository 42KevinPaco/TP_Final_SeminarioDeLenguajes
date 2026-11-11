"""Repository contracts.

Each entity exposes a small, focused interface (Interface Segregation). Services
depend on these abstractions, never on a concrete storage (Dependency Inversion),
so a SQL implementation can replace the CSV one without touching business code
(Open/Closed).
"""

from abc import ABC, abstractmethod

from app.models.producto import Producto
from app.models.carrito import ItemCarrito
from app.models.compra import Compra
from app.models.sucursal import StockSucursal, Sucursal
from app.models.usuario import Usuario


class IUsuarioRepository(ABC):
    @abstractmethod
    def listar(self) -> list[Usuario]: ...

    @abstractmethod
    def obtener_por_id(self, id_usuario: int) -> Usuario | None: ...

    @abstractmethod
    def obtener_por_nombre_usuario(self, nombre_usuario: str) -> Usuario | None: ...

    @abstractmethod
    def existe_email(self, email: str) -> bool: ...

    @abstractmethod
    def crear(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def eliminar(self, id_usuario: int) -> None: ...


class IProductoRepository(ABC):
    @abstractmethod
    def listar(self) -> list[Producto]: ...

    @abstractmethod
    def obtener_por_id(self, id_producto: int) -> Producto | None: ...

    @abstractmethod
    def crear(self, producto: Producto) -> Producto: ...

    @abstractmethod
    def actualizar(self, producto: Producto) -> Producto: ...

    @abstractmethod
    def eliminar(self, id_producto: int) -> None: ...


class ISucursalRepository(ABC):
    @abstractmethod
    def listar(self) -> list[Sucursal]: ...

    @abstractmethod
    def obtener_por_id(self, id_sucursal: int) -> Sucursal | None: ...

    @abstractmethod
    def crear(self, sucursal: Sucursal) -> Sucursal: ...

    @abstractmethod
    def actualizar(self, sucursal: Sucursal) -> Sucursal: ...

    @abstractmethod
    def eliminar(self, id_sucursal: int) -> None: ...


class IStockSucursalRepository(ABC):
    @abstractmethod
    def listar(self) -> list[StockSucursal]: ...

    @abstractmethod
    def listar_por_sucursal(self, id_sucursal: int) -> list[StockSucursal]: ...

    @abstractmethod
    def listar_por_producto(self, id_producto: int) -> list[StockSucursal]: ...

    @abstractmethod
    def obtener(self, id_producto: int, id_sucursal: int) -> StockSucursal | None: ...

    @abstractmethod
    def crear(self, stock: StockSucursal) -> StockSucursal: ...

    @abstractmethod
    def actualizar(self, stock: StockSucursal) -> StockSucursal: ...

    @abstractmethod
    def eliminar_por_producto(self, id_producto: int) -> None: ...

    @abstractmethod
    def eliminar_por_sucursal(self, id_sucursal: int) -> None: ...


class ICarritoRepository(ABC):
    """Persistence contract for one customer's cart lines."""

    @abstractmethod
    def listar_por_usuario(self, id_usuario: int) -> list[ItemCarrito]: ...

    @abstractmethod
    def obtener_item(self, id_usuario: int, id_producto: int) -> ItemCarrito | None: ...

    @abstractmethod
    def agregar(self, id_usuario: int, item: ItemCarrito) -> ItemCarrito: ...

    @abstractmethod
    def actualizar(self, id_usuario: int, item: ItemCarrito) -> ItemCarrito: ...

    @abstractmethod
    def eliminar(self, id_usuario: int, id_producto: int) -> None: ...

    @abstractmethod
    def vaciar(self, id_usuario: int) -> None: ...

    @abstractmethod
    def contar_unidades(self, id_usuario: int) -> int: ...


class ICompraRepository(ABC):
    """Persistence contract for confirmed purchases and their lines."""

    @abstractmethod
    def crear(self, compra: Compra) -> Compra: ...

    @abstractmethod
    def obtener_por_id(self, id_compra: int) -> Compra | None: ...

    @abstractmethod
    def listar_por_cliente(self, id_cliente: int) -> list[Compra]: ...
