# ===== DESPLIEGUE SFTP PERSONALIZADO DEUDOUT (PowerShell) =====
# Script que sube desde "Copia medio funcional" y crea carpeta "deudout" en el VPS

# Función para mostrar mensajes con colores
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Header {
    param([string]$Message)
    Write-Host "=================================" -ForegroundColor Magenta
    Write-Host $Message -ForegroundColor Magenta
    Write-Host "=================================" -ForegroundColor Magenta
}

function Write-Step {
    param([string]$Message)
    Write-Host "➤ $Message" -ForegroundColor Cyan
}

# Función para obtener la ruta del proyecto
function Get-ProjectPath {
    Write-Header "CONFIGURACIÓN DE RUTA LOCAL"
    
    # Ruta por defecto (la que mencionaste)
    $DefaultPath = "C:\Users\pmser\Downloads\Copia medio funcional"
    
    Write-Host ""
    Write-Step "Ruta por defecto detectada: '$DefaultPath'"
    $confirm = Read-Host "¿Es correcta esta ruta? (y/N)"
    
    if ($confirm -eq "y" -or $confirm -eq "Y") {
        $script:ProjectPath = $DefaultPath
    } else {
        Write-Host ""
        Write-Step "Por favor, ingresa la ruta completa a tu proyecto DEUDOUT:"
        $script:ProjectPath = Read-Host "Ruta"
    }
    
    # Verificar que la ruta existe
    if (-not (Test-Path $ProjectPath)) {
        Write-Error "La ruta '$ProjectPath' no existe o no es un directorio"
        exit 1
    }
    
    # Verificar que contiene archivos del proyecto
    if (-not (Test-Path "$ProjectPath\app.py")) {
        Write-Error "La ruta '$ProjectPath' no contiene app.py (no parece ser el proyecto DEUDOUT)"
        exit 1
    }
    
    Write-Success "Ruta del proyecto verificada: $ProjectPath"
    Write-Host ""
}

# Función para configurar conexión SFTP
function Setup-SftpConnection {
    Write-Header "CONFIGURACIÓN DE CONEXIÓN SFTP"
    
    Write-Host ""
    Write-Step "Configuración de conexión al VPS:"
    $script:VpsIp = Read-Host "IP del VPS"
    $script:VpsUser = Read-Host "Usuario del VPS (root)"
    $script:VpsPort = Read-Host "Puerto SSH (22)"
    if (-not $VpsPort) { $script:VpsPort = "22" }
    
    # Verificar conectividad
    Write-Step "Verificando conectividad con $VpsIp..."
    try {
        $ping = Test-Connection -ComputerName $VpsIp -Count 1 -Quiet
        if (-not $ping) {
            Write-Error "No se puede alcanzar $VpsIp"
            exit 1
        }
    } catch {
        Write-Warning "No se pudo verificar conectividad, continuando..."
    }
    
    Write-Success "Conexión configurada"
    Write-Host ""
}

# Función para preparar archivos para despliegue
function Prepare-Deployment {
    Write-Header "PREPARACIÓN DE ARCHIVOS"
    
    # Crear directorio temporal para el despliegue
    $script:TempDir = "C:\temp\deudout_deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    
    Write-Step "Preparando archivos desde: $ProjectPath"
    
    # Lista de archivos y directorios a incluir
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
        "nginx.conf"
    )
    
    # Copiar archivos al directorio temporal
    foreach ($item in $FilesToDeploy) {
        $sourcePath = Join-Path $ProjectPath $item
        if (Test-Path $sourcePath) {
            Write-Step "Copiando: $item"
            Copy-Item -Path $sourcePath -Destination $TempDir -Recurse -Force
        } else {
            Write-Warning "No encontrado: $item"
        }
    }
    
    # Copiar script de instalación optimizado
    $installScript = Join-Path $ProjectPath "install_ubuntu24_optimized.sh"
    if (Test-Path $installScript) {
        Copy-Item -Path $installScript -Destination $TempDir
        Write-Step "Script de instalación copiado"
    } else {
        Write-Warning "Script de instalación no encontrado en el directorio del proyecto"
    }
    
    Write-Success "Archivos preparados en: $TempDir"
    Write-Host ""
}

# Función para crear script de despliegue
function Create-DeploymentScripts {
    Write-Header "CREACIÓN DE SCRIPTS DE DESPLIEGUE"
    
    Write-Step "Creando script SFTP..."
    
    # Script SFTP que crea la carpeta "deudout"
    $SftpScript = Join-Path $TempDir "sftp_commands.txt"
    @"
# Comandos SFTP automáticos
cd /tmp
mkdir deudout
cd deudout
put -r *
bye
"@ | Out-File -FilePath $SftpScript -Encoding UTF8
    
    # Script de instalación remota
    $RemoteScript = Join-Path $TempDir "remote_install.sh"
    $remoteScriptContent = @'
#!/bin/bash
# Script de instalación remota

set -e

echo "🚀 Iniciando instalación remota de DEUDOUT..."
echo "📁 Directorio: /tmp/deudout"

# Navegar al directorio de despliegue
cd /tmp/deudout

# Verificar archivos
echo "📁 Verificando archivos..."
ls -la

# Dar permisos de ejecución al script de instalación
if [ -f "install_ubuntu24_optimized.sh" ]; then
    chmod +x install_ubuntu24_optimized.sh
    echo "🔧 Ejecutando instalación..."
    ./install_ubuntu24_optimized.sh
else
    echo "❌ Script de instalación no encontrado"
    echo "📋 Instrucciones manuales:"
    echo "   1. Navega a: cd /tmp/deudout"
    echo "   2. Ejecuta: chmod +x install_ubuntu24_optimized.sh"
    echo "   3. Ejecuta: ./install_ubuntu24_optimized.sh"
fi

echo "✅ Instalación completada"
echo "🌐 Aplicación disponible en: http://$(hostname -I | awk '{print $1}')"
'@
    
    $remoteScriptContent | Out-File -FilePath $RemoteScript -Encoding UTF8
    
    Write-Success "Scripts de despliegue creados"
    Write-Host ""
}

# Función para mostrar instrucciones de despliegue
function Show-DeploymentInstructions {
    Write-Header "DESPLIEGUE PREPARADO"
    
    Write-Success "¡Archivos preparados para despliegue!"
    Write-Host ""
    Write-Host "📁 Archivos listos en: $TempDir"
    Write-Host "🔄 Carpeta se renombrará a 'deudout' en el VPS"
    Write-Host ""
    Write-Host "📋 INSTRUCCIONES DE DESPLIEGUE:"
    Write-Host ""
    Write-Host "1️⃣  CONECTARSE AL VPS:"
    Write-Host "   ssh -p $VpsPort $VpsUser@$VpsIp"
    Write-Host ""
    Write-Host "2️⃣  CREAR CARPETA EN EL VPS:"
    Write-Host "   mkdir -p /tmp/deudout"
    Write-Host ""
    Write-Host "3️⃣  SUBIR ARCHIVOS (desde otra terminal):"
    Write-Host "   sftp -P $VpsPort $VpsUser@$VpsIp"
    Write-Host "   cd /tmp/deudout"
    Write-Host "   put -r $TempDir\*"
    Write-Host "   bye"
    Write-Host ""
    Write-Host "4️⃣  EJECUTAR INSTALACIÓN:"
    Write-Host "   cd /tmp/deudout"
    Write-Host "   chmod +x remote_install.sh"
    Write-Host "   ./remote_install.sh"
    Write-Host ""
    Write-Host "🌐 La aplicación estará disponible en: http://$VpsIp"
    Write-Host ""
    
    # Preguntar si quiere abrir el directorio temporal
    $openDir = Read-Host "¿Quieres abrir el directorio temporal para revisar archivos? (y/N)"
    if ($openDir -eq "y" -or $openDir -eq "Y") {
        Start-Process "explorer.exe" -ArgumentList $TempDir
    }
    
    Write-Success "¡Despliegue preparado! Sigue las instrucciones arriba."
    Write-Host ""
    Write-Host "💡 CONSEJO: Mantén esta ventana abierta para ver las instrucciones"
    Write-Host "   mientras haces el despliegue en otra terminal"
}

# Función principal
function Main {
    Write-Header "DESPLIEGUE SFTP PERSONALIZADO DEUDOUT (PowerShell)"
    Write-Host ""
    Write-Host "🎯 Este script:"
    Write-Host "   ✅ Toma archivos desde tu carpeta local"
    Write-Host "   ✅ Prepara todo para despliegue SFTP"
    Write-Host "   ✅ Crea scripts de instalación remota"
    Write-Host "   ✅ Te da instrucciones paso a paso"
    Write-Host ""
    
    # Obtener ruta del proyecto
    Get-ProjectPath
    
    # Configurar conexión SFTP
    Setup-SftpConnection
    
    # Preparar archivos
    Prepare-Deployment
    
    # Crear scripts de despliegue
    Create-DeploymentScripts
    
    # Mostrar instrucciones
    Show-DeploymentInstructions
}

# Ejecutar función principal
Main
