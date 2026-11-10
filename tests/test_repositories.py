"""CSV repository round-trip tests over temporary directories."""

import tempfile
import unittest
from pathlib import Path

from app.models.producto import Producto
from app.models.sucursal import StockSucursal, Sucursal
from app.models.usuario import Administrador, Cliente
from app.repository.csv_producto_repository import CsvProductoRepository
from app.repository.csv_stock_repository import CsvStockSucursalRepository
from app.repository.csv_sucursal_repository import CsvSucursalRepository
from app.repository.csv_usuario_repository import CsvUsuarioRepository


class RepositoryTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


class UsuarioRepositoryTest(RepositoryTestCase):
    def setUp(self):
        super().setUp()
        self.repo = CsvUsuarioRepository(self.data_dir / "usuarios.csv")

    def make_cliente(self, nombre_usuario="kevin", email="kevin@test.com") -> Cliente:
        return Cliente(
            id_usuario=0,
            nombre_usuario=nombre_usuario,
            contrasena_hash="hash",
            nombre="Kevin",
            apellido="Perez",
            email=email,
            domicilio="Calle 1",
            telefono="1123456789",
        )

    def test_crear_assigns_sequential_ids(self):
        primero = self.repo.crear(self.make_cliente("kevin", "kevin@test.com"))
        segundo = self.repo.crear(self.make_cliente("ana", "ana@test.com"))
        self.assertEqual(primero.id_usuario, 1)
        self.assertEqual(segundo.id_usuario, 2)

    def test_round_trip_preserves_client_fields(self):
        creado = self.repo.crear(self.make_cliente())
        recuperado = self.repo.obtener_por_nombre_usuario("kevin")

        self.assertIsInstance(recuperado, Cliente)
        self.assertEqual(recuperado.id_usuario, creado.id_usuario)
        self.assertEqual(recuperado.domicilio, "Calle 1")
        self.assertEqual(recuperado.telefono, "1123456789")

    def test_username_lookup_is_case_insensitive(self):
        self.repo.crear(self.make_cliente("Kevin"))
        self.assertIsNotNone(self.repo.obtener_por_nombre_usuario("KEVIN"))

    def test_administrador_is_rebuilt_with_its_role(self):
        self.repo.crear(
            Administrador(
                id_usuario=0,
                nombre_usuario="admin",
                contrasena_hash="hash",
                nombre="Admin",
                apellido="General",
                email="admin@test.com",
            )
        )
        recuperado = self.repo.obtener_por_nombre_usuario("admin")
        self.assertIsInstance(recuperado, Administrador)
        self.assertEqual(recuperado.rol, "administrador")

    def test_existe_email(self):
        self.repo.crear(self.make_cliente())
        self.assertTrue(self.repo.existe_email("KEVIN@test.com"))
        self.assertFalse(self.repo.existe_email("nadie@test.com"))

    def test_actualizar_and_eliminar(self):
        creado = self.repo.crear(self.make_cliente())
        creado.domicilio = "Calle 2"
        self.repo.actualizar(creado)
        self.assertEqual(self.repo.obtener_por_id(creado.id_usuario).domicilio, "Calle 2")

        self.repo.eliminar(creado.id_usuario)
        self.assertIsNone(self.repo.obtener_por_id(creado.id_usuario))
        self.assertEqual(self.repo.listar(), [])


class ProductoRepositoryTest(RepositoryTestCase):
    def setUp(self):
        super().setUp()
        self.repo = CsvProductoRepository(self.data_dir / "productos.csv")

    def test_round_trip_preserves_price(self):
        creado = self.repo.crear(Producto(0, "Yerba", "1kg", 950.5, "Playadito"))
        recuperado = self.repo.obtener_por_id(creado.id_producto)
        self.assertEqual(recuperado.precio, 950.5)
        self.assertEqual(recuperado.marca, "Playadito")

    def test_actualizar_and_eliminar(self):
        creado = self.repo.crear(Producto(0, "Yerba", "1kg", 950.0, "Playadito"))
        creado.precio = 1000.0
        self.repo.actualizar(creado)
        self.assertEqual(self.repo.obtener_por_id(creado.id_producto).precio, 1000.0)

        self.repo.eliminar(creado.id_producto)
        self.assertEqual(self.repo.listar(), [])


class StockRepositoryTest(RepositoryTestCase):
    def setUp(self):
        super().setUp()
        self.repo = CsvStockSucursalRepository(self.data_dir / "stock.csv")

    def test_create_and_query_by_product_and_branch(self):
        creado = self.repo.crear(StockSucursal(0, 1, 2, 10))
        self.assertEqual(self.repo.obtener(1, 2).id_stock, creado.id_stock)
        self.assertEqual(len(self.repo.listar_por_producto(1)), 1)
        self.assertEqual(len(self.repo.listar_por_sucursal(2)), 1)

    def test_actualizar_quantity(self):
        creado = self.repo.crear(StockSucursal(0, 1, 1, 10))
        creado.cantidad_disponible = 4
        self.repo.actualizar(creado)
        self.assertEqual(self.repo.obtener(1, 1).cantidad_disponible, 4)


class SucursalRepositoryTest(RepositoryTestCase):
    def setUp(self):
        super().setUp()
        self.repo = CsvSucursalRepository(self.data_dir / "sucursales.csv")

    def test_round_trip_preserves_coordinates(self):
        creado = self.repo.crear(Sucursal(0, "Centro", "Av 1", -34.6037, -58.3816))
        recuperado = self.repo.obtener_por_id(creado.id_sucursal)
        self.assertAlmostEqual(recuperado.latitud, -34.6037, places=6)
        self.assertAlmostEqual(recuperado.longitud, -58.3816, places=6)


if __name__ == "__main__":
    unittest.main()
