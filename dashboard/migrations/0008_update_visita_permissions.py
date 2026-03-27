# Generated manually to update VISITA user permissions

from django.db import migrations


def update_visita_permissions(apps, schema_editor):
    """Actualizar permisos de usuarios VISITA para que puedan ver relatos del hecho."""
    PerfilUsuario = apps.get_model('dashboard', 'PerfilUsuario')
    
    # Actualizar todos los usuarios VISITA para que puedan ver relatos del hecho
    PerfilUsuario.objects.filter(rol='VISITA').update(puede_ver_relato_hecho=True)


def reverse_visita_permissions(apps, schema_editor):
    """Revertir permisos de usuarios VISITA."""
    PerfilUsuario = apps.get_model('dashboard', 'PerfilUsuario')
    
    # Revertir permisos de usuarios VISITA
    PerfilUsuario.objects.filter(rol='VISITA').update(puede_ver_relato_hecho=False)


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_derechoadmision_apellido_derechoadmision_escudo_and_more'),
    ]

    operations = [
        migrations.RunPython(update_visita_permissions, reverse_visita_permissions),
    ]
