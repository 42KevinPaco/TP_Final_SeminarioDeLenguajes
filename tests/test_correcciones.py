"""Regression tests for the fixes made after reviewing the project against the brief."""

import re
import tempfile
import unittest
from pathlib import Path

import app.routes_frontend as routes
from app.container import Container
from app.models.pago import MAX_CUOTAS, PagoCredito, PagoEfectivo
from app.utils import geo
from app.utils.exceptions import DatosInvalidosError


class BaseRutas(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._contenedor_original = routes.container
        routes.container = Container.from_data_dir(Path(self._tmp.name), seed=True)
        routes.app.config["TESTING"] = True
        routes.app.config.pop("CSRF_ACTIVO", None)
        self.c = routes.container
        self.client = routes.app.test_client()

    def tearDown(self):
        routes.app.config.pop("CSRF_ACTIVO", None)
        routes.container = self._contenedor_original
        self._tmp.cleanup()

    def entrar(self, usuario, clave, client=None):
        return (client or self.client).post(
            "/login", data={"nombre_usuario": usuario, "contrasena": clave}
        )

    def crear_cliente(self, nombre="ana", clave="secreto123", email=None):
        return self.c.auth_service.registrar_cliente(
            nombre, clave, "Ana", "Pérez", email or f"{nombre}@mail.com", "Calle 1", "1123456789"
        )


# ------------------------------------------------------------------ usuarios (admin)
class AdminUsuariosTest(BaseRutas):
    def setUp(self):
        super().setUp()
        self.entrar("admin", "Admin1234")

    def test_admin_crea_un_cliente(self):
        r = self.client.post(
            "/admin/usuarios/nuevo",
            data={
                "tipo": "cliente", "nombre_usuario": "luis", "contrasena": "secreto123",
                "nombre": "Luis", "apellido": "Gómez", "email": "luis@mail.com",
                "domicilio": "Calle 2", "telefono": "1122334455",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.c.usuarios.obtener_por_nombre_usuario("luis").rol, "cliente")

    def test_admin_crea_otro_administrador(self):
        self.client.post(
            "/admin/usuarios/nuevo",
            data={
                "tipo": "administrador", "nombre_usuario": "jefe", "contrasena": "secreto123",
                "nombre": "Jefe", "apellido": "Dos", "email": "jefe@mail.com",
            },
        )
        self.assertEqual(self.c.usuarios.obtener_por_nombre_usuario("jefe").rol, "administrador")

    def test_alta_invalida_muestra_error_y_no_persiste(self):
        r = self.client.post(
            "/admin/usuarios/nuevo",
            data={"tipo": "cliente", "nombre_usuario": "x", "contrasena": "abc", "nombre": "X",
                  "apellido": "Y", "email": "x@mail.com", "domicilio": "d", "telefono": "1122334455"},
        )
        self.assertEqual(r.status_code, 400)
        self.assertIsNone(self.c.usuarios.obtener_por_nombre_usuario("x"))

    def test_admin_modifica_un_cliente_y_su_clave(self):
        cliente = self.crear_cliente()
        r = self.client.post(
            f"/admin/usuarios/{cliente.id_usuario}/modificar",
            data={"nombre": "Ana María", "apellido": "Pérez", "email": "ana@mail.com",
                  "domicilio": "Calle 99", "telefono": "1199998888", "contrasena": "nuevaclave1"},
        )
        self.assertEqual(r.status_code, 302)
        actualizado = self.c.usuarios.obtener_por_id(cliente.id_usuario)
        self.assertEqual(actualizado.nombre, "Ana María")
        self.assertEqual(actualizado.domicilio, "Calle 99")
        self.c.auth_service.autenticar("ana", "nuevaclave1")

    def test_modificar_sin_clave_conserva_la_anterior(self):
        cliente = self.crear_cliente()
        self.client.post(
            f"/admin/usuarios/{cliente.id_usuario}/modificar",
            data={"nombre": "Ana", "apellido": "Pérez", "email": "ana@mail.com",
                  "domicilio": "Otra", "telefono": "1123456789", "contrasena": ""},
        )
        self.c.auth_service.autenticar("ana", "secreto123")

    def test_no_se_puede_usar_el_email_de_otro_usuario(self):
        self.crear_cliente("ana")
        bob = self.crear_cliente("bob")
        r = self.client.post(
            f"/admin/usuarios/{bob.id_usuario}/modificar",
            data={"nombre": "Bob", "apellido": "P", "email": "ana@mail.com",
                  "domicilio": "d", "telefono": "1123456789"},
        )
        self.assertEqual(r.status_code, 400)

    def test_admin_elimina_cliente_y_se_vacia_su_carrito(self):
        cliente = self.crear_cliente()
        self.c.carrito_service.agregar(cliente.id_usuario, 1, 2)
        r = self.client.post(f"/admin/usuarios/{cliente.id_usuario}/eliminar")
        self.assertEqual(r.status_code, 302)
        self.assertIsNone(self.c.usuarios.obtener_por_id(cliente.id_usuario))
        self.assertEqual(self.c.carrito_service.contar_unidades(cliente.id_usuario), 0)

    def test_admin_no_puede_eliminarse_a_si_mismo(self):
        admin = self.c.usuarios.obtener_por_nombre_usuario("admin")
        self.client.post(f"/admin/usuarios/{admin.id_usuario}/eliminar")
        self.assertIsNotNone(self.c.usuarios.obtener_por_id(admin.id_usuario))

    def test_no_se_elimina_al_ultimo_administrador(self):
        admin = self.c.usuarios.obtener_por_nombre_usuario("admin")
        with self.assertRaises(DatosInvalidosError):
            self.c.auth_service.eliminar_usuario(admin.id_usuario, id_actor=999)

    def test_el_listado_ya_no_tiene_botones_deshabilitados(self):
        html = self.client.get("/admin/usuarios").data.decode("utf-8")
        self.assertNotIn("disabled", html)
        self.assertIn("/admin/usuarios/nuevo", html)

    def test_un_cliente_no_entra_al_abm_de_usuarios(self):
        self.crear_cliente()
        otro = routes.app.test_client()
        self.entrar("ana", "secreto123", otro)
        self.assertEqual(otro.get("/admin/usuarios/nuevo").status_code, 302)
        self.assertEqual(otro.post("/admin/usuarios/1/eliminar").status_code, 302)


# ------------------------------------------------------------------ catálogo
class CatalogoConsultaTest(BaseRutas):
    def test_producto_sin_stock_sigue_visible_y_marcado(self):
        self.c.producto_service.crear("Fantasma", "No hay", 10, "Nada")
        html = self.client.get("/catalogo").data.decode("utf-8")
        self.assertIn("Fantasma", html)
        self.assertIn("Sin stock por el momento", html)

    def test_se_muestra_el_stock_total_y_por_sucursal(self):
        html = self.client.get("/catalogo").data.decode("utf-8")
        self.assertIn("Disponible: 70 unidad(es)", html)  # Leche: 50 + 20
        self.assertIn("Sucursal Norte: 20", html)

    def test_buscador_ignora_mayusculas_y_acentos(self):
        html = self.client.get("/catalogo?q=serenisima").data.decode("utf-8")
        self.assertIn("Leche Entera", html)
        self.assertNotIn("Pan Lactal", html)

    def test_buscar_algo_inexistente_lo_dice(self):
        html = self.client.get("/catalogo?q=zzzz").data.decode("utf-8")
        self.assertIn("No existe ningún producto", html)

    def test_servicio_consultar_devuelve_stock_por_sucursal(self):
        item = self.c.catalogo_service.consultar("leche")[0]
        self.assertEqual(item.stock_total, 70)
        self.assertEqual({s.nombre: c for s, c in item.por_sucursal},
                         {"Sucursal Centro": 50, "Sucursal Norte": 20})

    def test_no_se_puede_agregar_al_carrito_un_producto_agotado(self):
        self.c.producto_service.crear("Fantasma", "No hay", 10, "Nada")
        cliente = self.crear_cliente()
        self.entrar("ana", "secreto123")
        r = self.client.post("/carrito/agregar", json={"id_producto": 6, "cantidad": 1})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.c.carrito_service.contar_unidades(cliente.id_usuario), 0)


# ------------------------------------------------------------------ sucursal cercana
class SucursalCercanaTest(BaseRutas):
    def setUp(self):
        super().setUp()
        self.cliente = self.crear_cliente()
        self.entrar("ana", "secreto123")

    def test_la_ubicacion_del_cliente_cambia_la_sucursal_mas_cercana(self):
        # Cerca de la Sucursal Sur (-34.62, -58.40)
        html = self.client.get("/cliente/sucursales-cercanas?lat=-34.6201&lon=-58.4001").data.decode("utf-8")
        primera = re.search(r"<h3>(Sucursal [^<]+)</h3>", html).group(1)
        self.assertEqual(primera, "Sucursal Sur")
        self.assertIn("Tu ubicación", html)

    def test_sin_ubicacion_avisa_que_usa_un_punto_de_referencia(self):
        html = self.client.get("/cliente/sucursales-cercanas").data.decode("utf-8")
        self.assertIn("punto de referencia", html)

    def test_ubicacion_invalida_se_rechaza(self):
        html = self.client.get("/cliente/sucursales-cercanas?lat=999&lon=abc", follow_redirects=True).data.decode("utf-8")
        self.assertIn("ubicación", html)
        self.assertIn("punto de referencia", html)

    def test_el_mapa_ya_no_esta_fijo_en_buenos_aires(self):
        # Una sucursal lejana mueve el bbox: el viejo valor fijo era -58.41,-34.63,-58.37,-34.59
        self.c.sucursal_service.crear("Jujuy", "Belgrano 1", -24.1858, -65.2995)
        html = self.client.get("/cliente/sucursales-cercanas?lat=-24.19&lon=-65.30").data.decode("utf-8")
        self.assertNotIn("bbox=-58.41", html)
        self.assertIn("-65.3", html)

    def test_la_ubicacion_se_recuerda_para_la_compra(self):
        self.client.get("/cliente/sucursales-cercanas?lat=-34.6201&lon=-58.4001")
        self.c.carrito_service.agregar(self.cliente.id_usuario, 3, 1)  # Arroz: hay en Centro y Sur
        html = self.client.get("/cliente/compra").data.decode("utf-8")
        self.assertIn("Ordenadas por distancia a tu ubicación", html)
        orden = re.findall(r"(Sucursal \w+) - ", html)
        self.assertEqual(orden[0], "Sucursal Sur")

    def test_helpers_geo(self):
        self.assertEqual(geo.parsear_ubicacion("-34.5", "-58.4"), (-34.5, -58.4))
        with self.assertRaises(DatosInvalidosError):
            geo.parsear_ubicacion("91", "0")
        oeste, sur, este, norte = map(float, geo.bbox_osm([(-34.0, -58.0), (-35.0, -59.0)], 0.1).split(","))
        self.assertAlmostEqual(oeste, -59.1)
        self.assertAlmostEqual(norte, -33.9)


# ------------------------------------------------------------------ compra
class CompraSucursalesTest(BaseRutas):
    def setUp(self):
        super().setUp()
        self.cliente = self.crear_cliente()
        self.entrar("ana", "secreto123")

    def test_el_checkout_deshabilita_sucursales_sin_stock_y_dice_cual_falta(self):
        # Pan Lactal: Centro 30 y Norte 15; Sur no tiene.
        self.c.carrito_service.agregar(self.cliente.id_usuario, 2, 5)
        html = self.client.get("/cliente/compra").data.decode("utf-8")
        self.assertRegex(html, r"Sucursal Sur[^<]*km\)\s*— sin stock de Pan Lactal")
        self.assertRegex(html, r'<option value="3"\s+disabled')

    def test_preselecciona_la_mas_cercana_que_puede_abastecer(self):
        self.c.carrito_service.agregar(self.cliente.id_usuario, 2, 5)
        html = self.client.get("/cliente/compra").data.decode("utf-8")
        self.assertRegex(html, r'<option value="1"\s+selected')

    def test_comprar_en_una_sucursal_sin_stock_sigue_rechazado_en_el_servidor(self):
        self.c.carrito_service.agregar(self.cliente.id_usuario, 2, 5)
        r = self.client.post(
            "/cliente/compra",
            data={"sucursal": "3", "metodoPago": "efectivo", "monto_recibido": "5000"},
        )
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.c.stock_service.obtener(2, 1).cantidad_disponible, 30)

    def test_evaluar_sucursales(self):
        self.c.carrito_service.agregar(self.cliente.id_usuario, 3, 40)  # Arroz: Centro 40, Sur 35
        opciones = self.c.compra_service.evaluar_sucursales(
            self.cliente.id_usuario, [(s, None) for s in self.c.sucursal_service.listar()]
        )
        completas = {o.sucursal.nombre: o.completa for o in opciones}
        self.assertEqual(completas, {"Sucursal Centro": True, "Sucursal Norte": False, "Sucursal Sur": False})

    def test_compra_exitosa_va_al_historial_con_metodo_de_pago(self):
        self.c.carrito_service.agregar(self.cliente.id_usuario, 1, 2)
        r = self.client.post(
            "/cliente/compra",
            data={"sucursal": "1", "metodoPago": "efectivo", "monto_recibido": "1000"},
        )
        self.assertIn("/cliente/compras", r.headers["Location"])
        html = self.client.get("/cliente/compras").data.decode("utf-8")
        self.assertIn("Compra #1", html)
        self.assertIn("Leche Entera", html)
        self.assertIn("Efectivo", html)
        self.assertIn("Sucursal Centro", html)

    def test_historial_vacio(self):
        html = self.client.get("/cliente/compras").data.decode("utf-8")
        self.assertIn("Todavía no realizaste ninguna compra", html)

    def test_el_historial_es_solo_del_cliente_logueado(self):
        otro = self.crear_cliente("bob")
        self.c.carrito_service.agregar(otro.id_usuario, 1, 1)
        self.c.compra_service.confirmar(otro.id_usuario, 1, PagoEfectivo(0, 150, monto_recibido=150))
        html = self.client.get("/cliente/compras").data.decode("utf-8")
        self.assertNotIn("Compra #1", html)


class CompraAtomicaTest(BaseRutas):
    def test_si_falla_el_guardado_el_stock_vuelve_a_su_valor(self):
        cliente = self.crear_cliente()
        self.c.carrito_service.agregar(cliente.id_usuario, 1, 5)
        antes = self.c.stock_service.obtener(1, 1).cantidad_disponible

        def falla(compra):
            raise OSError("disco lleno")

        self.c.compras.crear = falla
        with self.assertRaises(OSError):
            self.c.compra_service.confirmar(cliente.id_usuario, 1, PagoEfectivo(0, 750, monto_recibido=750))

        self.assertEqual(self.c.stock_service.obtener(1, 1).cantidad_disponible, antes)
        self.assertEqual(self.c.carrito_service.contar_unidades(cliente.id_usuario), 5)

    def test_si_falla_a_mitad_se_reponen_solo_los_descontados(self):
        cliente = self.crear_cliente()
        self.c.carrito_service.agregar(cliente.id_usuario, 1, 2)
        self.c.carrito_service.agregar(cliente.id_usuario, 2, 3)
        a1, a2 = (self.c.stock_service.obtener(p, 1).cantidad_disponible for p in (1, 2))
        original = self.c.stock_service.descontar
        llamadas = []

        def descontar(*args):
            if llamadas:
                raise OSError("falla en el segundo producto")
            llamadas.append(args)
            return original(*args)

        self.c.stock_service.descontar = descontar
        with self.assertRaises(OSError):
            self.c.compra_service.confirmar(cliente.id_usuario, 1, PagoEfectivo(0, 1000, monto_recibido=1000))
        self.assertEqual(
            (self.c.stock_service.obtener(1, 1).cantidad_disponible, self.c.stock_service.obtener(2, 1).cantidad_disponible),
            (a1, a2),
        )


# ------------------------------------------------------------------ carrito / stock / pagos
class CarritoYStockTest(BaseRutas):
    def test_borrar_un_producto_lo_saca_de_todos_los_carritos(self):
        cliente = self.crear_cliente()
        self.c.carrito_service.agregar(cliente.id_usuario, 1, 2)
        self.entrar("admin", "Admin1234", client=routes.app.test_client())
        admin = routes.app.test_client()
        self.entrar("admin", "Admin1234", admin)
        admin.post("/admin/productos/1/eliminar")
        self.assertEqual(self.c.carrito_service.contar_unidades(cliente.id_usuario), 0)
        self.assertEqual(len(self.c.carrito_service.obtener_carrito(cliente.id_usuario).items), 0)

    def test_el_contador_ignora_productos_que_ya_no_existen(self):
        cliente = self.crear_cliente()
        self.c.carrito_service.agregar(cliente.id_usuario, 1, 2)
        self.c.producto_service.eliminar(1)  # sin pasar por la cascada de la ruta
        self.assertEqual(self.c.carrito_service.contar_unidades(cliente.id_usuario), 0)

    def test_el_carrito_cobra_el_precio_vigente(self):
        cliente = self.crear_cliente()
        self.c.carrito_service.agregar(cliente.id_usuario, 1, 1)
        self.c.producto_service.actualizar(1, "Leche Entera", "d", 999, "m")
        item = self.c.carrito_service.obtener_carrito(cliente.id_usuario).items[0]
        self.assertEqual(item.precio_unitario, 999)
        self.c.carrito_service.agregar(cliente.id_usuario, 1, 1)
        compra = self.c.compra_service.confirmar(
            cliente.id_usuario, 1, PagoEfectivo(0, 1998, monto_recibido=2000)
        )
        self.assertEqual(compra.total, 1998)

    def test_asignar_stock_permite_cero(self):
        self.c.stock_service.asignar(1, 3, 0)
        self.assertEqual(self.c.stock_service.obtener(1, 3).cantidad_disponible, 0)

    def test_asignar_stock_negativo_se_rechaza(self):
        with self.assertRaises(DatosInvalidosError):
            self.c.stock_service.asignar(1, 3, -1)

    def test_reponer_suma_unidades(self):
        antes = self.c.stock_service.obtener(1, 1).cantidad_disponible
        self.c.stock_service.reponer(1, 1, 7)
        self.assertEqual(self.c.stock_service.obtener(1, 1).cantidad_disponible, antes + 7)

    def test_cuotas_tienen_tope(self):
        base = dict(id_pago=0, importe=100, numero_tarjeta="4" * 16, titular="X", vencimiento="12/99", cvv="123")
        self.assertTrue(PagoCredito(cuotas=MAX_CUOTAS, **base).validar_pago())
        self.assertFalse(PagoCredito(cuotas=MAX_CUOTAS + 1, **base).validar_pago())
        self.assertFalse(PagoCredito(cuotas=0, **base).validar_pago())

    def test_la_clave_minima_es_de_6_caracteres(self):
        with self.assertRaises(DatosInvalidosError):
            self.c.auth_service.registrar_cliente("zz", "12345", "Z", "Z", "z@mail.com", "d", "1123456789")


# ------------------------------------------------------------------ seguridad
class SeguridadTest(BaseRutas):
    def setUp(self):
        super().setUp()
        self.crear_cliente()
        routes.app.config["CSRF_ACTIVO"] = True

    def _token(self, client, ruta="/login"):
        html = client.get(ruta).data.decode("utf-8")
        return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)

    def test_post_sin_token_es_rechazado(self):
        r = self.client.post("/login", data={"nombre_usuario": "ana", "contrasena": "secreto123"})
        self.assertEqual(r.status_code, 400)

    def test_post_con_token_falso_es_rechazado(self):
        self._token(self.client)
        r = self.client.post(
            "/login", data={"nombre_usuario": "ana", "contrasena": "secreto123", "csrf_token": "falso"}
        )
        self.assertEqual(r.status_code, 400)

    def test_post_con_token_valido_funciona(self):
        token = self._token(self.client)
        r = self.client.post(
            "/login",
            data={"nombre_usuario": "ana", "contrasena": "secreto123", "csrf_token": token},
        )
        self.assertEqual(r.status_code, 302)

    def test_fetch_del_carrito_usa_el_header(self):
        token = self._token(self.client)
        self.client.post("/login", data={"nombre_usuario": "ana", "contrasena": "secreto123", "csrf_token": token})
        sin = self.client.post("/carrito/agregar", json={"id_producto": 1, "cantidad": 1})
        self.assertEqual(sin.status_code, 400)
        token = self._token(self.client, "/catalogo")
        con = self.client.post(
            "/carrito/agregar", json={"id_producto": 1, "cantidad": 1}, headers={"X-CSRF-Token": token}
        )
        self.assertEqual(con.status_code, 200)

    def test_todos_los_formularios_post_llevan_el_token(self):
        raiz = Path(routes.app.template_folder)
        for archivo in raiz.rglob("*.html"):
            texto = archivo.read_text(encoding="utf-8")
            for forma in re.finditer(r"<form\b[^>]*method=\"post\"[^>]*>(.*?)</form>", texto, re.S | re.I):
                self.assertIn("csrf_token", forma.group(1), f"falta el token en {archivo.name}")

    def test_logout_por_get_no_cierra_la_sesion(self):
        routes.app.config["CSRF_ACTIVO"] = False
        self.entrar("ana", "secreto123")
        self.assertEqual(self.client.get("/logout").status_code, 405)
        self.assertEqual(self.client.get("/cliente/dashboard").status_code, 200)

    def test_el_modo_debug_viene_apagado_por_defecto(self):
        from app.utils import config
        self.assertFalse(config.DEBUG)

    def test_la_clave_secreta_no_es_la_antigua_fija(self):
        self.assertNotEqual(routes.app.secret_key, "dev-only-secret-do-not-use-in-production")


if __name__ == "__main__":
    unittest.main()
