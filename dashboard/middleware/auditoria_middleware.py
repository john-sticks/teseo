"""
Middleware para auditoría automática de accesos y acciones.
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from ..services.auditoria_service import AuditoriaService

logger = logging.getLogger(__name__)

class AuditoriaMiddleware(MiddlewareMixin):
    """
    Middleware para registrar automáticamente accesos y acciones de usuarios.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.auditoria_service = AuditoriaService()
        super().__init__(get_response)

    def process_request(self, request):
        """Procesa la request y registra el acceso."""
        # Solo auditar usuarios autenticados
        if not request.user.is_authenticated:
            return None
        
        # URLs que no se auditan
        urls_excluidas = [
            '/admin/jsi18n/',
            '/static/',
            '/media/',
            '/favicon.png',
        ]
        
        # Verificar si la URL debe ser excluida
        if any(request.path.startswith(url) for url in urls_excluidas):
            return None
        
        # Determinar tipo de acción basado en la URL
        tipo_accion = self._determinar_tipo_accion(request)
        
        # Crear descripción de la acción
        descripcion = self._crear_descripcion_accion(request)
        
        # Registrar el acceso
        try:
            self.auditoria_service.registrar_acceso(
                usuario=request.user,
                tipo_accion=tipo_accion,
                descripcion=descripcion,
                request=request,
                exitoso=True
            )
        except Exception as e:
            logger.error(f"Error en middleware de auditoría: {e}")
        
        return None

    def process_response(self, request, response):
        """Procesa la response."""
        return response

    def _determinar_tipo_accion(self, request) -> str:
        """
        Determina el tipo de acción basado en la URL y método HTTP.
        
        Args:
            request: Objeto request de Django
            
        Returns:
            Tipo de acción como string
        """
        path = request.path.lower()
        method = request.method.upper()
        
        # Acciones de autenticación
        if 'login' in path:
            return 'LOGIN'
        elif 'logout' in path:
            return 'LOGOUT'
        
        # Acciones de sincronización
        elif 'sync' in path or 'sincronizar' in path:
            return 'SYNC'
        
        # Acciones de exportación
        elif 'export' in path or 'exportar' in path:
            return 'EXPORT'
        
        # Acciones de edición
        elif 'edit' in path or 'editar' in path:
            return 'EDIT'
        
        # Acciones CRUD
        elif method == 'POST':
            if 'create' in path or 'crear' in path:
                return 'CREATE'
            elif 'update' in path or 'actualizar' in path:
                return 'UPDATE'
            elif 'delete' in path or 'eliminar' in path:
                return 'DELETE'
            else:
                return 'UPDATE'
        
        # Acciones de visualización
        else:
            return 'VIEW'

    def _crear_descripcion_accion(self, request) -> str:
        """
        Crea una descripción legible de la acción.
        
        Args:
            request: Objeto request de Django
            
        Returns:
            Descripción de la acción
        """
        path = request.path
        method = request.method
        
        # Mapeo de URLs a descripciones
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
        }
        
        # Buscar descripción específica
        for url_pattern, descripcion in descripciones.items():
            if path.startswith(url_pattern):
                return descripcion
        
        # Descripción genérica
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

class SesionMiddleware(MiddlewareMixin):
    """
    Middleware para manejar sesiones de usuario.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.auditoria_service = AuditoriaService()
        super().__init__(get_response)

    def process_request(self, request):
        """Procesa la request y maneja la sesión."""
        if request.user.is_authenticated and hasattr(request, 'session'):
            session_key = request.session.session_key
            if session_key:
                try:
                    # Verificar si la sesión ya está registrada
                    from ..models_auditoria import SesionUsuario
                    sesion_existente = SesionUsuario.objects.filter(
                        usuario=request.user,
                        session_key=session_key,
                        activa=True
                    ).first()
                    
                    if not sesion_existente:
                        # Registrar nueva sesión
                        self.auditoria_service.registrar_sesion(
                            usuario=request.user,
                            session_key=session_key,
                            request=request
                        )
                    
                except Exception as e:
                    logger.error(f"Error en middleware de sesión: {e}")
        
        return None

    def process_response(self, request, response):
        """Procesa la response."""
        return response
