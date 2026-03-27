"""
Servicio para manejar auditoría de accesos y acciones de usuarios.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count
from django.contrib.sessions.models import Session
from django.contrib.contenttypes.models import ContentType

from ..models_auditoria import AuditoriaAcceso, SesionUsuario, PerfilUsuario

logger = logging.getLogger(__name__)

class AuditoriaService:
    """Servicio para manejar auditoría de accesos y acciones."""
    
    def __init__(self):
        self.logger = logger

    def registrar_acceso(self, usuario: User, tipo_accion: str, descripcion: str, 
                        request=None, exitoso: bool = True, detalles: Dict = None) -> AuditoriaAcceso:
        """
        Registra un acceso o acción del usuario.
        
        Args:
            usuario: Usuario que realiza la acción
            tipo_accion: Tipo de acción (LOGIN, VIEW, etc.)
            descripcion: Descripción de la acción
            request: Objeto request de Django (opcional)
            exitoso: Si la acción fue exitosa
            detalles: Detalles adicionales en formato dict
            
        Returns:
            Instancia de AuditoriaAcceso creada
        """
        try:
            ip_address = '127.0.0.1'
            user_agent = ''
            url = ''
            metodo_http = ''
            
            if request:
                ip_address = self._obtener_ip_cliente(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                url = request.build_absolute_uri()
                metodo_http = request.method
            
            auditoria = AuditoriaAcceso.objects.create(
                usuario=usuario,
                tipo_accion=tipo_accion,
                descripcion=descripcion,
                ip_address=ip_address,
                user_agent=user_agent,
                url=url,
                metodo_http=metodo_http,
                exitoso=exitoso,
                detalles_adicionales=detalles or {}
            )
            
            # Actualizar última actividad del perfil
            self._actualizar_ultima_actividad(usuario)
            
            return auditoria
            
        except Exception as e:
            self.logger.error(f"Error registrando acceso: {e}")
            return None

    def registrar_sesion(self, usuario: User, session_key: str, request=None) -> SesionUsuario:
        """
        Registra una nueva sesión de usuario.
        
        Args:
            usuario: Usuario que inicia sesión
            session_key: Clave de la sesión
            request: Objeto request de Django
            
        Returns:
            Instancia de SesionUsuario creada
        """
        try:
            ip_address = '127.0.0.1'
            user_agent = ''
            
            if request:
                ip_address = self._obtener_ip_cliente(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Cerrar sesiones anteriores del usuario
            SesionUsuario.objects.filter(usuario=usuario, activa=True).update(activa=False)
            
            sesion = SesionUsuario.objects.create(
                usuario=usuario,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return sesion
            
        except Exception as e:
            self.logger.error(f"Error registrando sesión: {e}")
            return None

    def cerrar_sesion(self, usuario: User, session_key: str = None):
        """
        Cierra la sesión del usuario.
        
        Args:
            usuario: Usuario que cierra sesión
            session_key: Clave de la sesión (opcional)
        """
        try:
            if session_key:
                SesionUsuario.objects.filter(
                    usuario=usuario, 
                    session_key=session_key, 
                    activa=True
                ).update(activa=False)
            else:
                SesionUsuario.objects.filter(
                    usuario=usuario, 
                    activa=True
                ).update(activa=False)
                
        except Exception as e:
            self.logger.error(f"Error cerrando sesión: {e}")

    def obtener_usuarios_activos(self) -> List[Dict[str, Any]]:
        """
        Obtiene lista de usuarios actualmente activos.
        
        Returns:
            Lista de diccionarios con información de usuarios activos
        """
        try:
            sesiones_activas = SesionUsuario.objects.filter(
                activa=True,
                fecha_ultima_actividad__gte=timezone.now() - timedelta(hours=1)
            ).select_related('usuario', 'usuario__perfil')
            
            usuarios_activos = []
            for sesion in sesiones_activas:
                usuarios_activos.append({
                    'usuario': sesion.usuario,
                    'perfil': getattr(sesion.usuario, 'perfil', None),
                    'ip_address': sesion.ip_address,
                    'fecha_inicio': sesion.fecha_inicio,
                    'fecha_ultima_actividad': sesion.fecha_ultima_actividad,
                    'duracion_sesion': sesion.duracion_sesion,
                    'tiempo_inactivo': sesion.tiempo_inactivo,
                    'ubicacion': sesion.ubicacion
                })
            
            return usuarios_activos
            
        except Exception as e:
            self.logger.error(f"Error obteniendo usuarios activos: {e}")
            return []

    def obtener_historial_usuario(self, usuario: User, dias: int = 30) -> List[AuditoriaAcceso]:
        """
        Obtiene el historial de acciones de un usuario.
        
        Args:
            usuario: Usuario del cual obtener historial
            dias: Número de días hacia atrás
            
        Returns:
            Lista de AuditoriaAcceso
        """
        try:
            fecha_limite = timezone.now() - timedelta(days=dias)
            return AuditoriaAcceso.objects.filter(
                usuario=usuario,
                fecha_accion__gte=fecha_limite
            ).order_by('-fecha_accion')
            
        except Exception as e:
            self.logger.error(f"Error obteniendo historial de usuario: {e}")
            return []

    def obtener_estadisticas_auditoria(self, dias: int = 30) -> Dict[str, Any]:
        """
        Obtiene estadísticas de auditoría.
        
        Args:
            dias: Número de días hacia atrás
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            fecha_limite = timezone.now() - timedelta(days=dias)
            
            # Accesos por tipo
            accesos_por_tipo = AuditoriaAcceso.objects.filter(
                fecha_accion__gte=fecha_limite
            ).values('tipo_accion').annotate(
                total=Count('id')
            ).order_by('-total')
            
            # Accesos por usuario
            accesos_por_usuario = AuditoriaAcceso.objects.filter(
                fecha_accion__gte=fecha_limite
            ).values('usuario__username').annotate(
                total=Count('id')
            ).order_by('-total')[:10]
            
            # Accesos por IP
            accesos_por_ip = AuditoriaAcceso.objects.filter(
                fecha_accion__gte=fecha_limite
            ).values('ip_address').annotate(
                total=Count('id')
            ).order_by('-total')[:10]
            
            # Usuarios activos
            usuarios_activos = self.obtener_usuarios_activos()
            
            return {
                'total_accesos': AuditoriaAcceso.objects.filter(fecha_accion__gte=fecha_limite).count(),
                'accesos_por_tipo': list(accesos_por_tipo),
                'accesos_por_usuario': list(accesos_por_usuario),
                'accesos_por_ip': list(accesos_por_ip),
                'usuarios_activos': len(usuarios_activos),
                'periodo_dias': dias
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas de auditoría: {e}")
            return {}

    def limpiar_auditoria_antigua(self, dias: int = 90):
        """
        Limpia registros de auditoría antiguos.
        
        Args:
            dias: Días de antigüedad para limpiar
        """
        try:
            fecha_limite = timezone.now() - timedelta(days=dias)
            
            # Limpiar auditoría antigua
            registros_eliminados = AuditoriaAcceso.objects.filter(
                fecha_accion__lt=fecha_limite
            ).delete()
            
            # Limpiar sesiones inactivas
            sesiones_eliminadas = SesionUsuario.objects.filter(
                activa=False,
                fecha_ultima_actividad__lt=fecha_limite
            ).delete()
            
            self.logger.info(f"Auditoría limpiada: {registros_eliminados[0]} registros, {sesiones_eliminadas[0]} sesiones")
            
        except Exception as e:
            self.logger.error(f"Error limpiando auditoría antigua: {e}")

    def _obtener_ip_cliente(self, request) -> str:
        """Obtiene la IP real del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _actualizar_ultima_actividad(self, usuario: User):
        """Actualiza la última actividad del usuario."""
        try:
            perfil, created = PerfilUsuario.objects.get_or_create(usuario=usuario)
            perfil.ultima_actividad = timezone.now()
            perfil.save()
            
            # Actualizar sesión activa
            SesionUsuario.objects.filter(
                usuario=usuario, 
                activa=True
            ).update(fecha_ultima_actividad=timezone.now())
            
        except Exception as e:
            self.logger.error(f"Error actualizando última actividad: {e}")

    def verificar_permisos_usuario(self, usuario: User, permiso: str) -> bool:
        """
        Verifica si un usuario tiene un permiso específico.
        
        Args:
            usuario: Usuario a verificar
            permiso: Permiso a verificar
            
        Returns:
            True si tiene el permiso, False en caso contrario
        """
        try:
            if not usuario.is_authenticated:
                return False
            
            # Superusuarios tienen todos los permisos
            if usuario.is_superuser:
                return True
            
            # Obtener perfil del usuario
            perfil = getattr(usuario, 'perfil', None)
            if not perfil:
                return False
            
            # Verificar permisos según el rol
            if perfil.rol == 'ADMINISTRADOR':
                return True
            elif perfil.rol == 'VISITA':
                # Los usuarios de visita tienen permisos limitados
                if permiso == 'ver_relato_hecho':
                    return perfil.puede_ver_relato_hecho
                elif permiso == 'editar_datos':
                    return perfil.puede_editar_datos
                elif permiso == 'sincronizar':
                    return perfil.puede_sincronizar
                elif permiso == 'exportar':
                    return perfil.puede_exportar
                else:
                    return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error verificando permisos: {e}")
            return False
