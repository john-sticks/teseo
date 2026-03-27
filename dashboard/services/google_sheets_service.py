"""
Servicio para la integración con Google Sheets API.
Maneja la sincronización bidireccional de datos del sistema REF.
"""
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    """Servicio para manejar la integración con Google Sheets."""
    
    def __init__(self):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = None
        self.client = None
        self.sheets_config = {
            'LPF': {
                'encuentros': '1-lYFhNHfLT7qnj6SxKqhUQ-fHYjdDAAT',
                'ranking': '1d1I_ljiyIP6UQ84dNxldg19yhUQ3iIFN',
                'mapa': '1d1I_ljiyIP6UQ84dNxldg19yhUQ3iIFN',
                'clubes': '18A90XIQ-0eXb9q_x8ZLYaavhQpmVWCHW',
                'derecho_admision': '1W9N9YmqRxlgSeCJ39WLbZ23L1ITDVTw6',
                'operacionales': '1jrJ_iWNGbqLQ5GDYOq9mgz5KQTEJNOb_'
            },
            'ASCENSO': {
                'encuentros': '1R_TYK51xLRJcyjiBAlHlrBtrKxHeehuo',
                'clubes': '1zOaXceeRJwja_0dsIMLjFHgl4Eux3bf7',
                'derecho_admision': '1PFgfR88ZCHFhleT_7bp8TN5p-QfIz7xZ',
                'operacionales': '1HMLGAbXifwHSvpJgqOKlaQKYNBMI_pL_',
                'mapa': '1sN8J7lUpf4eVIE_y3F9IWEC-_cRXXk8h'
            },
            'COPA_ARGENTINA': {
                'encuentros': '1TQYOmLbkdykEHz1iVw3AwKt8A3Wvn-gC',
                'clubes': '1hBkft64ISW7M6ESyBkveruUBqxrryT85',
                'derecho_admision': '1nf_oayZqj1c28ZEBeKvnZcXYEFYW8yhX',
                'operacionales': '1WblcUlEOUASAzWFovkJ2tu4JFuLd58Xh'
            },
            'COPA_SUDAMERICANA': {
                'encuentros': '1XnOvES7Rd3OVgvb37HYjQMtwJo1fRIhz',
                'clubes': '1T3MGWy0mVGxu6FqQAIw9zJqT7t_si1eD',
                'derecho_admision': '1UH8uoEImdYTXoGlLXiE_X5kVqcz62KPg',
                'operacionales': '1gXZwLgLd_bA29egKnjCE3DNoAVdb_OVc'
            },
            'COPA_LIBERTADORES': {
                'encuentros': '106MUaLytdvyvNiTiBiUZFHU0fqVMU1lW',
                'clubes': '1BodR1rkA3NaqtBpPMRdPQ1kcCSGz1_73',
                'derecho_admision': '1Dqbvm5XSbD0THhiVNa5zpgxTpV2qJ0V0',
                'operacionales': '1whwfYBDMcJ6wN-Tdml9aX-ZxJ4mMMNkL'
            }
        }
        self._conectar()
    
    def _conectar(self):
        """Establece conexión con Google Sheets API."""
        try:
            # Para desarrollo, usaremos credenciales de servicio
            # En producción, esto debería estar en variables de entorno
            creds_path = settings.GOOGLE_SHEETS_CREDENTIALS_PATH
            
            # Si no hay credenciales, usar acceso público (solo lectura)
            if creds_path and os.path.exists(creds_path):
                self.credentials = ServiceAccountCredentials.from_json_keyfile_name(
                    creds_path, self.scope
                )
                self.client = gspread.authorize(self.credentials)
            else:
                # Modo de solo lectura para desarrollo
                logger.warning("Credenciales de Google Sheets no encontradas. Usando modo solo lectura.")
                self.client = None
                
        except Exception as e:
            logger.error(f"Error conectando con Google Sheets: {e}")
            self.client = None
    
    def extraer_id_spreadsheet(self, url):
        """Extrae el ID del spreadsheet de la URL de Google Sheets."""
        # Patrón para URLs de Google Sheets
        patron = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(patron, url)
        if match:
            return match.group(1)
        return None
    
    def obtener_datos_encuentros(self, torneo):
        """Obtiene datos de encuentros desde Google Sheets."""
        try:
            if not self.client:
                return self._datos_mock_encuentros(torneo)
            
            sheets_config = settings.TOURNAMENT_SHEETS.get(torneo, {})
            url_encuentros = sheets_config.get('encuentros')
            
            if not url_encuentros:
                logger.error(f"No hay configuración de sheets para torneo {torneo}")
                return []
            
            spreadsheet_id = self.extraer_id_spreadsheet(url_encuentros)
            if not spreadsheet_id:
                logger.error(f"No se pudo extraer ID del spreadsheet: {url_encuentros}")
                return []
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            # Obtener todos los registros
            records = worksheet.get_all_records()
            
            # Procesar y limpiar datos
            encuentros_procesados = []
            for record in records:
                if record.get('Fecha') and record.get('Club Local'):
                    encuentro = {
                        'fecha': self._parsear_fecha(record.get('Fecha', '')),
                        'hora': self._parsear_hora(record.get('Hora', '')),
                        'club_local': record.get('Club Local', '').strip(),
                        'club_visitante': record.get('Club Visitante', '').strip(),
                        'estadio': record.get('Estadio', '').strip(),
                        'nivel_riesgo': record.get('Nivel Riesgo', 'BAJO').upper(),
                        'motivo_alerta': record.get('Motivo Alerta', '').strip(),
                        'relato_hecho': record.get('Relato del Hecho', '').strip(),
                    }
                    encuentros_procesados.append(encuentro)
            
            return encuentros_procesados
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de encuentros: {e}")
            return self._datos_mock_encuentros(torneo)
    
    def obtener_datos_ranking(self, torneo):
        """Obtiene datos del ranking de conflictividad."""
        try:
            if not self.client:
                return self._datos_mock_ranking(torneo)
            
            sheets_config = settings.TOURNAMENT_SHEETS.get(torneo, {})
            url_ranking = sheets_config.get('ranking')
            
            if not url_ranking:
                return []
            
            spreadsheet_id = self.extraer_id_spreadsheet(url_ranking)
            if not spreadsheet_id:
                return []
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            records = worksheet.get_all_records()
            
            ranking_procesado = []
            for record in records:
                if record.get('Club'):
                    ranking = {
                        'club': record.get('Club', '').strip(),
                        'cantidad_conflictos': int(record.get('Conflictos', 0) or 0),
                        'nivel_riesgo_promedio': record.get('Nivel Riesgo', 'BAJO').upper(),
                        'ultimo_incidente': self._parsear_fecha(record.get('Último Incidente', ''))
                    }
                    ranking_procesado.append(ranking)
            
            return ranking_procesado
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de ranking: {e}")
            return self._datos_mock_ranking(torneo)
    
    def obtener_datos_incidentes_mapa(self, torneo):
        """Obtiene datos de incidentes para el mapa."""
        try:
            if not self.client:
                return self._datos_mock_incidentes(torneo)
            
            sheets_config = settings.TOURNAMENT_SHEETS.get(torneo, {})
            url_mapa = sheets_config.get('mapa')
            
            if not url_mapa:
                return []
            
            spreadsheet_id = self.extraer_id_spreadsheet(url_mapa)
            if not spreadsheet_id:
                return []
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            records = worksheet.get_all_records()
            
            incidentes_procesados = []
            for record in records:
                if record.get('Latitud') and record.get('Longitud'):
                    incidente = {
                        'tipo': record.get('Tipo', 'OTRO').upper(),
                        'descripcion': record.get('Descripción', '').strip(),
                        'latitud': float(record.get('Latitud', 0) or 0),
                        'longitud': float(record.get('Longitud', 0) or 0),
                        'club_local': record.get('Club Local', '').strip(),
                        'club_visitante': record.get('Club Visitante', '').strip(),
                        'estadio': record.get('Estadio', '').strip(),
                        'fecha_incidente': self._parsear_fecha_hora(
                            record.get('Fecha', ''), 
                            record.get('Hora', '')
                        )
                    }
                    incidentes_procesados.append(incidente)
            
            return incidentes_procesados
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de incidentes: {e}")
            return self._datos_mock_incidentes(torneo)
    
    def actualizar_datos(self, torneo, datos, tipo_datos):
        """Actualiza datos en Google Sheets."""
        try:
            if not self.client:
                logger.warning("No se puede actualizar sin credenciales de Google Sheets")
                return False
            
            sheets_config = settings.TOURNAMENT_SHEETS.get(torneo, {})
            url_sheet = sheets_config.get(tipo_datos)
            
            if not url_sheet:
                logger.error(f"No hay configuración para {tipo_datos} en torneo {torneo}")
                return False
            
            spreadsheet_id = self.extraer_id_spreadsheet(url_sheet)
            if not spreadsheet_id:
                return False
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            # Limpiar hoja y escribir nuevos datos
            worksheet.clear()
            
            if datos:
                # Escribir headers
                headers = list(datos[0].keys())
                worksheet.append_row(headers)
                
                # Escribir datos
                for fila in datos:
                    valores = [fila.get(header, '') for header in headers]
                    worksheet.append_row(valores)
            
            return True
            
        except Exception as e:
            logger.error(f"Error actualizando datos: {e}")
            return False
    
    def sincronizar_torneo(self, torneo):
        """Sincroniza todos los datos de un torneo."""
        resultado = {
            'encuentros': 0,
            'ranking': 0,
            'incidentes': 0,
            'errores': []
        }
        
        try:
            # Sincronizar encuentros
            encuentros = self.obtener_datos_encuentros(torneo)
            if encuentros:
                resultado['encuentros'] = len(encuentros)
            
            # Sincronizar ranking
            ranking = self.obtener_datos_ranking(torneo)
            if ranking:
                resultado['ranking'] = len(ranking)
            
            # Sincronizar incidentes
            incidentes = self.obtener_datos_incidentes_mapa(torneo)
            if incidentes:
                resultado['incidentes'] = len(incidentes)
                
        except Exception as e:
            resultado['errores'].append(str(e))
            logger.error(f"Error sincronizando torneo {torneo}: {e}")
        
        return resultado
    
    def _parsear_fecha(self, fecha_str):
        """Parsea fecha desde string a objeto date."""
        if not fecha_str:
            return None
        
        try:
            # Intentar diferentes formatos
            formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
            for formato in formatos:
                try:
                    return datetime.strptime(fecha_str.strip(), formato).date()
                except ValueError:
                    continue
            return None
        except:
            return None
    
    def _parsear_hora(self, hora_str):
        """Parsea hora desde string a objeto time."""
        if not hora_str:
            return None
        
        try:
            # Limpiar string
            hora_str = hora_str.strip().replace('hs', '').replace(':', '')
            if len(hora_str) == 4:  # HHMM
                return datetime.strptime(hora_str, '%H%M').time()
            elif len(hora_str) == 3:  # HMM
                return datetime.strptime('0' + hora_str, '%H%M').time()
            return None
        except:
            return None
    
    def _parsear_fecha_hora(self, fecha_str, hora_str):
        """Parsea fecha y hora combinadas."""
        fecha = self._parsear_fecha(fecha_str)
        hora = self._parsear_hora(hora_str)
        
        if fecha and hora:
            return datetime.combine(fecha, hora)
        return datetime.now()
    
    def _datos_mock_encuentros(self, torneo):
        """Datos de ejemplo para desarrollo."""
        return [
            {
                'fecha': datetime.now().date(),
                'hora': datetime.now().time(),
                'club_local': 'Boca Juniors',
                'club_visitante': 'River Plate',
                'estadio': 'La Bombonera',
                'nivel_riesgo': 'ALTO',
                'motivo_alerta': 'Clásico de alto riesgo',
                'relato_hecho': 'Encuentro con alto nivel de tensión histórica'
            }
        ]
    
    def _datos_mock_ranking(self, torneo):
        """Ranking de ejemplo para desarrollo."""
        return [
            {
                'club': 'Boca Juniors',
                'cantidad_conflictos': 15,
                'nivel_riesgo_promedio': 'ALTO',
                'ultimo_incidente': datetime.now().date()
            }
        ]
    
    def _datos_mock_incidentes(self, torneo):
        """Incidentes de ejemplo para desarrollo."""
        return [
            {
                'tipo': 'VIOLENCIA',
                'descripcion': 'Incidente entre hinchadas',
                'latitud': -34.6037,
                'longitud': -58.3816,
                'club_local': 'Boca Juniors',
                'club_visitante': 'River Plate',
                'estadio': 'La Bombonera',
                'fecha_incidente': datetime.now()
            }
        ]
