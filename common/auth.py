from functools import wraps

from SmartDjango import E, Hc
from django.http import HttpRequest, JsonResponse

from common.space import Space


@E.register()
class AuthError:
    TOKEN = E('Unauthorized access. Please provide a valid token.', hc=Hc.Unauthorized)


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
                raise AuthError.TOKEN
            return func(request, *args, **kwargs)

        return wrapper
