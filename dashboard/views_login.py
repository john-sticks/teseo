import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .backends import CerberusBackend

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        backend = CerberusBackend()
        user = backend.authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user, backend="dashboard.backends.CerberusBackend")
            logger.info(f"Login exitoso: {username}")
            return redirect(request.GET.get("next", "dashboard:dashboard"))
        else:
            messages.error(request, "Credenciales incorrectas o servicio no disponible.")
            logger.warning(f"Login fallido para usuario: {username}")

    return render(request, "auth/login.html")


def logout_view(request):
    username = request.user.username if request.user.is_authenticated else "anónimo"
    logout(request)
    logger.info(f"Logout: {username}")
    return redirect("login")
