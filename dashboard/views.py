from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from datetime import datetime, timedelta
import json

from .models import Torneo, Encuentro, Incidente, RankingConflictividad, Club, DerechoAdmision, OperacionalDoc
from .services.sheets_sync_service import SheetsSyncService
# from .services.google_sheets_service import GoogleSheetsService
# from .services.rss_service import RSSService
# from .services.auditoria_service import AuditoriaService
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404


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
    
    # Filtros específicos para histórico de hechos
    historico_club = request.GET.get('historico_club', '')
    historico_tipo = request.GET.get('historico_tipo', '')
    historico_fecha_desde = request.GET.get('historico_fecha_desde', '')
    historico_fecha_hasta = request.GET.get('historico_fecha_hasta', '')
    
    # Mapear nombres de torneos para compatibilidad
    torneo_mapping = {
        'COPA LIBERTADORES': 'COPA LIBERTADORES',  # Los datos están guardados con espacio
        'COPA SUDAMERICA': 'COPA SUDAMERICA',
        'COPA ARGENTINA': 'COPA ARGENTINA'
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
    
    # Aplicar filtros específicos para histórico de hechos
    if historico_club:
        incidentes_query = incidentes_query.filter(
            Q(club_local__icontains=historico_club) | Q(club_visitante__icontains=historico_club)
        )
    
    if historico_tipo:
        incidentes_query = incidentes_query.filter(tipo=historico_tipo)
    
    if historico_fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(historico_fecha_desde, '%Y-%m-%d').date()
            incidentes_query = incidentes_query.filter(fecha_incidente__gte=fecha_desde_obj)
        except ValueError:
            pass
    
    if historico_fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(historico_fecha_hasta, '%Y-%m-%d').date()
            incidentes_query = incidentes_query.filter(fecha_incidente__lte=fecha_hasta_obj)
        except ValueError:
            pass
    
    # Calcular ranking de conflictividad desde incidentes reales
    RankingConflictividad.calcular_ranking_desde_incidentes(torneo_db_name)
    
    # Obtener TODOS los encuentros sin paginación
    proximos_encuentros = list(encuentros_query.order_by('fecha', 'hora'))
    ranking_data = list(ranking_query.order_by('-cantidad_conflictos')[:10])
    
    # Para el mapa, obtener TODOS los incidentes (no filtrado por torneo)
    incidentes_mapa_query = Incidente.objects.exclude(
        latitud__isnull=True, longitud__isnull=True
    )
    incidentes_mapa_data = []
    for incidente in incidentes_mapa_query.order_by('-fecha_incidente')[:50]:  # Limitar a 50 para rendimiento
        incidente_data = {
            'id': incidente.id,
            'tipo': incidente.tipo,
            'latitud': incidente.latitud,
            'longitud': incidente.longitud,
            'descripcion': incidente.descripcion,
            'club_local': incidente.club_local,
            'estadio': incidente.estadio,
            'fecha_incidente': incidente.fecha_incidente,
            'torneo': incidente.torneo,
            'raw_data': incidente.raw_data or {}
        }
        incidentes_mapa_data.append(incidente_data)
    
    # Para el histórico de hechos, usar los incidentes filtrados por torneo con paginación
    incidentes_paginator = Paginator(incidentes_query.order_by('-fecha_incidente'), 5)
    incidentes_page_number = request.GET.get('incidentes_page')
    incidentes = incidentes_paginator.get_page(incidentes_page_number)
    
    # Preparar datos para pirámides invertidas con filtros de fecha diferentes
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # Pirámide izquierda: Últimos 3 meses
    fecha_3_meses_atras = timezone.now() - timedelta(days=90)
    ranking_3_meses = ranking_query.filter(
        ultimo_incidente__gte=fecha_3_meses_atras
    ).order_by('-cantidad_conflictos')[:5]
    
    # Pirámide derecha: Desde 2020 hasta actualidad
    fecha_2020 = timezone.make_aware(datetime(2020, 1, 1))
    ranking_historico = ranking_query.filter(
        ultimo_incidente__gte=fecha_2020
    ).order_by('-cantidad_conflictos')[:5]
    
    def crear_datos_piramide(ranking_data, nombre_sufijo):
        """Función auxiliar para crear datos de pirámide"""
        piramide_data = []
        if ranking_data:
            max_conflictos = ranking_data[0].cantidad_conflictos
            
            for i, club_data in enumerate(ranking_data):
                # Calcular porcentaje basado en el club con más conflictos (100%)
                porcentaje = round((club_data.cantidad_conflictos / max_conflictos) * 100, 1) if max_conflictos > 0 else 0
                
                piramide_data.append({
                    'club': club_data.club,
                    'cantidad': club_data.cantidad_conflictos,
                    'porcentaje': porcentaje,
                    'nivel_riesgo': club_data.nivel_riesgo_promedio,
                    'color_clase': f'piramide-nivel-{i+1}'  # Para CSS
                })
        return piramide_data
    
    # Crear datos para ambas pirámides
    piramide_data_3_meses = crear_datos_piramide(list(ranking_3_meses), "3_meses")
    piramide_data_historico = crear_datos_piramide(list(ranking_historico), "historico")
    
    # Estadísticas generales
    total_encuentros = encuentros_query.count()
    encuentros_alto_riesgo = encuentros_query.filter(
        nivel_riesgo__in=['ALTO', 'CRITICO']
    ).count()
    total_incidentes = incidentes_query.count()
    
    # Determinar si es un torneo de copa (solo mostrar próximos encuentros)
    torneos_copa = ['COPA ARGENTINA', 'COPA LIBERTADORES', 'COPA SUDAMERICA']
    es_torneo_copa = torneo_selected in torneos_copa
    
    context.update({
        'torneo_actual': torneo_actual,
        'torneos': Torneo.objects.filter(activo=True),
        'encuentros': proximos_encuentros,  # Cambiado de proximos_encuentros a encuentros
        'proximos_encuentros': proximos_encuentros,
        'ranking_conflictividad': ranking_data,
        'piramide_data_3_meses': piramide_data_3_meses,  # Datos para pirámide de últimos 3 meses
        'piramide_data_historico': piramide_data_historico,  # Datos para pirámide histórica (2020-actualidad)
        'incidentes': incidentes,  # Para el histórico de hechos (filtrado por torneo con paginación)
        'incidentes_mapa': json.dumps(incidentes_mapa_data, default=str),  # Para el mapa (todos los incidentes)
        'es_torneo_copa': es_torneo_copa,  # Variable para identificar torneos de copa
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
        },
        'filtros_historico': {
            'club': historico_club,
            'tipo': historico_tipo,
            'fecha_desde': historico_fecha_desde,
            'fecha_hasta': historico_fecha_hasta,
        },
        'tipos_incidentes': ['VIOLENCIA', 'DESTRUCCION', 'INVASION', 'DISPUTA', 'OTRO'],
        'clubes_historico': sorted(set([inc.club_local for inc in incidentes_query if inc.club_local] + 
                                      [inc.club_visitante for inc in incidentes_query if inc.club_visitante]))
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
    """Vista del mapa interactivo de incidentes con filtros."""
    # Obtener parámetros de filtro
    torneo_filter = request.GET.get('torneo', '')
    club_filter = request.GET.get('club', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    
    # Query base para TODOS los incidentes (no filtrado por torneo)
    incidentes_query = Incidente.objects.exclude(
        latitud__isnull=True, longitud__isnull=True
    )
    
    # Aplicar filtros
    if torneo_filter:
        incidentes_query = incidentes_query.filter(torneo=torneo_filter)
    
    if club_filter:
        incidentes_query = incidentes_query.filter(
            Q(club_local__icontains=club_filter) | 
            Q(club_visitante__icontains=club_filter)
        )
    
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            incidentes_query = incidentes_query.filter(fecha_incidente__gte=fecha_desde_obj)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            incidentes_query = incidentes_query.filter(fecha_incidente__lte=fecha_hasta_obj)
        except ValueError:
            pass
    
    # Obtener incidentes filtrados con todos los campos necesarios
    incidentes_data = []
    for incidente in incidentes_query.order_by('-fecha_incidente'):
        incidente_data = {
            'id': incidente.id,
            'tipo': incidente.tipo,
            'latitud': incidente.latitud,
            'longitud': incidente.longitud,
            'descripcion': incidente.descripcion,
            'club_local': incidente.club_local,
            'club_visitante': incidente.club_visitante,
            'estadio': incidente.estadio,
            'fecha_incidente': incidente.fecha_incidente,
            'torneo': incidente.torneo,
            'raw_data': incidente.raw_data or {}
        }
        incidentes_data.append(incidente_data)
    
    # Obtener datos para los filtros
    torneos = Torneo.objects.filter(activo=True).values_list('nombre', flat=True)
    clubes = set()
    for incidente in incidentes_data:
        if incidente['club_local']:
            clubes.add(incidente['club_local'])
        if incidente['club_visitante']:
            clubes.add(incidente['club_visitante'])
    
    context = {
        'incidentes': json.dumps(incidentes_data, default=str),
        'torneos': sorted(torneos),
        'clubes': sorted(clubes),
        'filtros': {
            'torneo': torneo_filter,
            'club': club_filter,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        },
        'total_incidentes': len(incidentes_data)
    }
    
    return render(request, 'dashboard/mapa_incidentes.html', context)


@login_required
def sincronizar_view(request):
    """Vista para sincronizar datos con Google Sheets."""
    torneo = request.GET.get('torneo', 'LPF')
    
    # Mapear nombres de torneos para compatibilidad
    torneo_mapping = {
        'COPA LIBERTADORES': 'COPA LIBERTADORES',
        'COPA SUDAMERICA': 'COPA SUDAMERICA',
        'COPA ARGENTINA': 'COPA ARGENTINA',
        'ASCENSO': 'ASCENSO'
    }
    
    torneo_config = torneo_mapping.get(torneo, torneo)
    
    if request.method == 'POST':
        try:
            from sheets_config import SHEETS_MAP
            sync_service = SheetsSyncService()
            
            # Verificar si se solicita sincronización de tabla específica
            tabla = request.GET.get('tabla', 'all')
            print(f"DEBUG: Tabla solicitada: {tabla}")
            
            if torneo_config in SHEETS_MAP:
                sheets_config = SHEETS_MAP[torneo_config]
                print(f"DEBUG: Configuración completa: {sheets_config}")
                
                # Si se solicita solo clubes, filtrar la configuración
                if tabla == 'clubes':
                    clubes_config = {'clubes': sheets_config.get('clubes', {})}
                    print(f"DEBUG: Configuración solo clubes: {clubes_config}")
                    created, updated, deleted, errors = sync_service.sync_tournament(torneo_config, clubes_config)
                else:
                    # Sincronizar todo
                    created, updated, deleted, errors = sync_service.sync_tournament(torneo_config, sheets_config)
                
                return JsonResponse({
                    'success': True,
                    'resultado': {
                        'created': created,
                        'updated': updated,
                        'deleted': deleted,
                        'errors': errors
                    },
                    'message': f'Sincronización completada para {torneo}: {created} creados, {updated} actualizados, {deleted} eliminados'
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
            torneo=torneo_selected
        ).values(
            'tipo', 'descripcion', 'latitud', 'longitud', 
            'fecha_incidente', 'club_local', 'club_visitante'
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
    tabla = request.GET.get('tabla', 'all')  # Nueva opción para sincronizar tabla específica
    
    try:
        from .services.sheets_sync_service import SheetsSyncService
        from sheets_config import SHEETS_MAP
        
        # Mapear nombres de torneos para compatibilidad con SHEETS_MAP
        torneo_mapping = {
            'COPA LIBERTADORES': 'COPA LIBERTADORES',
            'COPA SUDAMERICA': 'COPA SUDAMERICA',
            'COPA ARGENTINA': 'COPA ARGENTINA'
        }
        
        torneo_sheets_name = torneo_mapping.get(torneo, torneo)
        
        sheets_service = SheetsSyncService()
        
        if tabla == 'all':
            # Sincronizar todo el torneo
            sheets_config = SHEETS_MAP.get(torneo_sheets_name, {})
            created, updated, deleted, errors = sheets_service.sync_tournament(torneo_sheets_name, sheets_config)
            
            resultado = {
                'created': created,
                'updated': updated,
                'deleted': deleted,
                'errors': errors
            }
        else:
            # Sincronizar tabla específica
            sheets_config = SHEETS_MAP.get(torneo_sheets_name, {})
            
            # Mapear nombres de tablas para compatibilidad
            tabla_mapping = {
                'encuentros': 'encuentros',  # Para Copa Libertadores usa 'encuentros'
                'ranking': 'ranking_clubes',
                'mapa': 'mapa_incidentes',
                'clubes': 'clubes',
                'derecho_admision': 'derechos_admision',
                'operacionales': 'operacionales_pdf'
            }
            
            tabla_key = tabla_mapping.get(tabla, tabla)
            info = sheets_config.get(tabla_key)
            
            if not info:
                return JsonResponse({
                    'success': False,
                    'error': f'No se encontró configuración para la tabla {tabla} en el torneo {torneo}'
                })
            
            created = updated = deleted = 0
            errors = []
            
            if tabla_key == 'operacionales_pdf':
                # Procesar documentos PDF
                file_id = info.get('drive_file_id')
                if file_id:
                    created, updated = sheets_service.process_operacionales(file_id, tabla_key, torneo)
                    # Los documentos operacionales no se eliminan, solo se crean/actualizan
                else:
                    errors.append('No se encontró drive_file_id para operacionales')
            else:
                # Procesar spreadsheet
                spreadsheet_id = info.get('spreadsheet_id')
                if not spreadsheet_id:
                    errors.append(f'No se encontró spreadsheet_id para {tabla}')
                else:
                    # Usar GID forzado si está disponible
                    force_gid = info.get('force_gid', '0')
                    csv_text = sheets_service.download_csv(spreadsheet_id, force_gid)
                    
                    if csv_text:
                        rows = sheets_service.parse_csv(csv_text)
                        created, updated, deleted = sheets_service._process_by_type(rows, tabla_key, torneo)
                    else:
                        errors.append(f'No se pudo descargar datos para {tabla} con GID {force_gid}')
            
            resultado = {
                'created': created,
                'updated': updated,
                'deleted': deleted,
                'errors': errors,
                'tabla': tabla
            }
        
        return JsonResponse({
            'success': True,
            'message': f'Datos sincronizados correctamente para {torneo}',
            'resultado': resultado
        })
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error en sincronización: {str(e)}")
        print(f"Traceback: {error_details}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'details': error_details
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
    busqueda = request.GET.get('busqueda', '')
    
    # Mapear nombres de torneos para compatibilidad
    torneo_mapping = {
        'COPA LIBERTADORES': 'COPA LIBERTADORES',  # Los datos están guardados con espacio
        'COPA SUDAMERICA': 'COPA SUDAMERICA',
        'COPA ARGENTINA': 'COPA ARGENTINA'
    }
    
    torneo_db_name = torneo_mapping.get(torneo_selected, torneo_selected)
    
    # Obtener clubes filtrados por torneo
    clubes_query = Club.objects.filter(torneo=torneo_db_name)
    
    # Aplicar filtro de búsqueda si se proporciona
    if busqueda:
        clubes_query = clubes_query.filter(
            Q(nombre__icontains=busqueda) |
            Q(estadio__icontains=busqueda) |
            Q(direccion__icontains=busqueda)
        )
    
    clubes = clubes_query.order_by('nombre')
    
    context = {
        'torneo_selected': torneo_selected,
        'clubes': clubes,
        'filtros': {
            'torneo_selected': torneo_selected,
            'busqueda': busqueda
        }
    }
    
    return render(request, 'dashboard/clubes.html', context)


@login_required
def derecho_admision_view(request):
    """Vista para mostrar derechos de admisión."""
    torneo_selected = request.GET.get('torneo', 'LPF')
    busqueda = request.GET.get('busqueda', '')
    
    # Mapear nombres de torneos para compatibilidad
    torneo_mapping = {
        'COPA LIBERTADORES': 'COPA LIBERTADORES',  # Los datos están guardados con espacio
        'COPA SUDAMERICA': 'COPA SUDAMERICA',
        'COPA ARGENTINA': 'COPA ARGENTINA'
    }
    
    torneo_db_name = torneo_mapping.get(torneo_selected, torneo_selected)
    
    # Obtener derechos de admisión filtrados por torneo
    derechos_query = DerechoAdmision.objects.filter(torneo=torneo_db_name)
    
    # Aplicar filtro de búsqueda si se proporciona
    if busqueda:
        derechos_query = derechos_query.filter(
            Q(nombre__icontains=busqueda) |
            Q(apellido__icontains=busqueda) |
            Q(club__icontains=busqueda) |
            Q(motivo__icontains=busqueda) |
            Q(estado__icontains=busqueda)
        )
    
    # Paginación
    derechos_paginator = Paginator(derechos_query.order_by('-fecha_inicio'), 10)
    derechos_page_number = request.GET.get('derechos_page')
    derechos = derechos_paginator.get_page(derechos_page_number)
    
    context = {
        'torneo_selected': torneo_selected,
        'derechos': derechos,
        'filtros': {
            'torneo_selected': torneo_selected,
            'busqueda': busqueda
        }
    }
    
    return render(request, 'dashboard/derecho_admision.html', context)


@login_required
def redes_monitoring_view(request):
    """Vista para monitoreo de redes sociales y análisis de tendencias."""
    torneo_selected = request.GET.get('torneo', 'LPF')
    
    try:
        from .services.rss_monitoring_service import RSSMonitoringService
        
        rss_service = RSSMonitoringService()
        
        # Obtener noticias del RSS feed - siempre JSON con fallback a XML
        noticias = rss_service.obtener_datos_rss('json')
        if not noticias:  # Si JSON falla, intentar XML
            noticias = rss_service.obtener_datos_rss('xml')
        
        # Obtener tendencias de keywords
        tendencias = rss_service.obtener_tendencias_keywords(dias=7)
        
        # Obtener alertas críticas
        alertas_criticas = rss_service.obtener_alertas_criticas()
        
        # Estadísticas generales
        total_noticias = len(noticias)
        noticias_alto_riesgo = len([n for n in noticias if n['nivel_riesgo'] in ['ALTO', 'CRITICO']])
        fuentes_unicas = len(set([n['fuente'] for n in noticias if n['fuente']]))
        
        # Agrupar por nivel de riesgo
        noticias_por_riesgo = {
            'CRITICO': [n for n in noticias if n['nivel_riesgo'] == 'CRITICO'],
            'ALTO': [n for n in noticias if n['nivel_riesgo'] == 'ALTO'],
            'MEDIO': [n for n in noticias if n['nivel_riesgo'] == 'MEDIO'],
            'BAJO': [n for n in noticias if n['nivel_riesgo'] == 'BAJO'],
            'SIN_RIESGO': [n for n in noticias if n['nivel_riesgo'] == 'SIN_RIESGO']
        }
        
    except Exception as e:
        logger.error(f"Error en redes_monitoring_view: {e}")
        noticias = []
        tendencias = []
        alertas_criticas = []
        total_noticias = 0
        noticias_alto_riesgo = 0
        fuentes_unicas = 0
        noticias_por_riesgo = {}
    
    context = {
        'torneo_selected': torneo_selected,
        'noticias': noticias,
        'tendencias': tendencias,
        'alertas_criticas': alertas_criticas,
        'noticias_por_riesgo': noticias_por_riesgo,
        'estadisticas': {
            'total_noticias': total_noticias,
            'noticias_alto_riesgo': noticias_alto_riesgo,
            'fuentes_unicas': fuentes_unicas,
            'porcentaje_riesgo': round((noticias_alto_riesgo / total_noticias * 100) if total_noticias > 0 else 0, 1)
        },
        'filtros': {
            'torneo_selected': torneo_selected
        }
    }
    
    return render(request, 'dashboard/redes_monitoring.html', context)


@login_required
def refresh_rss_data_view(request):
    """Vista AJAX para refrescar datos RSS."""
    if request.method == 'POST':
        try:
            from .services.rss_monitoring_service import RSSMonitoringService
            rss_service = RSSMonitoringService()
            
            # Obtener datos frescos - siempre JSON con fallback a XML
            noticias = rss_service.obtener_datos_rss('json')
            if not noticias:  # Si JSON falla, intentar XML
                noticias = rss_service.obtener_datos_rss('xml')
            tendencias = rss_service.obtener_tendencias_keywords(dias=7)
            alertas_criticas = rss_service.obtener_alertas_criticas()
            
            # Estadísticas
            total_noticias = len(noticias)
            noticias_alto_riesgo = len([n for n in noticias if n['nivel_riesgo'] in ['ALTO', 'CRITICO']])
            fuentes_unicas = len(set([n['fuente'] for n in noticias if n['fuente']]))
            
            return JsonResponse({
                'success': True,
                'data': {
                    'total_noticias': total_noticias,
                    'noticias_alto_riesgo': noticias_alto_riesgo,
                    'fuentes_unicas': fuentes_unicas,
                    'porcentaje_riesgo': round((noticias_alto_riesgo / total_noticias * 100) if total_noticias > 0 else 0, 1),
                    'tendencias': tendencias,
                    'alertas_criticas': alertas_criticas,
                    'noticias': noticias
                }
            })
            
        except Exception as e:
            logger.error(f"Error refrescando datos RSS: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def operacionales_view(request):
    """Vista para documentos operacionales vigentes."""
    torneo_selected = request.GET.get('torneo', 'LPF')
    
    # Mapear nombres de torneos para compatibilidad
    torneo_mapping = {
        'COPA LIBERTADORES': 'COPA LIBERTADORES',  # Los datos están guardados con espacio
        'COPA SUDAMERICA': 'COPA SUDAMERICA',
        'COPA ARGENTINA': 'COPA ARGENTINA'
    }
    
    torneo_db_name = torneo_mapping.get(torneo_selected, torneo_selected)
    
    # Obtener documentos operacionales filtrados por torneo
    operacionales = OperacionalDoc.objects.filter(torneo=torneo_db_name)
    
    # Si hay un PDF disponible para el torneo, mostrar página con JavaScript para abrir en nueva pestaña
    if operacionales.exists():
        # Tomar el primer PDF disponible (asumiendo que hay uno por torneo)
        pdf_doc = operacionales.first()
        if pdf_doc and pdf_doc.url:
            context = {
                'torneo_selected': torneo_selected,
                'pdf_url': pdf_doc.url,
                'pdf_name': pdf_doc.name,
                'filtros': {
                    'torneo_selected': torneo_selected
                }
            }
            return render(request, 'dashboard/operacionales_redirect.html', context)
    
    # Si no hay PDF disponible, mostrar la página de selección
    context = {
        'torneo_selected': torneo_selected,
        'operacionales': operacionales,
        'filtros': {
            'torneo_selected': torneo_selected
        }
    }
    
    return render(request, 'dashboard/operacionales.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def usuarios_list(request):
    usuarios = User.objects.all().order_by('username')
    return render(request, 'dashboard/usuarios_list.html', {'usuarios': usuarios})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def usuario_create(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        is_superuser = request.POST.get('is_superuser', False) == 'on'
        
        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_superuser = is_superuser
        user.is_staff = is_superuser
        user.save()
        return redirect('dashboard:usuarios_list')
    return render(request, 'dashboard/usuario_form.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def usuario_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.username = request.POST['username']
        user.email = request.POST['email']
        if 'password' in request.POST and request.POST['password']:
            user.set_password(request.POST['password'])
        user.is_superuser = request.POST.get('is_superuser', False) == 'on'
        user.is_staff = request.POST.get('is_superuser', False) == 'on'
        user.save()
        return redirect('dashboard:usuarios_list')
    return render(request, 'dashboard/usuario_form.html', {'user': user})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def usuario_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        return redirect('dashboard:usuarios_list')
    return render(request, 'dashboard/usuario_confirm_delete.html', {'user': user})


# ===== VISTAS PARA EDICIÓN DE GOOGLE SHEETS =====

@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_club_view(request, club_id):
    """Vista para editar un club específico."""
    from .services.google_sheets_write_service import GoogleSheetsWriteService
    
    club = get_object_or_404(Club, id=club_id)
    torneo = club.torneo
    
    if request.method == 'POST':
        campo = request.POST.get('campo')
        nuevo_valor = request.POST.get('nuevo_valor')
        
        try:
            sheets_service = GoogleSheetsWriteService()
            success = sheets_service.actualizar_club(torneo, club.nombre, campo, nuevo_valor)
            
            if success:
                # Actualizar también en la base de datos local
                if campo == 'nombre':
                    club.nombre = nuevo_valor
                elif campo == 'estadio':
                    club.estadio = nuevo_valor
                elif campo == 'direccion':
                    club.direccion = nuevo_valor
                elif campo == 'escudo_url':
                    club.escudo_url = nuevo_valor
                
                club.save()
                
                messages.success(request, f'Club {club.nombre} actualizado correctamente en Google Sheets y base de datos local.')
            else:
                messages.error(request, 'No se pudo actualizar el club en Google Sheets.')
                
        except Exception as e:
            error_msg = str(e)
            if 'FAILED_PRECONDITION' in error_msg:
                messages.warning(request, f'⚠️ No tienes permisos de edición en la hoja de Google Sheets. Solo se actualizó la base de datos local.')
                messages.info(request, f'💡 Para editar Google Sheets, ve a la hoja y compártela con: ref-583@just-coda-473000-f4.iam.gserviceaccount.com con permisos de Editor.')
                
                # Actualizar solo en la base de datos local
                if campo == 'nombre':
                    club.nombre = nuevo_valor
                elif campo == 'estadio':
                    club.estadio = nuevo_valor
                elif campo == 'direccion':
                    club.direccion = nuevo_valor
                elif campo == 'escudo_url':
                    club.escudo_url = nuevo_valor
                
                club.save()
                messages.success(request, '✅ Datos actualizados en la base de datos local.')
            else:
                messages.error(request, f'❌ Error actualizando el club: {error_msg}')
        
        return redirect('dashboard:clubes')
    
    context = {
        'club': club,
        'torneo': torneo,
        'campos_editables': [
            ('nombre', 'Nombre del Club'),
            ('estadio', 'Estadio'),
            ('direccion', 'Dirección'),
            ('escudo_url', 'URL del Escudo'),
        ]
    }
    
    return render(request, 'dashboard/editar_club.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def editar_encuentro_view(request, encuentro_id):
    """Vista para editar un encuentro específico."""
    from .services.google_sheets_write_service import GoogleSheetsWriteService
    
    encuentro = get_object_or_404(Encuentro, id=encuentro_id)
    torneo = encuentro.torneo.nombre
    
    if request.method == 'POST':
        campo = request.POST.get('campo')
        nuevo_valor = request.POST.get('nuevo_valor')
        
        try:
            sheets_service = GoogleSheetsWriteService()
            success = sheets_service.actualizar_encuentro(
                torneo, encuentro.club_local, encuentro.club_visitante, campo, nuevo_valor
            )
            
            if success:
                # Actualizar también en la base de datos local
                if campo == 'club_local':
                    encuentro.club_local = nuevo_valor
                elif campo == 'club_visitante':
                    encuentro.club_visitante = nuevo_valor
                elif campo == 'fecha':
                    encuentro.fecha = nuevo_valor
                elif campo == 'hora':
                    encuentro.hora = nuevo_valor
                elif campo == 'nivel_riesgo':
                    encuentro.nivel_riesgo = nuevo_valor
                elif campo == 'motivo_alerta':
                    encuentro.motivo_alerta = nuevo_valor
                
                encuentro.save()
                
                messages.success(request, f'Encuentro {encuentro.club_local} vs {encuentro.club_visitante} actualizado correctamente en Google Sheets y base de datos local.')
            else:
                messages.error(request, 'No se pudo actualizar el encuentro en Google Sheets.')
                
        except Exception as e:
            error_msg = str(e)
            if 'FAILED_PRECONDITION' in error_msg:
                messages.warning(request, f'⚠️ No tienes permisos de edición en la hoja de Google Sheets. Solo se actualizó la base de datos local.')
                messages.info(request, f'💡 Para editar Google Sheets, ve a la hoja y compártela con: ref-583@just-coda-473000-f4.iam.gserviceaccount.com con permisos de Editor.')
                
                # Actualizar solo en la base de datos local
                if campo == 'club_local':
                    encuentro.club_local = nuevo_valor
                elif campo == 'club_visitante':
                    encuentro.club_visitante = nuevo_valor
                elif campo == 'fecha':
                    encuentro.fecha = nuevo_valor
                elif campo == 'hora':
                    encuentro.hora = nuevo_valor
                elif campo == 'nivel_riesgo':
                    encuentro.nivel_riesgo = nuevo_valor
                elif campo == 'motivo_alerta':
                    encuentro.motivo_alerta = nuevo_valor
                
                encuentro.save()
                messages.success(request, '✅ Datos actualizados en la base de datos local.')
            else:
                messages.error(request, f'❌ Error actualizando el encuentro: {error_msg}')
        
        return redirect('dashboard:dashboard')
    
    context = {
        'encuentro': encuentro,
        'torneo': torneo,
        'campos_editables': [
            ('club_local', 'Club Local'),
            ('club_visitante', 'Club Visitante'),
            ('fecha', 'Fecha'),
            ('hora', 'Hora'),
            ('nivel_riesgo', 'Nivel de Riesgo'),
            ('motivo_alerta', 'Motivo de Alerta'),
        ]
    }
    
    return render(request, 'dashboard/editar_encuentro.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def test_google_sheets_connection(request):
    """Vista para probar la conexión con Google Sheets API."""
    from .services.google_sheets_write_service import GoogleSheetsWriteService
    from sheets_config import SHEETS_MAP
    
    context = {
        'conexion_ok': False,
        'permisos_hojas': {},
        'errores': []
    }
    
    try:
        sheets_service = GoogleSheetsWriteService()
        conexion_ok = sheets_service.verificar_conexion()
        
        if conexion_ok:
            context['conexion_ok'] = True
            messages.success(request, '✅ Conexión con Google Sheets API establecida correctamente.')
            
            # Probar la hoja de prueba primero
            prueba_ok = sheets_service.probar_hoja_prueba()
            context['prueba_hoja_ok'] = prueba_ok
            
            if prueba_ok:
                messages.success(request, '🎉 ¡Prueba de escritura exitosa! Los permisos están funcionando correctamente.')
            else:
                messages.warning(request, '⚠️ La prueba de escritura falló. Verifica los permisos.')
            
            # Verificar permisos en cada hoja
            for torneo, config in SHEETS_MAP.items():
                context['permisos_hojas'][torneo] = {}
                
                for tipo, info in config.items():
                    if 'spreadsheet_id' in info:
                        spreadsheet_id = info['spreadsheet_id']
                        tiene_permisos = sheets_service.verificar_permisos_hoja(spreadsheet_id)
                        context['permisos_hojas'][torneo][tipo] = {
                            'tiene_permisos': tiene_permisos,
                            'spreadsheet_id': spreadsheet_id
                        }
                        
                        if not tiene_permisos:
                            context['errores'].append(f"{torneo} - {tipo}")
        else:
            context['conexion_ok'] = False
            messages.error(request, '❌ No se pudo establecer conexión con Google Sheets API.')
            
    except Exception as e:
        context['errores'].append(f"Error general: {str(e)}")
        messages.error(request, f'❌ Error probando conexión: {str(e)}')
    
    return render(request, 'dashboard/test_google_sheets.html', context)


@login_required
def welcome_view(request):
    """Vista de bienvenida que se muestra al iniciar sesión."""
    context = {
        'user': request.user,
    }
    return render(request, 'dashboard/welcome.html', context)