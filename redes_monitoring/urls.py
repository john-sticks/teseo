from django.urls import path
from . import views

app_name = 'redes_monitoring'

urlpatterns = [
    path('', views.redes_monitoring_index_view, name='index'),
    path('feed-rss/', views.obtener_feed_rss_view, name='feed_rss'),
    path('alertas-club/', views.alertas_por_club_view, name='alertas_club'),
    path('marcar-procesada/<int:alerta_id>/', views.marcar_alerta_procesada_view, name='marcar_procesada'),
]
