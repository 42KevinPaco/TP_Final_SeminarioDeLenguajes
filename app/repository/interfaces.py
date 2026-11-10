"""Repository contracts.

Each entity exposes a small, focused interface (Interface Segregation). Services
depend on these abstractions, never on a concrete storage (Dependency Inversion),
so a SQL implementation can replace the CSV one without touching business code
(Open/Closed).
"""

from abc import ABC, abstractmethod

from app.models.producto import Producto
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
