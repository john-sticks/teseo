from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class DerechoAdmision(models.Model):
    """Modelo para representar los derechos de admisión."""
    
    ESTADO_CHOICES = [
        ('VIGENTE', 'Vigente'),
        ('LEVANTADO', 'Levantado'),
        ('SUSPENDIDO', 'Suspendido'),
    ]
    
    MOTIVO_CHOICES = [
        ('VIOLENCIA', 'Violencia'),
        ('DESTRUCCION', 'Destrucción de propiedad'),
        ('INVASION', 'Invasión de campo'),
        ('DISPUTA', 'Disputa entre hinchadas'),
        ('COMPORTAMIENTO', 'Mal comportamiento'),
        ('OTRO', 'Otro'),
    ]
    
    club = models.CharField(max_length=100)
    motivo = models.CharField(max_length=20, choices=MOTIVO_CHOICES)
    descripcion = models.TextField()
    fecha_imposicion = models.DateField()
    fecha_vencimiento = models.DateField(blank=True, null=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='VIGENTE')
    observaciones = models.TextField(blank=True, null=True)
    
    # Metadatos
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.club} - {self.get_motivo_display()} ({self.get_estado_display()})"
    
    @property
    def dias_restantes(self):
        """Calcula los días restantes hasta el vencimiento."""
        if self.fecha_vencimiento and self.estado == 'VIGENTE':
            delta = self.fecha_vencimiento - timezone.now().date()
            return delta.days
        return None
    
    @property
    def esta_vencido(self):
        """Verifica si el derecho de admisión está vencido."""
        if self.fecha_vencimiento and self.estado == 'VIGENTE':
            return timezone.now().date() > self.fecha_vencimiento
        return False
    
    class Meta:
        verbose_name = 'Derecho de Admisión'
        verbose_name_plural = 'Derechos de Admisión'
        ordering = ['-fecha_imposicion']
