from django.db import migrations

def revert_visita_permissions(apps, schema_editor):
    """Revertir permisos de usuarios VISITA - NO deben ver relato del hecho"""
    PerfilUsuario = apps.get_model('dashboard', 'PerfilUsuario')
    PerfilUsuario.objects.filter(rol='VISITA').update(puede_ver_relato_hecho=False)

def restore_visita_permissions(apps, schema_editor):
    """Restaurar permisos de usuarios VISITA (para rollback)"""
    PerfilUsuario = apps.get_model('dashboard', 'PerfilUsuario')
    PerfilUsuario.objects.filter(rol='VISITA').update(puede_ver_relato_hecho=True)

class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0008_update_visita_permissions'),
    ]

    operations = [
        migrations.RunPython(revert_visita_permissions, restore_visita_permissions),
    ]
