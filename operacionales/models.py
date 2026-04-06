from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class OperacionalVigente(models.Model):
    """Modelo para representar los operacionales vigentes."""
    
    TIPO_OPERACIONAL_CHOICES = [
        ('PLAN_SEGURIDAD', 'Plan de Seguridad'),
        ('PROTOCOLO', 'Protocolo'),
        ('MANUAL', 'Manual'),
        ('INSTRUCTIVO', 'Instructivo'),
        ('OTRO', 'Otro'),
    ]
    
    torneo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_OPERACIONAL_CHOICES)
    descripcion = models.TextField()
    archivo_pdf = models.FileField(upload_to='operacionales/pdfs/')
    fecha_creacion = models.DateField()
    fecha_vigencia = models.DateField(blank=True, null=True)
    version = models.CharField(max_length=20, default='1.0')
    activo = models.BooleanField(default=True)
    
    # Metadatos
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.torneo}"
    
    @property
    def esta_vencido(self):
        """Verifica si el operacional está vencido."""
        if self.fecha_vigencia and self.activo:
            return timezone.now().date() > self.fecha_vigencia
        return False
    
    @property
    def dias_restantes(self):
        """Calcula los días restantes hasta el vencimiento."""
        if self.fecha_vigencia and self.activo:
            delta = self.fecha_vigencia - timezone.now().date()
            return delta.days
        return None
    
    class Meta:
        verbose_name = 'Operacional Vigente'
        verbose_name_plural = 'Operacionales Vigentes'
        ordering = ['-fecha_registro']
