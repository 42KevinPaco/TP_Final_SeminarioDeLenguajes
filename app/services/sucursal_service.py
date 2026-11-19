"""Branch use cases, including distance-based ordering."""

from app.models.sucursal import Sucursal
from app.repository.interfaces import ISucursalRepository
from app.utils import validators
from app.utils.config import DEFAULT_LATITUD, DEFAULT_LONGITUD
from app.utils.exceptions import DatosInvalidosError, RecursoNoEncontradoError


class SucursalService:
    """Orchestrates branch operations over the repository abstraction."""

    def __init__(self, sucursal_repository: ISucursalRepository) -> None:
        self._sucursales = sucursal_repository

    def listar(self) -> list[Sucursal]:
        return self._sucursales.listar()

    def obtener(self, id_sucursal: int) -> Sucursal:
        sucursal = self._sucursales.obtener_por_id(id_sucursal)
        if sucursal is None:
            raise RecursoNoEncontradoError("La sucursal no existe")
        return sucursal

    def crear(self, nombre: str, direccion: str, latitud, longitud) -> Sucursal:
        sucursal = Sucursal(
            id_sucursal=0,
            nombre=validators.requerido(nombre, "nombre"),
            direccion=validators.requerido(direccion, "dirección"),
            latitud=_validar_coordenada(latitud, "latitud", -90, 90),
            longitud=_validar_coordenada(longitud, "longitud", -180, 180),
        )
        return self._sucursales.crear(sucursal)

    def actualizar(self, id_sucursal: int, nombre: str, direccion: str, latitud, longitud) -> Sucursal:
        actual = self.obtener(id_sucursal)
        actual.nombre = validators.requerido(nombre, "nombre")
        actual.direccion = validators.requerido(direccion, "dirección")
        actual.latitud = _validar_coordenada(latitud, "latitud", -90, 90)
        actual.longitud = _validar_coordenada(longitud, "longitud", -180, 180)
        return self._sucursales.actualizar(actual)

    def eliminar(self, id_sucursal: int) -> None:
        self.obtener(id_sucursal)
        self._sucursales.eliminar(id_sucursal)

    def listar_por_cercania(
        self,
        latitud: float | None = None,
        longitud: float | None = None,
    ) -> list[tuple[Sucursal, float]]:
        """Return every branch paired with its distance, nearest first."""
        origen_lat = DEFAULT_LATITUD if latitud is None else latitud
        origen_lon = DEFAULT_LONGITUD if longitud is None else longitud
        pares = [
            (sucursal, round(sucursal.distancia_km(origen_lat, origen_lon), 2))
            for sucursal in self._sucursales.listar()
        ]
        return sorted(pares, key=lambda par: par[1])


def _validar_coordenada(valor, campo: str, minimo: float, maximo: float) -> float:
    try:
        numero = float(valor)
    except (TypeError, ValueError) as exc:
        raise DatosInvalidosError(f"La {campo} debe ser numérica") from exc
    if not minimo <= numero <= maximo:
        raise DatosInvalidosError(f"La {campo} debe estar entre {minimo} y {maximo}")
    return numero
