from django.urls import path
from . import views
from . import views_usuarios

app_name = 'dashboard'

urlpatterns = [
    path('', views.welcome_view, name='welcome'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('encuentro/<int:encuentro_id>/', views.encuentros_detalle_view, name='encuentro_detalle'),
    path('mapa/', views.mapa_incidentes_view, name='mapa_incidentes'),
    path('exportar/', views.exportar_datos_view, name='exportar_datos'),
    path('sincronizar/', views.sincronizar_view, name='sincronizar_sheets'),
    path('rss-feed/', views.rss_feed_view, name='rss_feed'),
    # Nuevas secciones
    path('clubes/', views.clubes_view, name='clubes'),
    path('derecho-admision/', views.derecho_admision_view, name='derecho_admision'),
    path('redes-monitoring/', views.redes_monitoring_view, name='redes_monitoring'),
    path('operacionales/', views.operacionales_view, name='operacionales'),
    
    # URLs de gestión de usuarios (nuevas)
    path('gestion-usuarios/', views_usuarios.gestion_usuarios_view, name='gestion_usuarios'),
    path('crear-usuario/', views_usuarios.crear_usuario_view, name='crear_usuario'),
    path('editar-usuario/<int:user_id>/', views_usuarios.editar_usuario_view, name='editar_usuario'),
    path('eliminar-usuario/<int:user_id>/', views_usuarios.eliminar_usuario_view, name='eliminar_usuario'),
    path('auditoria/', views_usuarios.auditoria_view, name='auditoria'),
    path('usuarios-activos/', views_usuarios.usuarios_activos_view, name='usuarios_activos'),
    path('mi-perfil/', views_usuarios.mi_perfil_view, name='mi_perfil'),
    path('cerrar-sesion-otras/', views_usuarios.cerrar_sesion_otras_view, name='cerrar_sesion_otras'),
    
    # URLs de usuarios (legacy - mantener compatibilidad)
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/create/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:pk>/edit/', views.usuario_edit, name='usuario_edit'),
    path('usuarios/<int:pk>/delete/', views.usuario_delete, name='usuario_delete'),
    
    # Edición de Google Sheets
    path('editar/club/<int:club_id>/', views.editar_club_view, name='editar_club'),
    path('editar/encuentro/<int:encuentro_id>/', views.editar_encuentro_view, name='editar_encuentro'),
    path('test-google-sheets/', views.test_google_sheets_connection, name='test_google_sheets'),
    path('refresh-rss/', views.refresh_rss_data_view, name='refresh_rss'),
]
