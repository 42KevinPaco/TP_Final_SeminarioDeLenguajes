"""Domain models for users.

UML: Usuario is abstract; Cliente and Administrador inherit from it.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Usuario(ABC):
    """Common state for every authenticated user of the platform."""

    id_usuario: int
    nombre_usuario: str
    contrasena_hash: str = field(repr=False)
    nombre: str = ""
    apellido: str = ""
    email: str = ""

    @property
    @abstractmethod
    def rol(self) -> str:
        """Discriminator used for authorization and serialization."""

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}".strip()

    def __str__(self) -> str:
        return f"{self.nombre_completo} ({self.rol})"


@dataclass
class Cliente(Usuario):
    """Customer: adds shipping contact data."""

    domicilio: str = ""
    telefono: str = ""

    @property
    def rol(self) -> str:
        return "cliente"


@dataclass
class Administrador(Usuario):
    """Back-office user. Seeded, never self-registered."""

    @property
    def rol(self) -> str:
        return "administrador"
