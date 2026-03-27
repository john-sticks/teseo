"""
Comando de Django para sincronizar datos desde Google Sheets públicas.
Descarga datos directamente desde las URLs de exportación CSV sin necesidad de credenciales.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.services.sheets_sync_service import SheetsSyncService
from sheets_config import SHEETS_MAP
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sincroniza datos desde Google Sheets públicas sin credenciales'

    def add_arguments(self, parser):
        parser.add_argument(
            '--torneo',
            type=str,
            help='Torneo específico a sincronizar (LPF, ASCENSO, etc.)',
            choices=list(SHEETS_MAP.keys())
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sincronizar todos los torneos'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando sincronización con Google Sheets...')
        )

        service = SheetsSyncService()
        
        # Determinar qué torneos sincronizar
        if options['all']:
            torneos = list(SHEETS_MAP.keys())
        elif options['torneo']:
            torneos = [options['torneo']]
        else:
            torneos = ['LPF']  # Por defecto

        total_created = total_updated = total_deleted = 0
        total_errors = []

        for torneo in torneos:
            self.stdout.write(
                self.style.NOTICE(f'\n📊 Sincronizando torneo: {torneo}')
            )
            
            try:
                sheets_config = SHEETS_MAP[torneo]
                created, updated, deleted, errors = service.sync_tournament(torneo, sheets_config)
                
                total_created += created
                total_updated += updated
                total_errors.extend(errors)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {torneo}: {created} creados, {updated} actualizados, {deleted} eliminados'
                    )
                )
                
                if errors and options['verbose']:
                    for error in errors:
                        self.stdout.write(
                            self.style.WARNING(f'  ⚠️  {error}')
                        )
                        
            except Exception as e:
                error_msg = f'Error sincronizando {torneo}: {str(e)}'
                self.stdout.write(
                    self.style.ERROR(f'❌ {error_msg}')
                )
                total_errors.append(error_msg)
                logger.error(error_msg, exc_info=True)

        # Resumen final
        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Sincronización completada!\n'
                f'📈 Total creados: {total_created}\n'
                f'🔄 Total actualizados: {total_updated}\n'
                f'🗑️ Total eliminados: {total_deleted}\n'
                f'❌ Total errores: {len(total_errors)}'
            )
        )
        
        if total_errors and options['verbose']:
            self.stdout.write('\n📋 Errores encontrados:')
            for i, error in enumerate(total_errors, 1):
                self.stdout.write(f'  {i}. {error}')
        
        # Mostrar estadísticas de la base de datos
        self._show_database_stats()

    def _show_database_stats(self):
        """Muestra estadísticas de la base de datos después de la sincronización."""
        try:
            from dashboard.models import Encuentro, Incidente, Club, DerechoAdmision, OperacionalDoc, RankingConflictividad
            
            stats = {
                'Encuentros': Encuentro.objects.count(),
                'Incidentes': Incidente.objects.count(),
                'Clubes': Club.objects.count(),
                'Derechos de Admisión': DerechoAdmision.objects.count(),
                'Documentos Operacionales': OperacionalDoc.objects.count(),
                'Rankings': RankingConflictividad.objects.count(),
            }
            
            self.stdout.write('\n📊 Estadísticas de la base de datos:')
            for model_name, count in stats.items():
                self.stdout.write(f'  {model_name}: {count}')
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'No se pudieron obtener estadísticas: {e}')
            )
