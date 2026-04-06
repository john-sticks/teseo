"""
Agrega la columna last_login a la tabla usuarios de Cerberus.
Esta columna es requerida por Django pero no existe en el esquema original de Cerberus.
Es ignorada por los demás servicios del sistema.
"""
from django.db import migrations


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS last_login DATETIME NULL",
            reverse_sql="SELECT 1",  # No revertir: otros servicios podrían haber empezado a usarla
        ),
    ]
