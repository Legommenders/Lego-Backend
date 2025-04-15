from functools import wraps

from django.http import HttpRequest
from smartdjango import Error, Code

from common.space import Space


@Error.register
class AuthErrors:
    TOKEN = Error('Unauthorized access. Please provide a valid token.', code=Code.Unauthorized)


class Auth:

    @classmethod
    def require_login(cls, func):
        """
        Decorator to ensure a request is authenticated using a token-based system.
        """
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            auth_token = request.META.get('HTTP_AUTHENTICATION')
            if auth_token != Space.auth:
                raise AuthErrors.TOKEN
            return func(request, *args, **kwargs)

        return wrapper
