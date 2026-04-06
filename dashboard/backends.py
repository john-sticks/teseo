import logging
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)


class CerberusBackend(BaseBackend):
    """
    Backend de autenticación que delega a Cerberus vía API.
    El usuario se lee directamente de la tabla 'usuarios' compartida (DB cerberus).
    No se crean usuarios locales: la fuente de verdad es Cerberus.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        from .services.cerberus_service import CerberusService
        from .models_auditoria import PerfilUsuario

        User = get_user_model()

        token = CerberusService.remote_token(username, password)
        if not token:
            return None

        user_info = CerberusService.remote_user(token)
        if not user_info:
            return None

        try:
            user = User.objects.using('cerberus').get(username=username)
        except User.DoesNotExist:
            logger.warning(f"Usuario '{username}' autenticado en Cerberus pero no encontrado en la tabla usuarios.")
            return None

        # Guardar token en sesión para validaciones posteriores
        if request is not None:
            request.session['cerberus_token'] = token

        # Sincronizar PerfilUsuario (en DB default de Teseo) con el rol de Cerberus
        rol_cerberus = (user_info.get('rol') or '').upper()
        rol_teseo = 'ADMINISTRADOR' if rol_cerberus in ('ADMINISTRADOR', 'ADMIN') else 'VISITA'
        perfil, _ = PerfilUsuario.objects.get_or_create(usuario_id=user.pk)
        if perfil.rol != rol_teseo:
            perfil.rol = rol_teseo
            perfil.save()

        return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.using('cerberus').get(pk=user_id)
        except User.DoesNotExist:
            return None
