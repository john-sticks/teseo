"""
Servicio para la integración con Google Sheets API específico para el módulo de Clubes.
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from django.conf import settings
import logging
from datetime import datetime
import re
import os

logger = logging.getLogger(__name__)

class ClubesGoogleSheetsService:
    """Servicio para manejar la integración con Google Sheets para clubes."""
    
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
    
    def obtener_datos_clubes(self, torneo):
        """Obtiene datos de clubes desde Google Sheets."""
        try:
            if not self.client:
                return self._datos_mock_clubes(torneo)
            
            sheets_config = settings.TOURNAMENT_SHEETS.get(torneo, {})
            url_clubes = sheets_config.get('clubes')
            
            if not url_clubes:
                logger.error(f"No hay configuración de sheets para clubes en torneo {torneo}")
                return []
            
            spreadsheet_id = self.extraer_id_spreadsheet(url_clubes)
            if not spreadsheet_id:
                logger.error(f"No se pudo extraer ID del spreadsheet: {url_clubes}")
                return []
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            # Obtener todos los registros
            records = worksheet.get_all_records()
            
            # Procesar y limpiar datos
            clubes_procesados = []
            for record in records:
                if record.get('Nombre'):
                    club = {
                        'nombre': record.get('Nombre', '').strip(),
                        'nombre_corto': record.get('Nombre Corto', '').strip(),
                        'estadio': record.get('Estadio', '').strip(),
                        'direccion_estadio': record.get('Dirección Estadio', '').strip(),
                        'ciudad': record.get('Ciudad', '').strip(),
                        'provincia': record.get('Provincia', '').strip(),
                        'telefono': record.get('Teléfono', '').strip(),
                        'email': record.get('Email', '').strip(),
                        'sitio_web': record.get('Sitio Web', '').strip(),
                        'fundacion': self._parsear_fecha(record.get('Fundación', '')),
                        'colores': record.get('Colores', '').strip(),
                        'presidente': record.get('Presidente', '').strip(),
                    }
                    clubes_procesados.append(club)
            
            return clubes_procesados
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de clubes: {e}")
            return self._datos_mock_clubes(torneo)
    
    def obtener_datos_facciones(self, torneo):
        """Obtiene datos de facciones de hinchadas desde Google Sheets."""
        try:
            if not self.client:
                return self._datos_mock_facciones(torneo)
            
            # Para facciones, usamos la misma hoja de clubes pero con pestaña específica
            sheets_config = settings.TOURNAMENT_SHEETS.get(torneo, {})
            url_clubes = sheets_config.get('clubes')
            
            if not url_clubes:
                return []
            
            spreadsheet_id = self.extraer_id_spreadsheet(url_clubes)
            if not spreadsheet_id:
                return []
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # Intentar obtener la pestaña de facciones
            try:
                worksheet = spreadsheet.worksheet('Facciones')
            except:
                # Si no existe, usar la primera pestaña
                worksheet = spreadsheet.sheet1
            
            records = worksheet.get_all_records()
            
            facciones_procesadas = []
            for record in records:
                if record.get('Club') and record.get('Nombre Facción'):
                    faccion = {
                        'club': record.get('Club', '').strip(),
                        'nombre': record.get('Nombre Facción', '').strip(),
                        'tipo': record.get('Tipo', 'HINCHADA').upper(),
                        'descripcion': record.get('Descripción', '').strip(),
                        'activa': record.get('Activa', 'SÍ').upper() == 'SÍ',
                        'cantidad_estimada': int(record.get('Cantidad Estimada', 0) or 0),
                    }
                    facciones_procesadas.append(faccion)
            
            return facciones_procesadas
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de facciones: {e}")
            return self._datos_mock_facciones(torneo)
    
    def obtener_datos_antecedentes(self, torneo):
        """Obtiene datos de antecedentes desde Google Sheets."""
        try:
            if not self.client:
                return self._datos_mock_antecedentes(torneo)
            
            sheets_config = settings.TOURNAMENT_SHEETS.get(torneo, {})
            url_clubes = sheets_config.get('clubes')
            
            if not url_clubes:
                return []
            
            spreadsheet_id = self.extraer_id_spreadsheet(url_clubes)
            if not spreadsheet_id:
                return []
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # Intentar obtener la pestaña de antecedentes
            try:
                worksheet = spreadsheet.worksheet('Antecedentes')
            except:
                # Si no existe, usar la primera pestaña
                worksheet = spreadsheet.sheet1
            
            records = worksheet.get_all_records()
            
            antecedentes_procesados = []
            for record in records:
                if record.get('Club') and record.get('Tipo'):
                    antecedente = {
                        'club': record.get('Club', '').strip(),
                        'tipo': record.get('Tipo', '').upper(),
                        'descripcion': record.get('Descripción', '').strip(),
                        'fecha_incidente': self._parsear_fecha(record.get('Fecha Incidente', '')),
                        'lugar': record.get('Lugar', '').strip(),
                        'sancion_impuesta': record.get('Sanción Impuesta', '').strip(),
                        'monto_sancion': self._parsear_decimal(record.get('Monto Sanción', '')),
                        'observaciones': record.get('Observaciones', '').strip(),
                    }
                    antecedentes_procesados.append(antecedente)
            
            return antecedentes_procesados
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de antecedentes: {e}")
            return self._datos_mock_antecedentes(torneo)
    
    def actualizar_datos_clubes(self, torneo, datos):
        """Actualiza datos de clubes en Google Sheets."""
        try:
            if not self.client:
                logger.warning("No se puede actualizar sin credenciales de Google Sheets")
                return False
            
            sheets_config = settings.TOURNAMENT_SHEETS.get(torneo, {})
            url_clubes = sheets_config.get('clubes')
            
            if not url_clubes:
                logger.error(f"No hay configuración para clubes en torneo {torneo}")
                return False
            
            spreadsheet_id = self.extraer_id_spreadsheet(url_clubes)
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
            logger.error(f"Error actualizando datos de clubes: {e}")
            return False
    
    def sincronizar_clubes(self, torneo):
        """Sincroniza todos los datos de clubes de un torneo."""
        resultado = {
            'clubes': 0,
            'facciones': 0,
            'antecedentes': 0,
            'errores': []
        }
        
        try:
            # Sincronizar clubes
            clubes = self.obtener_datos_clubes(torneo)
            if clubes:
                resultado['clubes'] = len(clubes)
            
            # Sincronizar facciones
            facciones = self.obtener_datos_facciones(torneo)
            if facciones:
                resultado['facciones'] = len(facciones)
            
            # Sincronizar antecedentes
            antecedentes = self.obtener_datos_antecedentes(torneo)
            if antecedentes:
                resultado['antecedentes'] = len(antecedentes)
                
        except Exception as e:
            resultado['errores'].append(str(e))
            logger.error(f"Error sincronizando clubes del torneo {torneo}: {e}")
        
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
    
    def _parsear_decimal(self, decimal_str):
        """Parsea string a decimal."""
        if not decimal_str:
            return None
        
        try:
            # Limpiar string y convertir
            decimal_str = decimal_str.strip().replace(',', '').replace('$', '')
            return float(decimal_str)
        except:
            return None
    
    def _datos_mock_clubes(self, torneo):
        """Datos de ejemplo para desarrollo."""
        return [
            {
                'nombre': 'Club Atlético Boca Juniors',
                'nombre_corto': 'Boca',
                'estadio': 'La Bombonera',
                'direccion_estadio': 'Brandsen 805, La Boca',
                'ciudad': 'Buenos Aires',
                'provincia': 'Buenos Aires',
                'telefono': '+54 11 4309-4700',
                'email': 'info@bocajuniors.com.ar',
                'sitio_web': 'https://www.bocajuniors.com.ar',
                'fundacion': datetime(1905, 4, 3).date(),
                'colores': 'Azul y Amarillo',
                'presidente': 'Jorge Amor Ameal',
            },
            {
                'nombre': 'Club Atlético River Plate',
                'nombre_corto': 'River',
                'estadio': 'Estadio Monumental',
                'direccion_estadio': 'Av. Figueroa Alcorta 7597',
                'ciudad': 'Buenos Aires',
                'provincia': 'Buenos Aires',
                'telefono': '+54 11 4789-1200',
                'email': 'info@cariverplate.com.ar',
                'sitio_web': 'https://www.cariverplate.com.ar',
                'fundacion': datetime(1901, 5, 25).date(),
                'colores': 'Rojo y Blanco',
                'presidente': 'Jorge Brito',
            }
        ]
    
    def _datos_mock_facciones(self, torneo):
        """Facciones de ejemplo para desarrollo."""
        return [
            {
                'club': 'Boca',
                'nombre': 'La Doce',
                'tipo': 'BARRA_BRAVA',
                'descripcion': 'Barra brava principal de Boca Juniors',
                'activa': True,
                'cantidad_estimada': 5000,
            },
            {
                'club': 'River',
                'nombre': 'Los Borrachos del Tablón',
                'tipo': 'BARRA_BRAVA',
                'descripcion': 'Barra brava principal de River Plate',
                'activa': True,
                'cantidad_estimada': 4000,
            }
        ]
    
    def _datos_mock_antecedentes(self, torneo):
        """Antecedentes de ejemplo para desarrollo."""
        return [
            {
                'club': 'Boca',
                'tipo': 'INCIDENTE',
                'descripcion': 'Incidente en clásico contra River',
                'fecha_incidente': datetime.now().date(),
                'lugar': 'La Bombonera',
                'sancion_impuesta': 'Multa económica',
                'monto_sancion': 100000.00,
                'observaciones': 'Incidente menor entre hinchadas',
            }
        ]
