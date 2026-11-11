"""Product image file handling.

Images are binary files under `data/imagenes/`; the CSV only stores the safe
file name. Uploading is always optional: an empty result means "no image".
"""

import uuid
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.utils.config import IMAGENES_DIR
from app.utils.exceptions import DatosInvalidosError

EXTENSIONES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
TAMANIO_MAXIMO = 2 * 1024 * 1024  # 2 MB


def guardar_imagen(archivo: FileStorage | None, directorio: Path | None = None) -> str:
    """Persist an uploaded image and return its file name ('' when none sent)."""
    if archivo is None or not archivo.filename:
        return ""

    extension = Path(archivo.filename).suffix.lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise DatosInvalidosError("La imagen debe ser JPG, PNG, WEBP o GIF")

    datos = archivo.read()
    archivo.close()
    if not datos:
        return ""
    if len(datos) > TAMANIO_MAXIMO:
        raise DatosInvalidosError("La imagen no puede superar 2 MB")

    destino = _directorio(directorio)
    nombre = f"{uuid.uuid4().hex[:12]}{extension}"
    (destino / nombre).write_bytes(datos)
    return nombre


def eliminar_imagen(nombre: str, directorio: Path | None = None) -> None:
    """Delete an image file when it exists; empty names are a no-op."""
    if not nombre:
        return
    destino = _directorio(directorio) / _nombre_seguro(nombre)
    if destino.exists():
        destino.unlink()


def _nombre_seguro(nombre: str) -> str:
    """Re-run the safe-name check for names that came from stored data."""
    return secure_filename(nombre)


def _directorio(directorio: Path | None) -> Path:
    destino = Path(directorio) if directorio else IMAGENES_DIR
    destino.mkdir(parents=True, exist_ok=True)
    return destino
