import requests
from django.conf import settings


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


class CerberusService:

    @staticmethod
    def remote_token(username, password):
        """Obtiene un JWT token de Cerberus. Retorna el token o None."""
        try:
            response = requests.post(
                f"{settings.CERBERUS_API}/auth/token",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()["access_token"]
            return None
        except requests.RequestException:
            return None

    @staticmethod
    def remote_user(token):
        """Obtiene info del usuario autenticado. Retorna dict o None."""
        try:
            response = requests.get(
                f"{settings.CERBERUS_API}/users/info-servicio",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Service-Api-Key": settings.CERBERUS_API_KEY,
                },
                timeout=10,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException:
            return None

    @staticmethod
    def ip_habilitada(request):
        """Consulta si la IP del request está habilitada. Retorna (bloqueada, intentos_restantes, tiempo_espera)."""
        ip = _get_client_ip(request)
        try:
            response = requests.get(
                f"{settings.CERBERUS_API}/rate-limit/consultar-estado-ip?ip={ip}",
                headers={"Service-Api-Key": settings.CERBERUS_API_KEY},
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("bloqueada", False), data.get("intentos_restantes"), data.get("tiempo_espera")
        except requests.RequestException:
            pass
        return False, None, None

    @staticmethod
    def sumar_intento_fallido(request):
        """Registra un intento de login fallido en Cerberus."""
        ip = _get_client_ip(request)
        try:
            requests.post(
                f"{settings.CERBERUS_API}/rate-limit/sumar-fallido-login?ip={ip}",
                headers={"Service-Api-Key": settings.CERBERUS_API_KEY},
                timeout=5,
            )
        except requests.RequestException:
            pass
