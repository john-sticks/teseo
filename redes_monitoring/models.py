from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class AlertaRedes(models.Model):
    """Modelo para representar alertas de redes sociales."""
    
    NIVEL_RIESGO_CHOICES = [
        ('BAJO', 'Bajo'),
        ('MEDIO', 'Medio'),
        ('ALTO', 'Alto'),
        ('CRITICO', 'Crítico'),
    ]
    
    FUENTE_CHOICES = [
        ('TWITTER', 'Twitter'),
        ('FACEBOOK', 'Facebook'),
        ('INSTAGRAM', 'Instagram'),
        ('YOUTUBE', 'YouTube'),
        ('TIKTOK', 'TikTok'),
        ('MEDIO', 'Medio de Comunicación'),
        ('OTRO', 'Otro'),
    ]
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    url = models.URLField(blank=True, null=True)
    fuente = models.CharField(max_length=20, choices=FUENTE_CHOICES)
    nivel_riesgo = models.CharField(max_length=10, choices=NIVEL_RIESGO_CHOICES, default='BAJO')
    keywords = models.JSONField(default=list)  # Lista de palabras clave detectadas
    clubes_mencionados = models.JSONField(default=list)  # Clubes mencionados
    
    # Metadatos
    fecha_alerta = models.DateTimeField(default=timezone.now)
    procesado = models.BooleanField(default=False)
    procesado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_procesamiento = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.titulo} - {self.get_fuente_display()}"
    
    class Meta:
        verbose_name = 'Alerta de Redes'
        verbose_name_plural = 'Alertas de Redes'
        ordering = ['-fecha_alerta']


class TendenciasKeyword(models.Model):
    """Modelo para representar tendencias de keywords."""
    
    keyword = models.CharField(max_length=100)
    frecuencia = models.IntegerField(default=0)
    fecha_tendencia = models.DateField(default=timezone.now)
    
    def __str__(self):
        return f"{self.keyword} - {self.frecuencia} menciones"
    
    class Meta:
        verbose_name = 'Tendencia de Keyword'
        verbose_name_plural = 'Tendencias de Keywords'
        ordering = ['-frecuencia', '-fecha_tendencia']
        unique_together = ['keyword', 'fecha_tendencia']
