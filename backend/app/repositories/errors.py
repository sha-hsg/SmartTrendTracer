"""
Domain errors raised by the data-access layer.

Repositories must not depend on FastAPI; they raise these instead and the
API layer maps them to HTTP responses in one place (see app.main), with the
same {"detail": ...} body shape HTTPException produces.
"""


class RepositoryError(Exception):
    status_code = 500

    def __init__(self, detail: str = ""):
        super().__init__(detail)
        self.detail = detail


class NotFoundError(RepositoryError):
    status_code = 404


class InvalidInputError(RepositoryError):
    status_code = 400


class ConflictError(RepositoryError):
    status_code = 409


class DataAccessError(RepositoryError):
    """Unexpected failure while reading/writing data (HTTP 500)."""
    status_code = 500
