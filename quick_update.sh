#!/bin/bash

# ===== ACTUALIZACIÓN RÁPIDA DE CONFIGURACIÓN DEUDOUT =====
# Script para actualizar solo la configuración sin reinstalar todo

set -e

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

# Variables de configuración
APP_NAME="deudout"
APP_DIR="/home/$APP_NAME"
SERVICE_NAME="flaskapp"
NGINX_SITE="deudout"

# Función para actualizar configuración
update_config() {
    print_header "ACTUALIZANDO CONFIGURACIÓN"
    
    print_step "Deteniendo servicios..."
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
    systemctl stop nginx 2>/dev/null || true
    
    print_step "Actualizando archivos de configuración..."
    
    # Actualizar .env si existe
    if [ -f "$APP_DIR/.env" ]; then
        cp "$APP_DIR/.env" "$APP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
        print_success "Backup de .env creado"
    fi
    
    # Actualizar gunicorn.conf.py
    if [ -f "gunicorn.conf.py" ]; then
        cp gunicorn.conf.py "$APP_DIR/"
        chown www-data:www-data "$APP_DIR/gunicorn.conf.py"
        print_success "gunicorn.conf.py actualizado"
    fi
    
    # Actualizar nginx.conf
    if [ -f "nginx.conf" ]; then
        cp nginx.conf "/etc/nginx/sites-available/$NGINX_SITE"
        nginx -t
        print_success "nginx.conf actualizado"
    fi
    
    # Actualizar servicio systemd
    if [ -f "flaskapp.service" ]; then
        cp flaskapp.service "/etc/systemd/system/$SERVICE_NAME.service"
        systemctl daemon-reload
        print_success "Servicio systemd actualizado"
    fi
    
    print_step "Reiniciando servicios..."
    systemctl start "$SERVICE_NAME"
    systemctl start nginx
    
    print_success "Configuración actualizada"
}

# Función para verificar estado
check_status() {
    print_header "VERIFICANDO ESTADO"
    
    print_step "Verificando servicios..."
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Servicio $SERVICE_NAME activo"
    else
        print_error "Servicio $SERVICE_NAME inactivo"
    fi
    
    if systemctl is-active --quiet nginx; then
        print_success "Nginx activo"
    else
        print_error "Nginx inactivo"
    fi
    
    print_step "Verificando conectividad..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200\|302"; then
        print_success "Aplicación responde correctamente"
    else
        print_error "Aplicación no responde"
    fi
}

# Función principal
main() {
    print_header "ACTUALIZACIÓN RÁPIDA DE CONFIGURACIÓN"
    
    if [ "$EUID" -ne 0 ]; then
        print_error "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
    
    update_config
    check_status
    
    print_success "✅ Actualización completada"
    print_status "Los servicios han sido reiniciados con la nueva configuración"
}

# Ejecutar función principal
main "$@"

