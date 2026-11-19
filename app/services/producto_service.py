"""Catalog use cases: list, create, update and remove products."""

from app.models.producto import Producto
from app.repository.interfaces import IProductoRepository
from app.utils import validators
from app.utils.exceptions import RecursoNoEncontradoError


class ProductoService:
    """Orchestrates product operations over the repository abstraction."""

    def __init__(self, producto_repository: IProductoRepository) -> None:
        self._productos = producto_repository

    def listar(self) -> list[Producto]:
        return self._productos.listar()

    def obtener(self, id_producto: int) -> Producto:
        producto = self._productos.obtener_por_id(id_producto)
        if producto is None:
            raise RecursoNoEncontradoError("El producto no existe")
        return producto

    def crear(
        self,
        nombre: str,
        descripcion: str,
        precio,
        marca: str,
        imagen: str = "",
    ) -> Producto:
        producto = Producto(
            id_producto=0,
            nombre=validators.requerido(nombre, "nombre"),
            descripcion=validators.requerido(descripcion, "descripción"),
            precio=validators.validar_numero_positivo(precio, "precio"),
            marca=validators.requerido(marca, "marca"),
            imagen=imagen,
        )
        return self._productos.crear(producto)

    def actualizar(
        self,
        id_producto: int,
        nombre: str,
        descripcion: str,
        precio,
        marca: str,
        imagen: str | None = None,
    ) -> Producto:
        actual = self.obtener(id_producto)
        actual.nombre = validators.requerido(nombre, "nombre")
        actual.descripcion = validators.requerido(descripcion, "descripción")
        actual.precio = validators.validar_numero_positivo(precio, "precio")
        actual.marca = validators.requerido(marca, "marca")
        if imagen is not None:
            actual.imagen = imagen
        return self._productos.actualizar(actual)

    def eliminar(self, id_producto: int) -> None:
        self.obtener(id_producto)
        self._productos.eliminar(id_producto)
