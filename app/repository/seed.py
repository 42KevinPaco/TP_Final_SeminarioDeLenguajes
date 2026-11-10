"""Initial data for the CSV store.

Seeds exactly once (when a file is still missing or empty). The administrator is
pre-registered here: there is no self-registration form for that role.
"""

from app.models.producto import Producto
from app.models.sucursal import StockSucursal, Sucursal
from app.models.usuario import Administrador
from app.repository.interfaces import (
    IProductoRepository,
    IStockSucursalRepository,
    ISucursalRepository,
    IUsuarioRepository,
)
from app.repository.csv_producto_repository import CsvProductoRepository
from app.repository.csv_stock_repository import CsvStockSucursalRepository
from app.repository.csv_sucursal_repository import CsvSucursalRepository
from app.repository.csv_usuario_repository import CsvUsuarioRepository
from app.utils.security import hash_password

ADMIN_NOMBRE_USUARIO = "admin"
ADMIN_PASSWORD_INICIAL = "Admin1234"

PRODUCTOS_INICIALES = [
    ("Leche Entera", "Leche entera pasteurizada 1L", 150.00, "La Serenísima"),
    ("Pan Lactal", "Pan lactal blanco 500g", 200.00, "Bimbo"),
    ("Arroz", "Arroz largo fino 1kg", 120.00, "Gallo"),
    ("Yerba Mate", "Yerba mate elaborada con palo 1kg", 950.00, "Playadito"),
    ("Aceite de Girasol", "Aceite de girasol 1.5L", 780.00, "Natura"),
]

SUCURSALES_INICIALES = [
    ("Sucursal Centro", "Av. Principal 123", -34.6037, -58.3816),
    ("Sucursal Norte", "Calle Norte 456", -34.5950, -58.3800),
    ("Sucursal Sur", "Av. Sur 789", -34.6200, -58.4000),
]

STOCK_INICIAL = [
    (1, 1, 50),
    (2, 1, 30),
    (3, 1, 40),
    (4, 1, 25),
    (5, 1, 20),
    (1, 2, 20),
    (2, 2, 15),
    (3, 3, 35),
]


def seed_data(
    usuario_repo: IUsuarioRepository | None = None,
    producto_repo: IProductoRepository | None = None,
    sucursal_repo: ISucursalRepository | None = None,
    stock_repo: IStockSucursalRepository | None = None,
) -> None:
    """Populate each table only when it is still empty."""
    usuario_repo = usuario_repo or CsvUsuarioRepository()
    producto_repo = producto_repo or CsvProductoRepository()
    sucursal_repo = sucursal_repo or CsvSucursalRepository()
    stock_repo = stock_repo or CsvStockSucursalRepository()

    if not usuario_repo.listar():
        usuario_repo.crear(
            Administrador(
                id_usuario=0,
                nombre_usuario=ADMIN_NOMBRE_USUARIO,
                contrasena_hash=hash_password(ADMIN_PASSWORD_INICIAL),
                nombre="Administrador",
                apellido="General",
                email="admin@supermercado.local",
            )
        )

    if not producto_repo.listar():
        for nombre, descripcion, precio, marca in PRODUCTOS_INICIALES:
            producto_repo.crear(
                Producto(
                    id_producto=0,
                    nombre=nombre,
                    descripcion=descripcion,
                    precio=precio,
                    marca=marca,
                )
            )

    if not sucursal_repo.listar():
        for nombre, direccion, latitud, longitud in SUCURSALES_INICIALES:
            sucursal_repo.crear(
                Sucursal(
                    id_sucursal=0,
                    nombre=nombre,
                    direccion=direccion,
                    latitud=latitud,
                    longitud=longitud,
                )
            )

    if not stock_repo.listar():
        for id_producto, id_sucursal, cantidad in STOCK_INICIAL:
            stock_repo.crear(
                StockSucursal(
                    id_stock=0,
                    id_producto=id_producto,
                    id_sucursal=id_sucursal,
                    cantidad_disponible=cantidad,
                )
            )
