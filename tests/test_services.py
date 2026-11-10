"""Service-level tests over temporary data directories."""

import tempfile
import unittest
from pathlib import Path

from app.container import Container
from app.utils.exceptions import (
    CredencialesInvalidasError,
    DatosInvalidosError,
    RecursoNoEncontradoError,
    StockInsuficienteError,
    UsuarioDuplicadoError,
)
from app.utils.security import verify_password


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.container = Container.from_data_dir(Path(self._tmp.name), seed=True)

    def tearDown(self):
        self._tmp.cleanup()


class AuthServiceTest(ServiceTestCase):
    def registrar_kevin(self, **overrides):
        datos = {
            "nombre_usuario": "kevin",
            "contrasena": "secreto123",
            "nombre": "Kevin",
            "apellido": "Perez",
            "email": "kevin@test.com",
            "domicilio": "Calle 1",
            "telefono": "1123456789",
        }
        datos.update(overrides)
        return self.container.auth_service.registrar_cliente(**datos)

    def test_seeded_admin_can_log_in(self):
        usuario = self.container.auth_service.autenticar("admin", "Admin1234")
        self.assertEqual(usuario.rol, "administrador")

    def test_registration_stores_a_hash_not_the_plain_password(self):
        cliente = self.registrar_kevin()
        self.assertNotEqual(cliente.contrasena_hash, "secreto123")
        self.assertTrue(verify_password("secreto123", cliente.contrasena_hash))

        recuperado = self.container.auth_service.autenticar("kevin", "secreto123")
        self.assertEqual(recuperado.id_usuario, cliente.id_usuario)

    def test_wrong_password_is_rejected(self):
        self.registrar_kevin()
        with self.assertRaises(CredencialesInvalidasError):
            self.container.auth_service.autenticar("kevin", "otra-clave")

    def test_unknown_user_is_rejected(self):
        with self.assertRaises(CredencialesInvalidasError):
            self.container.auth_service.autenticar("nadie", "secreto123")

    def test_duplicate_username_is_rejected(self):
        self.registrar_kevin()
        with self.assertRaises(UsuarioDuplicadoError):
            self.registrar_kevin(email="otro@test.com")

    def test_duplicate_email_is_rejected(self):
        self.registrar_kevin()
        with self.assertRaises(UsuarioDuplicadoError):
            self.registrar_kevin(nombre_usuario="ana")

    def test_invalid_email_is_rejected(self):
        with self.assertRaises(DatosInvalidosError):
            self.registrar_kevin(email="sin-arroba")

    def test_invalid_phone_is_rejected(self):
        with self.assertRaises(DatosInvalidosError):
            self.registrar_kevin(telefono="123")

    def test_short_password_is_rejected(self):
        with self.assertRaises(DatosInvalidosError):
            self.registrar_kevin(contrasena="ab")

    def test_registration_never_creates_an_administrator(self):
        cliente = self.registrar_kevin()
        self.assertEqual(cliente.rol, "cliente")


class ProductoServiceTest(ServiceTestCase):
    def test_seeded_catalog_is_listed(self):
        productos = self.container.producto_service.listar()
        self.assertEqual(len(productos), 5)

    def test_create_and_read_product(self):
        creado = self.container.producto_service.crear("Fideos", "500g", 350.0, "Matarazzo")
        recuperado = self.container.producto_service.obtener(creado.id_producto)
        self.assertEqual(recuperado.nombre, "Fideos")

    def test_invalid_price_is_rejected(self):
        with self.assertRaises(DatosInvalidosError):
            self.container.producto_service.crear("Fideos", "500g", 0, "Matarazzo")

    def test_update_and_delete_product(self):
        creado = self.container.producto_service.crear("Fideos", "500g", 350.0, "Matarazzo")
        actualizado = self.container.producto_service.actualizar(
            creado.id_producto, "Fideos", "1kg", 700.0, "Matarazzo"
        )
        self.assertEqual(actualizado.precio, 700.0)

        self.container.producto_service.eliminar(creado.id_producto)
        with self.assertRaises(RecursoNoEncontradoError):
            self.container.producto_service.obtener(creado.id_producto)


class SucursalServiceTest(ServiceTestCase):
    def test_listar_por_cercania_orders_by_distance(self):
        cercanas = self.container.sucursal_service.listar_por_cercania(-34.6037, -58.3816)
        self.assertEqual(cercanas[0][0].nombre, "Sucursal Centro")
        distancias = [distancia for _, distancia in cercanas]
        self.assertEqual(distancias, sorted(distancias))

    def test_create_branch(self):
        creada = self.container.sucursal_service.crear("Oeste", "Calle Oeste 1", -34.61, -58.45)
        self.assertIsNotNone(self.container.sucursal_service.obtener(creada.id_sucursal))

    def test_invalid_coordinate_is_rejected(self):
        with self.assertRaises(DatosInvalidosError):
            self.container.sucursal_service.crear("Oeste", "Calle Oeste 1", -200, -58.45)

    def test_unknown_branch_raises(self):
        with self.assertRaises(RecursoNoEncontradoError):
            self.container.sucursal_service.obtener(999)


class StockServiceTest(ServiceTestCase):
    def test_asignar_creates_then_updates_the_same_row(self):
        creado = self.container.stock_service.asignar(1, 3, 10)
        actualizado = self.container.stock_service.asignar(1, 3, 25)

        self.assertEqual(creado.id_stock, actualizado.id_stock)
        self.assertEqual(self.container.stock_service.obtener(1, 3).cantidad_disponible, 25)

    def test_descontar_reduces_available_quantity(self):
        stock = self.container.stock_service.obtener(1, 1)
        esperado = stock.cantidad_disponible - 5

        self.container.stock_service.descontar(1, 1, 5)

        self.assertEqual(self.container.stock_service.obtener(1, 1).cantidad_disponible, esperado)

    def test_descontar_rejects_insufficient_stock(self):
        self.container.stock_service.asignar(1, 3, 2)
        with self.assertRaises(StockInsuficienteError):
            self.container.stock_service.descontar(1, 3, 5)

    def test_missing_stock_raises(self):
        with self.assertRaises(RecursoNoEncontradoError):
            self.container.stock_service.obtener(999, 999)

    def test_hay_disponibilidad(self):
        self.assertTrue(self.container.stock_service.hay_disponibilidad(1, 1, 1))
        self.assertFalse(self.container.stock_service.hay_disponibilidad(1, 1, 9999))


if __name__ == "__main__":
    unittest.main()
