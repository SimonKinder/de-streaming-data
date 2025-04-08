"""Custom Exceptions for use with Guardian API interaction"""


class RateLimitExceededError(BaseException):
    """Exception raised when the API rate limit has been exceeded."""


class ClientRequestError(BaseException):
    """Exception raised for 4XX response status codes, excluding 429."""


class ServerRequestError(BaseException):
    """Exception raised for 5XX response status codes."""
