from django.urls import path
from . import views

app_name = 'derecho_admision'

urlpatterns = [
    path('', views.derecho_admision_index_view, name='index'),
    path('derecho/<int:derecho_id>/', views.derecho_admision_detalle_view, name='detalle'),
    path('exportar/', views.exportar_derechos_view, name='exportar'),
    path('sincronizar/', views.sincronizar_derechos_view, name='sincronizar'),
]
