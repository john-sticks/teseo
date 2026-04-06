import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .backends import CerberusBackend
from .services.cerberus_service import CerberusService

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        # Verificar rate limiting antes de intentar autenticar
        bloqueada, intentos_restantes, tiempo_espera = CerberusService.ip_habilitada(request)
        if bloqueada:
            messages.error(
                request,
                f"Demasiados intentos fallidos. Intente nuevamente en {tiempo_espera} segundos."
            )
            return render(request, "auth/login.html")

        backend = CerberusBackend()
        user = backend.authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user, backend="dashboard.backends.CerberusBackend")
            logger.info(f"Login exitoso: {username}")
            return redirect(request.GET.get("next", "dashboard:dashboard"))
        else:
            CerberusService.sumar_intento_fallido(request)
            if intentos_restantes is not None:
                messages.error(
                    request,
                    f"Credenciales incorrectas. Intentos restantes: {intentos_restantes}."
                )
            else:
                messages.error(request, "Credenciales incorrectas o servicio no disponible.")
            logger.warning(f"Login fallido para usuario: {username}")

    return render(request, "auth/login.html")


def logout_view(request):
    username = request.user.username if request.user.is_authenticated else "anónimo"
    logout(request)
    logger.info(f"Logout: {username}")
    return redirect("login")
