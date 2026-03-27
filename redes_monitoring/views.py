from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import AlertaRedes, TendenciasKeyword
from .services.rss_service import RSSMonitoringService


@login_required
def redes_monitoring_index_view(request):
    """Vista principal del módulo de redes y monitoreo."""
    # Obtener filtros de la URL
    fuente = request.GET.get('fuente', '')
    nivel_riesgo = request.GET.get('nivel_riesgo', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    
    # Query base
    alertas_query = AlertaRedes.objects.all()
    
    # Aplicar filtros
    if fuente:
        alertas_query = alertas_query.filter(fuente=fuente)
    
    if nivel_riesgo:
        alertas_query = alertas_query.filter(nivel_riesgo=nivel_riesgo)
    
    if fecha_desde:
        alertas_query = alertas_query.filter(fecha_alerta__gte=fecha_desde)
    
    # Paginación
    paginator = Paginator(alertas_query, 20)
    page_number = request.GET.get('page')
    alertas = paginator.get_page(page_number)
    
    # Estadísticas
    total_alertas = AlertaRedes.objects.count()
    alertas_hoy = AlertaRedes.objects.filter(
        fecha_alerta__date=timezone.now().date()
    ).count()
    alertas_alto_riesgo = AlertaRedes.objects.filter(
        nivel_riesgo__in=['ALTO', 'CRITICO']
    ).count()
    
    # Tendencias de keywords (últimos 7 días)
    fecha_limite = timezone.now().date() - timedelta(days=7)
    tendencias = TendenciasKeyword.objects.filter(
        fecha_tendencia__gte=fecha_limite
    ).order_by('-frecuencia')[:10]
    
    context = {
        'alertas': alertas,
        'tendencias': tendencias,
        'estadisticas': {
            'total': total_alertas,
            'hoy': alertas_hoy,
            'alto_riesgo': alertas_alto_riesgo,
        },
        'filtros': {
            'fuente': fuente,
            'nivel_riesgo': nivel_riesgo,
            'fecha_desde': fecha_desde,
        }
    }
    
    return render(request, 'redes_monitoring/index.html', context)


@login_required
def obtener_feed_rss_view(request):
    """Vista para obtener el feed RSS actualizado."""
    try:
        rss_service = RSSMonitoringService()
        feed_data = rss_service.obtener_y_procesar_feed()
        
        return JsonResponse({
            'success': True,
            'data': feed_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def alertas_por_club_view(request):
    """Vista para mostrar alertas filtradas por club."""
    club = request.GET.get('club', '')
    
    if not club:
        return JsonResponse({
            'success': False,
            'error': 'Club no especificado'
        })
    
    alertas = AlertaRedes.objects.filter(
        clubes_mencionados__icontains=club
    ).order_by('-fecha_alerta')[:20]
    
    alertas_data = []
    for alerta in alertas:
        alertas_data.append({
            'id': alerta.id,
            'titulo': alerta.titulo,
            'descripcion': alerta.descripcion,
            'fuente': alerta.get_fuente_display(),
            'nivel_riesgo': alerta.get_nivel_riesgo_display(),
            'fecha_alerta': alerta.fecha_alerta.strftime('%d/%m/%Y %H:%M'),
            'url': alerta.url,
        })
    
    return JsonResponse({
        'success': True,
        'data': alertas_data
    })


@login_required
def marcar_alerta_procesada_view(request, alerta_id):
    """Vista para marcar una alerta como procesada."""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
    
    try:
        alerta = AlertaRedes.objects.get(id=alerta_id)
        alerta.procesado = True
        alerta.procesado_por = request.user
        alerta.fecha_procesamiento = timezone.now()
        alerta.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Alerta marcada como procesada'
        })
    except AlertaRedes.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Alerta no encontrada'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
