#!/usr/bin/env bash
# Script de inicio para Render

echo "🚀 Iniciando aplicación REF..."

# Verificar si la base de datos existe y tiene tablas
if [ ! -f "db.sqlite3" ] || [ ! -s "db.sqlite3" ]; then
    echo "📊 Base de datos no existe o está vacía, ejecutando configuración..."
    python manage.py setup_production --admin-username=admin --admin-password=1234 --admin-email=admin@ref.com
fi

# Iniciar la aplicación
echo "🌐 Iniciando servidor web..."
gunicorn ref_system.wsgi:application --bind 0.0.0.0:$PORT
