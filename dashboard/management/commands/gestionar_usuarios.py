from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from dashboard.models_auditoria import PerfilUsuario

class Command(BaseCommand):
    help = 'Gestiona usuarios del sistema REF'

    def add_arguments(self, parser):
        parser.add_argument(
            '--listar',
            action='store_true',
            help='Lista todos los usuarios del sistema'
        )
        parser.add_argument(
            '--cambiar-rol',
            type=str,
            nargs=2,
            metavar=('USERNAME', 'ROL'),
            help='Cambia el rol de un usuario (ADMINISTRADOR o VISITA)'
        )
        parser.add_argument(
            '--crear-admin',
            type=str,
            nargs=3,
            metavar=('USERNAME', 'EMAIL', 'PASSWORD'),
            help='Crea un nuevo usuario administrador'
        )
        parser.add_argument(
            '--crear-visita',
            type=str,
            nargs=3,
            metavar=('USERNAME', 'EMAIL', 'PASSWORD'),
            help='Crea un nuevo usuario de visita'
        )
        parser.add_argument(
            '--activar',
            type=str,
            help='Activa un usuario'
        )
        parser.add_argument(
            '--desactivar',
            type=str,
            help='Desactiva un usuario'
        )

    def handle(self, *args, **options):
        if options['listar']:
            self.listar_usuarios()
        elif options['cambiar_rol']:
            username, rol = options['cambiar_rol']
            self.cambiar_rol(username, rol)
        elif options['crear_admin']:
            username, email, password = options['crear_admin']
            self.crear_usuario(username, email, password, 'ADMINISTRADOR')
        elif options['crear_visita']:
            username, email, password = options['crear_visita']
            self.crear_usuario(username, email, password, 'VISITA')
        elif options['activar']:
            self.activar_usuario(options['activar'])
        elif options['desactivar']:
            self.desactivar_usuario(options['desactivar'])
        else:
            self.stdout.write(self.style.WARNING('Usa --help para ver las opciones disponibles'))

    def listar_usuarios(self):
        usuarios = User.objects.all().order_by('username')
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('LISTA DE USUARIOS'))
        self.stdout.write('='*80)
        
        for usuario in usuarios:
            perfil = getattr(usuario, 'perfil', None)
            rol = perfil.rol if perfil else 'Sin perfil'
            estado = 'Activo' if usuario.is_active else 'Inactivo'
            superuser = 'Sí' if usuario.is_superuser else 'No'
            
            self.stdout.write(f'👤 {usuario.username}')
            self.stdout.write(f'   📧 Email: {usuario.email or "No especificado"}')
            self.stdout.write(f'   👑 Rol: {rol}')
            self.stdout.write(f'   ✅ Estado: {estado}')
            self.stdout.write(f'   🔧 Superusuario: {superuser}')
            self.stdout.write(f'   📅 Último login: {usuario.last_login or "Nunca"}')
            self.stdout.write('-' * 40)

    def cambiar_rol(self, username, rol):
        try:
            usuario = User.objects.get(username=username)
            perfil, created = PerfilUsuario.objects.get_or_create(usuario=usuario)
            
            if rol not in ['ADMINISTRADOR', 'VISITA']:
                self.stdout.write(self.style.ERROR('❌ Rol inválido. Use ADMINISTRADOR o VISITA'))
                return
            
            perfil.rol = rol
            perfil.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Rol de {username} cambiado a {rol}'))
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Usuario {username} no encontrado'))

    def crear_usuario(self, username, email, password, rol):
        try:
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.ERROR(f'❌ El usuario {username} ya existe'))
                return
            
            usuario = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            perfil = PerfilUsuario.objects.create(
                usuario=usuario,
                rol=rol
            )
            
            self.stdout.write(self.style.SUCCESS(f'✅ Usuario {username} creado con rol {rol}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error creando usuario: {e}'))

    def activar_usuario(self, username):
        try:
            usuario = User.objects.get(username=username)
            usuario.is_active = True
            usuario.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Usuario {username} activado'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Usuario {username} no encontrado'))

    def desactivar_usuario(self, username):
        try:
            usuario = User.objects.get(username=username)
            usuario.is_active = False
            usuario.save()
            self.stdout.write(self.style.SUCCESS(f'✅ Usuario {username} desactivado'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Usuario {username} no encontrado'))
