@echo off
echo Iniciando sincronizacion automatica de Google Sheets...
echo Fecha: %date% Hora: %time%

cd /d "C:\Users\valentin\Desktop\REF\REF"

"C:\Users\valentin\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\valentin\Desktop\REF\REF\manage.py" sync_sheets --all --verbose

echo Sincronizacion completada.
echo Fecha: %date% Hora: %time%
