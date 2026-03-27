from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages

from .models import FaccionHinchas, ReferenteHinchas, TerritorioHinchas, AntecedenteClub
from dashboard.models import Club
# from .services.google_sheets_service import ClubesGoogleSheetsService


@login_required
def clubes_index_view(request):
    """Vista principal del módulo de clubes."""
    # Obtener filtros de la URL
    busqueda = request.GET.get('busqueda', '')
    provincia = request.GET.get('provincia', '')
    torneo_selected = request.GET.get('torneo', 'LPF')
    
    # Mapear nombres de torneos para compatibilidad
    torneo_mapping = {
        'COPA LIBERTADORES': 'COPA LIBERTADORES',
        'COPA SUDAMERICA': 'COPA SUDAMERICA', 
        'COPA ARGENTINA': 'COPA ARGENTINA'
    }
    
    torneo_db_name = torneo_mapping.get(torneo_selected, torneo_selected)
    
    # Query base - filtrar por torneo
    clubes_query = Club.objects.filter(torneo=torneo_db_name)
    
    # Aplicar filtros
    if busqueda:
        clubes_query = clubes_query.filter(
            Q(nombre__icontains=busqueda) |
            Q(estadio__icontains=busqueda) |
            Q(direccion__icontains=busqueda) |
            Q(ubicacion_sede__icontains=busqueda)
        )
    
    # Nota: El modelo Club del dashboard no tiene campo provincia, 
    # por lo que este filtro se mantiene pero no funcionará hasta que se agregue el campo
    
    # Paginación
    paginator = Paginator(clubes_query, 12)
    page_number = request.GET.get('page')
    clubes = paginator.get_page(page_number)
    
    # Obtener provincias únicas para el filtro (solo del torneo seleccionado)
    # Nota: El modelo Club del dashboard no tiene campo provincia, 
    # por lo que se usa una lista vacía hasta que se agregue el campo
    provincias = []
    
    context = {
        'clubes': clubes,
        'provincias': provincias,
        'torneo_selected': torneo_selected,
        'filtros': {
            'busqueda': busqueda,
            'provincia': provincia,
            'torneo_selected': torneo_selected,
        }
    }
    
    return render(request, 'clubes/index.html', context)


@login_required
def club_detalle_view(request, club_id):
    """Vista detallada de un club específico."""
    club = get_object_or_404(Club, id=club_id)
    
    # Obtener datos relacionados
    facciones = FaccionHinchas.objects.filter(club=club, activa=True).prefetch_related('referentes', 'territorios')
    antecedentes = AntecedenteClub.objects.filter(club=club).order_by('-fecha_incidente')[:10]
    
    # Estadísticas del club
    total_facciones = facciones.count()
    total_referentes = sum(faccion.referentes.count() for faccion in facciones)
    total_territorios = sum(faccion.territorios.count() for faccion in facciones)
    total_antecedentes = AntecedenteClub.objects.filter(club=club).count()
    
    context = {
        'club': club,
        'facciones': facciones,
        'antecedentes': antecedentes,
        'estadisticas': {
            'total_facciones': total_facciones,
            'total_referentes': total_referentes,
            'total_territorios': total_territorios,
            'total_antecedentes': total_antecedentes,
        },
        'user_can_edit': request.user.is_staff,  # Solo administradores pueden editar
    }
    
    return render(request, 'clubes/detalle.html', context)


@login_required
def facciones_view(request, club_id):
    """Vista de facciones de hinchadas de un club."""
    club = get_object_or_404(Club, id=club_id)
    facciones = FaccionHinchas.objects.filter(club=club).prefetch_related('referentes', 'territorios')
    
    context = {
        'club': club,
        'facciones': facciones,
    }
    
    return render(request, 'clubes/facciones.html', context)


@login_required
def antecedentes_view(request, club_id):
    """Vista de antecedentes de un club."""
    club = get_object_or_404(Club, id=club_id)
    
    # Filtros
    tipo = request.GET.get('tipo', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    antecedentes_query = AntecedenteClub.objects.filter(club=club)
    
    if tipo:
        antecedentes_query = antecedentes_query.filter(tipo=tipo)
    
    if fecha_desde:
        antecedentes_query = antecedentes_query.filter(fecha_incidente__gte=fecha_desde)
    
    if fecha_hasta:
        antecedentes_query = antecedentes_query.filter(fecha_incidente__lte=fecha_hasta)
    
    # Paginación
    paginator = Paginator(antecedentes_query, 15)
    page_number = request.GET.get('page')
    antecedentes = paginator.get_page(page_number)
    
    context = {
        'club': club,
        'antecedentes': antecedentes,
        'filtros': {
            'tipo': tipo,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
    }
    
    return render(request, 'clubes/antecedentes.html', context)


@login_required
def exportar_clubes_view(request):
    """Vista para exportar datos de clubes."""
    try:
        torneo = request.GET.get('torneo', 'LPF')
        
        # Mapear nombres de torneos para compatibilidad
        torneo_mapping = {
            'COPA LIBERTADORES': 'COPA LIBERTADORES',
            'COPA SUDAMERICA': 'COPA SUDAMERICA', 
            'COPA ARGENTINA': 'COPA ARGENTINA'
        }
        
        torneo_db_name = torneo_mapping.get(torneo, torneo)
        
        # Obtener datos desde la base de datos
        clubes = Club.objects.filter(torneo=torneo_db_name)
        
        datos_clubes = []
        for club in clubes:
            datos_clubes.append({
                'nombre': club.nombre,
                'escudo_url': club.escudo_url,
                'estadio': club.estadio,
                'capacidad': club.capacidad,
                'fecha_fundacion': club.fecha_fundacion,
                'direccion': club.direccion,
                'ubicacion_sede': club.ubicacion_sede,
                'barras': club.barras,
                'torneo': club.torneo,
            })
        
        return JsonResponse({
            'success': True,
            'data': datos_clubes,
            'tipo': 'clubes',
            'torneo': torneo
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def sincronizar_clubes_view(request):
    """Vista para sincronizar datos de clubes con Google Sheets."""
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
    
    try:
        from dashboard.services.sheets_sync_service import SheetsSyncService
        from sheets_config import SHEETS_MAP
        
        torneo = request.GET.get('torneo', 'LPF')
        
        # Mapear nombres de torneos para compatibilidad con sheets_config
        torneo_mapping = {
            'COPA LIBERTADORES': 'COPA LIBERTADORES',
            'COPA SUDAMERICA': 'COPA SUDAMERICA', 
            'COPA ARGENTINA': 'COPA ARGENTINA'
        }
        
        torneo_config_name = torneo_mapping.get(torneo, torneo)
        print(f"DEBUG: Torneo original: {torneo}")
        print(f"DEBUG: Torneo config name: {torneo_config_name}")
        
        # Obtener configuración de sheets para el torneo
        sheets_config = SHEETS_MAP.get(torneo_config_name, {})
        print(f"DEBUG: SHEETS_MAP keys: {list(SHEETS_MAP.keys())}")
        print(f"DEBUG: sheets_config para {torneo_config_name}: {sheets_config}")
        
        if not sheets_config:
            return JsonResponse({
                'success': False,
                'error': f'No hay configuración de sheets para el torneo {torneo}'
            })
        
        # Crear servicio de sincronización
        sync_service = SheetsSyncService()
        
        # Sincronizar solo clubes
        clubes_config = {'clubes': sheets_config.get('clubes', {})}
        
        # Debug: imprimir configuración
        print(f"DEBUG: Torneo config name: {torneo_config_name}")
        print(f"DEBUG: Sheets config: {sheets_config}")
        print(f"DEBUG: Clubes config: {clubes_config}")
        print(f"DEBUG: Clubes config detalle: {clubes_config.get('clubes', {})}")
        
        created, updated, deleted, errors = sync_service.sync_tournament(torneo_config_name, clubes_config)
        
        if errors:
            return JsonResponse({
                'success': False,
                'error': f'Errores durante la sincronización: {", ".join(errors)}',
                'debug_info': {
                    'torneo_config_name': torneo_config_name,
                    'sheets_config': str(sheets_config),
                    'clubes_config': str(clubes_config),
                    'errors': errors
                }
            })
        
        messages.success(request, f'Clubes sincronizados correctamente para {torneo}')
        
        return JsonResponse({
            'success': True,
            'message': f'Clubes sincronizados correctamente para {torneo}',
            'datos_actualizados': {
                'creados': created,
                'actualizados': updated,
                'eliminados': deleted
            },
            'debug_info': {
                'torneo_config_name': torneo_config_name,
                'sheets_config': str(sheets_config),
                'clubes_config': str(clubes_config)
            }
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"ERROR EN SINCRONIZACIÓN: {str(e)}")
        print(f"TRACEBACK: {error_traceback}")
        messages.error(request, f'Error al sincronizar clubes: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': error_traceback
        })


@login_required
def mapa_territorios_view(request):
    """Vista del mapa de territorios de hinchadas."""
    club_id = request.GET.get('club', '')
    
    if club_id:
        club = get_object_or_404(Club, id=club_id)
        territorios = TerritorioHinchas.objects.filter(
            faccion__club=club
        ).select_related('faccion')
    else:
        club = None
        territorios = TerritorioHinchas.objects.all().select_related('faccion')
    
    # Obtener todos los clubes para el filtro
    clubes = Club.objects.all().order_by('nombre')
    
    context = {
        'club': club,
        'clubes': clubes,
        'territorios': list(territorios.values(
            'id', 'nombre', 'coordenadas_lat', 'coordenadas_lng',
            'direccion', 'ciudad', 'provincia', 'observaciones',
            'faccion__nombre', 'faccion__club__nombre', 'faccion__club__nombre_corto'
        )),
    }
    
    return render(request, 'clubes/mapa_territorios.html', context)
