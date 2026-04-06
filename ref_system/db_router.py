class CerberusRouter:
    """
    Enruta las consultas del modelo UsuarioCerberus a la base de datos 'cerberus'
    (tabla usuarios compartida con Cerberus y el resto de los servicios).
    El resto de los modelos de Teseo usan la base de datos 'default'.
    """

    _cerberus_apps = {'cerberus_user'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self._cerberus_apps:
            return 'cerberus'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self._cerberus_apps:
            return 'cerberus'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Permitir relaciones entre modelos de diferentes DBs (FK con db_constraint=False)
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self._cerberus_apps:
            return db == 'cerberus'
        return db == 'default'
