from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .models import OperacionalVigente


@login_required
def operacionales_index_view(request):
    """Vista principal del módulo de operacionales vigentes."""
    # Obtener filtros de la URL
    torneo = request.GET.get('torneo', '')
    tipo = request.GET.get('tipo', '')
    busqueda = request.GET.get('busqueda', '')
    
    # Query base
    operacionales_query = OperacionalVigente.objects.filter(activo=True)
    
    # Aplicar filtros
    if torneo:
        operacionales_query = operacionales_query.filter(torneo=torneo)
    
    if tipo:
        operacionales_query = operacionales_query.filter(tipo=tipo)
    
    if busqueda:
        operacionales_query = operacionales_query.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(operacionales_query, 12)
    page_number = request.GET.get('page')
    operacionales = paginator.get_page(page_number)
    
    # Estadísticas
    total_operacionales = OperacionalVigente.objects.filter(activo=True).count()
    operacionales_vencidos = OperacionalVigente.objects.filter(
        activo=True,
        fecha_vigencia__lt=timezone.now().date()
    ).count()
    
    # Operacionales próximos a vencer (30 días)
    fecha_limite = timezone.now().date() + timedelta(days=30)
    proximos_vencer = OperacionalVigente.objects.filter(
        activo=True,
        fecha_vigencia__range=[timezone.now().date(), fecha_limite]
    ).count()
    
    context = {
        'operacionales': operacionales,
        'estadisticas': {
            'total': total_operacionales,
            'vencidos': operacionales_vencidos,
            'proximos_vencer': proximos_vencer,
        },
        'filtros': {
            'torneo': torneo,
            'tipo': tipo,
            'busqueda': busqueda,
        }
    }
    
    return render(request, 'operacionales/index.html', context)


@login_required
def operacional_detalle_view(request, operacional_id):
    """Vista detallada de un operacional específico."""
    operacional = get_object_or_404(OperacionalVigente, id=operacional_id)
    
    context = {
        'operacional': operacional,
        'user_can_edit': request.user.is_staff,
    }
    
    return render(request, 'operacionales/detalle.html', context)


@login_required
def descargar_pdf_view(request, operacional_id):
    """Vista para descargar el PDF del operacional."""
    operacional = get_object_or_404(OperacionalVigente, id=operacional_id)
    
    if operacional.archivo_pdf:
        response = HttpResponse(
            operacional.archivo_pdf.read(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{operacional.nombre}.pdf"'
        return response
    else:
        return HttpResponse("Archivo no encontrado", status=404)


@login_required
def ver_pdf_view(request, operacional_id):
    """Vista para ver el PDF del operacional en el navegador."""
    operacional = get_object_or_404(OperacionalVigente, id=operacional_id)
    
    if operacional.archivo_pdf:
        response = HttpResponse(
            operacional.archivo_pdf.read(),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'inline; filename="{operacional.nombre}.pdf"'
        return response
    else:
        return HttpResponse("Archivo no encontrado", status=404)
