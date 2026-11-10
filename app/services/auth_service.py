"""Authentication use cases: login and customer registration."""

from app.models.usuario import Cliente, Usuario
from app.repository.interfaces import IUsuarioRepository
from app.utils import validators
from app.utils.exceptions import (
    CredencialesInvalidasError,
    DatosInvalidosError,
    RecursoNoEncontradoError,
    UsuarioDuplicadoError,
)
from app.utils.security import hash_password, is_password_acceptable, verify_password


class AuthService:
    """Orchestrates authentication. Depends on the repository abstraction (DIP)."""

    def __init__(self, usuario_repository: IUsuarioRepository) -> None:
        self._usuarios = usuario_repository

    def autenticar(self, nombre_usuario: str, contrasena: str) -> Usuario:
        """Return the matching user or raise CredencialesInvalidasError."""
        usuario = self._usuarios.obtener_por_nombre_usuario(nombre_usuario)
        if usuario is None or not verify_password(contrasena, usuario.contrasena_hash):
            raise CredencialesInvalidasError("Usuario o contraseña incorrectos")
        return usuario

    def registrar_cliente(
        self,
        nombre_usuario: str,
        contrasena: str,
        nombre: str,
        apellido: str,
        email: str,
        domicilio: str,
        telefono: str,
    ) -> Cliente:
        """Validate input, hash the password and persist a new customer."""
        usuario_limpio = validators.requerido(nombre_usuario, "nombre de usuario")
        email_limpio = validators.validar_email(email)
        telefono_limpio = validators.validar_telefono(telefono)

        if not is_password_acceptable(contrasena):
            raise DatosInvalidosError("La contraseña debe tener al menos 4 caracteres")
        if self._usuarios.obtener_por_nombre_usuario(usuario_limpio) is not None:
            raise UsuarioDuplicadoError("El nombre de usuario ya está registrado")
        if self._usuarios.existe_email(email_limpio):
            raise UsuarioDuplicadoError("El email ya está registrado")

        cliente = Cliente(
            id_usuario=0,
            nombre_usuario=usuario_limpio,
            contrasena_hash=hash_password(contrasena),
            nombre=validators.requerido(nombre, "nombre"),
            apellido=validators.requerido(apellido, "apellido"),
            email=email_limpio,
            domicilio=validators.requerido(domicilio, "domicilio"),
            telefono=telefono_limpio,
        )
        return self._usuarios.crear(cliente)

    def obtener_usuario(self, id_usuario: int) -> Usuario:
        usuario = self._usuarios.obtener_por_id(id_usuario)
        if usuario is None:
            raise RecursoNoEncontradoError("El usuario no existe")
        return usuario

    def listar_usuarios(self) -> list[Usuario]:
        return self._usuarios.listar()
