import logging
import jwt
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class CerberusBackend(BaseBackend):
    """
    Backend de autenticación que delega a Cerberus vía API.
    - Llama a POST /auth/token para validar credenciales y obtener el JWT.
    - Decodifica el JWT localmente para extraer el username (sin llamadas extra).
    - Crea o actualiza un usuario Django local como referencia interna de Teseo.
    - No requiere registro en la tabla servicios de Cerberus.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        from .services.cerberus_service import CerberusService
        from .models_auditoria import PerfilUsuario

        # 1. Validar credenciales contra Cerberus
        token = CerberusService.remote_token(username, password)
        if not token:
            return None

        # 2. Decodificar JWT localmente para obtener el username
        try:
            payload = jwt.decode(
                token,
                settings.CERBERUS_JWT_SECRET,
                algorithms=["HS256"],
            )
            username_from_token = payload.get("sub")
            if not username_from_token:
                return None
        except jwt.InvalidTokenError:
            logger.warning("Token recibido de Cerberus no pudo ser decodificado.")
            return None

        # 3. Guardar token en sesión para validaciones posteriores
        if request is not None:
            request.session["cerberus_token"] = token

        # 4. Crear o actualizar usuario local de Teseo (sin contraseña propia)
        user, created = User.objects.get_or_create(username=username_from_token)
        if created:
            user.set_unusable_password()
            user.save()
            PerfilUsuario.objects.create(usuario=user, rol='VISITA')

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
