from django.contrib import admin
from .models import Club, FaccionHinchas, ReferenteHinchas, TerritorioHinchas, AntecedenteClub


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nombre_corto', 'ciudad', 'provincia', 'presidente']
    list_filter = ['provincia', 'ciudad']
    search_fields = ['nombre', 'nombre_corto', 'ciudad', 'estadio']
    readonly_fields = ['fecha_creacion', 'ultima_actualizacion']


@admin.register(FaccionHinchas)
class FaccionHinchasAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'club', 'tipo', 'activa', 'cantidad_estimada']
    list_filter = ['tipo', 'activa', 'club']
    search_fields = ['nombre', 'club__nombre']


@admin.register(ReferenteHinchas)
class ReferenteHinchasAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'apodo', 'faccion', 'telefono', 'activo']
    list_filter = ['activo', 'faccion__club']
    search_fields = ['nombre', 'apodo', 'faccion__nombre']


@admin.register(TerritorioHinchas)
class TerritorioHinchasAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'faccion', 'ciudad', 'provincia']
    list_filter = ['provincia', 'ciudad', 'faccion__club']
    search_fields = ['nombre', 'direccion', 'ciudad']


@admin.register(AntecedenteClub)
class AntecedenteClubAdmin(admin.ModelAdmin):
    list_display = ['club', 'tipo', 'fecha_incidente', 'lugar', 'monto_sancion']
    list_filter = ['tipo', 'fecha_incidente', 'club']
    search_fields = ['club__nombre', 'lugar', 'descripcion']
    date_hierarchy = 'fecha_incidente'
