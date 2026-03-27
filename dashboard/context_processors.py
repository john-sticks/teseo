"""
Context processors para el dashboard.
"""
from .models_auditoria import PerfilUsuario

def user_profile(request):
    """
    Context processor que agrega información del perfil del usuario a todos los templates.
    """
    context = {}
    
    if request.user.is_authenticated:
        try:
            perfil, created = PerfilUsuario.objects.get_or_create(usuario=request.user)
            context['user_perfil'] = perfil
            context['user_rol'] = perfil.rol
            context['puede_ver_relato_hecho'] = perfil.puede_ver_relato_hecho
            # Los usuarios VISITA pueden ver motivo del riesgo pero no relato del hecho
            context['puede_ver_motivo_riesgo'] = True  # Todos pueden ver motivo del riesgo
            context['puede_editar_datos'] = perfil.puede_editar_datos
            context['puede_sincronizar'] = perfil.puede_sincronizar
            context['puede_exportar'] = perfil.puede_exportar
        except Exception:
            # Si hay error, usar valores por defecto
            context['user_perfil'] = None
            context['user_rol'] = 'VISITA'
            context['puede_ver_relato_hecho'] = False  # Los usuarios de visita NO pueden ver relatos del hecho
            context['puede_ver_motivo_riesgo'] = True  # Todos pueden ver motivo del riesgo
            context['puede_editar_datos'] = False
            context['puede_sincronizar'] = False
            context['puede_exportar'] = False
    else:
        context['user_perfil'] = None
        context['user_rol'] = None
        context['puede_ver_relato_hecho'] = False
        context['puede_ver_motivo_riesgo'] = True  # Todos pueden ver motivo del riesgo
        context['puede_editar_datos'] = False
        context['puede_sincronizar'] = False
        context['puede_exportar'] = False
    
    return context
