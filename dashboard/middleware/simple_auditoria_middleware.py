"""
Middleware simplificado para auditoría básica.
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class SimpleAuditoriaMiddleware(MiddlewareMixin):
    """
    Middleware simplificado para registrar accesos básicos.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request):
        """Procesa la request y registra el acceso básico."""
        # Solo auditar usuarios autenticados
        if not request.user.is_authenticated:
            return None
        
        # URLs que no se auditan
        urls_excluidas = [
            '/admin/jsi18n/',
            '/static/',
            '/media/',
            '/favicon.png',
            '/login/',
            '/logout/',
        ]
        
        # Verificar si la URL debe ser excluida
        if any(request.path.startswith(url) for url in urls_excluidas):
            return None
        
        # Registrar en la base de datos
        try:
            from ..models_auditoria import AuditoriaAcceso
            
            # Determinar tipo de acción
            tipo_accion = self._determinar_tipo_accion(request)
            descripcion = self._crear_descripcion_accion(request)
            
            # Obtener IP del cliente
            ip_address = self._obtener_ip_cliente(request)
            
            # Crear registro de auditoría
            AuditoriaAcceso.objects.create(
                usuario=request.user,
                tipo_accion=tipo_accion,
                descripcion=descripcion,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                url=request.build_absolute_uri(),
                metodo_http=request.method,
                exitoso=True
            )
            
        except Exception as e:
            logger.error(f"Error en middleware de auditoría: {e}")
        
        return None

    def process_response(self, request, response):
        return response
    
    def _determinar_tipo_accion(self, request) -> str:
        """Determina el tipo de acción basado en la URL."""
        path = request.path.lower()
        method = request.method.upper()
        
        if 'login' in path:
            return 'LOGIN'
        elif 'logout' in path:
            return 'LOGOUT'
        elif 'sync' in path or 'sincronizar' in path:
            return 'SYNC'
        elif 'export' in path or 'exportar' in path:
            return 'EXPORT'
        elif 'edit' in path or 'editar' in path:
            return 'EDIT'
        elif method == 'POST':
            if 'create' in path or 'crear' in path:
                return 'CREATE'
            elif 'update' in path or 'actualizar' in path:
                return 'UPDATE'
            elif 'delete' in path or 'eliminar' in path:
                return 'DELETE'
            else:
                return 'UPDATE'
        else:
            return 'VIEW'
    
    def _crear_descripcion_accion(self, request) -> str:
        """Crea una descripción de la acción."""
        path = request.path
        method = request.method
        
        descripciones = {
            '/dashboard/': 'Acceso al Dashboard principal',
            '/dashboard/clubes/': 'Visualización de Clubes',
            '/dashboard/derecho_admision/': 'Visualización de Derechos de Admisión',
            '/dashboard/redes_monitoring/': 'Visualización de Redes y Navegadores',
            '/dashboard/operacionales/': 'Visualización de Operacionales',
            '/dashboard/mapa_incidentes/': 'Visualización del Mapa de Incidentes',
            '/dashboard/sincronizar/': 'Sincronización de datos',
            '/dashboard/exportar/': 'Exportación de datos',
            '/dashboard/editar/': 'Edición de datos',
            '/dashboard/usuarios/': 'Gestión de usuarios',
            '/dashboard/auditoria/': 'Visualización de auditoría',
            '/dashboard/gestion-usuarios/': 'Gestión de usuarios',
            '/dashboard/mi-perfil/': 'Acceso al perfil de usuario',
        }
        
        for url_pattern, descripcion in descripciones.items():
            if path.startswith(url_pattern):
                return descripcion
        
        if method == 'GET':
            return f"Visualización de {path}"
        elif method == 'POST':
            return f"Acción POST en {path}"
        elif method == 'PUT':
            return f"Actualización en {path}"
        elif method == 'DELETE':
            return f"Eliminación en {path}"
        else:
            return f"Acción {method} en {path}"
    
    def _obtener_ip_cliente(self, request) -> str:
        """Obtiene la IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
