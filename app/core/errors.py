class ApiError(Exception):
    """Domain error rendered as {"error": message} with the given HTTP status."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)
