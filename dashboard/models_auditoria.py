"""
Modelos para auditoría de accesos y acciones de usuarios.
"""
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class TipoAccion(models.TextChoices):
    """Tipos de acciones que se pueden auditar."""
    LOGIN = 'LOGIN', 'Inicio de sesión'
    LOGOUT = 'LOGOUT', 'Cierre de sesión'
    VIEW = 'VIEW', 'Visualización'
    CREATE = 'CREATE', 'Creación'
    UPDATE = 'UPDATE', 'Actualización'
    DELETE = 'DELETE', 'Eliminación'
    SYNC = 'SYNC', 'Sincronización'
    EXPORT = 'EXPORT', 'Exportación'
    EDIT = 'EDIT', 'Edición'

class AuditoriaAcceso(models.Model):
    """Modelo para registrar accesos y acciones de usuarios."""
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auditoria_accesos')
    tipo_accion = models.CharField(max_length=20, choices=TipoAccion.choices)
    descripcion = models.TextField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    metodo_http = models.CharField(max_length=10, blank=True, null=True)
    
    # Campos para auditoría de objetos específicos
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Metadatos
    fecha_accion = models.DateTimeField(default=timezone.now)
    exitoso = models.BooleanField(default=True)
    detalles_adicionales = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Auditoría de Acceso'
        verbose_name_plural = 'Auditorías de Accesos'
        ordering = ['-fecha_accion']
        indexes = [
            models.Index(fields=['usuario', 'fecha_accion']),
            models.Index(fields=['tipo_accion', 'fecha_accion']),
            models.Index(fields=['ip_address', 'fecha_accion']),
        ]
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_accion_display()} - {self.fecha_accion.strftime('%d/%m/%Y %H:%M')}"

class SesionUsuario(models.Model):
    """Modelo para rastrear sesiones activas de usuarios."""
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sesiones')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_ultima_actividad = models.DateTimeField(default=timezone.now)
    activa = models.BooleanField(default=True)
    ubicacion = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Sesión de Usuario'
        verbose_name_plural = 'Sesiones de Usuarios'
        ordering = ['-fecha_ultima_actividad']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.ip_address} - {self.fecha_inicio.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def duracion_sesion(self):
        """Calcula la duración de la sesión."""
        if self.activa:
            return timezone.now() - self.fecha_inicio
        return self.fecha_ultima_actividad - self.fecha_inicio
    
    @property
    def tiempo_inactivo(self):
        """Calcula el tiempo de inactividad."""
        return timezone.now() - self.fecha_ultima_actividad

class PerfilUsuario(models.Model):
    """Modelo extendido para perfiles de usuario con roles personalizados."""
    
    ROLES_CHOICES = [
        ('ADMINISTRADOR', 'Administrador'),
        ('VISITA', 'Visita'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=20, choices=ROLES_CHOICES, default='VISITA')
    telefono = models.CharField(max_length=20, blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    cargo = models.CharField(max_length=100, blank=True, null=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    ultima_actividad = models.DateTimeField(default=timezone.now)
    activo = models.BooleanField(default=True)
    
    # Configuraciones de permisos específicos
    puede_ver_relato_hecho = models.BooleanField(default=False)
    puede_editar_datos = models.BooleanField(default=False)
    puede_sincronizar = models.BooleanField(default=False)
    puede_exportar = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'
    
    def __str__(self):
        return f"{self.usuario.username} - {self.get_rol_display()}"
    
    def save(self, *args, **kwargs):
        """Override save para configurar permisos según el rol."""
        if self.rol == 'ADMINISTRADOR':
            self.puede_ver_relato_hecho = True
            self.puede_editar_datos = True
            self.puede_sincronizar = True
            self.puede_exportar = True
        elif self.rol == 'VISITA':
            self.puede_ver_relato_hecho = False  # Los usuarios de visita NO pueden ver relatos del hecho
            self.puede_editar_datos = False
            self.puede_sincronizar = False
            self.puede_exportar = False
        
        super().save(*args, **kwargs)
