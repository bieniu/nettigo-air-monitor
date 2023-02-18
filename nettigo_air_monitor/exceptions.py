"""NAM exceptions."""


class NamError(Exception):
    """Base class for NAM errors."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class ApiError(NamError):
    """Raised when request ended in error."""


class NotRespondingError(NamError):
    """Raised when device is not responding."""


class AuthFailedError(NamError):
    """Raised if auth fails."""


class CannotGetMacError(NamError):
    """Raised when cannot get device MAC address."""


class InvalidSensorDataError(NamError):
    """Raised when sensor data is invalid."""
