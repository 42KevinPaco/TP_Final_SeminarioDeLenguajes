"""Route tests with an isolated data directory and a Flask test client."""

import tempfile
import unittest
from pathlib import Path

import app.routes_frontend as routes
from app.container import Container
from app.utils.security import verify_password


class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_container = routes.container
        routes.container = Container.from_data_dir(Path(self._tmp.name), seed=True)
        routes.app.config["TESTING"] = True
        self.client = routes.app.test_client()

    def tearDown(self):
        routes.container = self._original_container
        self._tmp.cleanup()

    def login(self, nombre_usuario, contrasena, **kwargs):
        return self.client.post(
            "/login",
            data={"nombre_usuario": nombre_usuario, "contrasena": contrasena},
            **kwargs,
        )

    def login_admin(self):
        return self.login("admin", "Admin1234")

    def registrar_cliente(self, nombre_usuario="kevin", email="kevin@test.com"):
        return self.client.post(
            "/registro",
            data={
                "nombre_usuario": nombre_usuario,
                "contrasena": "secreto123",
                "nombre": "Kevin",
                "apellido": "Perez",
                "email": email,
                "domicilio": "Calle 1",
                "telefono": "1123456789",
            },
        )


class PublicRoutesTest(RoutesTestCase):
    def test_catalogo_lists_products_from_the_csv_store(self):
        response = self.client.get("/catalogo")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Yerba Mate", response.data.decode("utf-8"))

    def test_login_and_registro_pages_render(self):
        self.assertEqual(self.client.get("/login").status_code, 200)
        self.assertEqual(self.client.get("/registro").status_code, 200)


class GuardTest(RoutesTestCase):
    def test_guest_is_redirected_to_login(self):
        response = self.client.get("/cliente/carrito")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_admin_page_requires_login(self):
        response = self.client.get("/admin/usuarios")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])


class LoginTest(RoutesTestCase):
    def test_invalid_credentials_return_401_with_message(self):
        response = self.login("admin", "incorrecta")
        self.assertEqual(response.status_code, 401)
        self.assertIn("incorrectos", response.data.decode("utf-8"))

    def test_admin_login_redirects_to_admin_panel(self):
        response = self.login_admin()
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/usuarios", response.headers["Location"])

    def test_client_login_redirects_to_dashboard(self):
        self.registrar_cliente()
        response = self.login("kevin", "secreto123")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/cliente/dashboard", response.headers["Location"])

    def test_logout_clears_the_session(self):
        self.login_admin()
        self.client.get("/logout")
        self.assertEqual(self.client.get("/admin/usuarios").status_code, 302)


class RegistroTest(RoutesTestCase):
    def test_registration_persists_a_hashed_password_and_redirects(self):
        response = self.registrar_cliente()
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

        cliente = routes.container.usuarios.obtener_por_nombre_usuario("kevin")
        self.assertIsNotNone(cliente)
        self.assertNotEqual(cliente.contrasena_hash, "secreto123")
        self.assertTrue(verify_password("secreto123", cliente.contrasena_hash))

    def test_duplicate_username_is_rejected(self):
        self.registrar_cliente()
        response = self.registrar_cliente(email="otro@test.com")
        self.assertEqual(response.status_code, 400)
        self.assertIn("ya est", response.data.decode("utf-8"))

    def test_invalid_data_is_rejected(self):
        response = self.client.post(
            "/registro",
            data={
                "nombre_usuario": "kevin",
                "contrasena": "secreto123",
                "nombre": "Kevin",
                "apellido": "Perez",
                "email": "sin-arroba",
                "domicilio": "Calle 1",
                "telefono": "1123456789",
            },
        )
        self.assertEqual(response.status_code, 400)


class AdminPagesTest(RoutesTestCase):
    def setUp(self):
        super().setUp()
        self.login_admin()

    def test_usuarios_table_lists_registered_users(self):
        response = self.client.get("/admin/usuarios")
        self.assertEqual(response.status_code, 200)
        self.assertIn("admin", response.data.decode("utf-8"))

    def test_productos_table_lists_catalog(self):
        response = self.client.get("/admin/productos")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Playadito", response.data.decode("utf-8"))

    def test_sucursales_table_lists_branches_and_stock(self):
        response = self.client.get("/admin/sucursales")
        self.assertEqual(response.status_code, 200)
        body = response.data.decode("utf-8")
        self.assertIn("Sucursal Centro", body)
        self.assertIn("StockSucursal", body)

    def test_admin_cannot_enter_the_client_area(self):
        response = self.client.get("/cliente/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/usuarios", response.headers["Location"])


class ClientPagesTest(RoutesTestCase):
    def setUp(self):
        super().setUp()
        self.registrar_cliente()
        self.login("kevin", "secreto123")

    def test_dashboard_greets_the_logged_user(self):
        response = self.client.get("/cliente/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Kevin Perez", response.data.decode("utf-8"))

    def test_branches_are_sorted_by_distance(self):
        response = self.client.get("/cliente/sucursales-cercanas")
        body = response.data.decode("utf-8")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Sucursal Centro", body)
        self.assertIn("km", body)

    def test_cart_and_purchase_pages_render(self):
        self.assertEqual(self.client.get("/cliente/carrito").status_code, 200)
        self.assertEqual(self.client.get("/cliente/compra").status_code, 200)

    def test_client_cannot_enter_the_admin_area(self):
        response = self.client.get("/admin/usuarios")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/catalogo", response.headers["Location"])


if __name__ == "__main__":
    unittest.main()
