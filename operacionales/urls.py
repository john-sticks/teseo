from django.urls import path
from . import views

app_name = 'operacionales'

urlpatterns = [
    path('', views.operacionales_index_view, name='index'),
    path('operacional/<int:operacional_id>/', views.operacional_detalle_view, name='detalle'),
    path('descargar/<int:operacional_id>/', views.descargar_pdf_view, name='descargar'),
    path('ver/<int:operacional_id>/', views.ver_pdf_view, name='ver_pdf'),
]
