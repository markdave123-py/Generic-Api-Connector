class APIClientError(Exception):
    """Base class for connector errors."""


class AuthenticationError(APIClientError):
    pass


class NotFoundError(APIClientError):
    pass


class RateLimitError(APIClientError):
    pass


class ServerError(APIClientError):
    pass
