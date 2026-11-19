"""Small geographic helpers for the nearest-branch feature."""

from app.utils.exceptions import DatosInvalidosError


def parsear_ubicacion(latitud, longitud) -> tuple[float, float]:
    """Validate the coordinates that the browser (or a form) sent."""
    try:
        lat = float(latitud)
        lon = float(longitud)
    except (TypeError, ValueError) as exc:
        raise DatosInvalidosError("La ubicación debe ser numérica") from exc
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise DatosInvalidosError("La ubicación está fuera de rango")
    return lat, lon


def bbox_osm(puntos: list[tuple[float, float]], margen: float = 0.01) -> str:
    """`west,south,east,north` for the OpenStreetMap embed, around every point."""
    latitudes = [lat for lat, _ in puntos]
    longitudes = [lon for _, lon in puntos]
    oeste, este = min(longitudes) - margen, max(longitudes) + margen
    sur, norte = min(latitudes) - margen, max(latitudes) + margen
    return f"{oeste:.5f},{sur:.5f},{este:.5f},{norte:.5f}"
