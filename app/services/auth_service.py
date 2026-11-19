"""Authentication use cases: login and customer registration."""

from app.models.usuario import Administrador, Cliente, Usuario
from app.repository.interfaces import IUsuarioRepository
from app.utils import validators
from app.utils.exceptions import (
    CredencialesInvalidasError,
    DatosInvalidosError,
    RecursoNoEncontradoError,
    UsuarioDuplicadoError,
)
from app.utils.security import (
    MIN_PASSWORD_LENGTH,
    hash_password,
    is_password_acceptable,
    verify_password,
)


MENSAJE_CONTRASENA = f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres"


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
            raise DatosInvalidosError(MENSAJE_CONTRASENA)
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

    # ------------------------------------------------------------ admin: usuarios
    def crear_administrador(
        self,
        nombre_usuario: str,
        contrasena: str,
        nombre: str,
        apellido: str,
        email: str,
    ) -> Administrador:
        """Back-office accounts are created only by another administrator."""
        usuario_limpio = validators.requerido(nombre_usuario, "nombre de usuario")
        email_limpio = validators.validar_email(email)
        if not is_password_acceptable(contrasena):
            raise DatosInvalidosError(MENSAJE_CONTRASENA)
        if self._usuarios.obtener_por_nombre_usuario(usuario_limpio) is not None:
            raise UsuarioDuplicadoError("El nombre de usuario ya está registrado")
        if self._usuarios.existe_email(email_limpio):
            raise UsuarioDuplicadoError("El email ya está registrado")
        return self._usuarios.crear(
            Administrador(
                id_usuario=0,
                nombre_usuario=usuario_limpio,
                contrasena_hash=hash_password(contrasena),
                nombre=validators.requerido(nombre, "nombre"),
                apellido=validators.requerido(apellido, "apellido"),
                email=email_limpio,
            )
        )

    def actualizar_usuario(
        self,
        id_usuario: int,
        nombre: str,
        apellido: str,
        email: str,
        domicilio: str = "",
        telefono: str = "",
        contrasena: str = "",
    ) -> Usuario:
        """Edit profile data. The user name and the role never change; an empty
        password keeps the current one."""
        usuario = self.obtener_usuario(id_usuario)
        email_limpio = validators.validar_email(email)
        otro = next(
            (u for u in self._usuarios.listar() if u.email.lower() == email_limpio and u.id_usuario != id_usuario),
            None,
        )
        if otro is not None:
            raise UsuarioDuplicadoError("El email ya está registrado")

        usuario.nombre = validators.requerido(nombre, "nombre")
        usuario.apellido = validators.requerido(apellido, "apellido")
        usuario.email = email_limpio
        if isinstance(usuario, Cliente):
            usuario.domicilio = validators.requerido(domicilio, "domicilio")
            usuario.telefono = validators.validar_telefono(telefono)
        if contrasena:
            if not is_password_acceptable(contrasena):
                raise DatosInvalidosError(MENSAJE_CONTRASENA)
            usuario.contrasena_hash = hash_password(contrasena)
        return self._usuarios.actualizar(usuario)

    def eliminar_usuario(self, id_usuario: int, id_actor: int) -> Usuario:
        """Delete an account, never one's own and never the last administrator."""
        usuario = self.obtener_usuario(id_usuario)
        if id_usuario == id_actor:
            raise DatosInvalidosError("No podés eliminar tu propia cuenta")
        if isinstance(usuario, Administrador):
            administradores = [u for u in self._usuarios.listar() if isinstance(u, Administrador)]
            if len(administradores) <= 1:
                raise DatosInvalidosError("No se puede eliminar al único administrador")
        self._usuarios.eliminar(id_usuario)
        return usuario
