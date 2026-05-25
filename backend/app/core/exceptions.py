class AppException(Exception):
    """Base exception for custom business logic errors."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code