"""
Comando de Django para configurar la base de datos en producción.
Ejecuta migraciones y crea el usuario admin.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth.models import User
from django.db import connection
import os


class Command(BaseCommand):
    help = 'Configura la base de datos para producción'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='Nombre de usuario para el admin (default: admin)'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='1234',
            help='Contraseña para el admin (default: 1234)'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            default='admin@ref.com',
            help='Email para el admin (default: admin@ref.com)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando configuración de producción...')
        )

        # Verificar si la base de datos existe
        db_path = os.path.join(os.getcwd(), 'db.sqlite3')
        db_exists = os.path.exists(db_path)
        
        self.stdout.write(f'📊 Base de datos existe: {db_exists}')

        try:
            # Ejecutar migraciones
            self.stdout.write('🔄 Ejecutando migraciones...')
            call_command('migrate', verbosity=0)
            self.stdout.write(
                self.style.SUCCESS('✅ Migraciones completadas')
            )

            # Crear usuario admin si no existe
            admin_username = options['admin_username']
            admin_password = options['admin_password']
            admin_email = options['admin_email']

            if User.objects.filter(username=admin_username).exists():
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Usuario {admin_username} ya existe')
                )
            else:
                # Crear superusuario
                user = User.objects.create_superuser(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password
                )
                
                # Crear perfil de usuario con rol de ADMINISTRADOR
                from dashboard.models_auditoria import PerfilUsuario
                PerfilUsuario.objects.create(
                    usuario=user,
                    rol='ADMINISTRADOR',
                    telefono='',
                    departamento='',
                    cargo='Administrador'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Usuario admin creado: {admin_username} / {admin_password}'
                    )
                )

            # Recopilar archivos estáticos
            self.stdout.write('📁 Recopilando archivos estáticos...')
            call_command('collectstatic', '--noinput', verbosity=0)
            self.stdout.write(
                self.style.SUCCESS('✅ Archivos estáticos recopilados')
            )

            # Mostrar información de la base de datos
            with connection.cursor() as cursor:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                self.stdout.write(f'📋 Tablas creadas: {len(tables)}')

            self.stdout.write(
                self.style.SUCCESS(
                    '\n🎉 Configuración de producción completada!\n'
                    f'👤 Usuario: {admin_username}\n'
                    f'🔑 Contraseña: {admin_password}\n'
                    f'📧 Email: {admin_email}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error durante la configuración: {str(e)}')
            )
            raise
