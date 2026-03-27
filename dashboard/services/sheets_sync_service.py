"""
Servicio para sincronización automática con Google Sheets públicas.
Descarga datos directamente desde las URLs de exportación CSV sin necesidad de credenciales.
"""
import re
import io
import csv
import requests
import traceback
from datetime import datetime
from django.utils import timezone
from django.core.management.base import BaseCommand
from django.conf import settings
import logging

from dashboard.models import (
    Encuentro, Incidente, RankingConflictividad, Club, 
    DerechoAdmision, OperacionalDoc, Torneo
)
from sheets_config import SHEETS_MAP

logger = logging.getLogger(__name__)


class SheetsSyncService:
    """Servicio para sincronizar datos desde Google Sheets públicas."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_spreadsheet_tabs(self, spreadsheet_id):
        """
        Intenta detectar pestañas y sus gid parseando la página /edit.
        Retorna lista de dicts [{'name':..., 'gid':...}, ...] o None si no puede.
        """
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
        try:
            response = self.session.get(url, timeout=15)
            logger.info(f"Respuesta para detección de pestañas: status={response.status_code}")
            
            if response.status_code != 200:
                logger.warning(f"No se pudo acceder a la página de edición: {response.status_code}")
                return None
            
            text = response.text
            tabs = []
            
            # Regex para buscar "sheetId":12345,"title":"Nombre"
            pattern = r'"sheetId":\s*([0-9]+).*?"title":"([^"]+)"'
            matches = list(re.finditer(pattern, text, re.S))
            logger.info(f"Encontrados {len(matches)} matches de pestañas")
            
            for match in matches:
                sheet_id = match.group(1)
                title = match.group(2)
                tabs.append({'name': title, 'gid': sheet_id})
                logger.info(f"Pestaña detectada: {title} (GID: {sheet_id})")
            
            if tabs:
                logger.info(f"Total pestañas detectadas: {len(tabs)}")
                return tabs
            else:
                logger.warning("No se detectaron pestañas con el patrón regex")
                return None
            
        except Exception as e:
            logger.error(f"Error obteniendo pestañas de {spreadsheet_id}: {e}")
            return None
    
    def download_csv(self, spreadsheet_id, gid):
        """Descarga CSV desde Google Sheets usando el GID específico."""
        url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
        logger.info(f"Descargando CSV desde: {url}")
        try:
            response = self.session.get(url, timeout=20)
            logger.info(f"Respuesta HTTP: {response.status_code}, Tamaño: {len(response.content) if response.content else 0}")
            
            if response.status_code == 200 and response.content and len(response.content) > 10:
                content = response.content.decode('utf-8', errors='replace')
                logger.info(f"CSV descargado exitosamente, {len(content)} caracteres")
                return content
            else:
                logger.error(f"Error en descarga: status={response.status_code}, content_len={len(response.content) if response.content else 0}")
                return None
        except Exception as e:
            logger.error(f"Error descargando CSV gid={gid}: {e}")
            return None
    
    def parse_csv(self, csv_text):
        """Convierte texto CSV en lista de diccionarios."""
        if not csv_text:
            return []
        
        try:
            f = io.StringIO(csv_text)
            reader = csv.DictReader(f)
            return [row for row in reader]
        except Exception as e:
            logger.error(f"Error parseando CSV: {e}")
            return []
    
    def process_encuentros(self, rows, torneo_name):
        """Procesa filas de encuentros y los guarda en la base de datos."""
        created = updated = deleted = 0
        
        # Obtener o crear torneo
        torneo, _ = Torneo.objects.get_or_create(
            nombre=torneo_name,
            defaults={
                'fecha_inicio': timezone.now().date(),
                'fecha_fin': timezone.now().date()
            }
        )
        
        # Obtener todos los external_ids actuales de la hoja
        current_external_ids = set()
        
        for row in rows:
            # Limpiar datos
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            
            # Verificar que tenga datos mínimos
            club_local = row.get('CLUB LOCAL') or row.get('LOCAL') or ''
            club_visitante = row.get('CLUB VISITANTE') or row.get('VISITANTE') or ''
            fecha_text = row.get('FECHA') or row.get('FECHA DEL ENCUENTRO') or ''
            
            if not club_local or not club_visitante or not fecha_text:
                continue
            
            # Generar external_id único
            external_id = f"{torneo_name}_{club_local}_{club_visitante}_{fecha_text}"
            current_external_ids.add(external_id)
            
            # Parsear fecha y hora
            hora_text = row.get('HORA') or ''
            fecha = self.parse_fecha(fecha_text)
            hora = self.parse_hora(hora_text)
            
            # Mapear nivel de riesgo
            riesgo_text = (row.get('RIESGO') or row.get('NIVEL RIESGO') or '1').upper()
            nivel_riesgo = self.map_nivel_riesgo(riesgo_text)
            
            # Obtener motivo del riesgo (limpiar caracteres especiales)
            motivo_riesgo = row.get('MOTIVO DEL RIESGO') or row.get('MOTIVO') or row.get('MOTIVO ALERTA') or ''
            motivo_riesgo = motivo_riesgo.replace('\r', '').replace('\n', ' ').strip()
            
            # Obtener escudos
            escudo_local = row.get('ESCUDO LOCAL') or ''
            escudo_visitante = row.get('ESCUDO VISITANTE') or ''
            
            defaults = {
                'torneo': torneo,
                'fecha': fecha or timezone.now().date(),
                'hora': hora or timezone.now().time(),
                'club_local': club_local,
                'club_visitante': club_visitante,
                'estadio': row.get('ESTADIO') or '',
                'nivel_riesgo': nivel_riesgo,
                'motivo_alerta': motivo_riesgo,
                'relato_hecho': motivo_riesgo,  # Usar motivo como relato si no hay relato específico
                'fecha_text': fecha_text,
                'hora_text': hora_text,
                'escudo_local': escudo_local,
                'escudo_visitante': escudo_visitante,
                'raw_data': row,
                'last_sync': timezone.now()
            }
            
            obj, created_flag = Encuentro.objects.update_or_create(
                external_id=str(external_id),
                defaults=defaults
            )
            
            if created_flag:
                created += 1
            else:
                updated += 1
        
        # Eliminar registros que ya no están en la hoja
        existing_encuentros = Encuentro.objects.filter(torneo=torneo)
        for encuentro in existing_encuentros:
            if encuentro.external_id and encuentro.external_id not in current_external_ids:
                encuentro.delete()
                deleted += 1
        
        return created, updated, deleted
    
    def process_incidentes(self, rows, torneo_name):
        """Procesa filas de incidentes para el mapa."""
        created = updated = deleted = 0
        
        # Obtener todos los external_ids actuales de la hoja
        current_external_ids = set()
        
        for row in rows:
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            
            club_futbol = row.get('CLUB DE FÚTBOL') or ''
            fecha_hecho = row.get('FECHA DEL HECHO') or ''
            
            if not club_futbol or not fecha_hecho:
                continue
            
            external_id = f"{torneo_name}_{club_futbol}_{fecha_hecho}"
            current_external_ids.add(external_id)
            
            # Parsear coordenadas desde la columna COORDENADAS
            coordenadas_text = row.get('COORDENADAS') or ''
            lat, lng = self.parse_coordenadas(coordenadas_text)
            
            if not lat or not lng:
                # Si no hay coordenadas válidas, saltar este registro
                continue
            
            # Mapear tipo de incidente basado en el contexto/motivo
            contexto = row.get('CONTEXTO') or ''
            motivo = row.get('MOTIVO') or ''
            tipo = self.map_tipo_incidente_from_context(contexto, motivo)
            
            defaults = {
                'tipo': tipo,
                'descripcion': row.get('RELATO DEL HECHO') or motivo,
                'latitud': lat,
                'longitud': lng,
                'fecha_incidente': self.parse_fecha_hora(fecha_hecho, ''),
                'torneo': torneo_name,
                'club_local': club_futbol,
                'club_visitante': '',  # No hay club visitante en datos de mapa
                'estadio': row.get('TIPO DE LUGAR') or '',
                'raw_data': row,
                'last_sync': timezone.now()
            }
            
            obj, created_flag = Incidente.objects.update_or_create(
                external_id=str(external_id),
                defaults=defaults
            )
            
            if created_flag:
                created += 1
            else:
                updated += 1
        
        # Eliminar registros que ya no están en la hoja
        existing_incidentes = Incidente.objects.filter(torneo=torneo_name)
        for incidente in existing_incidentes:
            if incidente.external_id and incidente.external_id not in current_external_ids:
                incidente.delete()
                deleted += 1
        
        return created, updated, deleted
    
    def process_clubes(self, rows, torneo_name):
        """Procesa filas de clubes."""
        created = updated = deleted = 0
        
        logger.info(f"Procesando {len(rows)} filas de clubes para torneo {torneo_name}")
        
        # Debug: imprimir las primeras filas para ver la estructura
        if rows:
            logger.info(f"Primera fila de datos: {rows[0]}")
            logger.info(f"Columnas disponibles: {list(rows[0].keys()) if rows[0] else 'No hay columnas'}")
            
            # Verificar si son datos de clubes o encuentros
            columns = list(rows[0].keys()) if rows[0] else []
            if 'CLUB LOCAL' in columns and 'CLUB VISITANTE' in columns:
                logger.warning("ADVERTENCIA: Los datos parecen ser de ENCUENTROS, no de CLUBES")
                logger.warning("Se esperaban columnas como CLUB, ESCUDO, ESTADIO, etc.")
                logger.warning("Se encontraron columnas como CLUB LOCAL, CLUB VISITANTE, etc.")
            elif 'CLUB' in columns and 'ESCUDO' in columns:
                logger.info("CORRECTO: Los datos parecen ser de CLUBES")
        
        # Obtener todos los external_ids actuales de la hoja
        current_external_ids = set()
        
        for row in rows:
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            
            # Buscar nombre de club en la columna CLUB
            club_name = row.get('CLUB', '').strip()
            if not club_name:
                logger.warning(f"Fila sin nombre de club: {row}")
                continue
                
            # Crear external_id único combinando torneo y club
            external_id = f"{torneo_name}_{club_name}"
            current_external_ids.add(external_id)
            
            defaults = {
                'nombre': club_name,
                'escudo_url': row.get('ESCUDO', ''),
                'estadio': row.get('ESTADIO', ''),
                'capacidad': row.get('CAPACIDAD', ''),
                'fecha_fundacion': row.get('FECHA DE FUNDACIÓN', ''),
                'direccion': row.get('DIRECCIÓN', ''),
                'ubicacion_sede': row.get('UBICACIÓN DE LA SEDE', ''),
                'barras': row.get('HINCHADAS CARACTERIZADAS', '') or row.get('BARRAS', ''),
                'torneo': torneo_name,
                'raw_data': row,
                'last_sync': timezone.now()
            }
            
            obj, created_flag = Club.objects.update_or_create(
                external_id=str(external_id),
                defaults=defaults
            )
            
            if created_flag:
                created += 1
                logger.info(f"Club creado: {club_name} (ID: {obj.id})")
            else:
                updated += 1
                logger.info(f"Club actualizado: {club_name} (ID: {obj.id})")
        
        # Eliminar registros que ya no están en la hoja
        existing_clubes = Club.objects.filter(torneo=torneo_name)
        for club in existing_clubes:
            if club.external_id and club.external_id not in current_external_ids:
                club.delete()
                deleted += 1
        
        return created, updated, deleted
    
    def process_derechos(self, rows, torneo_name):
        """Procesa filas de derechos de admisión."""
        created = updated = deleted = 0
        
        # Obtener todos los external_ids actuales de la hoja
        current_external_ids = set()
        
        for row in rows:
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            
            club_name = row.get('CLUB') or ''
            nombre = row.get('NOMBRE') or ''
            apellido = row.get('APELLIDO') or ''
            
            if not club_name or not nombre:
                continue
                
            # Crear external_id único 
            external_id = f"{torneo_name}_{club_name}_{nombre}_{apellido}"
            current_external_ids.add(external_id)
            
            defaults = {
                'club': club_name,
                'escudo': row.get('ESCUDO') or '',
                'nombre': nombre,
                'apellido': apellido,
                'motivo': row.get('MOTIVO') or '',
                'estado': row.get('ESTADO') or '',
                'fecha_inicio': '',  # No hay columnas específicas de fecha en tu layout
                'fecha_fin': '',
                'torneo': torneo_name,
                'raw_data': row,
                'last_sync': timezone.now()
            }
            
            obj, created_flag = DerechoAdmision.objects.update_or_create(
                external_id=str(external_id),
                defaults=defaults
            )
            
            if created_flag:
                created += 1
            else:
                updated += 1
        
        # Eliminar registros que ya no están en la hoja
        existing_derechos = DerechoAdmision.objects.filter(torneo=torneo_name)
        for derecho in existing_derechos:
            if derecho.external_id and derecho.external_id not in current_external_ids:
                derecho.delete()
                deleted += 1
        
        return created, updated, deleted
    
    def process_ranking(self, rows, torneo_name):
        """Procesa filas de ranking de conflictividad."""
        created = updated = deleted = 0
        
        # Obtener o crear torneo
        torneo, _ = Torneo.objects.get_or_create(
            nombre=torneo_name,
            defaults={
                'fecha_inicio': timezone.now().date(),
                'fecha_fin': timezone.now().date()
            }
        )
        
        # Obtener todos los external_ids actuales de la hoja
        current_external_ids = set()
        
        for row in rows:
            row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            
            club = row.get('CLUB') or row.get('NOMBRE')
            if not club:
                continue
            
            external_id = f"{torneo_name}_{club}"
            current_external_ids.add(external_id)
            
            defaults = {
                'club': club,
                'torneo': torneo,
                'cantidad_conflictos': self.parse_int(row.get('CONFLICTOS') or row.get('CANTIDAD')),
                'nivel_riesgo_promedio': self.map_nivel_riesgo(
                    (row.get('NIVEL RIESGO') or 'BAJO').upper()
                ),
                'ultimo_incidente': self.parse_fecha(row.get('ULTIMO INCIDENTE') or ''),
                'raw_data': row,
                'last_sync': timezone.now()
            }
            
            obj, created_flag = RankingConflictividad.objects.update_or_create(
                external_id=external_id,
                defaults=defaults
            )
            
            if created_flag:
                created += 1
            else:
                updated += 1
        
        # Eliminar registros que ya no están en la hoja
        existing_rankings = RankingConflictividad.objects.filter(torneo=torneo)
        for ranking in existing_rankings:
            if ranking.external_id and ranking.external_id not in current_external_ids:
                ranking.delete()
                deleted += 1
        
        return created, updated, deleted
    
    def process_operacionales(self, file_id, name, torneo_name):
        """Procesa documentos operacionales (PDFs)."""
        url = f"https://drive.google.com/file/d/{file_id}/view"
        
        defaults = {
            'name': name,
            'url': url,
            'torneo': torneo_name,
            'raw_data': {'file_id': file_id, 'torneo': torneo_name},
            'last_sync': timezone.now()
        }
        
        obj, created = OperacionalDoc.objects.update_or_create(
            file_id=file_id,
            defaults=defaults
        )
        
        return 1 if created else 0, 0 if created else 1
    
    def sync_tournament(self, tournament_name, sheets_config):
        """Sincroniza todos los datos de un torneo."""
        total_created = total_updated = total_deleted = 0
        errors = []
        
        for key, info in sheets_config.items():
            try:
                if key == 'operacionales_pdf':
                    # Procesar documentos PDF
                    file_id = info.get('drive_file_id')
                    if file_id:
                        c, u = self.process_operacionales(file_id, key, tournament_name)
                        total_created += c
                        total_updated += u
                        # Los documentos operacionales no se eliminan, solo se crean/actualizan
                        logger.info(f"Procesado documento operacional: {key}")
                    continue
                
                spreadsheet_id = info.get('spreadsheet_id')
                if not spreadsheet_id:
                    continue
                
                logger.info(f"Procesando {key} para {tournament_name}")
                logger.info(f"Info config: {info}")
                
                # Verificar si hay un GID forzado
                force_gid = info.get('force_gid')
                logger.info(f"Force GID encontrado: {force_gid}")
                if force_gid:
                    logger.info(f"Usando GID forzado: {force_gid} para {key} en torneo {tournament_name}")
                    csv_text = self.download_csv(spreadsheet_id, force_gid)
                    if csv_text:
                        rows = self.parse_csv(csv_text)
                        logger.info(f"CSV parseado exitosamente: {len(rows)} filas para {key}")
                        
                        # Debug específico para Copa Argentina
                        if tournament_name == 'COPA ARGENTINA' and key == 'clubes':
                            logger.info(f"=== DEBUG COPA ARGENTINA CLUBES ===")
                            logger.info(f"Spreadsheet ID: {spreadsheet_id}")
                            logger.info(f"GID usado: {force_gid}")
                            logger.info(f"Filas obtenidas: {len(rows)}")
                            if rows:
                                logger.info(f"Primera fila: {rows[0]}")
                                logger.info(f"Columnas: {list(rows[0].keys())}")
                        
                        c, u, d = self._process_by_type(rows, key, tournament_name)
                        total_created += c
                        total_updated += u
                        total_deleted += d
                        logger.info(f"Procesadas {len(rows)} filas con GID {force_gid} - Creados: {c}, Actualizados: {u}, Eliminados: {d}")
                    else:
                        logger.error(f"No se pudo descargar {key} con GID {force_gid}")
                        # Intentar con GID 0 como fallback
                        logger.info(f"Intentando con GID 0 como fallback")
                        csv_text = self.download_csv(spreadsheet_id, 0)
                        if csv_text:
                            rows = self.parse_csv(csv_text)
                            c, u, d = self._process_by_type(rows, key, tournament_name)
                            total_created += c
                            total_updated += u
                            total_deleted += d
                            logger.info(f"Procesadas {len(rows)} filas con GID 0")
                        else:
                            errors.append(f"No se pudo descargar {key} con GID {force_gid} ni con GID 0")
                    continue
                
                # Intentar obtener pestañas
                tabs = self.get_spreadsheet_tabs(spreadsheet_id)
                
                if not tabs:
                    # Fallback: intentar con gid=0
                    logger.warning(f"No se detectaron pestañas para {key}, intentando gid=0")
                    csv_text = self.download_csv(spreadsheet_id, 0)
                    if csv_text:
                        rows = self.parse_csv(csv_text)
                        # Verificar si son datos de encuentros (GID 0 incorrecto)
                        if rows and 'CLUB LOCAL' in list(rows[0].keys()):
                            logger.error(f"GID 0 contiene datos de encuentros, no de {key}")
                            logger.error(f"Se necesitan datos con columnas como CLUB, ESCUDO, ESTADIO")
                            errors.append(f"GID 0 contiene datos de encuentros, no de {key}")
                        else:
                            c, u, d = self._process_by_type(rows, key, tournament_name)
                            total_created += c
                            total_updated += u
                            total_deleted += d
                            logger.info(f"Procesadas {len(rows)} filas con gid=0")
                    else:
                        logger.error(f"No se pudo descargar {key}")
                        errors.append(f"No se pudo descargar {key}")
                else:
                    # Procesar cada pestaña
                    for tab in tabs:
                        gid = tab['gid']
                        name = tab['name']
                        
                        csv_text = self.download_csv(spreadsheet_id, gid)
                        if csv_text:
                            rows = self.parse_csv(csv_text)
                            
                            # Verificar si esta pestaña contiene los datos correctos
                            if rows and self._is_correct_data_type(rows, key):
                                c, u, d = self._process_by_type(rows, key, tournament_name)
                                total_created += c
                                total_updated += u
                                total_deleted += d
                                logger.info(f"Procesada pestaña '{name}' (GID {gid}): {len(rows)} filas")
                            else:
                                logger.info(f"Pestaña '{name}' (GID {gid}) no contiene datos de {key}, saltando")
                        else:
                            logger.warning(f"No se pudo descargar pestaña '{name}'")
                
            except Exception as e:
                error_msg = f"Error procesando {key}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        return total_created, total_updated, total_deleted, errors
    
    def _is_correct_data_type(self, rows, key):
        """Verifica si las filas contienen el tipo de datos correcto."""
        if not rows:
            return False
            
        columns = list(rows[0].keys()) if rows[0] else []
        
        if 'club' in key.lower():
            # Para clubes, buscar las columnas exactas que mencionó el usuario
            required_columns = ['CLUB', 'ESCUDO', 'ESTADIO', 'CAPACIDAD', 'FECHA DE FUNDACIÓN', 'DIRECCIÓN', 'UBICACIÓN DE LA SEDE', 'BARRAS', 'HINCHADAS CARACTERIZADAS']
            found_columns = [col for col in required_columns if col in columns]
            logger.info(f"Columnas encontradas para clubes: {found_columns}")
            # Requerir al menos las primeras 3 columnas principales
            return len(found_columns) >= 3 and 'CLUB' in columns and 'ESCUDO' in columns and 'ESTADIO' in columns
        elif any(k in key.lower() for k in ['encuentro', 'encuentros', 'próximos', 'alerta']):
            # Para encuentros, buscar columnas específicas
            return ('CLUB LOCAL' in columns and 'CLUB VISITANTE' in columns)
        elif 'derecho' in key.lower():
            # Para derechos de admisión
            return ('CLUB' in columns and 'NOMBRE' in columns and 'APELLIDO' in columns)
        elif 'ranking' in key.lower():
            # Para ranking
            return ('CLUB' in columns and 'CONFLICTOS' in columns)
        elif 'mapa' in key.lower():
            # Para mapa de incidentes
            return ('COORDENADAS' in columns and 'CLUB DE FÚTBOL' in columns)
        
        return True  # Por defecto, procesar si no se puede determinar
    
    def _process_by_type(self, rows, key, tournament_name):
        """Procesa filas según el tipo de datos."""
        if any(k in key.lower() for k in ['encuentro', 'encuentros', 'próximos', 'alerta']):
            return self.process_encuentros(rows, tournament_name)
        elif 'club' in key.lower():
            return self.process_clubes(rows, tournament_name)
        elif 'derecho' in key.lower():
            return self.process_derechos(rows, tournament_name)
        elif 'ranking' in key.lower():
            return self.process_ranking(rows, tournament_name)
        elif 'mapa' in key.lower():
            return self.process_incidentes(rows, tournament_name)
        else:
            # Fallback: intentar como encuentros
            return self.process_encuentros(rows, tournament_name)
    
    def parse_fecha(self, fecha_str):
        """Parsea fecha desde string a objeto date."""
        if not fecha_str:
            return None
        
        try:
            # Limpiar string
            fecha_str = str(fecha_str).strip()
            
            # Intentar diferentes formatos
            formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y']
            for formato in formatos:
                try:
                    return datetime.strptime(fecha_str, formato).date()
                except ValueError:
                    continue
            return None
        except:
            return None
    
    def parse_hora(self, hora_str):
        """Parsea hora desde string a objeto time."""
        if not hora_str:
            return None
        
        try:
            # Limpiar string
            hora_str = str(hora_str).strip().replace('hs', '').replace(':', '')
            
            if len(hora_str) == 4:  # HHMM
                return datetime.strptime(hora_str, '%H%M').time()
            elif len(hora_str) == 3:  # HMM
                return datetime.strptime('0' + hora_str, '%H%M').time()
            elif ':' in str(hora_str):
                return datetime.strptime(str(hora_str), '%H:%M').time()
            return None
        except:
            return None
    
    def parse_fecha_hora(self, fecha_str, hora_str):
        """Parsea fecha y hora combinadas."""
        fecha = self.parse_fecha(fecha_str)
        hora = self.parse_hora(hora_str)
        
        if fecha and hora:
            return datetime.combine(fecha, hora)
        elif fecha:
            return datetime.combine(fecha, datetime.min.time())
        else:
            return timezone.now()
    
    def parse_float(self, value):
        """Parsea string a float."""
        if not value:
            return None
        try:
            return float(str(value).replace(',', '.'))
        except:
            return None
    
    def parse_int(self, value):
        """Parsea string a int."""
        if not value:
            return 0
        try:
            return int(str(value))
        except:
            return 0
    
    def map_nivel_riesgo(self, riesgo_text):
        """Mapea texto de riesgo a opciones del modelo."""
        riesgo_text = str(riesgo_text).upper().strip()
        
        # Mapear números a niveles de riesgo
        if riesgo_text in ['1', 'UNO']:
            return 'BAJO'
        elif riesgo_text in ['2', 'DOS']:
            return 'MEDIO'
        elif riesgo_text in ['3', 'TRES']:
            return 'ALTO'
        elif riesgo_text in ['4', 'CUATRO', '5', 'CINCO']:
            return 'CRITICO'
        # Mapear texto
        elif any(word in riesgo_text for word in ['CRITICO', 'CRÍTICO', 'ALTO']):
            return 'CRITICO'
        elif any(word in riesgo_text for word in ['MEDIO', 'MEDIANO']):
            return 'MEDIO'
        elif any(word in riesgo_text for word in ['BAJO']):
            return 'BAJO'
        else:
            return 'BAJO'
    
    def map_tipo_incidente(self, tipo_text):
        """Mapea texto de tipo a opciones del modelo."""
        tipo_text = str(tipo_text).upper()
        
        if any(word in tipo_text for word in ['VIOLENCIA', 'VIOLENTO']):
            return 'VIOLENCIA'
        elif any(word in tipo_text for word in ['DESTRUCCION', 'DESTRUCCIÓN']):
            return 'DESTRUCCION'
        elif any(word in tipo_text for word in ['INVASION', 'INVASIÓN']):
            return 'INVASION'
        elif any(word in tipo_text for word in ['DISPUTA', 'PELEA']):
            return 'DISPUTA'
        else:
            return 'OTRO'
    
    def parse_coordenadas(self, coordenadas_text):
        """Parsea coordenadas del formato 'lat,lng' o similares."""
        if not coordenadas_text:
            return None, None
        
        try:
            # Intentar varios formatos comunes
            coords_clean = str(coordenadas_text).strip()
            
            # Formato: "lat,lng" o "lat, lng"
            if ',' in coords_clean:
                parts = coords_clean.split(',')
                if len(parts) >= 2:
                    lat = float(parts[0].strip())
                    lng = float(parts[1].strip())
                    return lat, lng
            
            # Formato: "lat lng" (separado por espacio)
            if ' ' in coords_clean:
                parts = coords_clean.split()
                if len(parts) >= 2:
                    lat = float(parts[0].strip())
                    lng = float(parts[1].strip())
                    return lat, lng
                    
        except (ValueError, TypeError, AttributeError):
            pass
            
        return None, None
    
    def map_tipo_incidente_from_context(self, contexto, motivo):
        """Mapea tipo de incidente basado en contexto y motivo."""
        contexto_lower = str(contexto).lower()
        motivo_lower = str(motivo).lower()
        
        combined = f"{contexto_lower} {motivo_lower}"
        
        if any(word in combined for word in ['violencia', 'agresión', 'pelea', 'golpe']):
            return 'VIOLENCIA'
        elif any(word in combined for word in ['vandalism', 'daño', 'rotura', 'destrozo']):
            return 'VANDALISMO'
        elif any(word in combined for word in ['droga', 'narcótico', 'estupefaciente']):
            return 'DROGAS'
        elif any(word in combined for word in ['robo', 'hurto', 'sustracción']):
            return 'ROBO'
        elif any(word in combined for word in ['disturbio', 'desorden', 'tumulto']):
            return 'DISTURBIO'
        else:
            return 'OTRO'
