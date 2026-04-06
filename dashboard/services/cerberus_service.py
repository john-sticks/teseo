import requests
from django.conf import settings


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
