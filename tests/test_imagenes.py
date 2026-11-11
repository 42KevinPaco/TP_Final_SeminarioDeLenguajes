"""Product image upload tests (storage, routes and catalog rendering)."""

import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app.routes_frontend as routes
from app.container import Container
from app.utils import imagenes

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def _datos_producto(**overrides):
    datos = {
        "nombre": "Alfajores",
        "descripcion": "Caja x6",
        "precio": "1200",
        "marca": "Havanna",
    }
    datos.update(overrides)
    return datos


class RepositorioImagenTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ruta = Path(self._tmp.name) / "productos.csv"

    def tearDown(self):
        self._tmp.cleanup()

    def test_csv_viejo_sin_columna_imagen_sigue_cargando(self):
        with self.ruta.open("w", encoding="utf-8", newline="") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["id_producto", "nombre", "descripcion", "precio", "marca"])
            escritor.writerow(["1", "Leche Entera", "Leche 1L", "150.00", "La Serenisima"])

        from app.repository.csv_producto_repository import CsvProductoRepository

        producto = CsvProductoRepository(self.ruta).listar()[0]

        self.assertEqual(producto.imagen, "")
        self.assertEqual(producto.nombre, "Leche Entera")

    def test_la_imagen_sobrevive_al_roundtrip(self):
        from app.models.producto import Producto
        from app.repository.csv_producto_repository import CsvProductoRepository

        repositorio = CsvProductoRepository(self.ruta)
        creado = repositorio.crear(
            Producto(
                id_producto=0,
                nombre="Alfajores",
                descripcion="Caja x6",
                precio=1200,
                marca="Havanna",
                imagen="abc123.png",
            )
        )
        leido = repositorio.obtener_por_id(creado.id_producto)

        self.assertEqual(leido.imagen, "abc123.png")


class ImagenesAdminTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.imagenes_dir = self.data_dir / "imagenes"
        self._original_container = routes.container
        routes.container = Container.from_data_dir(self.data_dir, seed=True)
        routes.app.config["TESTING"] = True
        self.client = routes.app.test_client()
        self.parche_imagenes = patch.object(imagenes, "IMAGENES_DIR", self.imagenes_dir)
        self.parche_rutas = patch.object(routes, "IMAGENES_DIR", self.imagenes_dir)
        self.parche_imagenes.start()
        self.parche_rutas.start()
        self.client.post(
            "/login",
            data={"nombre_usuario": "admin", "contrasena": "Admin1234"},
        )

    def tearDown(self):
        self.parche_imagenes.stop()
        self.parche_rutas.stop()
        routes.container = self._original_container
        self._tmp.cleanup()

    def test_alta_con_imagen_persiste_archivo_y_columna(self):
        respuesta = self.client.post(
            "/admin/productos/nuevo",
            data={**_datos_producto(), "imagen": (io.BytesIO(PNG_BYTES), "foto.png")},
        )

        self.assertEqual(respuesta.status_code, 302)
        productos = routes.container.producto_service.listar()
        creado = productos[-1]
        self.assertTrue(creado.imagen.endswith(".png"))
        self.assertTrue((self.imagenes_dir / creado.imagen).exists())

        # La tabla admin muestra la miniatura...
        tabla = self.client.get("/admin/productos").data.decode("utf-8")
        self.assertIn(f"/imagenes/{creado.imagen}", tabla)

        # ...y el catálogo del cliente sólo lo muestra cuando tiene stock (S10).
        self.client.post(
            "/admin/stock/asignar",
            data={"id_producto": str(creado.id_producto), "id_sucursal": "1", "cantidad": "5"},
        )
        catalogo = self.client.get("/catalogo").data.decode("utf-8")
        self.assertIn(f"/imagenes/{creado.imagen}", catalogo)

        servida = self.client.get(f"/imagenes/{creado.imagen}")
        self.assertEqual(servida.status_code, 200)

    def test_extension_invalida_rechaza_y_no_persiste(self):
        respuesta = self.client.post(
            "/admin/productos/nuevo",
            data={**_datos_producto(), "imagen": (io.BytesIO(b"hola"), "foto.txt")},
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual([p for p in routes.container.producto_service.listar() if p.nombre == "Alfajores"], [])
        self.assertEqual(list(self.imagenes_dir.glob("*")), [])

    def test_imagen_de_mas_de_2mb_rechaza(self):
        grande = io.BytesIO(b"0" * (2 * 1024 * 1024 + 1))

        respuesta = self.client.post(
            "/admin/productos/nuevo",
            data={**_datos_producto(), "imagen": (grande, "grande.png")},
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(list(self.imagenes_dir.glob("*")), [])

    def test_modificar_reemplaza_la_imagen_y_borra_la_vieja(self):
        self.client.post(
            "/admin/productos/nuevo",
            data={**_datos_producto(), "imagen": (io.BytesIO(PNG_BYTES), "vieja.png")},
        )
        actual = routes.container.producto_service.listar()[-1]
        viejo_archivo = self.imagenes_dir / actual.imagen

        respuesta = self.client.post(
            f"/admin/productos/{actual.id_producto}/modificar",
            data={
                **_datos_producto(nombre="Alfajores Marplatenses"),
                "imagen": (io.BytesIO(PNG_BYTES), "nueva.png"),
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        actualizado = routes.container.producto_service.obtener(actual.id_producto)
        self.assertNotEqual(actualizado.imagen, actual.imagen)
        self.assertFalse(viejo_archivo.exists())
        self.assertTrue((self.imagenes_dir / actualizado.imagen).exists())

    def test_modificar_sin_imagen_nueva_la_mantiene(self):
        self.client.post(
            "/admin/productos/nuevo",
            data={**_datos_producto(), "imagen": (io.BytesIO(PNG_BYTES), "vieja.png")},
        )
        actual = routes.container.producto_service.listar()[-1]

        self.client.post(
            f"/admin/productos/{actual.id_producto}/modificar",
            data=_datos_producto(nombre="Alfajores Renombrados"),
        )

        actualizado = routes.container.producto_service.obtener(actual.id_producto)
        self.assertEqual(actualizado.imagen, actual.imagen)
        self.assertTrue((self.imagenes_dir / actual.imagen).exists())

    def test_eliminar_producto_borra_su_imagen(self):
        self.client.post(
            "/admin/productos/nuevo",
            data={**_datos_producto(), "imagen": (io.BytesIO(PNG_BYTES), "foto.png")},
        )
        actual = routes.container.producto_service.listar()[-1]

        respuesta = self.client.post(f"/admin/productos/{actual.id_producto}/eliminar")

        self.assertEqual(respuesta.status_code, 302)
        self.assertFalse((self.imagenes_dir / actual.imagen).exists())

    def test_imagen_inexistente_da_404(self):
        respuesta = self.client.get("/imagenes/no-existe.png")
        self.assertEqual(respuesta.status_code, 404)

    def test_producto_sin_imagen_muestra_placeholder(self):
        cuerpo = self.client.get("/catalogo").data.decode("utf-8")
        self.assertIn("product-imagen-placeholder", cuerpo)


class UtilidadesImagenTest(unittest.TestCase):
    def test_sin_archivo_devuelve_cadena_vacia(self):
        from werkzeug.datastructures import FileStorage

        self.assertEqual(imagenes.guardar_imagen(None), "")
        self.assertEqual(imagenes.guardar_imagen(FileStorage(filename="")), "")
        self.assertEqual(
            imagenes.guardar_imagen(FileStorage(stream=io.BytesIO(b"x"), filename="")),
            "",
        )

    def test_eliminar_imagen_vacia_no_hace_nada(self):
        imagenes.eliminar_imagen("")


if __name__ == "__main__":
    unittest.main()
