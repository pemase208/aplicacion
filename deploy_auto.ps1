# Script de despliegue automático para Deudout
Write-Host "=== DESPLIEGUE AUTOMATICO DEUDOUT ===" -ForegroundColor Green

# Configuración del VPS
$VPS_IP = "217.154.102.76"
$VPS_USER = "root"
$VPS_PORT = "22"

Write-Host "Conectando al VPS $VPS_IP..." -ForegroundColor Yellow

# Crear directorio temporal
$tempDir = "C:\temp\deudout_deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

# Copiar archivos necesarios
Copy-Item "app.py" $tempDir
Copy-Item "models.py" $tempDir
Copy-Item "requirements.txt" $tempDir
Copy-Item "init_db.py" $tempDir
Copy-Item "crear_admin.py" $tempDir
Copy-Item "gunicorn.conf.py" $tempDir
Copy-Item "nginx.conf" $tempDir
Copy-Item "install_ubuntu24_optimized.sh" $tempDir

Write-Host "Archivos preparados en: $tempDir" -ForegroundColor Green

# Subir archivos vía SCP (más simple que SFTP)
Write-Host "Subiendo archivos al VPS..." -ForegroundColor Yellow
scp -P $VPS_PORT -r "$tempDir\*" "${VPS_USER}@${VPS_IP}:/tmp/deudout/"

Write-Host "¡Despliegue completado!" -ForegroundColor Green
Write-Host "Conectate al VPS: ssh -p $VPS_PORT $VPS_USER@$VPS_IP" -ForegroundColor Cyan
Write-Host "Ejecuta: cd /tmp/deudout && chmod +x install_ubuntu24_optimized.sh && ./install_ubuntu24_optimized.sh" -ForegroundColor Cyan
