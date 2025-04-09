"""Custom Exceptions for use with Guardian API interaction"""


class APIError(BaseException):
    """Exception raised when an issue occurs with Guardian API interaction."""


class RateLimitExceededError(APIError):
    """Exception raised when the API rate limit has been exceeded."""


class ClientRequestError(APIError):
    """Exception raised for 4XX response status codes, excluding 429."""


class ServerRequestError(APIError):
    """Exception raised for 5XX response status codes."""


class BotocoreError(BaseException):
    """Exception raised when an issue occurs with Boto3 interaction."""
