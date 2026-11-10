"""CSV implementation of the user repository.

The `tipo` column is the discriminator that rebuilds Cliente or Administrador.
Passwords are stored only as hashes.
"""

from dataclasses import replace
from pathlib import Path

from app.models.usuario import Administrador, Cliente, Usuario
from app.repository.csv_base import CsvTable
from app.repository.interfaces import IUsuarioRepository
from app.utils.config import DATA_DIR

FIELDNAMES = [
    "id_usuario",
    "nombre_usuario",
    "contrasena_hash",
    "nombre",
    "apellido",
    "email",
    "tipo",
    "domicilio",
    "telefono",
]

TIPO_CLIENTE = "cliente"
TIPO_ADMINISTRADOR = "administrador"


class CsvUsuarioRepository(IUsuarioRepository):
    """Persists users in `data/usuarios.csv`."""

    def __init__(self, path: Path | None = None) -> None:
        self._table = CsvTable(Path(path) if path else DATA_DIR / "usuarios.csv", FIELDNAMES)
        self._table.ensure()

    # ---------- reads ----------
    def listar(self) -> list[Usuario]:
        return [self._to_model(row) for row in self._table.read_rows()]

    def obtener_por_id(self, id_usuario: int) -> Usuario | None:
        for row in self._table.read_rows():
            if int(row["id_usuario"]) == id_usuario:
                return self._to_model(row)
        return None

    def obtener_por_nombre_usuario(self, nombre_usuario: str) -> Usuario | None:
        objetivo = (nombre_usuario or "").strip().lower()
        for row in self._table.read_rows():
            if (row.get("nombre_usuario") or "").strip().lower() == objetivo:
                return self._to_model(row)
        return None

    def existe_email(self, email: str) -> bool:
        objetivo = (email or "").strip().lower()
        return any((row.get("email") or "").strip().lower() == objetivo for row in self._table.read_rows())

    # ---------- writes ----------
    def crear(self, usuario: Usuario) -> Usuario:
        id_asignado = self._table.next_id("id_usuario")
        creado = replace(usuario, id_usuario=id_asignado)
        self._table.append_row(self._to_row(creado))
        return creado

    def actualizar(self, usuario: Usuario) -> Usuario:
        rows = self._table.read_rows()
        for index, row in enumerate(rows):
            if int(row["id_usuario"]) == usuario.id_usuario:
                rows[index] = self._to_row(usuario)
                self._table.write_rows(rows)
                return usuario
        raise ValueError(f"No existe el usuario con id {usuario.id_usuario}")

    def eliminar(self, id_usuario: int) -> None:
        rows = self._table.read_rows()
        restantes = [row for row in rows if int(row["id_usuario"]) != id_usuario]
        if len(restantes) == len(rows):
            return
        self._table.write_rows(restantes)

    # ---------- mapping ----------
    def _to_model(self, row: dict[str, str]) -> Usuario:
        comun = {
            "id_usuario": int(row["id_usuario"]),
            "nombre_usuario": row.get("nombre_usuario", ""),
            "contrasena_hash": row.get("contrasena_hash", ""),
            "nombre": row.get("nombre", ""),
            "apellido": row.get("apellido", ""),
            "email": row.get("email", ""),
        }
        if (row.get("tipo") or TIPO_CLIENTE) == TIPO_ADMINISTRADOR:
            return Administrador(**comun)
        return Cliente(
            **comun,
            domicilio=row.get("domicilio", ""),
            telefono=row.get("telefono", ""),
        )

    def _to_row(self, usuario: Usuario) -> dict[str, str]:
        row = {
            "id_usuario": str(usuario.id_usuario),
            "nombre_usuario": usuario.nombre_usuario,
            "contrasena_hash": usuario.contrasena_hash,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "email": usuario.email,
            "tipo": usuario.rol,
            "domicilio": "",
            "telefono": "",
        }
        if isinstance(usuario, Cliente):
            row["domicilio"] = usuario.domicilio
            row["telefono"] = usuario.telefono
        return row
