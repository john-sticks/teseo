"""
URL configuration simplificada para el sistema REF.
"""
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse

def home_view(request):
    return HttpResponse("""
    <html>
    <head>
        <title>Sistema REF - Funcionando</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #dc3545; }
            .success { color: #28a745; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏆 Sistema REF - Riesgo en Encuentro Futbolístico</h1>
            <p class="success">✅ El sistema está funcionando correctamente!</p>
            <p>Django está instalado y configurado.</p>
            <p>Puedes acceder al <a href="/admin/">panel de administración</a>.</p>
        </div>
    </body>
    </html>
    """)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
]
