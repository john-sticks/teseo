"""
Comando de Django para sincronizar datos con Google Sheets.
"""
from django.core.management.base import BaseCommand
from dashboard.services.google_sheets_service import GoogleSheetsService
from django.conf import settings
import json

class Command(BaseCommand):
    help = 'Sincroniza datos del sistema REF con Google Sheets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--torneo',
            type=str,
            help='Torneo específico a sincronizar (LPF, ASCENSO, etc.)',
            choices=['LPF', 'ASCENSO', 'COPA_ARGENTINA', 'COPA_SUDAMERICANA', 'COPA_LIBERTADORES']
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sincronizar todos los torneos'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Iniciando sincronización con Google Sheets...')
        )

        service = GoogleSheetsService()
        
        if options['all']:
            torneos = settings.TOURNAMENT_SHEETS.keys()
        elif options['torneo']:
            torneos = [options['torneo']]
        else:
            torneos = ['LPF']  # Por defecto

        for torneo in torneos:
            self.stdout.write(f'Sincronizando torneo: {torneo}')
            
            try:
                resultado = service.sincronizar_torneo(torneo)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ {torneo}: {resultado["encuentros"]} encuentros, '
                        f'{resultado["ranking"]} rankings, '
                        f'{resultado["incidentes"]} incidentes'
                    )
                )
                
                if resultado['errores']:
                    for error in resultado['errores']:
                        self.stdout.write(
                            self.style.ERROR(f'  Error: {error}')
                        )
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error sincronizando {torneo}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS('Sincronización completada.')
        )