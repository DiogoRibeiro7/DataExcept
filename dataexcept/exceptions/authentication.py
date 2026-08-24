# authentication.py
from .base import JobError


class AuthenticationError(JobError):
    """Raised when user authentication fails."""

    def __init__(self, user: str, message: str | None = None):
        self.user = user
        self.message = message or f"Authentication failed for user '{user}'"
        super().__init__(self.message)


class AuthorizationError(JobError):
    """Raised when user lacks permission for an action."""

    def __init__(self, user: str, permission: str):
        self.user = user
        self.permission = permission
        msg = f"User '{user}' lacks permission '{permission}'"
        super().__init__(msg)
