"""Cart, catalog filtering and purchase tests (services and routes)."""

import tempfile
import unittest
from pathlib import Path

import app.routes_frontend as routes
from app.container import Container
from app.models.pago import PagoCredito, PagoEfectivo
from app.utils.exceptions import DatosInvalidosError, StockInsuficienteError


def _datos_cliente(**overrides):
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
    return datos


class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.container = Container.from_data_dir(self.data_dir, seed=True)

    def tearDown(self):
        self._tmp.cleanup()

    def nuevo_cliente(self) -> int:
        cliente = self.container.auth_service.registrar_cliente(**_datos_cliente())
        return cliente.id_usuario


class CatalogoServiceTest(ServiceTestCase):
    def test_producto_sin_stock_no_aparece_en_el_catalogo_del_cliente(self):
        self.container.producto_service.crear(
            nombre="Producto Fantasma",
            descripcion="Sin stock en ninguna sucursal",
            precio=100,
            marca="Generica",
        )

        disponibles = [p.nombre for p in self.container.catalogo_service.listar_disponibles()]

        self.assertNotIn("Producto Fantasma", disponibles)
        self.assertIn("Yerba Mate", disponibles)
        self.assertEqual(len(disponibles), 5)

    def test_el_panel_admin_sigue_listando_todos_los_productos(self):
        self.container.producto_service.crear(
            nombre="Producto Fantasma",
            descripcion="Sin stock en ninguna sucursal",
            precio=100,
            marca="Generica",
        )

        nombres = [p.nombre for p in self.container.producto_service.listar()]

        self.assertIn("Producto Fantasma", nombres)


class CarritoServiceTest(ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.id_cliente = self.nuevo_cliente()

    def test_agregar_persiste_en_csv_y_sobrevive_al_refresco(self):
        self.container.carrito_service.agregar(self.id_cliente, 1, 2)

        self.assertTrue((self.data_dir / "carrito.csv").exists())

        # Un contenedor nuevo sobre el mismo directorio simula un refresh/restart.
        recargado = Container.from_data_dir(self.data_dir)
        self.assertEqual(recargado.carrito_service.contar_unidades(self.id_cliente), 2)

    def test_agregar_el_mismo_producto_fusiona_la_linea(self):
        self.container.carrito_service.agregar(self.id_cliente, 1, 1)
        carrito = self.container.carrito_service.agregar(self.id_cliente, 1, 2)

        self.assertEqual(len(carrito.items), 1)
        self.assertEqual(carrito.items[0].cantidad, 3)

    def test_agregar_mas_que_el_stock_total_falla(self):
        with self.assertRaises(StockInsuficienteError):
            self.container.carrito_service.agregar(self.id_cliente, 5, 21)
        self.assertEqual(self.container.carrito_service.contar_unidades(self.id_cliente), 0)

    def test_agregar_producto_sin_stock_falla(self):
        producto = self.container.producto_service.crear(
            nombre="Producto Fantasma",
            descripcion="Sin stock en ninguna sucursal",
            precio=100,
            marca="Generica",
        )

        with self.assertRaises(StockInsuficienteError):
            self.container.carrito_service.agregar(self.id_cliente, producto.id_producto, 1)

    def test_actualizar_y_eliminar_validan_las_lineas(self):
        self.container.carrito_service.agregar(self.id_cliente, 1, 1)

        carrito = self.container.carrito_service.actualizar_cantidad(self.id_cliente, 1, 4)
        self.assertEqual(carrito.items[0].cantidad, 4)

        with self.assertRaises(StockInsuficienteError):
            self.container.carrito_service.actualizar_cantidad(self.id_cliente, 1, 71)

        carrito = self.container.carrito_service.eliminar(self.id_cliente, 1)
        self.assertEqual(carrito.items, [])
        self.assertEqual(self.container.carrito_service.contar_unidades(self.id_cliente), 0)

    def test_vaciar_borra_solo_el_carrito_del_cliente(self):
        otro = self.container.auth_service.registrar_cliente(
            **_datos_cliente(nombre_usuario="ana", email="ana@test.com")
        )
        self.container.carrito_service.agregar(self.id_cliente, 1, 1)
        self.container.carrito_service.agregar(otro.id_usuario, 2, 1)

        self.container.carrito_service.vaciar(self.id_cliente)

        self.assertEqual(self.container.carrito_service.contar_unidades(self.id_cliente), 0)
        self.assertEqual(self.container.carrito_service.contar_unidades(otro.id_usuario), 1)


class CompraServiceTest(ServiceTestCase):
    def setUp(self):
        super().setUp()
        self.id_cliente = self.nuevo_cliente()

    def test_confirmar_persiste_descuenta_stock_y_vacia_el_carrito(self):
        self.container.carrito_service.agregar(self.id_cliente, 1, 2)
        pago = PagoEfectivo(id_pago=0, importe=300.0, monto_recibido=500.0)

        compra = self.container.compra_service.confirmar(self.id_cliente, 1, pago)

        self.assertGreater(compra.id_compra, 0)
        self.assertEqual(compra.estado, "confirmada")
        self.assertEqual(compra.total, 300.0)
        self.assertEqual(len(compra.detalles), 1)
        self.assertEqual(
            self.container.stock_service.obtener(1, 1).cantidad_disponible, 48
        )
        self.assertEqual(self.container.carrito_service.contar_unidades(self.id_cliente), 0)

        compras = self.container.compra_service.listar_por_cliente(self.id_cliente)
        self.assertEqual(len(compras), 1)
        self.assertEqual(compras[0].id_compra, compra.id_compra)
        self.assertTrue((self.data_dir / "compras.csv").exists())
        self.assertTrue((self.data_dir / "compra_detalles.csv").exists())

    def test_no_persiste_datos_de_tarjeta_solo_el_metodo(self):
        self.container.carrito_service.agregar(self.id_cliente, 1, 1)
        pago = PagoCredito(
            id_pago=0,
            importe=150.0,
            numero_tarjeta="4111111111111111",
            titular="Kevin Perez",
            vencimiento="12/30",
            cvv="123",
            cuotas=3,
        )

        self.container.compra_service.confirmar(self.id_cliente, 1, pago)

        contenido = (self.data_dir / "compras.csv").read_text(encoding="utf-8")
        self.assertIn("credito", contenido)
        self.assertNotIn("4111", contenido)
        self.assertNotIn("123", contenido)

    def test_rechaza_stock_insuficiente_en_la_sucursal_elegida(self):
        # El producto 5 sólo tiene stock en la sucursal 1.
        self.container.carrito_service.agregar(self.id_cliente, 5, 5)
        pago = PagoEfectivo(id_pago=0, importe=3900.0, monto_recibido=5000.0)

        with self.assertRaises(StockInsuficienteError):
            self.container.compra_service.confirmar(self.id_cliente, 2, pago)

        self.assertEqual(self.container.carrito_service.contar_unidades(self.id_cliente), 5)
        self.assertEqual(self.container.compra_service.listar_por_cliente(self.id_cliente), [])

    def test_pago_rechazado_no_persiste_ni_vacia_el_carrito(self):
        self.container.carrito_service.agregar(self.id_cliente, 1, 1)
        pago = PagoEfectivo(id_pago=0, importe=150.0, monto_recibido=100.0)

        with self.assertRaises(DatosInvalidosError):
            self.container.compra_service.confirmar(self.id_cliente, 1, pago)

        self.assertEqual(self.container.carrito_service.contar_unidades(self.id_cliente), 1)
        self.assertEqual(self.container.compra_service.listar_por_cliente(self.id_cliente), [])


class CartRoutesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self._original_container = routes.container
        routes.container = Container.from_data_dir(self.data_dir, seed=True)
        routes.app.config["TESTING"] = True
        self.client = routes.app.test_client()

        self.client.post("/registro", data=_datos_cliente())
        self.client.post(
            "/login",
            data={"nombre_usuario": "kevin", "contrasena": "secreto123"},
        )
        with self.client.session_transaction() as sesion:
            self.id_cliente = sesion["id_usuario"]

    def tearDown(self):
        routes.container = self._original_container
        self._tmp.cleanup()

    def test_agregar_por_ajax_responde_json_sin_redirigir(self):
        respuesta = self.client.post(
            "/carrito/agregar",
            json={"id_producto": 1, "cantidad": 2},
        )

        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.get_json()
        self.assertTrue(datos["ok"])
        self.assertEqual(datos["cantidad_total"], 2)
        self.assertEqual(datos["total"], 300.0)
        self.assertEqual(respuesta.headers.get("Location"), None)

    def test_agregar_sin_sesion_devuelve_401_json(self):
        anonimo = routes.app.test_client()

        respuesta = anonimo.post("/carrito/agregar", json={"id_producto": 1, "cantidad": 1})

        self.assertEqual(respuesta.status_code, 401)
        self.assertFalse(respuesta.get_json()["ok"])

    def test_stock_insuficiente_devuelve_400_con_mensaje(self):
        respuesta = self.client.post(
            "/carrito/agregar",
            json={"id_producto": 5, "cantidad": 21},
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertFalse(respuesta.get_json()["ok"])
        self.assertIn("unidad", respuesta.get_json()["mensaje"])

    def test_carrito_persiste_entre_requests_y_muestra_el_contador(self):
        self.client.post("/carrito/agregar", json={"id_producto": 1, "cantidad": 2})

        carrito = self.client.get("/cliente/carrito")
        catalogo = self.client.get("/catalogo")

        self.assertEqual(carrito.status_code, 200)
        self.assertIn("Leche Entera", carrito.data.decode("utf-8"))
        self.assertIn("$ 300.00", carrito.data.decode("utf-8"))
        self.assertIn("js-carrito-contador", catalogo.data.decode("utf-8"))

    def test_compra_confirma_vacia_el_carrito_y_redirige(self):
        self.client.post("/carrito/agregar", json={"id_producto": 1, "cantidad": 1})

        respuesta = self.client.post(
            "/cliente/compra",
            data={"sucursal": "1", "metodoPago": "efectivo", "monto_recibido": "500"},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/cliente/dashboard", respuesta.headers["Location"])
        self.assertEqual(routes.container.carrito_service.contar_unidades(self.id_cliente), 0)
        self.assertEqual(routes.container.stock_service.obtener(1, 1).cantidad_disponible, 49)
        self.assertEqual(len(routes.container.compra_service.listar_por_cliente(self.id_cliente)), 1)

    def test_compra_con_pago_insuficiente_vuelve_a_mostrar_el_formulario(self):
        self.client.post("/carrito/agregar", json={"id_producto": 1, "cantidad": 1})

        respuesta = self.client.post(
            "/cliente/compra",
            data={"sucursal": "1", "metodoPago": "efectivo", "monto_recibido": "10"},
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(routes.container.carrito_service.contar_unidades(self.id_cliente), 1)

    def test_compra_sin_metodo_de_pago_es_rechazada(self):
        self.client.post("/carrito/agregar", json={"id_producto": 1, "cantidad": 1})

        respuesta = self.client.post("/cliente/compra", data={"sucursal": "1"})

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(routes.container.carrito_service.contar_unidades(self.id_cliente), 1)


if __name__ == "__main__":
    unittest.main()
