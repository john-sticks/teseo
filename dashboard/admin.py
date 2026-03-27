from django.contrib import admin
from .models import Torneo, Encuentro, Incidente, RankingConflictividad


@admin.register(Torneo)
class TorneoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'activo', 'fecha_inicio', 'fecha_fin']
    list_filter = ['activo', 'nombre']
    search_fields = ['nombre']


@admin.register(Encuentro)
class EncuentroAdmin(admin.ModelAdmin):
    list_display = ['club_local', 'club_visitante', 'fecha', 'hora', 'nivel_riesgo', 'torneo']
    list_filter = ['torneo', 'nivel_riesgo', 'fecha']
    search_fields = ['club_local', 'club_visitante', 'estadio']
    date_hierarchy = 'fecha'
    ordering = ['fecha', 'hora']


@admin.register(Incidente)
class IncidenteAdmin(admin.ModelAdmin):
    list_display = ['encuentro', 'tipo', 'fecha_incidente', 'reportado_por']
    list_filter = ['tipo', 'fecha_incidente']
    search_fields = ['descripcion', 'encuentro__club_local', 'encuentro__club_visitante']
    date_hierarchy = 'fecha_incidente'


@admin.register(RankingConflictividad)
class RankingConflictividadAdmin(admin.ModelAdmin):
    list_display = ['club', 'torneo', 'cantidad_conflictos', 'nivel_riesgo_promedio']
    list_filter = ['torneo', 'nivel_riesgo_promedio']
    search_fields = ['club']
    ordering = ['-cantidad_conflictos']
