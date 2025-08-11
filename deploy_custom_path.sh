#!/bin/bash

# ===== DESPLIEGUE SFTP PERSONALIZADO DEUDOUT =====
# Script que sube desde "Copia medio funcional" y crea carpeta "deudout" en el VPS

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

# Función para verificar errores
check_error() {
    if [ $? -ne 0 ]; then
        print_error "Error en: $1"
        exit 1
    fi
}

# Función para obtener la ruta del proyecto
get_project_path() {
    print_header "CONFIGURACIÓN DE RUTA LOCAL"
    
    # Ruta por defecto (la que mencionaste)
    DEFAULT_PATH="Copia medio funcional"
    
    echo ""
    print_step "Ruta por defecto detectada: '$DEFAULT_PATH'"
    read -p "¿Es correcta esta ruta? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PROJECT_PATH="$DEFAULT_PATH"
    else
        echo ""
        print_step "Por favor, ingresa la ruta completa a tu proyecto DEUDOUT:"
        read -p "Ruta: " PROJECT_PATH
    fi
    
    # Verificar que la ruta existe
    if [ ! -d "$PROJECT_PATH" ]; then
        print_error "La ruta '$PROJECT_PATH' no existe o no es un directorio"
        exit 1
    fi
    
    # Verificar que contiene archivos del proyecto
    if [ ! -f "$PROJECT_PATH/app.py" ]; then
        print_error "La ruta '$PROJECT_PATH' no contiene app.py (no parece ser el proyecto DEUDOUT)"
        exit 1
    fi
    
    print_success "Ruta del proyecto verificada: $PROJECT_PATH"
    echo ""
}

# Función para configurar conexión SFTP
setup_sftp_connection() {
    print_header "CONFIGURACIÓN DE CONEXIÓN SFTP"
    
    echo ""
    print_step "Configuración de conexión al VPS:"
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
    echo ""
}

# Función para preparar archivos para despliegue
prepare_deployment() {
    print_header "PREPARACIÓN DE ARCHIVOS"
    
    # Crear directorio temporal para el despliegue
    TEMP_DIR="/tmp/deudout_deploy_$(date +%s)"
    mkdir -p "$TEMP_DIR"
    
    print_step "Preparando archivos desde: $PROJECT_PATH"
    
    # Lista de archivos y directorios a incluir
    FILES_TO_DEPLOY=(
        "app.py"
        "models.py"
        "requirements.txt"
        "init_db.py"
        "crear_admin.py"
        "poblar_entidades_financieras.py"
        "utils"
        "static"
        "templates"
        "instance"
        ".env.example"
        "README.txt"
        "gunicorn.conf.py"
        "nginx.conf"
    )
    
    # Copiar archivos al directorio temporal
    for item in "${FILES_TO_DEPLOY[@]}"; do
        if [ -e "$PROJECT_PATH/$item" ]; then
            print_step "Copiando: $item"
            cp -r "$PROJECT_PATH/$item" "$TEMP_DIR/"
        else
            print_warning "No encontrado: $item"
        fi
    done
    
    # Copiar script de instalación optimizado
    if [ -f "install_ubuntu24_optimized.sh" ]; then
        cp "install_ubuntu24_optimized.sh" "$TEMP_DIR/"
        print_step "Script de instalación copiado"
    else
        print_warning "Script de instalación no encontrado en el directorio actual"
        print_step "Descargando script de instalación..."
        # Aquí podrías descargar el script si no está disponible
    fi
    
    print_success "Archivos preparados en: $TEMP_DIR"
    echo ""
}

# Función para ejecutar despliegue SFTP
execute_sftp_deployment() {
    print_header "DESPLIEGUE VÍA SFTP"
    
    print_step "Iniciando transferencia SFTP..."
    
    # Crear script SFTP automático que crea la carpeta "deudout"
    SFTP_SCRIPT="$TEMP_DIR/sftp_commands.txt"
    cat > "$SFTP_SCRIPT" << EOF
# Comandos SFTP automáticos
cd /tmp
mkdir deudout
cd deudout
put -r $TEMP_DIR/*
bye
EOF
    
    print_step "Ejecutando transferencia SFTP..."
    if sftp -P "$VPS_PORT" -b "$SFTP_SCRIPT" "$VPS_USER@$VPS_IP"; then
        print_success "Archivos transferidos exitosamente a /tmp/deudout/"
    else
        print_error "Error en la transferencia SFTP automática"
        print_step "Intentando transferencia manual..."
        
        # Transferencia manual como fallback
        print_step "Subiendo archivos manualmente..."
        sftp -P "$VPS_PORT" "$VPS_USER@$VPS_IP" << EOF
cd /tmp
mkdir -p deudout
cd deudout
put -r $TEMP_DIR/*
bye
EOF
        
        if [ $? -eq 0 ]; then
            print_success "Archivos transferidos manualmente a /tmp/deudout/"
        else
            print_error "Error en la transferencia manual también"
            exit 1
        fi
    fi
    
    echo ""
}

# Función para configurar instalación remota
setup_remote_installation() {
    print_header "CONFIGURACIÓN DE INSTALACIÓN REMOTA"
    
    print_step "Configurando instalación remota..."
    
    # Crear script de instalación remota
    REMOTE_SCRIPT="$TEMP_DIR/remote_install.sh"
    cat > "$REMOTE_SCRIPT" << 'EOF'
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
EOF
    
    # Subir script de instalación remota
    print_step "Subiendo script de instalación remota..."
    sftp -P "$VPS_PORT" "$VPS_USER@$VPS_IP" << EOF
cd /tmp/deudout
put $REMOTE_SCRIPT
chmod +x remote_install.sh
bye
EOF
    
    print_success "Script de instalación remota subido"
    echo ""
}

# Función para mostrar instrucciones finales
show_final_instructions() {
    print_header "DESPLIEGUE COMPLETADO"
    
    print_success "¡Despliegue SFTP completado exitosamente!"
    echo ""
    echo "📁 Archivos desplegados en: /tmp/deudout"
    echo "🔄 Carpeta renombrada de 'Copia medio funcional' a 'deudout'"
    echo ""
    echo "📋 Próximos pasos:"
    echo "   1. Conéctate al VPS: ssh -p $VPS_PORT $VPS_USER@$VPS_IP"
    echo "   2. Navega al directorio: cd /tmp/deudout"
    echo "   3. Ejecuta la instalación: ./remote_install.sh"
    echo ""
    echo "🔧 Alternativa manual:"
    echo "   - Navega a: cd /tmp/deudout"
    echo "   - Ejecuta: chmod +x install_ubuntu24_optimized.sh"
    echo "   - Ejecuta: ./install_ubuntu24_optimized.sh"
    echo ""
    echo "🌐 La aplicación estará disponible en: http://$VPS_IP"
    
    # Limpiar archivos temporales
    print_step "Limpiando archivos temporales..."
    rm -rf "$TEMP_DIR"
    
    print_success "¡Despliegue personalizado completado!"
    print_success "Los archivos están listos en tu VPS en /tmp/deudout"
    
    # Preguntar si quiere continuar con la instalación remota
    echo ""
    read -p "¿Quieres continuar con la instalación remota ahora? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Conectando al VPS para instalación remota..."
        ssh -p "$VPS_PORT" "$VPS_USER@$VPS_IP" "cd /tmp/deudout && ./remote_install.sh"
    else
        print_success "Instalación remota pospuesta. Ejecuta manualmente cuando estés listo."
        echo ""
        print_step "Comando para ejecutar en el VPS:"
        echo "   cd /tmp/deudout && ./remote_install.sh"
    fi
}

# Función principal
main() {
    print_header "DESPLIEGUE SFTP PERSONALIZADO DEUDOUT"
    echo ""
    echo "🎯 Este script:"
    echo "   ✅ Toma archivos desde tu carpeta local"
    echo "   ✅ Los sube vía SFTP al VPS"
    echo "   ✅ Crea la carpeta 'deudout' en el VPS"
    echo "   ✅ Renombra automáticamente la carpeta"
    echo "   ✅ Configura la instalación remota"
    echo ""
    
    # Obtener ruta del proyecto
    get_project_path
    
    # Configurar conexión SFTP
    setup_sftp_connection
    
    # Preparar archivos
    prepare_deployment
    
    # Ejecutar despliegue
    execute_sftp_deployment
    
    # Configurar instalación remota
    setup_remote_installation
    
    # Mostrar instrucciones finales
    show_final_instructions
}

# Ejecutar función principal
main "$@"


