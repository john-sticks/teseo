#!/usr/bin/env bash
# Script de construcción para Render

echo "🚀 Iniciando construcción del proyecto REF..."

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

# Ejecutar migraciones
echo "🔄 Ejecutando migraciones..."
python manage.py migrate

# Crear usuario admin
echo "👤 Creando usuario admin..."
python manage.py setup_production --admin-username=admin --admin-password=RefAdmin2025! --admin-email=admin@ref.com

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Construcción completada!"
