"""Composition root.

Single place that decides which concrete repositories are used. Every service
receives the interfaces, so swapping CSV for SQL only changes this module.
"""

from pathlib import Path

from app.repository.csv_producto_repository import CsvProductoRepository
from app.repository.csv_stock_repository import CsvStockSucursalRepository
from app.repository.csv_sucursal_repository import CsvSucursalRepository
from app.repository.csv_usuario_repository import CsvUsuarioRepository
from app.repository.interfaces import (
    IProductoRepository,
    IStockSucursalRepository,
    ISucursalRepository,
    IUsuarioRepository,
)
from app.repository.seed import seed_data
from app.services.auth_service import AuthService
from app.services.producto_service import ProductoService
from app.services.stock_service import StockService
from app.services.sucursal_service import SucursalService


class Container:
    """Holds the wired repositories and services for one application context."""

    def __init__(
        self,
        usuario_repository: IUsuarioRepository | None = None,
        producto_repository: IProductoRepository | None = None,
        sucursal_repository: ISucursalRepository | None = None,
        stock_repository: IStockSucursalRepository | None = None,
    ) -> None:
        self.usuarios = usuario_repository or CsvUsuarioRepository()
        self.productos = producto_repository or CsvProductoRepository()
        self.sucursales = sucursal_repository or CsvSucursalRepository()
        self.stock = stock_repository or CsvStockSucursalRepository()

        self.auth_service = AuthService(self.usuarios)
        self.producto_service = ProductoService(self.productos)
        self.sucursal_service = SucursalService(self.sucursales)
        self.stock_service = StockService(self.stock)

    @classmethod
    def from_data_dir(cls, data_dir: Path, seed: bool = False) -> "Container":
        """Build the container over an alternate data directory (tests, demos)."""
        base = Path(data_dir)
        container = cls(
            usuario_repository=CsvUsuarioRepository(base / "usuarios.csv"),
            producto_repository=CsvProductoRepository(base / "productos.csv"),
            sucursal_repository=CsvSucursalRepository(base / "sucursales.csv"),
            stock_repository=CsvStockSucursalRepository(base / "stock.csv"),
        )
        if seed:
            seed_data(
                usuario_repo=container.usuarios,
                producto_repo=container.productos,
                sucursal_repo=container.sucursales,
                stock_repo=container.stock,
            )
        return container


def build_container() -> Container:
    """Production entry point: CSV store under `data/`, seeded once."""
    container = Container()
    seed_data(
        usuario_repo=container.usuarios,
        producto_repo=container.productos,
        sucursal_repo=container.sucursales,
        stock_repo=container.stock,
    )
    return container
