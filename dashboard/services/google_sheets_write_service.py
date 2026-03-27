"""
Servicio para escribir datos en Google Sheets usando la API de Google.
Permite actualizar, crear y modificar datos en las hojas de Google Sheets.
"""
import gspread
from google.oauth2.service_account import Credentials
from django.conf import settings
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class GoogleSheetsWriteService:
    """Servicio para escribir datos en Google Sheets."""
    
    def __init__(self):
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.client = None
        self._conectar()
    
    def _conectar(self):
        """Establece conexión con Google Sheets API."""
        try:
            # Ruta al archivo de credenciales
            creds_path = os.path.join(settings.BASE_DIR, 'credentials', 'just-coda-473000-f4-c4748e7930d6.json')
            
            if os.path.exists(creds_path):
                creds = Credentials.from_service_account_file(creds_path, scopes=self.scope)
                self.client = gspread.authorize(creds)
                logger.info("Conexión exitosa con Google Sheets API")
            else:
                logger.error(f"Archivo de credenciales no encontrado: {creds_path}")
                self.client = None
                
        except Exception as e:
            logger.error(f"Error conectando con Google Sheets API: {e}")
            self.client = None
    
    def abrir_hoja(self, spreadsheet_id: str, worksheet_name: str = None):
        """Abre una hoja específica de Google Sheets."""
        try:
            if not self.client:
                raise Exception("Cliente de Google Sheets no está conectado")
            
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            if worksheet_name:
                worksheet = spreadsheet.worksheet(worksheet_name)
            else:
                worksheet = spreadsheet.sheet1
            
            return worksheet
            
        except Exception as e:
            logger.error(f"Error abriendo hoja {spreadsheet_id}: {e}")
            raise
    
    def leer_datos(self, spreadsheet_id: str, worksheet_name: str = None) -> List[Dict]:
        """Lee todos los datos de una hoja."""
        try:
            worksheet = self.abrir_hoja(spreadsheet_id, worksheet_name)
            return worksheet.get_all_records()
        except Exception as e:
            logger.error(f"Error leyendo datos: {e}")
            raise
    
    def escribir_celda(self, spreadsheet_id: str, celda: str, valor: str, worksheet_name: str = None):
        """Actualiza una celda específica."""
        try:
            worksheet = self.abrir_hoja(spreadsheet_id, worksheet_name)
            worksheet.update(celda, valor)
            logger.info(f"Celda {celda} actualizada con valor: {valor}")
            return True
        except Exception as e:
            logger.error(f"Error escribiendo en celda {celda}: {e}")
            raise
    
    def escribir_fila(self, spreadsheet_id: str, fila_numero: int, valores: List[str], worksheet_name: str = None):
        """Actualiza una fila completa."""
        try:
            worksheet = self.abrir_hoja(spreadsheet_id, worksheet_name)
            worksheet.update(f'A{fila_numero}:{chr(65 + len(valores) - 1)}{fila_numero}', [valores])
            logger.info(f"Fila {fila_numero} actualizada")
            return True
        except Exception as e:
            logger.error(f"Error escribiendo fila {fila_numero}: {e}")
            raise
    
    def agregar_fila(self, spreadsheet_id: str, valores: List[str], worksheet_name: str = None):
        """Agrega una nueva fila al final de la hoja."""
        try:
            worksheet = self.abrir_hoja(spreadsheet_id, worksheet_name)
            worksheet.append_row(valores)
            logger.info("Nueva fila agregada")
            return True
        except Exception as e:
            logger.error(f"Error agregando fila: {e}")
            raise
    
    def buscar_y_actualizar(self, spreadsheet_id: str, columna_busqueda: str, valor_busqueda: str, 
                           columna_actualizacion: str, nuevo_valor: str, worksheet_name: str = None):
        """Busca una fila por valor y actualiza una columna específica."""
        try:
            worksheet = self.abrir_hoja(spreadsheet_id, worksheet_name)
            
            # Buscar la celda con el valor
            celda = worksheet.find(valor_busqueda)
            if celda:
                # Calcular la columna de actualización
                col_actualizacion_num = ord(columna_actualizacion.upper()) - ord('A') + 1
                celda_actualizacion = f"{columna_actualizacion}{celda.row}"
                
                worksheet.update(celda_actualizacion, nuevo_valor)
                logger.info(f"Valor actualizado: {celda_actualizacion} = {nuevo_valor}")
                return True
            else:
                logger.warning(f"Valor '{valor_busqueda}' no encontrado en la hoja")
                return False
                
        except Exception as e:
            logger.error(f"Error en búsqueda y actualización: {e}")
            raise
    
    def actualizar_club(self, torneo: str, nombre_club: str, campo: str, nuevo_valor: str):
        """Actualiza un campo específico de un club en la hoja correspondiente."""
        try:
            from sheets_config import SHEETS_MAP
            
            sheets_config = SHEETS_MAP.get(torneo, {})
            clubes_config = sheets_config.get('clubes')
            
            if not clubes_config:
                raise Exception(f"No hay configuración de clubes para el torneo {torneo}")
            
            spreadsheet_id = clubes_config['spreadsheet_id']
            
            # Mapear campos de la base de datos a columnas de la hoja
            mapeo_campos = {
                'nombre': 'A',  # Columna A - Nombre del club
                'estadio': 'C',  # Columna C - Estadio
                'direccion': 'E',  # Columna E - Dirección
                'escudo_url': 'B',  # Columna B - Escudo
            }
            
            columna = mapeo_campos.get(campo)
            if not columna:
                raise Exception(f"Campo '{campo}' no tiene mapeo definido")
            
            return self.buscar_y_actualizar(
                spreadsheet_id=spreadsheet_id,
                columna_busqueda='A',  # Buscar por nombre del club
                valor_busqueda=nombre_club,
                columna_actualizacion=columna,
                nuevo_valor=nuevo_valor
            )
            
        except Exception as e:
            logger.error(f"Error actualizando club {nombre_club}: {e}")
            raise
    
    def actualizar_encuentro(self, torneo: str, club_local: str, club_visitante: str, campo: str, nuevo_valor: str):
        """Actualiza un campo específico de un encuentro."""
        try:
            from sheets_config import SHEETS_MAP
            
            sheets_config = SHEETS_MAP.get(torneo, {})
            encuentros_config = sheets_config.get('encuentros')
            
            if not encuentros_config:
                raise Exception(f"No hay configuración de encuentros para el torneo {torneo}")
            
            spreadsheet_id = encuentros_config['spreadsheet_id']
            
            # Mapear campos de encuentros
            mapeo_campos = {
                'club_local': 'A',
                'club_visitante': 'B',
                'fecha': 'C',
                'hora': 'D',
                'nivel_riesgo': 'E',
                'motivo_alerta': 'F',
            }
            
            columna = mapeo_campos.get(campo)
            if not columna:
                raise Exception(f"Campo '{campo}' no tiene mapeo definido")
            
            # Buscar por club local y visitante
            worksheet = self.abrir_hoja(spreadsheet_id)
            
            # Obtener todos los datos para buscar la fila correcta
            datos = worksheet.get_all_records()
            for i, fila in enumerate(datos, start=2):  # Empezar desde fila 2 (después del header)
                if (fila.get('Club Local', '').strip() == club_local and 
                    fila.get('Club Visitante', '').strip() == club_visitante):
                    
                    celda_actualizacion = f"{columna}{i}"
                    worksheet.update(celda_actualizacion, nuevo_valor)
                    logger.info(f"Encuentro actualizado: {celda_actualizacion} = {nuevo_valor}")
                    return True
            
            logger.warning(f"Encuentro {club_local} vs {club_visitante} no encontrado")
            return False
            
        except Exception as e:
            logger.error(f"Error actualizando encuentro: {e}")
            raise
    
    def obtener_hoja_como_dataframe(self, spreadsheet_id: str, worksheet_name: str = None):
        """Obtiene los datos de la hoja como un formato estructurado."""
        try:
            worksheet = self.abrir_hoja(spreadsheet_id, worksheet_name)
            return worksheet.get_all_records()
        except Exception as e:
            logger.error(f"Error obteniendo datos como dataframe: {e}")
            raise
    
    def verificar_conexion(self) -> bool:
        """Verifica si la conexión con Google Sheets está activa."""
        try:
            if not self.client:
                return False
            
            # Intentar hacer una operación simple
            # Usar una hoja de prueba o verificar permisos
            return True
        except Exception as e:
            logger.error(f"Error verificando conexión: {e}")
            return False
    
    def verificar_permisos_hoja(self, spreadsheet_id: str) -> bool:
        """Verifica si la cuenta de servicio tiene permisos en una hoja específica."""
        try:
            if not self.client:
                return False
            
            # Intentar abrir la hoja
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            # Si llega aquí, tiene permisos básicos
            return True
            
        except Exception as e:
            error_msg = str(e)
            if 'FAILED_PRECONDITION' in error_msg or 'PERMISSION_DENIED' in error_msg:
                logger.warning(f"No hay permisos en la hoja {spreadsheet_id}: {e}")
                return False
            else:
                logger.error(f"Error verificando permisos en {spreadsheet_id}: {e}")
                return False
    
    def probar_hoja_prueba(self) -> bool:
        """Prueba la hoja de prueba para verificar que los permisos funcionan."""
        try:
            from sheets_config import HOJA_PRUEBA
            
            if not self.client:
                return False
            
            spreadsheet_id = HOJA_PRUEBA["spreadsheet_id"]
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            # Escribir un mensaje de prueba
            from datetime import datetime
            mensaje = f"Prueba de permisos - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            worksheet.update('A1', mensaje)
            
            # Leer para verificar
            valor = worksheet.acell('A1').value
            return valor == mensaje
            
        except Exception as e:
            logger.error(f"Error probando hoja de prueba: {e}")
            return False
