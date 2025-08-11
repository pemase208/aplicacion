#!/bin/bash

# ===== SCRIPT DE DESPLIEGUE SFTP PARA DEUDOUT =====
# Sube archivos vía SFTP y ejecuta instalación remota

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Función para mostrar mensajes
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

print_step() {
    echo -e "${CYAN}➤ $1${NC}"
}

# Verificar que estamos en el directorio del proyecto
if [ ! -f "app.py" ]; then
    print_error "Este script debe ejecutarse desde el directorio raíz del proyecto DEUDOUT"
    print_error "Asegúrate de que app.py esté presente"
    exit 1
fi

print_header "CONFIGURACIÓN DE DESPLIEGUE SFTP"

# Solicitar información de conexión
echo ""
print_step "Configuración de conexión SFTP:"
read -p "IP del VPS: " VPS_IP
read -p "Usuario del VPS (root): " VPS_USER
read -p "Puerto SSH (22): " VPS_PORT
VPS_PORT=${VPS_PORT:-22}

# Verificar conectividad
print_step "Verificando conectividad con $VPS_IP..."
if ! ping -c 1 "$VPS_IP" > /dev/null 2>&1; then
    print_error "No se puede alcanzar $VPS_IP"
    exit 1
fi

# Verificar acceso SSH
print_step "Verificando acceso SSH..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes -p "$VPS_PORT" "$VPS_USER@$VPS_IP" exit 2>/dev/null; then
    print_warning "No se puede acceder vía SSH sin contraseña"
    print_warning "Asegúrate de tener configuradas las claves SSH o prepara la contraseña"
fi

print_success "Conexión verificada"

print_header "PREPARACIÓN DE ARCHIVOS"

# Crear directorio temporal para el despliegue
TEMP_DIR="/tmp/deudout_deploy_$(date +%s)"
mkdir -p "$TEMP_DIR"

print_step "Preparando archivos para despliegue..."

# Lista de archivos y directorios a incluir
FILES_TO_DEPLOY=(
    "app.py"
    "models.py"
    "requirements.txt"
    "init_db.py"
    "crear_admin.py"
    "poblar_entidades_financieras.py"
    "utils/"
    "static/"
    "templates/"
    "instance/"
    ".env.example"
    "README.txt"
    "gunicorn.conf.py"
    "nginx.conf"
    "install_ubuntu24_optimized.sh"
)

# Copiar archivos al directorio temporal
for item in "${FILES_TO_DEPLOY[@]}"; do
    if [ -e "$item" ]; then
        print_step "Copiando: $item"
        cp -r "$item" "$TEMP_DIR/"
    else
        print_warning "No encontrado: $item"
    fi
done

# Crear archivo de configuración de despliegue
cat > "$TEMP_DIR/deploy_config.txt" << EOF
# Configuración de despliegue DEUDOUT
# Generado el: $(date)
# VPS: $VPS_IP
# Usuario: $VPS_USER
# Puerto: $VPS_PORT

ARCHIVOS_INCLUIDOS:
$(ls -la "$TEMP_DIR" | grep -v "^total")

INSTRUCCIONES:
1. Los archivos se han subido vía SFTP
2. Ejecuta: chmod +x install_ubuntu24_optimized.sh
3. Ejecuta: ./install_ubuntu24_optimized.sh
4. Verifica la instalación con: /home/deudout/health_check.sh

NOTAS:
- Asegúrate de que el VPS esté limpio (Ubuntu 24.04)
- El script de instalación se ejecutará como root
- La aplicación estará disponible en: http://$VPS_IP
EOF

print_success "Archivos preparados en: $TEMP_DIR"

print_header "DESPLIEGUE VÍA SFTP"

print_step "Iniciando transferencia SFTP..."

# Crear script SFTP automático
SFTP_SCRIPT="$TEMP_DIR/sftp_commands.txt"
cat > "$SFTP_SCRIPT" << EOF
# Comandos SFTP automáticos
cd /tmp
mkdir deudout_deploy
cd deudout_deploy
put -r $TEMP_DIR/*
bye
EOF

print_step "Ejecutando transferencia SFTP..."
if sftp -P "$VPS_PORT" -b "$SFTP_SCRIPT" "$VPS_USER@$VPS_IP"; then
    print_success "Archivos transferidos exitosamente"
else
    print_error "Error en la transferencia SFTP"
    print_step "Intentando transferencia manual..."
    
    # Transferencia manual como fallback
    print_step "Subiendo archivos manualmente..."
    sftp -P "$VPS_PORT" "$VPS_USER@$VPS_IP" << EOF
cd /tmp
mkdir -p deudout_deploy
cd deudout_deploy
put -r $TEMP_DIR/*
bye
EOF
fi

print_header "CONFIGURACIÓN REMOTA"

print_step "Configurando instalación remota..."

# Crear script de instalación remota
REMOTE_SCRIPT="$TEMP_DIR/remote_install.sh"
cat > "$REMOTE_SCRIPT" << 'EOF'
#!/bin/bash
# Script de instalación remota

set -e

echo "🚀 Iniciando instalación remota de DEUDOUT..."

# Navegar al directorio de despliegue
cd /tmp/deudout_deploy

# Verificar archivos
echo "📁 Verificando archivos..."
ls -la

# Dar permisos de ejecución
chmod +x install_ubuntu24_optimized.sh

# Ejecutar instalación
echo "🔧 Ejecutando instalación..."
./install_ubuntu24_optimized.sh

echo "✅ Instalación completada"
echo "🌐 Aplicación disponible en: http://$(hostname -I | awk '{print $1}')"
EOF

# Subir script de instalación remota
print_step "Subiendo script de instalación remota..."
sftp -P "$VPS_PORT" "$VPS_USER@$VPS_IP" << EOF
cd /tmp/deudout_deploy
put $REMOTE_SCRIPT
chmod +x remote_install.sh
bye
EOF

print_success "Script de instalación remota subido"

print_header "INSTRUCCIONES FINALES"

print_success "¡Despliegue completado exitosamente!"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Conéctate al VPS: ssh -p $VPS_PORT $VPS_USER@$VPS_IP"
echo "   2. Navega al directorio: cd /tmp/deudout_deploy"
echo "   3. Ejecuta la instalación: ./remote_install.sh"
echo ""
echo "🔧 Alternativa manual:"
echo "   - Navega a: cd /tmp/deudout_deploy"
echo "   - Ejecuta: chmod +x install_ubuntu24_optimized.sh"
echo "   - Ejecuta: ./install_ubuntu24_optimized.sh"
echo ""
echo "📁 Archivos desplegados en: /tmp/deudout_deploy"
echo "📝 Configuración en: /tmp/deudout_deploy/deploy_config.txt"

# Limpiar archivos temporales
print_step "Limpiando archivos temporales..."
rm -rf "$TEMP_DIR"

print_success "¡Despliegue SFTP completado!"
print_success "Los archivos están listos en tu VPS para la instalación"


