# ===== DESPLIEGUE SIMPLE DEUDOUT =====
# Script simplificado para preparar archivos para SFTP

Write-Host "=================================" -ForegroundColor Magenta
Write-Host "DESPLIEGUE SFTP DEUDOUT" -ForegroundColor Magenta
Write-Host "=================================" -ForegroundColor Magenta
Write-Host ""

# Configuración automática
$ProjectPath = "C:\Users\pmser\Downloads\Copia medio funcional"
$VpsIp = "217.154.102.76"
$VpsUser = "root"
$VpsPort = "22"

Write-Host "✅ Ruta del proyecto: $ProjectPath" -ForegroundColor Green
Write-Host "✅ IP del VPS: $VpsIp" -ForegroundColor Green
Write-Host "✅ Usuario: $VpsUser" -ForegroundColor Green
Write-Host "✅ Puerto: $VpsPort" -ForegroundColor Green
Write-Host ""

# Verificar que la ruta existe
if (-not (Test-Path $ProjectPath)) {
    Write-Host "❌ ERROR: La ruta '$ProjectPath' no existe" -ForegroundColor Red
    exit 1
}

# Crear directorio temporal
$TempDir = "C:\temp\deudout_deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

Write-Host "📁 Creando directorio temporal: $TempDir" -ForegroundColor Blue

# Lista de archivos a copiar
$FilesToDeploy = @(
    "app.py",
    "models.py", 
    "requirements.txt",
    "init_db.py",
    "crear_admin.py",
    "poblar_entidades_financieras.py",
    "utils",
    "static",
    "templates",
    "instance",
    ".env.example",
    "README.txt",
    "gunicorn.conf.py",
    "nginx.conf",
    "install_ubuntu24_optimized.sh"
)

# Copiar archivos
foreach ($item in $FilesToDeploy) {
    $sourcePath = Join-Path $ProjectPath $item
    if (Test-Path $sourcePath) {
        Write-Host "📋 Copiando: $item" -ForegroundColor Cyan
        Copy-Item -Path $sourcePath -Destination $TempDir -Recurse -Force
    } else {
        Write-Host "⚠️  No encontrado: $item" -ForegroundColor Yellow
    }
}

# Crear script de instalación remota
$RemoteScript = Join-Path $TempDir "remote_install.sh"
$scriptContent = @'
#!/bin/bash
echo "🚀 Iniciando instalación remota de DEUDOUT..."
echo "📁 Directorio: /tmp/deudout"
cd /tmp/deudout
echo "📁 Verificando archivos..."
ls -la
if [ -f "install_ubuntu24_optimized.sh" ]; then
    chmod +x install_ubuntu24_optimized.sh
    echo "🔧 Ejecutando instalación..."
    ./install_ubuntu24_optimized.sh
else
    echo "❌ Script de instalación no encontrado"
    echo "📋 Ejecuta manualmente: chmod +x install_ubuntu24_optimized.sh && ./install_ubuntu24_optimized.sh"
fi
echo "✅ Instalación completada"
'@

$scriptContent | Out-File -FilePath $RemoteScript -Encoding UTF8

# Crear script SFTP
$SftpScript = Join-Path $TempDir "sftp_commands.txt"
$sftpContent = @"
cd /tmp
mkdir deudout
cd deudout
put -r *
bye
"@

$sftpContent | Out-File -FilePath $SftpScript -Encoding UTF8

Write-Host ""
Write-Host "=================================" -ForegroundColor Green
Write-Host "DESPLIEGUE PREPARADO" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Archivos listos en: $TempDir" -ForegroundColor Green
Write-Host "🔄 Carpeta se creará como 'deudout' en el VPS" -ForegroundColor Green
Write-Host ""
Write-Host "📋 INSTRUCCIONES DE DESPLIEGUE:" -ForegroundColor White
Write-Host ""
Write-Host "1️⃣  CONECTARSE AL VPS:" -ForegroundColor Cyan
Write-Host "   ssh -p $VpsPort $VpsUser@$VpsIp" -ForegroundColor White
Write-Host ""
Write-Host "2️⃣  CREAR CARPETA EN EL VPS:" -ForegroundColor Cyan
Write-Host "   mkdir -p /tmp/deudout" -ForegroundColor White
Write-Host ""
Write-Host "3️⃣  SUBIR ARCHIVOS (desde otra terminal):" -ForegroundColor Cyan
Write-Host "   sftp -P $VpsPort $VpsUser@$VpsIp" -ForegroundColor White
Write-Host "   cd /tmp/deudout" -ForegroundColor White
Write-Host "   put -r $TempDir\*" -ForegroundColor White
Write-Host "   bye" -ForegroundColor White
Write-Host ""
Write-Host "4️⃣  EJECUTAR INSTALACIÓN:" -ForegroundColor Cyan
Write-Host "   cd /tmp/deudout" -ForegroundColor White
Write-Host "   chmod +x remote_install.sh" -ForegroundColor White
Write-Host "   ./remote_install.sh" -ForegroundColor White
Write-Host ""
Write-Host "🌐 La aplicación estará disponible en: http://$VpsIp" -ForegroundColor Green
Write-Host ""

# Preguntar si quiere abrir el directorio temporal
$openDir = Read-Host "¿Quieres abrir el directorio temporal para revisar archivos? (y/N)"
if ($openDir -eq "y" -or $openDir -eq "Y") {
    Start-Process "explorer.exe" -ArgumentList $TempDir
}

Write-Host "💡 CONSEJO: Mantén esta ventana abierta para ver las instrucciones" -ForegroundColor Yellow
Write-Host "   mientras haces el despliegue en otra terminal" -ForegroundColor Yellow
Write-Host ""
Write-Host "✅ ¡Todo listo para el despliegue!" -ForegroundColor Green


