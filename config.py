"""
Configuración de ejemplo para el Sistema REF.
Copia este archivo como config_local.py y ajusta los valores según tu entorno.
"""

import os
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Configuración de la base de datos
DATABASE_CONFIG = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Para producción, usar PostgreSQL:
# DATABASE_CONFIG = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'ref_system',
#         'USER': 'usuario_db',
#         'PASSWORD': 'contraseña_db',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }

# Configuración de Google Sheets
GOOGLE_SHEETS_CONFIG = {
    'CREDENTIALS_PATH': BASE_DIR / 'credentials' / 'google_sheets_credentials.json',
    'SCOPES': [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
}

# URLs de las hojas de Google Sheets por torneo
TOURNAMENT_SHEETS_URLS = {
    'LPF': {
        'encuentros': 'https://docs.google.com/spreadsheets/d/1-lYFhNHfLT7qnj6SxKqhUQ-fHYjdDAAT/edit',
        'ranking': 'https://docs.google.com/spreadsheets/d/1d1I_ljiyIP6UQ84dNxldg19yhUQ3iIFN/edit',
        'mapa': 'https://docs.google.com/spreadsheets/d/1d1I_ljiyIP6UQ84dNxldg19yhUQ3iIFN/edit',
        'clubes': 'https://docs.google.com/spreadsheets/d/18A90XIQ-0eXb9q_x8ZLYaavhQpmVWCHW/edit',
        'derecho_admision': 'https://docs.google.com/spreadsheets/d/1W9N9YmqRxlgSeCJ39WLbZ23L1ITDVTw6/edit',
        'operacionales': 'https://drive.google.com/file/d/1jrJ_iWNGbqLQ5GDYOq9mgz5KQTEJNOb_/view',
    },
    'ASCENSO': {
        'encuentros': 'https://docs.google.com/spreadsheets/d/1R_TYK51xLRJcyjiBAlHlrBtrKxHeehuo/edit',
        'clubes': 'https://docs.google.com/spreadsheets/d/1zOaXceeRJwja_0dsIMLjFHgl4Eux3bf7/edit',
        'derecho_admision': 'https://docs.google.com/spreadsheets/d/1PFgfR88ZCHFhleT_7bp8TN5p-QfIz7xZ/edit',
        'operacionales': 'https://drive.google.com/file/d/1HMLGAbXifwHSvpJgqOKlaQKYNBMI_pL_/view',
        'mapa': 'https://docs.google.com/spreadsheets/d/1sN8J7lUpf4eVIE_y3F9IWEC-_cRXXk8h/edit',
    },
    'COPA_ARGENTINA': {
        'encuentros': 'https://docs.google.com/spreadsheets/d/1TQYOmLbkdykEHz1iVw3AwKt8A3Wvn-gC/edit',
        'clubes': 'https://docs.google.com/spreadsheets/d/1hBkft64ISW7M6ESyBkveruUBqxrryT85/edit',
        'derecho_admision': 'https://docs.google.com/spreadsheets/d/1nf_oayZqj1c28ZEBeKvnZcXYEFYW8yhX/edit',
        'operacionales': 'https://drive.google.com/file/d/1WblcUlEOUASAzWFovkJ2tu4JFuLd58Xh/view',
    },
    'COPA_SUDAMERICANA': {
        'encuentros': 'https://docs.google.com/spreadsheets/d/1XnOvES7Rd3OVgvb37HYjQMtwJo1fRIhz/edit',
        'clubes': 'https://docs.google.com/spreadsheets/d/1T3MGWy0mVGxu6FqQAIw9zJqT7t_si1eD/edit',
        'derecho_admision': 'https://docs.google.com/spreadsheets/d/1UH8uoEImdYTXoGlLXiE_X5kVqcz62KPg/edit',
        'operacionales': 'https://drive.google.com/file/d/1gXZwLgLd_bA29egKnjCE3DNoAVdb_OVc/view',
    },
    'COPA_LIBERTADORES': {
        'encuentros': 'https://docs.google.com/spreadsheets/d/106MUaLytdvyvNiTiBiUZFHU0fqVMU1lW/edit',
        'clubes': 'https://docs.google.com/spreadsheets/d/1BodR1rkA3NaqtBpPMRdPQ1kcCSGz1_73/edit',
        'derecho_admision': 'https://docs.google.com/spreadsheets/d/1Dqbvm5XSbD0THhiVNa5zpgxTpV2qJ0V0/edit',
        'operacionales': 'https://drive.google.com/file/d/1whwfYBDMcJ6wN-Tdml9aX-ZxJ4mMMNkL/view',
    }
}

# Configuración de RSS
RSS_CONFIG = {
    'FEED_URL': 'https://rss.app/feeds/_aUBB2qjedDT2RxdW.json',
    'TIMEOUT': 30,
    'USER_AGENT': 'REF-System/1.0 (Monitoreo RSS)',
    'KEYWORDS_RIESGO': [
        'violencia', 'pelea', 'conflicto', 'hinchada', 'barra brava',
        'incidente', 'disturbio', 'policía', 'seguridad', 'estadio',
        'fútbol', 'clásico', 'derby', 'rivalidad'
    ]
}

# Configuración de logging
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'ref_system.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Configuración de seguridad
SECURITY_CONFIG = {
    'SECRET_KEY': 'django-insecure-change-this-in-production',
    'DEBUG': True,
    'ALLOWED_HOSTS': ['localhost', '127.0.0.1'],
    'CSRF_TRUSTED_ORIGINS': ['http://localhost:8000', 'http://127.0.0.1:8000'],
}

# Configuración de archivos estáticos y media
STATIC_MEDIA_CONFIG = {
    'STATIC_URL': '/static/',
    'STATIC_ROOT': BASE_DIR / 'staticfiles',
    'MEDIA_URL': '/media/',
    'MEDIA_ROOT': BASE_DIR / 'media',
    'STATICFILES_DIRS': [BASE_DIR / 'static'],
}

# Configuración de caché (opcional)
CACHE_CONFIG = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Para producción, usar Redis:
# CACHE_CONFIG = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }

# Configuración de email (opcional)
EMAIL_CONFIG = {
    'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    # Para producción:
    # 'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
    # 'HOST': 'smtp.gmail.com',
    # 'PORT': 587,
    # 'USE_TLS': True,
    # 'USER': 'tu-email@gmail.com',
    # 'PASSWORD': 'tu-contraseña-app',
}

# Configuración de internacionalización
I18N_CONFIG = {
    'LANGUAGE_CODE': 'es-ar',
    'TIME_ZONE': 'America/Argentina/Buenos_Aires',
    'USE_I18N': True,
    'USE_TZ': True,
}

# Configuración de sesiones
SESSION_CONFIG = {
    'SESSION_ENGINE': 'django.contrib.sessions.backends.db',
    'SESSION_COOKIE_AGE': 3600,  # 1 hora
    'SESSION_SAVE_EVERY_REQUEST': True,
    'SESSION_EXPIRE_AT_BROWSER_CLOSE': True,
}

# Configuración de autenticación
AUTH_CONFIG = {
    'LOGIN_URL': '/login/',
    'LOGIN_REDIRECT_URL': '/',
    'LOGOUT_REDIRECT_URL': '/login/',
    'PASSWORD_RESET_TIMEOUT': 3600,  # 1 hora
}

# Configuración de archivos
FILE_CONFIG = {
    'FILE_UPLOAD_MAX_MEMORY_SIZE': 5242880,  # 5MB
    'DATA_UPLOAD_MAX_MEMORY_SIZE': 5242880,  # 5MB
    'DATA_UPLOAD_MAX_NUMBER_FIELDS': 1000,
}

# Configuración de aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'dashboard',
    'clubes',
    'derecho_admision',
    'redes_monitoring',
    'operacionales',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'ref_system.middleware.AuditMiddleware',
]

# Configuración de templates
TEMPLATE_CONFIG = {
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {
        'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ],
    },
}

# Configuración de Crispy Forms
CRISPY_CONFIG = {
    'ALLOWED_TEMPLATE_PACKS': 'bootstrap5',
    'TEMPLATE_PACK': 'bootstrap5',
}

print("Configuración del Sistema REF cargada correctamente.")
