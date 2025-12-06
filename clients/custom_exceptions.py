"""
Custom exception classes for API clients.
"""


class ApiError(Exception):
    """
    Exception raised for API errors.
    Includes optional status code for HTTP errors.
    """
    def __init__(self, message, status_code=None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
    
    def __str__(self):
        if self.status_code:
            return f"ApiError (Status {self.status_code}): {self.message}"
        return f"ApiError: {self.message}"


class RateLimitError(ApiError):
    """
    Exception raised when API rate limit is exceeded.
    """
    def __init__(self, message, status_code=429):
        super().__init__(message, status_code)
    
    def __str__(self):
        return f"RateLimitError: {self.message}"
