from django.urls import path
from . import views

app_name = 'clubes'

urlpatterns = [
    path('', views.clubes_index_view, name='index'),
    path('club/<int:club_id>/', views.club_detalle_view, name='detalle'),
    path('club/<int:club_id>/facciones/', views.facciones_view, name='facciones'),
    path('club/<int:club_id>/antecedentes/', views.antecedentes_view, name='antecedentes'),
    path('exportar/', views.exportar_clubes_view, name='exportar'),
    path('sincronizar/', views.sincronizar_clubes_view, name='sincronizar'),
    path('mapa-territorios/', views.mapa_territorios_view, name='mapa_territorios'),
]
