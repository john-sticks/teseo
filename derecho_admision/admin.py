from django.contrib import admin
from .models import DerechoAdmision


@admin.register(DerechoAdmision)
class DerechoAdmisionAdmin(admin.ModelAdmin):
    list_display = ['club', 'motivo', 'fecha_imposicion', 'fecha_vencimiento', 'estado']
    list_filter = ['estado', 'motivo', 'fecha_imposicion']
    search_fields = ['club', 'descripcion']
    date_hierarchy = 'fecha_imposicion'
    readonly_fields = ['fecha_creacion', 'ultima_actualizacion']
