"""Admin CRUD route tests (products, branches and stock)."""

import tempfile
import unittest
from pathlib import Path

import app.routes_frontend as routes
from app.container import Container


class AdminCrudTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self._original_container = routes.container
        routes.container = Container.from_data_dir(self.data_dir, seed=True)
        routes.app.config["TESTING"] = True
        self.client = routes.app.test_client()
        self.login_admin()

    def tearDown(self):
        routes.container = self._original_container
        self._tmp.cleanup()

    def login_admin(self):
        self.client.post(
            "/login",
            data={"nombre_usuario": "admin", "contrasena": "Admin1234"},
        )


class ProductoCrudTest(AdminCrudTestCase):
    def test_agregar_producto_persiste_y_aparece_en_la_tabla(self):
        respuesta = self.client.post(
            "/admin/productos/nuevo",
            data={
                "nombre": "Dulce de Leche",
                "descripcion": "Dulce de leche repostero 500g",
                "precio": "890.50",
                "marca": "La Salamandra",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/admin/productos", respuesta.headers["Location"])

        nombres = [p.nombre for p in routes.container.producto_service.listar()]
        self.assertIn("Dulce de Leche", nombres)
        self.assertIn("Dulce de Leche", self.client.get("/admin/productos").data.decode("utf-8"))

    def test_agregar_producto_invalido_no_persiste(self):
        respuesta = self.client.post(
            "/admin/productos/nuevo",
            data={"nombre": "X", "descripcion": "Y", "precio": "caro", "marca": "Z"},
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(len(routes.container.producto_service.listar()), 5)

    def test_formulario_de_modificacion_prefill_y_guarda(self):
        formulario = self.client.get("/admin/productos/1/modificar")
        self.assertEqual(formulario.status_code, 200)
        self.assertIn('value="Leche Entera"', formulario.data.decode("utf-8"))

        respuesta = self.client.post(
            "/admin/productos/1/modificar",
            data={
                "nombre": "Leche Descremada",
                "descripcion": "Leche descremada 1L",
                "precio": "160",
                "marca": "La Serenísima",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        producto = routes.container.producto_service.obtener(1)
        self.assertEqual(producto.nombre, "Leche Descremada")
        self.assertEqual(producto.precio, 160.0)

    def test_modificar_producto_inexistente_redirige(self):
        respuesta = self.client.get("/admin/productos/999/modificar")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/admin/productos", respuesta.headers["Location"])

    def test_eliminar_producto_borra_tambien_su_stock(self):
        routes.container.producto_service.crear(
            nombre="Cerveza Artesanal",
            descripcion="Cerveza rubia 1L",
            precio=450,
            marca="Local",
        )
        routes.container.stock_service.asignar(6, 1, 10)

        respuesta = self.client.post("/admin/productos/6/eliminar")

        self.assertEqual(respuesta.status_code, 302)
        self.assertNotIn(6, [p.id_producto for p in routes.container.producto_service.listar()])
        self.assertEqual(routes.container.stock_service.listar_por_producto(6), [])
        self.assertNotIn("Cerveza Artesanal", self.client.get("/admin/productos").data.decode("utf-8"))

    def test_anonimo_no_puede_entrar_al_crud(self):
        anonimo = routes.app.test_client()
        respuesta = anonimo.get("/admin/productos/nuevo")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/login", respuesta.headers["Location"])


class SucursalCrudTest(AdminCrudTestCase):
    def test_agregar_sucursal_persiste(self):
        respuesta = self.client.post(
            "/admin/sucursales/nueva",
            data={
                "nombre": "Sucursal Oeste",
                "direccion": "Av. Oeste 1010",
                "latitud": "-34.6100",
                "longitud": "-58.5000",
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        sucursal = routes.container.sucursal_service.obtener(4)
        self.assertEqual(sucursal.nombre, "Sucursal Oeste")

    def test_coordenada_invalida_no_persiste(self):
        respuesta = self.client.post(
            "/admin/sucursales/nueva",
            data={"nombre": "Mala", "direccion": "Dir", "latitud": "-200", "longitud": "0"},
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(len(routes.container.sucursal_service.listar()), 3)

    def test_modificar_sucursal(self):
        formulario = self.client.get("/admin/sucursales/1/modificar")
        self.assertEqual(formulario.status_code, 200)
        self.assertIn('value="Sucursal Centro"', formulario.data.decode("utf-8"))

        respuesta = self.client.post(
            "/admin/sucursales/1/modificar",
            data={"nombre": "Sucursal Centro Renovada", "direccion": "Av. Principal 999",
                  "latitud": "-34.6037", "longitud": "-58.3816"},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(
            routes.container.sucursal_service.obtener(1).nombre,
            "Sucursal Centro Renovada",
        )

    def test_eliminar_sucursal_borra_tambien_su_stock(self):
        routes.container.sucursal_service.crear(
            nombre="Sucursal Este", direccion="Av. Este 22", latitud=-34.61, longitud=-58.36
        )
        routes.container.stock_service.asignar(1, 4, 8)

        respuesta = self.client.post("/admin/sucursales/4/eliminar")

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(routes.container.stock_service.listar_por_sucursal(4), [])

    def test_eliminar_sucursal_inexistente_no_revienta(self):
        respuesta = self.client.post("/admin/sucursales/999/eliminar")
        self.assertEqual(respuesta.status_code, 302)


class StockCrudTest(AdminCrudTestCase):
    def test_formulario_de_asignacion_renderiza(self):
        respuesta = self.client.get("/admin/stock/asignar")
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.data.decode("utf-8")
        self.assertIn("Yerba Mate", cuerpo)
        self.assertIn("Sucursal Norte", cuerpo)

    def test_asignar_stock_crea_y_luego_reemplaza(self):
        respuesta = self.client.post(
            "/admin/stock/asignar",
            data={"id_producto": "1", "id_sucursal": "3", "cantidad": "12"},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(routes.container.stock_service.obtener(1, 3).cantidad_disponible, 12)

        self.client.post(
            "/admin/stock/asignar",
            data={"id_producto": "1", "id_sucursal": "3", "cantidad": "7"},
        )
        self.assertEqual(routes.container.stock_service.obtener(1, 3).cantidad_disponible, 7)

    def test_asignar_stock_invalido_no_persiste(self):
        respuesta = self.client.post(
            "/admin/stock/asignar",
            data={"id_producto": "1", "id_sucursal": "3", "cantidad": "-5"},
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(
            [s for s in routes.container.stock_service.listar() if s.id_producto == 1 and s.id_sucursal == 3],
            [],
        )

    def test_actualizar_stock_permite_cero_y_rechaza_basura(self):
        routes.container.stock_service.asignar(1, 3, 9)

        respuesta = self.client.post("/admin/stock/9/actualizar", data={"cantidad": "0"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(routes.container.stock_service.obtener(1, 3).cantidad_disponible, 0)

        respuesta = self.client.post("/admin/stock/9/actualizar", data={"cantidad": "mucho"})
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(routes.container.stock_service.obtener(1, 3).cantidad_disponible, 0)

    def test_actualizar_stock_inexistente_redirige(self):
        respuesta = self.client.post("/admin/stock/999/actualizar", data={"cantidad": "3"})
        self.assertEqual(respuesta.status_code, 302)


if __name__ == "__main__":
    unittest.main()
