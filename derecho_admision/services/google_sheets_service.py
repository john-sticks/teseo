"""
Servicio para la integración con Google Sheets API específico para el módulo de Derecho de Admisión.
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
import logging
from datetime import datetime
import re
import os

logger = logging.getLogger(__name__)

class DerechoAdmisionGoogleSheetsService:
    """Servicio para manejar la integración con Google Sheets para derechos de admisión."""
    
    def __init__(self):
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.credentials = None
        self.client = None
        self._conectar()
    
    def _conectar(self):
        """Establece conexión con Google Sheets API."""
        try:
            creds_path = settings.GOOGLE_SHEETS_CREDENTIALS_PATH
            
            if creds_path and os.path.exists(creds_path):
                self.credentials = ServiceAccountCredentials.from_json_keyfile_name(
                    creds_path, self.scope
                )
                self.client = gspread.authorize(self.credentials)
            else:
                logger.warning("Credenciales de Google Sheets no encontradas. Usando modo solo lectura.")
                self.client = None
                
        except Exception as e:
            logger.error(f"Error conectando con Google Sheets: {e}")
            self.client = None
    
    def extraer_id_spreadsheet(self, url):
        """Extrae el ID del spreadsheet de la URL de Google Sheets."""
        patron = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(patron, url)
        if match:
            return match.group(1)
        return None
    
    def obtener_datos_derechos(self, torneo):
        """Obtiene datos de derechos de admisión desde Google Sheets."""
        try:
            if not self.client:
                return self._datos_mock_derechos(torneo)
            
            sheets_config = settings.TOURNAMENT_SHEETS.get(torneo, {})
            url_derechos = sheets_config.get('derecho_admision')
            
            if not url_derechos:
                logger.error(f"No hay configuración de sheets para derechos en torneo {torneo}")
                return []
            
            spreadsheet_id = self.extraer_id_spreadsheet(url_derechos)
            if not spreadsheet_id:
                logger.error(f"No se pudo extraer ID del spreadsheet: {url_derechos}")
                return []
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            # Obtener todos los registros
            records = worksheet.get_all_records()
            
            # Procesar y limpiar datos
            derechos_procesados = []
            for record in records:
                if record.get('Club'):
                    derecho = {
                        'club': record.get('Club', '').strip(),
                        'motivo': record.get('Motivo', 'OTRO').upper(),
                        'descripcion': record.get('Descripción', '').strip(),
                        'fecha_imposicion': self._parsear_fecha(record.get('Fecha Imposición', '')),
                        'fecha_vencimiento': self._parsear_fecha(record.get('Fecha Vencimiento', '')),
                        'estado': record.get('Estado', 'VIGENTE').upper(),
                        'observaciones': record.get('Observaciones', '').strip(),
                    }
                    derechos_procesados.append(derecho)
            
            return derechos_procesados
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de derechos: {e}")
            return self._datos_mock_derechos(torneo)
    
    def sincronizar_derechos(self, torneo):
        """Sincroniza todos los datos de derechos de admisión de un torneo."""
        resultado = {
            'derechos': 0,
            'errores': []
        }
        
        try:
            # Sincronizar derechos
            derechos = self.obtener_datos_derechos(torneo)
            if derechos:
                resultado['derechos'] = len(derechos)
                
        except Exception as e:
            resultado['errores'].append(str(e))
            logger.error(f"Error sincronizando derechos del torneo {torneo}: {e}")
        
        return resultado
    
    def _parsear_fecha(self, fecha_str):
        """Parsea fecha desde string a objeto date."""
        if not fecha_str:
            return None
        
        try:
            formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
            for formato in formatos:
                try:
                    return datetime.strptime(fecha_str.strip(), formato).date()
                except ValueError:
                    continue
            return None
        except:
            return None
    
    def _datos_mock_derechos(self, torneo):
        """Datos de ejemplo para desarrollo."""
        return [
            {
                'club': 'Boca Juniors',
                'motivo': 'VIOLENCIA',
                'descripcion': 'Incidente en clásico contra River Plate',
                'fecha_imposicion': datetime.now().date(),
                'fecha_vencimiento': datetime.now().date().replace(month=12, day=31),
                'estado': 'VIGENTE',
                'observaciones': 'Derecho de admisión por incidentes violentos',
            },
            {
                'club': 'River Plate',
                'motivo': 'INVASION',
                'descripcion': 'Invasión de campo en partido vs San Lorenzo',
                'fecha_imposicion': datetime.now().date(),
                'fecha_vencimiento': None,
                'estado': 'LEVANTADO',
                'observaciones': 'Derecho levantado tras cumplimiento de medidas',
            }
        ]
