# Script de sincronización automática para REF
Write-Host "Iniciando sincronización automática de Google Sheets..." -ForegroundColor Green
Write-Host "Fecha: $(Get-Date)" -ForegroundColor Yellow

Set-Location "C:\Users\valentin\Desktop\REF\REF"

& "C:\Users\valentin\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\valentin\Desktop\REF\REF\manage.py" sync_sheets --all --verbose

Write-Host "Sincronización completada." -ForegroundColor Green
Write-Host "Fecha: $(Get-Date)" -ForegroundColor Yellow
