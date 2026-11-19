"""Domain exceptions shared by models, repositories and services."""


class ErrorDeNegocio(Exception):
    """Base class for every expected business error."""


class DatosInvalidosError(ErrorDeNegocio):
    """User input does not satisfy the domain rules."""


class CredencialesInvalidasError(ErrorDeNegocio):
    """Username/password pair does not match a registered user."""


class UsuarioDuplicadoError(ErrorDeNegocio):
    """Username or email is already registered."""


class RecursoNoEncontradoError(ErrorDeNegocio):
    """Requested entity does not exist."""


class StockInsuficienteError(ErrorDeNegocio):
    """Not enough units available in the selected branch."""
