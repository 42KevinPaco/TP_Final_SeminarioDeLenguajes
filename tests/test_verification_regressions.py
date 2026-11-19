"""Regression tests for the security and extensibility invariants of S5-S6.

These complement the main suite with checks that a rejected request never
mutates the store, that no administrator can be self-registered, that seeding
is idempotent, and that services work over any repository implementation.
"""

import csv
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from app.container import Container
from app.models.usuario import Usuario
from app.repository.interfaces import IUsuarioRepository
from app.repository.seed import seed_data
from app.services.auth_service import AuthService

import app.routes_frontend as routes

DATOS_REGISTRO = {
    "nombre_usuario": "kevin",
    "contrasena": "secreto123",
    "nombre": "Kevin",
    "apellido": "Perez",
    "email": "kevin@test.com",
    "domicilio": "Calle 1",
    "telefono": "1123456789",
}


class InMemoryUsuarioRepository(IUsuarioRepository):
    """Minimal alternate implementation used to prove DIP/LSP."""

    def __init__(self) -> None:
        self._datos: dict[int, Usuario] = {}

    def listar(self) -> list[Usuario]:
        return list(self._datos.values())

    def obtener_por_id(self, id_usuario: int) -> Usuario | None:
        return self._datos.get(id_usuario)

    def obtener_por_nombre_usuario(self, nombre_usuario: str) -> Usuario | None:
        return next(
            (u for u in self._datos.values() if u.nombre_usuario == nombre_usuario),
            None,
        )

    def existe_email(self, email: str) -> bool:
        return any(u.email == email for u in self._datos.values())

    def crear(self, usuario: Usuario) -> Usuario:
        creado = replace(usuario, id_usuario=len(self._datos) + 1)
        self._datos[creado.id_usuario] = creado
        return creado

    def actualizar(self, usuario: Usuario) -> Usuario:
        self._datos[usuario.id_usuario] = usuario
        return usuario

    def eliminar(self, id_usuario: int) -> None:
        self._datos.pop(id_usuario, None)


class StoreIntegrityTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self._original_container = routes.container
        routes.container = Container.from_data_dir(self.data_dir, seed=True)
        routes.app.config["TESTING"] = True
        self.client = routes.app.test_client()
        self.usuarios_csv = self.data_dir / "usuarios.csv"

    def tearDown(self):
        routes.container = self._original_container
        self._tmp.cleanup()

    def registrar(self, **overrides):
        return self.client.post("/registro", data={**DATOS_REGISTRO, **overrides})

    def test_rejected_requests_do_not_mutate_the_store(self):
        self.assertEqual(self.registrar().status_code, 302)
        antes = self.usuarios_csv.read_bytes()

        self.assertEqual(self.registrar(email="otro@test.com").status_code, 400)
        self.assertEqual(
            self.client.post(
                "/login", data={"nombre_usuario": "kevin", "contrasena": "mala"}
            ).status_code,
            401,
        )
        self.assertEqual(self.usuarios_csv.read_bytes(), antes)

    def test_registration_ignores_a_forged_role_field(self):
        self.registrar(tipo="administrador", rol="administrador")

        with self.usuarios_csv.open(encoding="utf-8", newline="") as handle:
            filas = list(csv.DictReader(handle))
        creado = next(fila for fila in filas if fila["nombre_usuario"] == "kevin")
        self.assertEqual(creado["tipo"], "cliente")

    def test_there_is_no_administrator_registration_endpoint(self):
        reglas = {
            (regla.rule, regla.endpoint)
            for regla in routes.app.url_map.iter_rules()
            if "regist" in regla.rule.lower() or "regist" in regla.endpoint.lower()
        }
        self.assertEqual(reglas, {("/registro", "registro")})

    def test_seed_is_idempotent(self):
        seed_data(
            routes.container.usuarios,
            routes.container.productos,
            routes.container.sucursales,
            routes.container.stock,
        )

        with self.usuarios_csv.open(encoding="utf-8", newline="") as handle:
            usuarios = [fila["nombre_usuario"] for fila in csv.DictReader(handle)]
        self.assertEqual(usuarios, ["admin"])


class RepositorySubstitutionTest(unittest.TestCase):
    def test_auth_service_works_over_any_repository_implementation(self):
        servicio = AuthService(InMemoryUsuarioRepository())

        cliente = servicio.registrar_cliente(
            "memoria", "MemPass1", "Memo", "Ria", "memo@test.com", "Calle 9", "1122233344"
        )

        self.assertEqual(cliente.rol, "cliente")
        self.assertEqual(
            servicio.autenticar("memoria", "MemPass1").id_usuario, cliente.id_usuario
        )


if __name__ == "__main__":
    unittest.main()
