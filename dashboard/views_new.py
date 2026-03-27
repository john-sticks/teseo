from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from datetime import datetime, timedelta
import json

from .models import Torneo, Encuentro, Incidente, RankingConflictividad, Club, DerechoAdmision, OperacionalDoc
from .services.google_sheets_service import GoogleSheetsService
from .services.sheets_sync_service import SheetsSyncService
from .services.rss_service import RSSService


@login_required
def dashboard_view(request):
    """Vista principal del dashboard con información crítica."""
    context = {}
    
    # Obtener filtros de la URL
    torneo_selected = request.GET.get('torneo', 'LPF')
    club_filter = request.GET.get('club', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    nivel_riesgo = request.GET.get('nivel_riesgo', '')
    
    # Mapear nombres de torneos para compatibilidad
    torneo_mapping = {
        'COPA LIBERTADORES': 'COPA_LIBERTADORES',
        'COPA SUDAMERICA': 'COPA_SUDAMERICANA'
    }
    
    torneo_db_name = torneo_mapping.get(torneo_selected, torneo_selected)
    
    # Obtener torneo actual
    try:
        torneo_actual = Torneo.objects.get(nombre=torneo_db_name)
    except Torneo.DoesNotExist:
        torneo_actual = None
    
    # Obtener datos desde la base de datos (sincronizados)
    encuentros_query = Encuentro.objects.filter(torneo__nombre=torneo_db_name)
    incidentes_query = Incidente.objects.filter(torneo=torneo_db_name)
    ranking_query = RankingConflictividad.objects.filter(torneo__nombre=torneo_db_name)
    
    # Aplicar filtros
    if club_filter:
        encuentros_query = encuentros_query.filter(
            Q(club_local__icontains=club_filter) | Q(club_visitante__icontains=club_filter)
        )
        incidentes_query = incidentes_query.filter(
            Q(club_local__icontains=club_filter) | Q(club_visitante__icontains=club_filter)
        )
    
    if nivel_riesgo:
        encuentros_query = encuentros_query.filter(nivel_riesgo=nivel_riesgo.upper())
    
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            encuentros_query = encuentros_query.filter(fecha__gte=fecha_desde_obj)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            encuentros_query = encuentros_query.filter(fecha__lte=fecha_hasta_obj)
        except ValueError:
            pass
    
    # Obtener datos procesados
    proximos_encuentros = encuentros_query.order_by('fecha', 'hora')[:10]
    ranking_data = list(ranking_query.order_by('-cantidad_conflictos')[:10])
    incidentes_data = list(incidentes_query.values(
        'id', 'tipo', 'latitud', 'longitud', 'descripcion',
        'club_local', 'club_visitante', 'estadio', 'fecha_incidente'
    ))
    
    # Estadísticas generales
    total_encuentros = encuentros_query.count()
    encuentros_alto_riesgo = encuentros_query.filter(
        nivel_riesgo__in=['ALTO', 'CRITICO']
    ).count()
    total_incidentes = incidentes_query.count()
    
    context.update({
        'torneo_actual': torneo_actual,
        'torneos': Torneo.objects.filter(activo=True),
        'proximos_encuentros': proximos_encuentros,
        'ranking_conflictividad': ranking_data,
        'incidentes_mapa': json.dumps(incidentes_data, default=str),
        'estadisticas': {
            'total_encuentros': total_encuentros,
            'encuentros_alto_riesgo': encuentros_alto_riesgo,
            'total_incidentes': total_incidentes,
            'porcentaje_riesgo': round((encuentros_alto_riesgo / total_encuentros * 100) if total_encuentros > 0 else 0, 1)
        },
        'filtros': {
            'torneo_selected': torneo_selected,
            'club_filter': club_filter,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'nivel_riesgo': nivel_riesgo,
        }
    })
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def encuentros_detalle_view(request, encuentro_id):
    """Vista detallada de un encuentro específico."""
    encuentro = get_object_or_404(Encuentro, id=encuentro_id)
    incidentes = Incidente.objects.filter(encuentro=encuentro).order_by('-fecha_incidente')
    
    context = {
        'encuentro': encuentro,
        'incidentes': incidentes,
        'user_can_edit': request.user.is_staff,  # Solo administradores pueden editar
    }
    
    return render(request, 'dashboard/encuentro_detalle.html', context)


@login_required
def mapa_incidentes_view(request):
    """Vista del mapa interactivo de incidentes."""
    torneo_selected = request.GET.get('torneo', 'LPF')
    
    # Obtener incidentes sincronizados desde la base de datos
    incidentes = Incidente.objects.filter(torneo=torneo_selected).exclude(
        latitud__isnull=True, longitud__isnull=True
    )
    
    context = {
        'incidentes': list(incidentes.values(
            'id', 'tipo', 'latitud', 'longitud', 'descripcion',
            'club_local', 'club_visitante', 'estadio', 'fecha_incidente'
        )),
        'torneos': Torneo.objects.filter(activo=True),
        'torneo_selected': torneo_selected,
    }
    
    return render(request, 'dashboard/mapa_incidentes.html', context)


@login_required
def sincronizar_view(request):
    """Vista para sincronizar datos con Google Sheets."""
    torneo = request.GET.get('torneo', 'LPF')
    
    # Mapear nombres de torneos para compatibilidad
    torneo_mapping = {
        'COPA LIBERTADORES': 'COPA LIBERTADORES',
        'COPA SUDAMERICA': 'COPA SUDAMERICA'
    }
    
    torneo_config = torneo_mapping.get(torneo, torneo)
    
    if request.method == 'POST':
        try:
            sync_service = SheetsSyncService()
            from sheets_config import SHEETS_MAP
            
            if torneo_config in SHEETS_MAP:
                created, updated, errors = sync_service.sync_tournament(torneo_config, SHEETS_MAP[torneo_config])
                
                return JsonResponse({
                    'success': True,
                    'resultado': {
                        'created': created,
                        'updated': updated,
                        'errors': errors
                    },
                    'message': f'Sincronización completada para {torneo}: {created} creados, {updated} actualizados'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Torneo {torneo} no encontrado en la configuración'
                })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error en la sincronización: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido'
    }, status=405)


@login_required
def exportar_datos_view(request):
    """Vista para exportar datos en formato CSV/Excel."""
    torneo_selected = request.GET.get('torneo', 'LPF')
    tipo_datos = request.GET.get('tipo', 'encuentros')
    
    if tipo_datos == 'encuentros':
        datos = Encuentro.objects.filter(torneo__nombre=torneo_selected).values(
            'fecha', 'hora', 'club_local', 'club_visitante', 
            'estadio', 'nivel_riesgo', 'motivo_alerta'
        )
    elif tipo_datos == 'incidentes':
        datos = Incidente.objects.filter(
            encuentro__torneo__nombre=torneo_selected
        ).values(
            'tipo', 'descripcion', 'latitud', 'longitud', 
            'fecha_incidente', 'encuentro__club_local', 'encuentro__club_visitante'
        )
    elif tipo_datos == 'ranking':
        datos = RankingConflictividad.objects.filter(
            torneo__nombre=torneo_selected
        ).values(
            'club', 'cantidad_conflictos', 'nivel_riesgo_promedio', 'ultimo_incidente'
        )
    else:
        datos = []
    
    # Convertir a lista para JSON
    datos_lista = list(datos)
    
    return JsonResponse({
        'success': True,
        'data': datos_lista,
        'tipo': tipo_datos,
        'torneo': torneo_selected
    })


@login_required
def sincronizar_google_sheets_view(request):
    """Vista para sincronizar datos con Google Sheets."""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
    
    torneo = request.GET.get('torneo', 'LPF')
    
    try:
        sheets_service = GoogleSheetsService()
        resultado = sheets_service.sincronizar_torneo(torneo)
        
        return JsonResponse({
            'success': True,
            'message': f'Datos sincronizados correctamente para {torneo}',
            'datos_actualizados': resultado
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def rss_feed_view(request):
    """Vista para mostrar el feed RSS de redes sociales."""
    try:
        rss_service = RSSService()
        feed_data = rss_service.obtener_feed()
        
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
def clubes_view(request):
    """Vista para mostrar información de clubes."""
    torneo_selected = request.GET.get('torneo', 'LPF')
    
    # Mapear nombres de torneos para compatibilidad
    torneo_mapping = {
        'COPA LIBERTADORES': 'COPA_LIBERTADORES',
        'COPA SUDAMERICA': 'COPA_SUDAMERICANA'
    }
    
    torneo_db_name = torneo_mapping.get(torneo_selected, torneo_selected)
    
    # Obtener clubes del torneo seleccionado
    clubes = Club.objects.filter(torneo__nombre=torneo_db_name)
    
    context = {
        'torneo_selected': torneo_selected,
        'clubes': clubes,
        'filtros': {
            'torneo_selected': torneo_selected
        }
    }
    
    return render(request, 'dashboard/clubes.html', context)


@login_required
def derecho_admision_view(request):
    """Vista para mostrar derechos de admisión."""
    torneo_selected = request.GET.get('torneo', 'LPF')
    
    # Mapear nombres de torneos para compatibilidad
    torneo_mapping = {
        'COPA LIBERTADORES': 'COPA_LIBERTADORES',
        'COPA SUDAMERICA': 'COPA_SUDAMERICANA'
    }
    
    torneo_db_name = torneo_mapping.get(torneo_selected, torneo_selected)
    
    # Obtener derechos de admisión del torneo seleccionado
    derechos = DerechoAdmision.objects.filter(torneo__nombre=torneo_db_name)
    
    context = {
        'torneo_selected': torneo_selected,
        'derechos': derechos,
        'filtros': {
            'torneo_selected': torneo_selected
        }
    }
    
    return render(request, 'dashboard/derecho_admision.html', context)


@login_required
def redes_monitoring_view(request):
    """Vista para monitoreo de redes y navegadores."""
    torneo_selected = request.GET.get('torneo', 'LPF')
    
    context = {
        'torneo_selected': torneo_selected,
        'filtros': {
            'torneo_selected': torneo_selected
        }
    }
    
    return render(request, 'dashboard/redes_monitoring.html', context)


@login_required
def operacionales_view(request):
    """Vista para documentos operacionales vigentes."""
    torneo_selected = request.GET.get('torneo', 'LPF')
    
    # Mapear nombres de torneos para compatibilidad
    torneo_mapping = {
        'COPA LIBERTADORES': 'COPA_LIBERTADORES',
        'COPA SUDAMERICA': 'COPA_SUDAMERICANA'
    }
    
    torneo_db_name = torneo_mapping.get(torneo_selected, torneo_selected)
    
    # Obtener documentos operacionales del torneo seleccionado
    operacionales = OperacionalDoc.objects.filter(torneo__nombre=torneo_db_name)
    
    context = {
        'torneo_selected': torneo_selected,
        'operacionales': operacionales,
        'filtros': {
            'torneo_selected': torneo_selected
        }
    }
    
    return render(request, 'dashboard/operacionales.html', context)
