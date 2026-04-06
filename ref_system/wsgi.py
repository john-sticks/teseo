import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ref_system.settings')


class SubpathMiddleware:
    """
    Middleware WSGI que permite servir Django bajo un subpath (ej: /teseo/).
    Strips el SCRIPT_NAME del PATH_INFO para que el router de Django lo maneje correctamente.
    """
    def __init__(self, app, script_name):
        self.app = app
        self.script_name = script_name.rstrip('/')

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path.startswith(self.script_name + '/') or path == self.script_name:
            environ['PATH_INFO'] = path[len(self.script_name):] or '/'
            environ['SCRIPT_NAME'] = self.script_name
        return self.app(environ, start_response)


application = SubpathMiddleware(get_wsgi_application(), '/teseo')
