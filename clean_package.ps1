# Script PowerShell para crear un paquete limpio de la aplicación Flask
# Elimina archivos innecesarios y crea un archivo comprimido

Write-Host "Limpiando archivos innecesarios..." -ForegroundColor Green

# Eliminar directorios y archivos innecesarios
if (Test-Path "__pycache__") { Remove-Item "__pycache__" -Recurse -Force }
if (Test-Path "venv") { Remove-Item "venv" -Recurse -Force }
if (Test-Path "instance") { Remove-Item "instance" -Recurse -Force }
if (Test-Path "generados") { Remove-Item "generados" -Recurse -Force }
if (Test-Path ".vscode") { Remove-Item ".vscode" -Recurse -Force }
if (Test-Path ".idea") { Remove-Item ".idea" -Recurse -Force }

# Eliminar archivos de base de datos
Get-ChildItem -Path "." -Filter "*.db" | Remove-Item -Force
Get-ChildItem -Path "." -Filter "*.sqlite" | Remove-Item -Force
Get-ChildItem -Path "." -Filter "*.sqlite3" | Remove-Item -Force

# Eliminar archivos de log
Get-ChildItem -Path "." -Filter "*.log" | Remove-Item -Force

# Eliminar archivos de configuración local
if (Test-Path ".env") { Remove-Item ".env" -Force }

# Eliminar archivos generados
Get-ChildItem -Path "." -Filter "*.pdf" | Remove-Item -Force
Get-ChildItem -Path "." -Filter "*.xlsx" | Remove-Item -Force
Get-ChildItem -Path "." -Filter "*.docx" | Remove-Item -Force

# Eliminar archivos temporales
Get-ChildItem -Path "." -Filter "*.tmp" | Remove-Item -Force
Get-ChildItem -Path "." -Filter "*.temp" | Remove-Item -Force
Get-ChildItem -Path "." -Filter "*.bak" | Remove-Item -Force
Get-ChildItem -Path "." -Filter "*.backup" | Remove-Item -Force

# Eliminar archivos de Python compilados
Get-ChildItem -Path "." -Recurse -Filter "*.pyc" | Remove-Item -Force
Get-ChildItem -Path "." -Recurse -Filter "*.pyo" | Remove-Item -Force
Get-ChildItem -Path "." -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

Write-Host "Creando paquete limpio..." -ForegroundColor Green

# Crear directorio para el paquete
$packageDir = "../flask_app_clean"
if (Test-Path $packageDir) { Remove-Item $packageDir -Recurse -Force }
New-Item -ItemType Directory -Path $packageDir | Out-Null

# Lista de archivos y directorios a copiar
$filesToCopy = @(
    "app.py",
    "models.py", 
    "requirements.txt",
    "static",
    "templates",
    "utils",
    "config.env.example",
    "README.txt",
    "DEPLOY.md",
    "NAVEGACION.md",
    "MAPA_NAVEGACION_DETALLADO.md",
    "DIAGRAMA_FLUJOS.md",
    "CONFIGURACION_PDF_EMAIL.md",
    ".gitignore",
    "deploy_script.sh",
    "deploy_app.sh",
    "gunicorn.conf.py",
    "nginx.conf",
    "flaskapp.service",
    "test_navigation.py",
    "test_flows.py"
)

# Copiar archivos necesarios
foreach ($file in $filesToCopy) {
    if (Test-Path $file) {
        if (Test-Path $file -PathType Container) {
            Copy-Item -Path $file -Destination $packageDir -Recurse
        } else {
            Copy-Item -Path $file -Destination $packageDir
        }
        Write-Host "Copiado: $file" -ForegroundColor Green
    } else {
        Write-Host "No encontrado: $file" -ForegroundColor Yellow
    }
}

# Crear archivo comprimido
Write-Host "Comprimiendo archivos..." -ForegroundColor Green
$zipPath = "../flask_app_clean.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

Compress-Archive -Path $packageDir -DestinationPath $zipPath

Write-Host "Paquete limpio creado:" -ForegroundColor Green
Write-Host "   - $zipPath" -ForegroundColor Cyan
Write-Host "   - Directorio: $packageDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "Archivos incluidos en el paquete:" -ForegroundColor Green
Get-ChildItem -Path $packageDir | Format-Table Name, Length, LastWriteTime
