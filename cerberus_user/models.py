from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    def get_by_natural_key(self, username):
        return self.get(username=username)


class UsuarioCerberus(AbstractBaseUser):
    """
    Modelo que mapea directamente a la tabla 'usuarios' de Cerberus.
    managed=False: Django no crea ni altera esta tabla, la gestiona Cerberus.
    La autenticación se delega al backend CerberusBackend vía API.
    """

    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True, db_column='user')

    # Mapea la columna 'pass' de Cerberus. Django no valida este campo directamente
    # ya que la autenticación se hace vía API de Cerberus.
    password = models.CharField(max_length=255, db_column='pass')

    es_admin = models.BooleanField(default=False)
    nombre = models.CharField(max_length=50, blank=True, null=True)
    apellido = models.CharField(max_length=50, blank=True, null=True)
    mail = models.CharField(max_length=100, blank=True, null=True)
    legajo = models.IntegerField(default=0)
    jerarquia = models.CharField(max_length=30, default='')
    telefono = models.CharField(max_length=20, default='')
    destino_id = models.IntegerField(null=True, blank=True)
    estado = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    # Columna agregada para compatibilidad con Django (no usada por Cerberus)
    last_login = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    objects = UsuarioManager()

    class Meta:
        managed = False
        db_table = 'usuarios'
        app_label = 'cerberus_user'

    def __str__(self):
        return self.username

    # --- Propiedades requeridas por Django ---

    @property
    def is_active(self):
        return self.estado

    @property
    def is_staff(self):
        return self.es_admin

    @property
    def is_superuser(self):
        return self.es_admin

    @property
    def first_name(self):
        return self.nombre or ''

    @property
    def last_name(self):
        return self.apellido or ''

    @property
    def email(self):
        return self.mail or ''

    def get_full_name(self):
        return f"{self.nombre or ''} {self.apellido or ''}".strip() or self.username

    def get_short_name(self):
        return self.nombre or self.username

    def has_perm(self, perm, obj=None):
        return self.es_admin

    def has_module_perms(self, app_label):
        return self.es_admin
