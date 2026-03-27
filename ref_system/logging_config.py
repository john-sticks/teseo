"""
Configuración de logging para el sistema REF.
"""
import os
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

LOGGING = {
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
        'audit': {
            'format': 'AUDIT {asctime} {levelname} {message}',
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
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'audit.log',
            'formatter': 'audit',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'google_sheets': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'google_sheets.log',
            'formatter': 'verbose',
        },
        'rss': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'rss.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'ref_system.middleware': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'dashboard.services': {
            'handlers': ['google_sheets', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'clubes.services': {
            'handlers': ['google_sheets', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'derecho_admision.services': {
            'handlers': ['google_sheets', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'redes_monitoring.services': {
            'handlers': ['rss', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
