"""
Servicio para monitoreo de RSS feeds y análisis de keywords/tendencias.
"""
import requests
import json
import csv
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from django.conf import settings
import re

logger = logging.getLogger(__name__)

class RSSMonitoringService:
    """Servicio para monitorear RSS feeds y analizar contenido."""
    
    def __init__(self):
        self.rss_urls = {
            'xml': 'https://rss.app/feeds/_aUBB2qjedDT2RxdW.xml',
            'json': 'https://rss.app/feeds/v1.1/_aUBB2qjedDT2RxdW.json',
            'csv': 'https://rss.app/feeds/_aUBB2qjedDT2RxdW.csv'
        }
        
        # Keywords relacionadas con fútbol y conflictividad
        self.keywords_alerta = [
            'violencia', 'conflicto', 'incidente', 'hinchada', 'barra brava',
            'pelea', 'agresión', 'disturbio', 'escándalo', 'sanción',
            'expulsión', 'suspensión', 'multa', 'prohibición', 'riesgo',
            'peligro', 'alerta', 'emergencia', 'policía', 'seguridad',
            'estadio', 'cancha', 'tribuna', 'hinchada', 'aficionado'
        ]
        
        # Nombres de clubes para detectar menciones
        self.clubes_keywords = [
            'boca', 'river', 'racing', 'independiente', 'san lorenzo',
            'estudiantes', 'gimnasia', 'velez', 'lanus', 'banfield',
            'defensa y justicia', 'tigre', 'huracan', 'rosario central',
            'newells', 'colón', 'unión', 'talleres', 'belgrano', 'instituto'
        ]

    def obtener_datos_rss(self, formato='json') -> List[Dict[str, Any]]:
        """
        Obtiene datos del RSS feed en el formato especificado.
        
        Args:
            formato: 'xml', 'json' o 'csv'
            
        Returns:
            Lista de noticias procesadas
        """
        try:
            url = self.rss_urls.get(formato)
            if not url:
                logger.error(f"Formato no soportado: {formato}")
                return []
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            if formato == 'json':
                return self._procesar_json(response.text)
            elif formato == 'xml':
                return self._procesar_xml(response.text)
            elif formato == 'csv':
                return self._procesar_csv(response.text)
                
        except requests.RequestException as e:
            logger.error(f"Error obteniendo datos RSS: {e}")
            return []
        except Exception as e:
            logger.error(f"Error procesando datos RSS: {e}")
            return []

    def _procesar_json(self, json_text: str) -> List[Dict[str, Any]]:
        """Procesa datos JSON del RSS feed."""
        try:
            data = json.loads(json_text)
            noticias = []
            
            # Estructura puede variar según el proveedor RSS
            items = data.get('items', data.get('entries', []))
            
            for item in items:
                noticia = self._procesar_item(item)
                if noticia:
                    noticias.append(noticia)
                    
            return noticias
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decodificando JSON: {e}")
            return []

    def _procesar_xml(self, xml_text: str) -> List[Dict[str, Any]]:
        """Procesa datos XML del RSS feed."""
        try:
            root = ET.fromstring(xml_text)
            noticias = []
            
            # Buscar items en diferentes estructuras XML
            items = root.findall('.//item') or root.findall('.//entry')
            
            for item in items:
                noticia = self._procesar_item_xml(item)
                if noticia:
                    noticias.append(noticia)
                    
            return noticias
            
        except ET.ParseError as e:
            logger.error(f"Error parseando XML: {e}")
            return []

    def _procesar_csv(self, csv_text: str) -> List[Dict[str, Any]]:
        """Procesa datos CSV del RSS feed."""
        try:
            csv_reader = csv.DictReader(csv_text.splitlines())
            noticias = []
            
            for row in csv_reader:
                noticia = self._procesar_item_csv(row)
                if noticia:
                    noticias.append(noticia)
                    
            return noticias
            
        except Exception as e:
            logger.error(f"Error procesando CSV: {e}")
            return []

    def _procesar_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un item individual del feed."""
        try:
            # Extraer información básica
            titulo = item.get('title', '')
            descripcion_raw = item.get('description', item.get('content', ''))
            url = item.get('url', item.get('link', ''))
            fecha = item.get('published', item.get('date', ''))
            
            # Limpiar descripción de HTML
            descripcion = self._limpiar_html(descripcion_raw)
            
            # Extraer imagen
            imagen = self._extraer_imagen_xml(descripcion_raw) or item.get('image', '')
            
            # Procesar fecha
            fecha_procesada = self._parsear_fecha(fecha)
            fecha_relativa = self._formatear_fecha_relativa(fecha_procesada)
            
            # Analizar contenido
            analisis = self._analizar_contenido(titulo, descripcion)
            
            return {
                'titulo': titulo,
                'descripcion': descripcion,
                'url': url,
                'fecha': fecha_procesada,
                'fecha_relativa': fecha_relativa,
                'imagen': imagen,
                'fuente': self._extraer_fuente(url),
                'nivel_riesgo': analisis['nivel_riesgo'],
                'keywords_detectadas': analisis['keywords'],
                'clubes_mencionados': analisis['clubes'],
                'score_riesgo': analisis['score']
            }
            
        except Exception as e:
            logger.error(f"Error procesando item: {e}")
            return None

    def _procesar_item_xml(self, item) -> Dict[str, Any]:
        """Procesa un item XML individual."""
        try:
            titulo = self._get_xml_text(item, 'title')
            descripcion_raw = self._get_xml_text(item, 'description') or self._get_xml_text(item, 'content')
            url = self._get_xml_text(item, 'link')
            fecha = self._get_xml_text(item, 'pubDate') or self._get_xml_text(item, 'published')
            
            # Limpiar descripción de HTML
            descripcion = self._limpiar_html(descripcion_raw)
            
            # Extraer imagen de la descripción
            imagen = self._extraer_imagen_xml(descripcion_raw)
            
            fecha_procesada = self._parsear_fecha(fecha)
            fecha_relativa = self._formatear_fecha_relativa(fecha_procesada)
            analisis = self._analizar_contenido(titulo, descripcion)
            
            return {
                'titulo': titulo,
                'descripcion': descripcion,
                'url': url,
                'fecha': fecha_procesada,
                'fecha_relativa': fecha_relativa,
                'imagen': imagen,
                'fuente': self._extraer_fuente(url),
                'nivel_riesgo': analisis['nivel_riesgo'],
                'keywords_detectadas': analisis['keywords'],
                'clubes_mencionados': analisis['clubes'],
                'score_riesgo': analisis['score']
            }
            
        except Exception as e:
            logger.error(f"Error procesando item XML: {e}")
            return None

    def _procesar_item_csv(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Procesa una fila CSV individual."""
        try:
            titulo = row.get('title', '')
            descripcion = row.get('description', '')
            url = row.get('url', '')
            fecha = row.get('published', '')
            
            fecha_procesada = self._parsear_fecha(fecha)
            analisis = self._analizar_contenido(titulo, descripcion)
            
            return {
                'titulo': titulo,
                'descripcion': descripcion,
                'url': url,
                'fecha': fecha_procesada,
                'fuente': self._extraer_fuente(url),
                'nivel_riesgo': analisis['nivel_riesgo'],
                'keywords_detectadas': analisis['keywords'],
                'clubes_mencionados': analisis['clubes'],
                'score_riesgo': analisis['score']
            }
            
        except Exception as e:
            logger.error(f"Error procesando fila CSV: {e}")
            return None

    def _get_xml_text(self, element, tag_name: str) -> str:
        """Obtiene texto de un elemento XML."""
        try:
            elem = element.find(tag_name)
            return elem.text if elem is not None else ''
        except:
            return ''

    def _limpiar_html(self, html_text: str) -> str:
        """Limpia texto HTML y extrae solo el contenido de texto."""
        if not html_text:
            return ''
        
        try:
            import re
            # Remover tags HTML
            clean_text = re.sub(r'<[^>]+>', '', html_text)
            # Remover entidades HTML
            clean_text = clean_text.replace('&nbsp;', ' ')
            clean_text = clean_text.replace('&amp;', '&')
            clean_text = clean_text.replace('&lt;', '<')
            clean_text = clean_text.replace('&gt;', '>')
            clean_text = clean_text.replace('&quot;', '"')
            # Limpiar espacios múltiples
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            return clean_text
        except:
            return html_text

    def _extraer_imagen_xml(self, html_text: str) -> str:
        """Extrae URL de imagen del HTML."""
        if not html_text:
            return ''
        
        try:
            import re
            # Buscar tags img
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            matches = re.findall(img_pattern, html_text, re.IGNORECASE)
            if matches:
                return matches[0]
            
            # Buscar URLs de imagen en el texto
            url_pattern = r'https?://[^\s<>"]+\.(?:jpg|jpeg|png|gif|webp)'
            matches = re.findall(url_pattern, html_text, re.IGNORECASE)
            if matches:
                return matches[0]
            
            return ''
        except:
            return ''

    def _formatear_fecha_relativa(self, fecha_str: str) -> str:
        """Formatea fecha como tiempo relativo (38m, 1h, etc.)."""
        try:
            from datetime import datetime, timedelta
            
            fecha_noticia = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')
            ahora = datetime.now()
            diferencia = ahora - fecha_noticia
            
            if diferencia.days > 0:
                return f"{diferencia.days}d"
            elif diferencia.seconds >= 3600:
                horas = diferencia.seconds // 3600
                return f"{horas}h"
            elif diferencia.seconds >= 60:
                minutos = diferencia.seconds // 60
                return f"{minutos}m"
            else:
                return "ahora"
        except:
            return "hace un momento"

    def _analizar_contenido(self, titulo: str, descripcion: str) -> Dict[str, Any]:
        """Analiza el contenido para detectar keywords y nivel de riesgo."""
        contenido_completo = f"{titulo} {descripcion}".lower()
        
        keywords_encontradas = []
        clubes_encontrados = []
        score = 0
        
        # Detectar keywords de alerta
        for keyword in self.keywords_alerta:
            if keyword.lower() in contenido_completo:
                keywords_encontradas.append(keyword)
                score += 1
        
        # Detectar menciones de clubes
        for club in self.clubes_keywords:
            if club.lower() in contenido_completo:
                clubes_encontrados.append(club.title())
                score += 0.5
        
        # Determinar nivel de riesgo
        if score >= 5:
            nivel_riesgo = 'CRITICO'
        elif score >= 3:
            nivel_riesgo = 'ALTO'
        elif score >= 2:
            nivel_riesgo = 'MEDIO'
        elif score >= 1:
            nivel_riesgo = 'BAJO'
        else:
            nivel_riesgo = 'SIN_RIESGO'
        
        return {
            'keywords': keywords_encontradas,
            'clubes': clubes_encontrados,
            'score': score,
            'nivel_riesgo': nivel_riesgo
        }

    def _parsear_fecha(self, fecha_str: str) -> str:
        """Parsea fecha a formato legible."""
        if not fecha_str:
            return datetime.now().strftime('%Y-%m-%d %H:%M')
        
        try:
            # Intentar diferentes formatos de fecha
            formatos = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M',
                '%d/%m/%Y',
                '%a, %d %b %Y %H:%M:%S %z'
            ]
            
            for formato in formatos:
                try:
                    fecha = datetime.strptime(fecha_str, formato)
                    return fecha.strftime('%Y-%m-%d %H:%M')
                except ValueError:
                    continue
            
            return datetime.now().strftime('%Y-%m-%d %H:%M')
            
        except:
            return datetime.now().strftime('%Y-%m-%d %H:%M')

    def _extraer_fuente(self, url: str) -> str:
        """Extrae el nombre de la fuente desde la URL."""
        if not url:
            return 'Desconocida'
        
        try:
            # Extraer dominio
            domain = url.split('/')[2] if '://' in url else url.split('/')[0]
            
            # Mapear dominios conocidos
            fuentes_conocidas = {
                'twitter.com': 'Twitter',
                'facebook.com': 'Facebook',
                'instagram.com': 'Instagram',
                'youtube.com': 'YouTube',
                'tiktok.com': 'TikTok',
                'infobae.com': 'Infobae',
                'clarin.com': 'Clarín',
                'lanacion.com': 'La Nación',
                'pagina12.com.ar': 'Página 12',
                'ambito.com': 'Ámbito',
                'ellitoral.com': 'El Litoral',
                'tycsports.com': 'TyC Sports',
                'ole.com.ar': 'Olé',
                'lacomuderacing.com': 'La Comu de Racing',
                'airedesantafe.com.ar': 'Aire de Santa Fe',
                'lagaceta.com.ar': 'La Gaceta',
                'espn.com': 'ESPN',
                'foxsports.com': 'Fox Sports'
            }
            
            for dominio, nombre in fuentes_conocidas.items():
                if dominio in domain:
                    return nombre
            
            return domain.split('.')[-2] if '.' in domain else domain
            
        except:
            return 'Desconocida'

    def obtener_tendencias_keywords(self, dias: int = 7) -> List[Dict[str, Any]]:
        """Obtiene tendencias de keywords en los últimos días."""
        try:
            noticias = self.obtener_datos_rss('json')
            
            # Filtrar noticias de los últimos días
            fecha_limite = datetime.now() - timedelta(days=dias)
            noticias_recientes = []
            
            for noticia in noticias:
                try:
                    fecha_noticia = datetime.strptime(noticia['fecha'], '%Y-%m-%d %H:%M')
                    if fecha_noticia >= fecha_limite:
                        noticias_recientes.append(noticia)
                except:
                    continue
            
            # Contar keywords
            keyword_counts = {}
            for noticia in noticias_recientes:
                for keyword in noticia.get('keywords_detectadas', []):
                    keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            
            # Crear tendencias
            tendencias = []
            for keyword, count in keyword_counts.items():
                tendencias.append({
                    'keyword': keyword,
                    'frecuencia': count,
                    'tendencia': 'ALTA' if count >= 5 else 'MEDIA' if count >= 2 else 'BAJA'
                })
            
            return sorted(tendencias, key=lambda x: x['frecuencia'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo tendencias: {e}")
            return []

    def obtener_alertas_criticas(self) -> List[Dict[str, Any]]:
        """Obtiene alertas críticas basadas en el análisis de contenido."""
        try:
            noticias = self.obtener_datos_rss('json')
            
            alertas = []
            for noticia in noticias:
                if noticia['nivel_riesgo'] in ['ALTO', 'CRITICO']:
                    alertas.append({
                        'titulo': noticia['titulo'],
                        'descripcion': noticia['descripcion'][:200] + '...' if len(noticia['descripcion']) > 200 else noticia['descripcion'],
                        'url': noticia['url'],
                        'fecha': noticia['fecha'],
                        'fuente': noticia['fuente'],
                        'nivel_riesgo': noticia['nivel_riesgo'],
                        'keywords': noticia['keywords_detectadas'],
                        'clubes': noticia['clubes_mencionados'],
                        'score': noticia['score_riesgo']
                    })
            
            return sorted(alertas, key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error obteniendo alertas críticas: {e}")
            return []
