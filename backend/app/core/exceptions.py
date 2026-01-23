class KotakAppException(Exception):
    """Base exception for the application."""
    pass

class KotakAPIError(KotakAppException):
    """Raised when Kotak API returns an error."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class AuthenticationError(KotakAppException):
    """Raised when authentication fails."""
    pass

class OrderError(KotakAppException):
    """Raised when order placement/modification fails."""
    pass
