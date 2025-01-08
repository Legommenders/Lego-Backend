from functools import wraps
from django.http import HttpRequest, JsonResponse
from django.core.exceptions import PermissionDenied

from common.space import Space


class Auth:
    AUTH_ERROR_MESSAGE = 'Unauthorized access. Please provide a valid token.'

    @classmethod
    def require_login(cls, func):
        """
        Decorator to ensure a request is authenticated using a token-based system.
        """
        @wraps(func)
        def wrapper(self, request: HttpRequest, *args, **kwargs):
            auth_token = request.META.get('HTTP_TOKEN')
            if auth_token != Space.auth:
                return JsonResponse({"error": cls.AUTH_ERROR_MESSAGE}, status=401)
            return func(self, request, *args, **kwargs)

        return wrapper
