from django.conf import settings
from django.db import models
from django.utils import timezone


class Club(models.Model):
    """Modelo para representar los clubes de fútbol."""
    
    nombre = models.CharField(max_length=100, unique=True)
    nombre_corto = models.CharField(max_length=20, unique=True)
    escudo = models.ImageField(upload_to='clubes/escudos/', blank=True, null=True)
    estadio = models.CharField(max_length=200)
    direccion_estadio = models.TextField()
    ciudad = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    sitio_web = models.URLField(blank=True, null=True)
    
    # Información adicional
    fundacion = models.DateField(blank=True, null=True)
    colores = models.CharField(max_length=200, blank=True, null=True)
    presidente = models.CharField(max_length=100, blank=True, null=True)
    
    # Metadatos
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, db_constraint=False)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = 'Club'
        verbose_name_plural = 'Clubes'
        ordering = ['nombre']


class FaccionHinchas(models.Model):
    """Modelo para representar las facciones de hinchadas."""
    
    TIPO_FACCION_CHOICES = [
        ('BARRA_BRAVA', 'Barra Brava'),
        ('HINCHADA', 'Hinchada'),
        ('GRUPO', 'Grupo'),
        ('BANDA', 'Banda'),
        ('OTRO', 'Otro'),
    ]
    
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='facciones')
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_FACCION_CHOICES)
    descripcion = models.TextField(blank=True, null=True)
    activa = models.BooleanField(default=True)
    cantidad_estimada = models.IntegerField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.club.nombre_corto}"
    
    class Meta:
        verbose_name = 'Facción de Hinchadas'
        verbose_name_plural = 'Facciones de Hinchadas'
        unique_together = ['club', 'nombre']


class ReferenteHinchas(models.Model):
    """Modelo para representar los referentes de las hinchadas."""
    
    faccion = models.ForeignKey(FaccionHinchas, on_delete=models.CASCADE, related_name='referentes')
    nombre = models.CharField(max_length=100)
    apodo = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True, null=True)
    
    def __str__(self):
        apodo_str = f" ({self.apodo})" if self.apodo else ""
        return f"{self.nombre}{apodo_str} - {self.faccion.nombre}"
    
    class Meta:
        verbose_name = 'Referente de Hinchadas'
        verbose_name_plural = 'Referentes de Hinchadas'


class TerritorioHinchas(models.Model):
    """Modelo para representar los territorios de las hinchadas."""
    
    faccion = models.ForeignKey(FaccionHinchas, on_delete=models.CASCADE, related_name='territorios')
    nombre = models.CharField(max_length=100)
    direccion = models.TextField(blank=True, null=True)
    ciudad = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    coordenadas_lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    coordenadas_lng = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.nombre} - {self.faccion.nombre}"
    
    class Meta:
        verbose_name = 'Territorio de Hinchadas'
        verbose_name_plural = 'Territorios de Hinchadas'


class AntecedenteClub(models.Model):
    """Modelo para representar antecedentes de los clubes."""
    
    TIPO_ANTECEDENTE_CHOICES = [
        ('INCIDENTE', 'Incidente'),
        ('SANCIÓN', 'Sanción'),
        ('VIOLENCIA', 'Violencia'),
        ('DESTRUCCIÓN', 'Destrucción de propiedad'),
        ('INVASIÓN', 'Invasión de campo'),
        ('OTRO', 'Otro'),
    ]
    
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='antecedentes')
    tipo = models.CharField(max_length=20, choices=TIPO_ANTECEDENTE_CHOICES)
    descripcion = models.TextField()
    fecha_incidente = models.DateField()
    lugar = models.CharField(max_length=200)
    sancion_impuesta = models.TextField(blank=True, null=True)
    monto_sancion = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    
    # Metadatos
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, db_constraint=False)
    fecha_registro = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.club.nombre_corto} - {self.get_tipo_display()} ({self.fecha_incidente})"
    
    class Meta:
        verbose_name = 'Antecedente de Club'
        verbose_name_plural = 'Antecedentes de Clubes'
        ordering = ['-fecha_incidente']
