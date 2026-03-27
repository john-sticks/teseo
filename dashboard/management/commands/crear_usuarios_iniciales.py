"""
Comando para crear usuarios iniciales del sistema.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models_auditoria import PerfilUsuario

class Command(BaseCommand):
    help = 'Crea usuarios iniciales del sistema REF'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            type=str,
            default='admin',
            help='Nombre de usuario para el administrador'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='admin123',
            help='Contraseña para el administrador'
        )
        parser.add_argument(
            '--admin-email',
            type=str,
            default='admin@ref.com',
            help='Email para el administrador'
        )

    def handle(self, *args, **options):
        admin_username = options['admin_username']
        admin_password = options['admin_password']
        admin_email = options['admin_email']

        # Crear superusuario si no existe
        if not User.objects.filter(username=admin_username).exists():
            admin_user = User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                first_name='Administrador',
                last_name='Sistema REF'
            )
            
            # Crear perfil de administrador
            PerfilUsuario.objects.create(
                usuario=admin_user,
                rol='ADMINISTRADOR',
                telefono='+54 11 1234-5678',
                departamento='Sistemas',
                cargo='Administrador del Sistema'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Usuario administrador creado: {admin_username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'⚠️ El usuario administrador {admin_username} ya existe')
            )

        # Crear usuario de visita de ejemplo
        if not User.objects.filter(username='visita').exists():
            visita_user = User.objects.create_user(
                username='visita',
                email='visita@ref.com',
                password='visita123',
                first_name='Usuario',
                last_name='Visita'
            )
            
            # Crear perfil de visita
            PerfilUsuario.objects.create(
                usuario=visita_user,
                rol='VISITA',
                telefono='+54 11 8765-4321',
                departamento='Operaciones',
                cargo='Operador'
            )
            
            self.stdout.write(
                self.style.SUCCESS('✅ Usuario de visita creado: visita')
            )
        else:
            self.stdout.write(
                self.style.WARNING('⚠️ El usuario de visita ya existe')
            )

        # Mostrar información de acceso
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('🔐 INFORMACIÓN DE ACCESO:'))
        self.stdout.write('='*50)
        self.stdout.write(f'👑 Administrador:')
        self.stdout.write(f'   Usuario: {admin_username}')
        self.stdout.write(f'   Contraseña: {admin_password}')
        self.stdout.write(f'   Email: {admin_email}')
        self.stdout.write('')
        self.stdout.write('👤 Usuario Visita:')
        self.stdout.write('   Usuario: visita')
        self.stdout.write('   Contraseña: visita123')
        self.stdout.write('   Email: visita@ref.com')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('⚠️ IMPORTANTE: Cambia estas contraseñas en producción!'))
        self.stdout.write('='*50)
