"""
Servicio para el monitoreo de RSS feeds de redes sociales.
"""
import requests
import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class RSSService:
    """Servicio para manejar feeds RSS de redes sociales."""
    
    def __init__(self):
        self.feed_url = settings.RSS_FEED_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'REF-System/1.0 (Monitoreo RSS)'
        })
    
    def obtener_feed(self) -> Dict[str, Any]:
        """Obtiene y procesa el feed RSS."""
        try:
            response = self.session.get(self.feed_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return self._procesar_feed_data(data)
            
        except requests.RequestException as e:
            logger.error(f"Error obteniendo feed RSS: {e}")
            return self._datos_mock_feed()
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON del feed: {e}")
            return self._datos_mock_feed()
        except Exception as e:
            logger.error(f"Error inesperado en RSS service: {e}")
            return self._datos_mock_feed()
    
    def _procesar_feed_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa los datos del feed RSS."""
        try:
            items = data.get('items', [])
            keywords_riesgo = [
                'violencia', 'pelea', 'conflicto', 'hinchada', 'barra brava',
                'incidente', 'disturbio', 'policía', 'seguridad', 'estadio',
                'fútbol', 'clásico', 'derby', 'rivalidad'
            ]
            
            alertas = []
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
                    alerta = {
                        'titulo': item.get('title', ''),
                        'descripcion': item.get('description', ''),
                        'url': item.get('link', ''),
                        'fecha': self._parsear_fecha_rss(item.get('pubDate', '')),
                        'keywords': keywords_encontradas,
                        'nivel_riesgo': self._calcular_nivel_riesgo(keywords_encontradas),
                        'fuente': self._extraer_fuente(item.get('link', ''))
                    }
                    alertas.append(alerta)
                
                # Actualizar tendencias
                for keyword in keywords_encontradas:
                    tendencias[keyword] = tendencias.get(keyword, 0) + 1
            
            # Ordenar alertas por fecha (más recientes primero)
            alertas.sort(key=lambda x: x['fecha'], reverse=True)
            
            # Obtener top tendencias
            top_tendencias = sorted(
                tendencias.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            return {
                'alertas': alertas[:20],  # Últimas 20 alertas
                'tendencias': dict(top_tendencias),
                'total_alertas': len(alertas),
                'fecha_actualizacion': datetime.now().isoformat(),
                'fuente': 'RSS Feed'
            }
            
        except Exception as e:
            logger.error(f"Error procesando datos del feed: {e}")
            return self._datos_mock_feed()
    
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
    
    def _extraer_fuente(self, url: str) -> str:
        """Extrae la fuente del URL."""
        if not url:
            return 'Desconocida'
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            dominio = parsed.netloc.lower()
            
            # Mapear dominios conocidos
            fuentes = {
                'twitter.com': 'Twitter',
                'facebook.com': 'Facebook',
                'instagram.com': 'Instagram',
                'youtube.com': 'YouTube',
                'tiktok.com': 'TikTok',
                'infobae.com': 'Infobae',
                'lanacion.com.ar': 'La Nación',
                'clarin.com': 'Clarín',
                'ole.com.ar': 'Olé',
                'tycsports.com': 'TyC Sports'
            }
            
            for dominio_key, fuente in fuentes.items():
                if dominio_key in dominio:
                    return fuente
            
            return dominio.split('.')[0].title()
        except:
            return 'Desconocida'
    
    def _datos_mock_feed(self) -> Dict[str, Any]:
        """Datos de ejemplo para desarrollo."""
        return {
            'alertas': [
                {
                    'titulo': 'Incidente en el clásico Boca vs River',
                    'descripcion': 'Se reportaron disturbios en las inmediaciones del estadio...',
                    'url': 'https://ejemplo.com/noticia/1',
                    'fecha': datetime.now(),
                    'keywords': ['violencia', 'clásico', 'estadio'],
                    'nivel_riesgo': 'ALTO',
                    'fuente': 'Infobae'
                },
                {
                    'titulo': 'Hinchadas de San Lorenzo y Huracán se enfrentaron',
                    'descripcion': 'Conflicto entre hinchadas en el barrio de Boedo...',
                    'url': 'https://ejemplo.com/noticia/2',
                    'fecha': datetime.now() - timedelta(hours=2),
                    'keywords': ['conflicto', 'hinchada', 'enfrentaron'],
                    'nivel_riesgo': 'MEDIO',
                    'fuente': 'Clarín'
                }
            ],
            'tendencias': {
                'violencia': 5,
                'clásico': 4,
                'hinchada': 3,
                'estadio': 3,
                'conflicto': 2
            },
            'total_alertas': 2,
            'fecha_actualizacion': datetime.now().isoformat(),
            'fuente': 'RSS Feed (Mock)'
        }
    
    def obtener_alertas_por_club(self, club: str) -> List[Dict[str, Any]]:
        """Filtra alertas por un club específico."""
        feed_data = self.obtener_feed()
        alertas = feed_data.get('alertas', [])
        
        club_lower = club.lower()
        alertas_club = []
        
        for alerta in alertas:
            titulo_desc = f"{alerta['titulo']} {alerta['descripcion']}".lower()
            if club_lower in titulo_desc:
                alertas_club.append(alerta)
        
        return alertas_club
    
    def obtener_alertas_por_periodo(self, horas: int = 24) -> List[Dict[str, Any]]:
        """Obtiene alertas de las últimas N horas."""
        feed_data = self.obtener_feed()
        alertas = feed_data.get('alertas', [])
        
        fecha_limite = datetime.now() - timedelta(hours=horas)
        alertas_recientes = [
            alerta for alerta in alertas 
            if alerta['fecha'] >= fecha_limite
        ]
        
        return alertas_recientes
