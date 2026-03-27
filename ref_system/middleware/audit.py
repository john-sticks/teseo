"""
Middleware para auditoría de accesos y acciones del sistema REF.
"""
import logging
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import User
import os

logger = logging.getLogger(__name__)

class AuditMiddleware(MiddlewareMixin):
    """
    Middleware que registra todas las acciones de los usuarios
    para auditoría del sistema.
    """
    
    def process_request(self, request):
        """Registra el acceso del usuario."""
        if request.user.is_authenticated:
            user = request.user
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Log de acceso
            logger.info(
                f"AUDIT_ACCESS - Usuario: {user.username} | "
                f"IP: {ip_address} | "
                f"URL: {request.get_full_path()} | "
                f"Timestamp: {timestamp} | "
                f"User-Agent: {user_agent[:100]}"
            )
    
    def get_client_ip(self, request):
        """Obtiene la IP real del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
