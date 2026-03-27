from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages

from .models import DerechoAdmision
# from .services.google_sheets_service import DerechoAdmisionGoogleSheetsService


@login_required
def derecho_admision_index_view(request):
    """Vista principal del módulo de derecho de admisión."""
    # Obtener filtros de la URL
    club = request.GET.get('club', '')
    estado = request.GET.get('estado', '')
    motivo = request.GET.get('motivo', '')
    
    # Query base
    derechos_query = DerechoAdmision.objects.all()
    
    # Aplicar filtros
    if club:
        derechos_query = derechos_query.filter(club__icontains=club)
    
    if estado:
        derechos_query = derechos_query.filter(estado=estado)
    
    if motivo:
        derechos_query = derechos_query.filter(motivo=motivo)
    
    # Paginación
    paginator = Paginator(derechos_query, 15)
    page_number = request.GET.get('page')
    derechos = paginator.get_page(page_number)
    
    # Estadísticas
    total_derechos = DerechoAdmision.objects.count()
    derechos_vigentes = DerechoAdmision.objects.filter(estado='VIGENTE').count()
    derechos_vencidos = DerechoAdmision.objects.filter(
        estado='VIGENTE',
        fecha_vencimiento__lt=timezone.now().date()
    ).count()
    
    context = {
        'derechos': derechos,
        'estadisticas': {
            'total': total_derechos,
            'vigentes': derechos_vigentes,
            'vencidos': derechos_vencidos,
        },
        'filtros': {
            'club': club,
            'estado': estado,
            'motivo': motivo,
        }
    }
    
    return render(request, 'derecho_admision/index.html', context)


@login_required
def derecho_admision_detalle_view(request, derecho_id):
    """Vista detallada de un derecho de admisión específico."""
    derecho = get_object_or_404(DerechoAdmision, id=derecho_id)
    
    context = {
        'derecho': derecho,
        'user_can_edit': request.user.is_staff,
    }
    
    return render(request, 'derecho_admision/detalle.html', context)


@login_required
def exportar_derechos_view(request):
    """Vista para exportar datos de derechos de admisión."""
    try:
        sheets_service = DerechoAdmisionGoogleSheetsService()
        torneo = request.GET.get('torneo', 'LPF')
        
        datos_derechos = sheets_service.obtener_datos_derechos(torneo)
        
        return JsonResponse({
            'success': True,
            'data': datos_derechos,
            'tipo': 'derechos_admision',
            'torneo': torneo
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def sincronizar_derechos_view(request):
    """Vista para sincronizar datos de derechos de admisión con Google Sheets."""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
    
    try:
        sheets_service = DerechoAdmisionGoogleSheetsService()
        torneo = request.GET.get('torneo', 'LPF')
        
        resultado = sheets_service.sincronizar_derechos(torneo)
        
        messages.success(request, f'Derechos de admisión sincronizados correctamente para {torneo}')
        
        return JsonResponse({
            'success': True,
            'message': f'Derechos sincronizados correctamente para {torneo}',
            'datos_actualizados': resultado
        })
    except Exception as e:
        messages.error(request, f'Error al sincronizar derechos: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


from django.utils import timezone
