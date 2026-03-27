from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class Torneo(models.Model):
    """Modelo para representar los diferentes torneos."""
    TORNEOS_CHOICES = [
        ('LPF', 'Liga Profesional de Fútbol'),
        ('ASCENSO', 'Primera Nacional'),
        ('COPA_ARGENTINA', 'Copa Argentina'),
        ('COPA_SUDAMERICANA', 'Copa Sudamericana'),
        ('COPA_LIBERTADORES', 'Copa Libertadores'),
    ]
    
    nombre = models.CharField(max_length=50, choices=TORNEOS_CHOICES, unique=True)
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    def __str__(self):
        return self.get_nombre_display()
    
    class Meta:
        verbose_name = 'Torneo'
        verbose_name_plural = 'Torneos'


class Encuentro(models.Model):
    """Modelo para representar los encuentros deportivos."""
    NIVEL_RIESGO_CHOICES = [
        ('BAJO', 'Bajo'),
        ('MEDIO', 'Medio'),
        ('ALTO', 'Alto'),
        ('CRITICO', 'Crítico'),
    ]
    
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    club_local = models.CharField(max_length=100)
    club_visitante = models.CharField(max_length=100)
    estadio = models.CharField(max_length=200)
    nivel_riesgo = models.CharField(max_length=10, choices=NIVEL_RIESGO_CHOICES, default='BAJO')
    motivo_alerta = models.TextField(blank=True, null=True)
    relato_hecho = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    
    # Campos para sincronización con Google Sheets
    external_id = models.CharField(max_length=200, unique=True, blank=True, null=True)
    fecha_text = models.CharField(max_length=50, blank=True, null=True)
    hora_text = models.CharField(max_length=50, blank=True, null=True)
    escudo_local = models.URLField(blank=True, null=True)
    escudo_visitante = models.URLField(blank=True, null=True)
    raw_data = models.JSONField(blank=True, null=True)
    last_sync = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.club_local} vs {self.club_visitante} - {self.fecha}"
    
    class Meta:
        verbose_name = 'Encuentro'
        verbose_name_plural = 'Encuentros'
        ordering = ['fecha', 'hora']


class Incidente(models.Model):
    """Modelo para representar incidentes en el mapa."""
    TIPO_INCIDENTE_CHOICES = [
        ('VIOLENCIA', 'Violencia'),
        ('DESTRUCCION', 'Destrucción de propiedad'),
        ('INVASION', 'Invasión de campo'),
        ('DISPUTA', 'Disputa entre hinchadas'),
        ('OTRO', 'Otro'),
    ]
    
    encuentro = models.ForeignKey(Encuentro, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_INCIDENTE_CHOICES)
    descripcion = models.TextField()
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    fecha_incidente = models.DateTimeField()
    reportado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Campos para sincronización con Google Sheets
    external_id = models.CharField(max_length=200, unique=True, blank=True, null=True)
    torneo = models.CharField(max_length=50, blank=True, null=True)
    club_local = models.CharField(max_length=100, blank=True, null=True)
    club_visitante = models.CharField(max_length=100, blank=True, null=True)
    estadio = models.CharField(max_length=200, blank=True, null=True)
    raw_data = models.JSONField(blank=True, null=True)
    last_sync = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.encuentro}"
    
    class Meta:
        verbose_name = 'Incidente'
        verbose_name_plural = 'Incidentes'


class RankingConflictividad(models.Model):
    """Modelo para el ranking de conflictividad por club."""
    club = models.CharField(max_length=100)
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE)
    cantidad_conflictos = models.IntegerField(default=0)
    nivel_riesgo_promedio = models.CharField(max_length=10, choices=Encuentro.NIVEL_RIESGO_CHOICES, default='BAJO')
    ultimo_incidente = models.DateTimeField(blank=True, null=True)
    
    # Campos para sincronización con Google Sheets
    external_id = models.CharField(max_length=200, unique=True, blank=True, null=True)
    raw_data = models.JSONField(blank=True, null=True)
    last_sync = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.club} - {self.cantidad_conflictos} conflictos"
    
    class Meta:
        verbose_name = 'Ranking de Conflictividad'
        verbose_name_plural = 'Rankings de Conflictividad'
        unique_together = ['club', 'torneo']
    
    @classmethod
    def calcular_ranking_desde_incidentes(cls, torneo_nombre):
        """Calcula el ranking de conflictividad basado en los incidentes reales."""
        from collections import Counter
        from django.db.models import Count, Max
        
        # Obtener el objeto torneo
        try:
            torneo_obj = Torneo.objects.get(nombre=torneo_nombre)
        except Torneo.DoesNotExist:
            from datetime import date
            # Crear torneo con fechas por defecto si no existe
            torneo_obj, _ = Torneo.objects.get_or_create(
                nombre=torneo_nombre, 
                defaults={
                    'activo': True,
                    'fecha_inicio': date.today(),
                    'fecha_fin': date.today().replace(year=date.today().year + 1)
                }
            )
        
        # Limpiar ranking anterior
        cls.objects.filter(torneo=torneo_obj).delete()
        
        # Obtener incidentes del torneo
        incidentes = Incidente.objects.filter(torneo=torneo_nombre)
        
        # Contar incidentes por club
        club_counts = Counter()
        club_fechas = {}
        
        for incidente in incidentes:
            if incidente.club_local:
                club_counts[incidente.club_local] += 1
                if incidente.club_local not in club_fechas or incidente.fecha_incidente > club_fechas[incidente.club_local]:
                    club_fechas[incidente.club_local] = incidente.fecha_incidente
        
        # Crear registros de ranking
        for club, cantidad in club_counts.items():
            # Determinar nivel de riesgo promedio basado en cantidad
            if cantidad >= 10:
                nivel_riesgo = 'CRITICO'
            elif cantidad >= 7:
                nivel_riesgo = 'ALTO'
            elif cantidad >= 4:
                nivel_riesgo = 'MEDIO'
            else:
                nivel_riesgo = 'BAJO'
            
            cls.objects.create(
                club=club,
                torneo=torneo_obj,
                cantidad_conflictos=cantidad,
                nivel_riesgo_promedio=nivel_riesgo,
                ultimo_incidente=club_fechas.get(club),
                external_id=f"{torneo_nombre}_{club}"
            )
        
        return cls.objects.filter(torneo=torneo_obj).order_by('-cantidad_conflictos')


class Club(models.Model):
    """Modelo para representar los clubes de fútbol."""
    external_id = models.CharField(max_length=200, unique=True)
    nombre = models.CharField(max_length=250, blank=True)
    escudo_url = models.URLField(blank=True, null=True)
    estadio = models.CharField(max_length=250, blank=True)
    capacidad = models.CharField(max_length=50, blank=True, null=True)
    fecha_fundacion = models.CharField(max_length=50, blank=True, null=True)
    direccion = models.CharField(max_length=500, blank=True)
    ubicacion_sede = models.CharField(max_length=500, blank=True, null=True)
    barras = models.TextField(blank=True, null=True)
    torneo = models.CharField(max_length=50, blank=True)
    raw_data = models.JSONField(blank=True, null=True)
    last_sync = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre or f"Club {self.external_id}"
    
    class Meta:
        verbose_name = 'Club'
        verbose_name_plural = 'Clubes'
        ordering = ['nombre']


class DerechoAdmision(models.Model):
    """Modelo para representar los derechos de admisión."""
    external_id = models.CharField(max_length=200, unique=True)
    club = models.CharField(max_length=200, blank=True)
    escudo = models.URLField(blank=True, null=True)
    nombre = models.CharField(max_length=200, blank=True)
    apellido = models.CharField(max_length=200, blank=True)
    motivo = models.TextField(blank=True)
    estado = models.CharField(max_length=50, blank=True)
    fecha_inicio = models.CharField(max_length=50, blank=True)
    fecha_fin = models.CharField(max_length=50, blank=True)
    torneo = models.CharField(max_length=50, blank=True)
    raw_data = models.JSONField(blank=True, null=True)
    last_sync = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.club} - {self.estado}"
    
    class Meta:
        verbose_name = 'Derecho de Admisión'
        verbose_name_plural = 'Derechos de Admisión'
        ordering = ['club']


class OperacionalDoc(models.Model):
    """Modelo para documentos operacionales (PDFs)."""
    file_id = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=300, blank=True)
    url = models.URLField(blank=True)
    spreadsheet_id = models.CharField(max_length=200, blank=True)
    torneo = models.CharField(max_length=50, blank=True)
    raw_data = models.JSONField(blank=True, null=True)
    last_sync = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name or f"Documento {self.file_id}"
    
    class Meta:
        verbose_name = 'Documento Operacional'
        verbose_name_plural = 'Documentos Operacionales'
        ordering = ['name']
