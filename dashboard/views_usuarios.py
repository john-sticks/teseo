"""
Vistas para gestión de usuarios y auditoría.
"""
import logging
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models_auditoria import AuditoriaAcceso, SesionUsuario, PerfilUsuario
from .services.auditoria_service import AuditoriaService

logger = logging.getLogger(__name__)

def es_administrador(user):
    """Verifica si el usuario es administrador."""
    if not user.is_authenticated:
        return False
    
    perfil = getattr(user, 'perfil', None)
    if perfil:
        return perfil.rol == 'ADMINISTRADOR'
    
    return user.is_superuser

@login_required
@user_passes_test(es_administrador)
def gestion_usuarios_view(request):
    """Vista para gestión de usuarios."""
    try:
        # Obtener parámetros de búsqueda
        busqueda = request.GET.get('busqueda', '')
        rol_filtro = request.GET.get('rol', '')
        estado_filtro = request.GET.get('estado', '')
        
        # Obtener usuarios con perfiles
        User = get_user_model()
        usuarios_query = User.objects.using('cerberus').all()
        
        # Aplicar filtros
        if busqueda:
            usuarios_query = usuarios_query.filter(
                Q(username__icontains=busqueda) |
                Q(first_name__icontains=busqueda) |
                Q(last_name__icontains=busqueda) |
                Q(email__icontains=busqueda)
            )
        
        if rol_filtro:
            usuarios_query = usuarios_query.filter(perfil__rol=rol_filtro)
        
        if estado_filtro == 'activo':
            usuarios_query = usuarios_query.filter(is_active=True)
        elif estado_filtro == 'inactivo':
            usuarios_query = usuarios_query.filter(is_active=False)
        
        # Paginación
        paginator = Paginator(usuarios_query, 20)
        page_number = request.GET.get('page')
        usuarios = paginator.get_page(page_number)
        
        # Estadísticas
        User = get_user_model()
        total_usuarios = User.objects.using('cerberus').count()
        usuarios_activos = User.objects.using('cerberus').filter(estado=True).count()
        administradores = PerfilUsuario.objects.filter(rol='ADMINISTRADOR').count()
        visitas = PerfilUsuario.objects.filter(rol='VISITA').count()
        
        context = {
            'usuarios': usuarios,
            'busqueda': busqueda,
            'rol_filtro': rol_filtro,
            'estado_filtro': estado_filtro,
            'estadisticas': {
                'total_usuarios': total_usuarios,
                'usuarios_activos': usuarios_activos,
                'administradores': administradores,
                'visitas': visitas,
            }
        }
        
        return render(request, 'dashboard/gestion_usuarios.html', context)
        
    except Exception as e:
        logger.error(f"Error en gestión de usuarios: {e}")
        messages.error(request, 'Error al cargar la gestión de usuarios.')
        return redirect('dashboard:dashboard')

@login_required
@user_passes_test(es_administrador)
def crear_usuario_view(request):
    """Vista para crear un nuevo usuario."""
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            rol = request.POST.get('rol')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            
            # Validaciones
            if User.objects.filter(username=username).exists():
                messages.error(request, 'El nombre de usuario ya existe.')
                return render(request, 'dashboard/crear_usuario.html')
            
            if email and User.objects.filter(email=email).exists():
                messages.error(request, 'El email ya está en uso.')
                return render(request, 'dashboard/crear_usuario.html')
            
            # Crear usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Crear perfil
            perfil = PerfilUsuario.objects.create(
                usuario=user,
                rol=rol
            )
            
            # Registrar en auditoría
            auditoria_service = AuditoriaService()
            auditoria_service.registrar_acceso(
                usuario=request.user,
                tipo_accion='CREATE',
                descripcion=f'Usuario creado: {username} con rol {rol}',
                request=request
            )
            
            messages.success(request, f'Usuario {username} creado exitosamente.')
            return redirect('dashboard:gestion_usuarios')
            
        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
            messages.error(request, 'Error al crear el usuario.')
    
    return render(request, 'dashboard/crear_usuario.html')

@login_required
@user_passes_test(es_administrador)
def editar_usuario_view(request, user_id):
    """Vista para editar un usuario."""
    usuario = get_object_or_404(User, id=user_id)
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=usuario)
    
    if request.method == 'POST':
        try:
            # Actualizar datos del usuario
            usuario.first_name = request.POST.get('first_name', usuario.first_name)
            usuario.last_name = request.POST.get('last_name', usuario.last_name)
            usuario.email = request.POST.get('email', usuario.email)
            usuario.is_active = request.POST.get('is_active') == 'on'
            usuario.save()
            
            # Actualizar perfil
            perfil.rol = request.POST.get('rol', perfil.rol)
            perfil.telefono = request.POST.get('telefono', perfil.telefono)
            perfil.departamento = request.POST.get('departamento', perfil.departamento)
            perfil.cargo = request.POST.get('cargo', perfil.cargo)
            perfil.save()
            
            # Cambiar contraseña si se proporciona
            nueva_password = request.POST.get('nueva_password')
            if nueva_password:
                usuario.set_password(nueva_password)
                usuario.save()
            
            # Registrar en auditoría
            auditoria_service = AuditoriaService()
            auditoria_service.registrar_acceso(
                usuario=request.user,
                tipo_accion='UPDATE',
                descripcion=f'Usuario editado: {usuario.username}',
                request=request
            )
            
            messages.success(request, f'Usuario {usuario.username} actualizado exitosamente.')
            return redirect('dashboard:gestion_usuarios')
            
        except Exception as e:
            logger.error(f"Error editando usuario: {e}")
            messages.error(request, 'Error al actualizar el usuario.')
    
    context = {
        'usuario': usuario,
        'perfil': perfil
    }
    
    return render(request, 'dashboard/editar_usuario.html', context)

@login_required
@user_passes_test(es_administrador)
def eliminar_usuario_view(request, user_id):
    """Vista para eliminar un usuario."""
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            username = usuario.username
            
            # Registrar en auditoría antes de eliminar
            auditoria_service = AuditoriaService()
            auditoria_service.registrar_acceso(
                usuario=request.user,
                tipo_accion='DELETE',
                descripcion=f'Usuario eliminado: {username}',
                request=request
            )
            
            usuario.delete()
            messages.success(request, f'Usuario {username} eliminado exitosamente.')
            return redirect('dashboard:gestion_usuarios')
            
        except Exception as e:
            logger.error(f"Error eliminando usuario: {e}")
            messages.error(request, 'Error al eliminar el usuario.')
    
    return render(request, 'dashboard/eliminar_usuario.html', {'usuario': usuario})

@login_required
@user_passes_test(es_administrador)
def auditoria_view(request):
    """Vista para mostrar auditoría de accesos."""
    try:
        # Obtener parámetros
        dias = int(request.GET.get('dias', 30))
        tipo_accion = request.GET.get('tipo_accion', '')
        usuario_filtro = request.GET.get('usuario', '')
        
        # Obtener registros de auditoría
        auditoria_query = AuditoriaAcceso.objects.select_related('usuario').all()
        
        # Filtrar por días
        fecha_limite = timezone.now() - timedelta(days=dias)
        auditoria_query = auditoria_query.filter(fecha_accion__gte=fecha_limite)
        
        # Aplicar filtros adicionales
        if tipo_accion:
            auditoria_query = auditoria_query.filter(tipo_accion=tipo_accion)
        
        if usuario_filtro:
            auditoria_query = auditoria_query.filter(
                usuario__username__icontains=usuario_filtro
            )
        
        # Paginación
        paginator = Paginator(auditoria_query.order_by('-fecha_accion'), 50)
        page_number = request.GET.get('page')
        registros_auditoria = paginator.get_page(page_number)
        
        # Estadísticas
        auditoria_service = AuditoriaService()
        estadisticas = auditoria_service.obtener_estadisticas_auditoria(dias)
        
        context = {
            'registros_auditoria': registros_auditoria,
            'dias': dias,
            'tipo_accion': tipo_accion,
            'usuario_filtro': usuario_filtro,
            'estadisticas': estadisticas,
            'tipos_accion': [
                ('LOGIN', 'Inicio de sesión'),
                ('LOGOUT', 'Cierre de sesión'),
                ('VIEW', 'Visualización'),
                ('CREATE', 'Creación'),
                ('UPDATE', 'Actualización'),
                ('DELETE', 'Eliminación'),
                ('SYNC', 'Sincronización'),
                ('EXPORT', 'Exportación'),
                ('EDIT', 'Edición'),
            ]
        }
        
        return render(request, 'dashboard/auditoria.html', context)
        
    except Exception as e:
        logger.error(f"Error en auditoría: {e}")
        messages.error(request, 'Error al cargar la auditoría.')
        return redirect('dashboard:dashboard')

@login_required
@user_passes_test(es_administrador)
def usuarios_activos_view(request):
    """Vista para mostrar usuarios activos."""
    try:
        auditoria_service = AuditoriaService()
        usuarios_activos = auditoria_service.obtener_usuarios_activos()
        
        context = {
            'usuarios_activos': usuarios_activos,
            'total_activos': len(usuarios_activos)
        }
        
        return render(request, 'dashboard/usuarios_activos.html', context)
        
    except Exception as e:
        logger.error(f"Error obteniendo usuarios activos: {e}")
        messages.error(request, 'Error al cargar usuarios activos.')
        return redirect('dashboard:dashboard')

@login_required
def mi_perfil_view(request):
    """Vista para que el usuario vea y edite su perfil."""
    perfil, created = PerfilUsuario.objects.get_or_create(usuario=request.user)
    
    if request.method == 'POST':
        try:
            # Actualizar datos del usuario
            request.user.first_name = request.POST.get('first_name', request.user.first_name)
            request.user.last_name = request.POST.get('last_name', request.user.last_name)
            request.user.email = request.POST.get('email', request.user.email)
            request.user.save()
            
            # Actualizar perfil
            perfil.telefono = request.POST.get('telefono', perfil.telefono)
            perfil.departamento = request.POST.get('departamento', perfil.departamento)
            perfil.cargo = request.POST.get('cargo', perfil.cargo)
            perfil.save()
            
            # Cambiar contraseña si se proporciona
            nueva_password = request.POST.get('nueva_password')
            if nueva_password:
                request.user.set_password(nueva_password)
                request.user.save()
                messages.success(request, 'Contraseña actualizada exitosamente.')
            
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('dashboard:mi_perfil')
            
        except Exception as e:
            logger.error(f"Error actualizando perfil: {e}")
            messages.error(request, 'Error al actualizar el perfil.')
    
    # Obtener historial del usuario
    auditoria_service = AuditoriaService()
    historial = auditoria_service.obtener_historial_usuario(request.user, dias=7)
    
    context = {
        'perfil': perfil,
        'historial': historial[:10]  # Últimas 10 acciones
    }
    
    return render(request, 'dashboard/mi_perfil.html', context)

@login_required
def cerrar_sesion_otras_view(request):
    """Vista para cerrar otras sesiones del usuario."""
    if request.method == 'POST':
        try:
            auditoria_service = AuditoriaService()
            auditoria_service.cerrar_sesion(request.user)
            
            messages.success(request, 'Otras sesiones cerradas exitosamente.')
            return redirect('dashboard:mi_perfil')
            
        except Exception as e:
            logger.error(f"Error cerrando sesiones: {e}")
            messages.error(request, 'Error al cerrar otras sesiones.')
    
    return redirect('dashboard:mi_perfil')
