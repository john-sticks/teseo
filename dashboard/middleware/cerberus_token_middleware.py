import logging
import jwt
from django.conf import settings
from django.contrib.auth import logout
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

# Rutas que no requieren validación de token
_RUTAS_EXCLUIDAS = ("/login/", "/logout/", "/static/", "/media/", "/admin/", "/favicon")


class CerberusTokenMiddleware:
    """
    Valida el token JWT de Cerberus en cada request de usuarios autenticados.
    Usa decodificación local para no hacer una llamada HTTP a Cerberus en cada request.
    Si el token expiró o no existe, cierra la sesión y redirige al login.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not any(
            request.path.startswith(ruta) for ruta in _RUTAS_EXCLUIDAS
        ):
            token = request.session.get("cerberus_token")
            if not token or not self._token_valido(token):
                logout(request)
                return redirect(f"/login/?next={request.path}")

        return self.get_response(request)

    def _token_valido(self, token):
        try:
            jwt.decode(
                token,
                settings.CERBERUS_JWT_SECRET,
                algorithms=["HS256"],
            )
            return True
        except jwt.ExpiredSignatureError:
            logger.info("Token de Cerberus expirado, cerrando sesión.")
            return False
        except jwt.InvalidTokenError:
            logger.warning("Token de Cerberus inválido.")
            return False
