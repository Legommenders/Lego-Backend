from functools import wraps

from smartdjango import Error, Code, analyse

from common.space import Space


@Error.register
class AuthErrors:
    TOKEN = Error('Unauthorized access. Please provide a valid token.', code=Code.Unauthorized)


def require_login(func):
    """
    Decorator to ensure a request is authenticated using a token-based system.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = analyse.get_request(*args)
        auth_token = request.META.get('HTTP_AUTHENTICATION')
        if auth_token != Space.auth:
            raise AuthErrors.TOKEN
        return func(*args, **kwargs)

    return wrapper
