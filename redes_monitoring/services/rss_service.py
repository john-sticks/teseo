"""
Servicio para el monitoreo de RSS feeds específico para el módulo de redes y monitoreo.
"""
import requests
import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class RSSMonitoringService:
    """Servicio para manejar feeds RSS de redes sociales en el módulo de monitoreo."""
    
    def __init__(self):
        self.feed_url = settings.RSS_FEED_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'REF-System-Monitoring/1.0'
        })
    
    def obtener_y_procesar_feed(self) -> Dict[str, Any]:
        """Obtiene y procesa el feed RSS, guardando alertas en la base de datos."""
        try:
            response = self.session.get(self.feed_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return self._procesar_y_guardar_feed_data(data)
            
        except requests.RequestException as e:
            logger.error(f"Error obteniendo feed RSS: {e}")
            return self._datos_mock_feed()
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON del feed: {e}")
            return self._datos_mock_feed()
        except Exception as e:
            logger.error(f"Error inesperado en RSS monitoring service: {e}")
            return self._datos_mock_feed()
    
    def _procesar_y_guardar_feed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa los datos del feed RSS y guarda alertas en la base de datos."""
        try:
            from ..models import AlertaRedes, TendenciasKeyword
            
            items = data.get('items', [])
            keywords_riesgo = [
                'violencia', 'pelea', 'conflicto', 'hinchada', 'barra brava',
                'incidente', 'disturbio', 'policía', 'seguridad', 'estadio',
                'fútbol', 'clásico', 'derby', 'rivalidad'
            ]
            
            alertas_creadas = 0
            tendencias = {}
            
            for item in items:
                # Procesar cada item del feed
                titulo = item.get('title', '').lower()
                descripcion = item.get('description', '').lower()
                contenido_completo = f"{titulo} {descripcion}"
                
                # Detectar keywords de riesgo
                keywords_encontradas = [
                    keyword for keyword in keywords_riesgo 
                    if keyword in contenido_completo
                ]
                
                if keywords_encontradas:
                    # Determinar nivel de riesgo
                    nivel_riesgo = self._calcular_nivel_riesgo(keywords_encontradas)
                    
                    # Extraer clubes mencionados
                    clubes_mencionados = self._extraer_clubes_mencionados(contenido_completo)
                    
                    # Crear alerta en la base de datos
                    alerta = AlertaRedes.objects.create(
                        titulo=item.get('title', ''),
                        descripcion=item.get('description', ''),
                        url=item.get('link', ''),
                        fuente=self._extraer_fuente(item.get('link', '')),
                        nivel_riesgo=nivel_riesgo,
                        keywords=keywords_encontradas,
                        clubes_mencionados=clubes_mencionados,
                        fecha_alerta=self._parsear_fecha_rss(item.get('pubDate', ''))
                    )
                    alertas_creadas += 1
                
                # Actualizar tendencias
                for keyword in keywords_encontradas:
                    tendencias[keyword] = tendencias.get(keyword, 0) + 1
            
            # Guardar tendencias en la base de datos
            fecha_hoy = datetime.now().date()
            for keyword, frecuencia in tendencias.items():
                tendencia, created = TendenciasKeyword.objects.get_or_create(
                    keyword=keyword,
                    fecha_tendencia=fecha_hoy,
                    defaults={'frecuencia': frecuencia}
                )
                if not created:
                    tendencia.frecuencia += frecuencia
                    tendencia.save()
            
            # Obtener alertas recientes para mostrar
            alertas_recientes = AlertaRedes.objects.filter(
                fecha_alerta__gte=datetime.now() - timedelta(hours=24)
            ).order_by('-fecha_alerta')[:20]
            
            alertas_data = []
            for alerta in alertas_recientes:
                alertas_data.append({
                    'id': alerta.id,
                    'titulo': alerta.titulo,
                    'descripcion': alerta.descripcion,
                    'fuente': alerta.get_fuente_display(),
                    'nivel_riesgo': alerta.get_nivel_riesgo_display(),
                    'fecha_alerta': alerta.fecha_alerta.strftime('%d/%m/%Y %H:%M'),
                    'url': alerta.url,
                    'keywords': alerta.keywords,
                    'clubes_mencionados': alerta.clubes_mencionados,
                })
            
            # Obtener top tendencias
            top_tendencias = TendenciasKeyword.objects.filter(
                fecha_tendencia=fecha_hoy
            ).order_by('-frecuencia')[:10]
            
            tendencias_dict = {t.keyword: t.frecuencia for t in top_tendencias}
            
            return {
                'alertas': alertas_data,
                'tendencias': tendencias_dict,
                'total_alertas': alertas_creadas,
                'fecha_actualizacion': datetime.now().isoformat(),
                'fuente': 'RSS Feed'
            }
            
        except Exception as e:
            logger.error(f"Error procesando y guardando datos del feed: {e}")
            return self._datos_mock_feed()
    
    def _calcular_nivel_riesgo(self, keywords: List[str]) -> str:
        """Calcula el nivel de riesgo basado en las keywords encontradas."""
        keywords_alto_riesgo = ['violencia', 'pelea', 'disturbio', 'barra brava']
        keywords_medio_riesgo = ['conflicto', 'incidente', 'hinchada', 'rivalidad']
        
        if any(keyword in keywords_alto_riesgo for keyword in keywords):
            return 'ALTO'
        elif any(keyword in keywords_medio_riesgo for keyword in keywords):
            return 'MEDIO'
        else:
            return 'BAJO'
    
    def _extraer_clubes_mencionados(self, contenido: str) -> List[str]:
        """Extrae clubes mencionados del contenido."""
        clubes_conocidos = [
            'boca', 'river', 'racing', 'independiente', 'san lorenzo', 
            'huracán', 'vélez', 'estudiantes', 'gimnasia', 'banfield',
            'lanús', 'defensa y justicia', 'tigre', 'argentinos juniors',
            'rosario central', 'newells', 'colón', 'unión', 'aldosivi',
            'patronato', 'arsenal', 'central córdoba', 'sarmiento',
            'platense', 'barracas central', 'instituto', 'belgrano'
        ]
        
        clubes_encontrados = []
        for club in clubes_conocidos:
            if club in contenido:
                clubes_encontrados.append(club.title())
        
        return clubes_encontrados
    
    def _extraer_fuente(self, url: str) -> str:
        """Extrae la fuente del URL."""
        if not url:
            return 'OTRO'
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            dominio = parsed.netloc.lower()
            
            # Mapear dominios conocidos
            fuentes = {
                'twitter.com': 'TWITTER',
                'facebook.com': 'FACEBOOK',
                'instagram.com': 'INSTAGRAM',
                'youtube.com': 'YOUTUBE',
                'tiktok.com': 'TIKTOK',
                'infobae.com': 'MEDIO',
                'lanacion.com.ar': 'MEDIO',
                'clarin.com': 'MEDIO',
                'ole.com.ar': 'MEDIO',
                'tycsports.com': 'MEDIO'
            }
            
            for dominio_key, fuente in fuentes.items():
                if dominio_key in dominio:
                    return fuente
            
            return 'OTRO'
        except:
            return 'OTRO'
    
    def _parsear_fecha_rss(self, fecha_str: str) -> datetime:
        """Parsea fecha desde formato RSS."""
        if not fecha_str:
            return datetime.now()
        
        try:
            # Formatos comunes de RSS
            formatos = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S %Z',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%d %H:%M:%S'
            ]
            
            for formato in formatos:
                try:
                    return datetime.strptime(fecha_str, formato)
                except ValueError:
                    continue
            
            return datetime.now()
        except:
            return datetime.now()
    
    def _datos_mock_feed(self) -> Dict[str, Any]:
        """Datos de ejemplo para desarrollo."""
        return {
            'alertas': [
                {
                    'id': 1,
                    'titulo': 'Incidente en el clásico Boca vs River',
                    'descripcion': 'Se reportaron disturbios en las inmediaciones del estadio...',
                    'url': 'https://ejemplo.com/noticia/1',
                    'fuente': 'Medio de Comunicación',
                    'nivel_riesgo': 'Alto',
                    'fecha_alerta': datetime.now().strftime('%d/%m/%Y %H:%M'),
                    'keywords': ['violencia', 'clásico', 'estadio'],
                    'clubes_mencionados': ['Boca', 'River'],
                }
            ],
            'tendencias': {
                'violencia': 5,
                'clásico': 4,
                'hinchada': 3,
                'estadio': 3,
                'conflicto': 2
            },
            'total_alertas': 1,
            'fecha_actualizacion': datetime.now().isoformat(),
            'fuente': 'RSS Feed (Mock)'
        }
