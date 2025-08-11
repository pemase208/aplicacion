#!/bin/bash

# ===== INSTALACIÓN OPTIMIZADA DE DEUDOUT EN UBUNTU 24.04 =====
# Script completo que integra todas las optimizaciones realizadas

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
DOMAIN=""
EMAIL=""

# Función para obtener información del usuario
get_user_input() {
    print_header "CONFIGURACIÓN INICIAL"
    
    echo -e "${CYAN}Por favor, proporciona la siguiente información:${NC}"
    
    read -p "Dominio de tu aplicación (deja vacío para usar IP): " DOMAIN
    read -p "Email para certificados SSL (opcional): " EMAIL
    
    if [ -z "$DOMAIN" ]; then
        DOMAIN=$(hostname -I | awk '{print $1}')
        print_warning "Usando IP del servidor: $DOMAIN"
    fi
    
    print_success "Configuración guardada:"
    print_status "  - Dominio: $DOMAIN"
    print_status "  - Email: $EMAIL"
    print_status "  - Directorio: $APP_DIR"
}

# Función para verificar sistema
check_system() {
    print_header "VERIFICANDO SISTEMA"
    
    print_step "Verificando versión de Ubuntu..."
    if ! grep -q "Ubuntu" /etc/os-release; then
        print_error "Este script solo funciona en Ubuntu"
        exit 1
    fi
    
    version=$(grep VERSION= /etc/os-release | cut -d'"' -f2)
    print_success "Ubuntu $version detectado"
    
    print_step "Verificando privilegios de root..."
    if [ "$EUID" -ne 0 ]; then
        print_error "Este script debe ejecutarse como root (sudo)"
        exit 1
    fi
    print_success "Privilegios de root confirmados"
    
    print_step "Verificando conexión a internet..."
    if ! ping -c 1 8.8.8.8 &>/dev/null; then
        print_error "No hay conexión a internet"
        exit 1
    fi
    print_success "Conexión a internet confirmada"
}

# Función para actualizar sistema
update_system() {
    print_header "ACTUALIZANDO SISTEMA"
    
    print_step "Actualizando lista de paquetes..."
    apt update -y
    
    print_step "Actualizando paquetes del sistema..."
    apt upgrade -y
    
    print_step "Instalando paquetes esenciales..."
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        nginx \
        ufw \
        curl \
        wget \
        git \
        unzip \
        supervisor \
        logrotate \
        sqlite3 \
        certbot \
        python3-certbot-nginx \
        htop \
        nano \
        vim \
        tree \
        net-tools \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release
    
    print_success "Sistema actualizado y paquetes instalados"
}

# Función para crear usuario y directorios
setup_user_and_dirs() {
    print_header "CONFIGURANDO USUARIO Y DIRECTORIOS"
    
    print_step "Creando usuario $APP_NAME..."
    if ! id "$APP_NAME" &>/dev/null; then
        useradd -m -s /bin/bash "$APP_NAME"
        usermod -aG sudo "$APP_NAME"
        print_success "Usuario $APP_NAME creado"
    else
        print_success "Usuario $APP_NAME ya existe"
    fi
    
    print_step "Creando directorios de la aplicación..."
    mkdir -p "$APP_DIR"
    mkdir -p "$APP_DIR/static"
    mkdir -p "$APP_DIR/templates"
    mkdir -p "$APP_DIR/uploads"
    mkdir -p "$APP_DIR/instance"
    mkdir -p "$APP_DIR/logs"
    
    print_step "Creando directorios del sistema..."
    mkdir -p /var/log/flaskapp
    mkdir -p /var/log/gunicorn
    mkdir -p /var/run/gunicorn
    mkdir -p /var/www/flaskapp
    
    print_step "Configurando permisos..."
    chown -R "$APP_NAME:$APP_NAME" "$APP_DIR"
    chown -R www-data:www-data /var/log/flaskapp
    chown -R www-data:www-data /var/log/gunicorn
    chown -R www-data:www-data /var/run/gunicorn
    chown -R www-data:www-data /var/www/flaskapp
    
    print_success "Usuario y directorios configurados"
}

# Función para configurar entorno Python
setup_python_env() {
    print_header "CONFIGURANDO ENTORNO PYTHON"
    
    print_step "Creando entorno virtual..."
    cd "$APP_DIR"
    python3 -m venv venv
    chown -R "$APP_NAME:$APP_NAME" venv
    
    print_step "Activando entorno virtual..."
    source venv/bin/activate
    
    print_step "Actualizando pip..."
    pip install --upgrade pip setuptools wheel
    
    print_step "Instalando dependencias Python..."
    pip install -r requirements.txt
    
    print_success "Entorno Python configurado"
}

# Función para configurar archivos de la aplicación
setup_app_files() {
    print_header "CONFIGURANDO ARCHIVOS DE LA APLICACIÓN"
    
    print_step "Copiando archivos de la aplicación..."
    cp -r . "$APP_DIR/"
    chown -R "$APP_NAME:$APP_NAME" "$APP_DIR"
    
    print_step "Configurando archivo .env..."
    if [ -f "$APP_DIR/config.env.example" ]; then
        cp "$APP_DIR/config.env.example" "$APP_DIR/.env"
        
        # Generar SECRET_KEY
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        sed -i "s/your-secret-key-here/$SECRET_KEY/" "$APP_DIR/.env"
        
        # Configurar dominio
        sed -i "s/tu-dominio.com/$DOMAIN/" "$APP_DIR/.env"
        
        print_success "Archivo .env configurado"
    fi
    
    print_step "Configurando permisos de archivos..."
    chmod 644 "$APP_DIR/.env"
    chmod 755 "$APP_DIR/app.py"
    chmod 755 "$APP_DIR/gunicorn.conf.py"
    
    print_success "Archivos de la aplicación configurados"
}

# Función para configurar base de datos
setup_database() {
    print_header "CONFIGURANDO BASE DE DATOS"
    
    print_step "Inicializando base de datos..."
    cd "$APP_DIR"
    source venv/bin/activate
    
    if [ -f "init_db.py" ]; then
        python3 init_db.py
        print_success "Base de datos inicializada"
    else
        print_warning "init_db.py no encontrado, creando base de datos básica..."
        python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
print('Base de datos creada')
"
    fi
    
    print_step "Configurando permisos de base de datos..."
    chown "$APP_NAME:$APP_NAME" "$APP_DIR/mibasedatos.db"
    chmod 644 "$APP_DIR/mibasedatos.db"
    
    print_success "Base de datos configurada"
}

# Función para configurar Gunicorn
setup_gunicorn() {
    print_header "CONFIGURANDO GUNICORN"
    
    print_step "Verificando configuración de Gunicorn..."
    if [ -f "$APP_DIR/gunicorn.conf.py" ]; then
        print_success "Configuración de Gunicorn encontrada"
    else
        print_error "Configuración de Gunicorn no encontrada"
        exit 1
    fi
    
    print_step "Configurando servicio Systemd..."
    cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Deudout Flask Application
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    print_step "Recargando configuración de Systemd..."
    systemctl daemon-reload
    
    print_step "Habilitando servicio..."
    systemctl enable "$SERVICE_NAME"
    
    print_success "Gunicorn configurado"
}

# Función para configurar Nginx
setup_nginx() {
    print_header "CONFIGURANDO NGINX"
    
    print_step "Verificando configuración de Nginx..."
    if [ -f "$APP_DIR/nginx.conf" ]; then
        print_success "Configuración de Nginx encontrada"
    else
        print_error "Configuración de Nginx no encontrada"
        exit 1
    fi
    
    print_step "Configurando sitio de Nginx..."
    cp "$APP_DIR/nginx.conf" "/etc/nginx/sites-available/$NGINX_SITE"
    
    # Configurar dominio en nginx
    sed -i "s/tu-dominio.com/$DOMAIN/g" "/etc/nginx/sites-available/$NGINX_SITE"
    
    print_step "Habilitando sitio..."
    ln -sf "/etc/nginx/sites-available/$NGINX_SITE" "/etc/nginx/sites-enabled/"
    
    print_step "Deshabilitando sitio por defecto..."
    rm -f /etc/nginx/sites-enabled/default
    
    print_step "Verificando configuración..."
    if nginx -t; then
        print_success "Configuración de Nginx válida"
    else
        print_error "Configuración de Nginx inválida"
        exit 1
    fi
    
    print_success "Nginx configurado"
}

# Función para configurar firewall
setup_firewall() {
    print_header "CONFIGURANDO FIREWALL"
    
    print_step "Configurando UFW..."
    ufw --force reset
    
    print_step "Configurando reglas por defecto..."
    ufw default deny incoming
    ufw default allow outgoing
    
    print_step "Abriendo puertos necesarios..."
    ufw allow 22/tcp    # SSH
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    
    print_step "Activando firewall..."
    ufw --force enable
    
    print_success "Firewall configurado"
}

# Función para configurar logs
setup_logging() {
    print_header "CONFIGURANDO SISTEMA DE LOGS"
    
    print_step "Configurando logrotate..."
    cat > "/etc/logrotate.d/$SERVICE_NAME" << EOF
/var/log/flaskapp/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF
    
    print_step "Configurando permisos de logs..."
    chown -R www-data:www-data /var/log/flaskapp
    chown -R www-data:www-data /var/log/gunicorn
    chmod -R 755 /var/log/flaskapp
    chmod -R 755 /var/log/gunicorn
    
    print_success "Sistema de logs configurado"
}

# Función para configurar SSL (opcional)
setup_ssl() {
    if [ -n "$EMAIL" ]; then
        print_header "CONFIGURANDO SSL CON CERTBOT"
        
        print_step "Instalando Certbot..."
        apt install -y certbot python3-certbot-nginx
        
        print_step "Obteniendo certificado SSL..."
        if certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive; then
            print_success "Certificado SSL configurado"
            
            print_step "Configurando renovación automática..."
            echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
            print_success "Renovación automática configurada"
        else
            print_warning "No se pudo obtener el certificado SSL"
            print_status "Puedes configurarlo manualmente más tarde con: certbot --nginx"
        fi
    else
        print_warning "Email no proporcionado, SSL no configurado"
        print_status "Puedes configurarlo manualmente más tarde con: certbot --nginx"
    fi
}

# Función para iniciar servicios
start_services() {
    print_header "INICIANDO SERVICIOS"
    
    print_step "Iniciando servicio de la aplicación..."
    systemctl start "$SERVICE_NAME"
    
    print_step "Verificando estado del servicio..."
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Servicio de la aplicación iniciado"
    else
        print_error "Error al iniciar el servicio"
        systemctl status "$SERVICE_NAME"
        exit 1
    fi
    
    print_step "Iniciando Nginx..."
    systemctl start nginx
    systemctl enable nginx
    
    if systemctl is-active --quiet nginx; then
        print_success "Nginx iniciado"
    else
        print_error "Error al iniciar Nginx"
        systemctl status nginx
        exit 1
    fi
    
    print_success "Todos los servicios están ejecutándose"
}

# Función para verificar instalación
verify_installation() {
    print_header "VERIFICANDO INSTALACIÓN"
    
    print_step "Ejecutando script de verificación..."
    if [ -f "$APP_DIR/check_installation.sh" ]; then
        chmod +x "$APP_DIR/check_installation.sh"
        bash "$APP_DIR/check_installation.sh"
    else
        print_warning "Script de verificación no encontrado"
        print_step "Verificando manualmente..."
        
        # Verificaciones básicas
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            print_success "Servicio activo"
        else
            print_error "Servicio inactivo"
        fi
        
        if systemctl is-active --quiet nginx; then
            print_success "Nginx activo"
        else
            print_error "Nginx inactivo"
        fi
        
        if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200\|302"; then
            print_success "Aplicación responde correctamente"
        else
            print_error "Aplicación no responde"
        fi
    fi
}

# Función para mostrar información final
show_final_info() {
    print_header "INSTALACIÓN COMPLETADA"
    
    print_success "🎉 ¡Deudout ha sido instalado exitosamente!"
    
    echo ""
    print_status "📋 INFORMACIÓN DE LA INSTALACIÓN:"
    print_status "   - Aplicación: http://$DOMAIN/"
    print_status "   - Directorio: $APP_DIR"
    print_status "   - Usuario: $APP_NAME"
    print_status "   - Servicio: $SERVICE_NAME"
    
    echo ""
    print_status "🔧 COMANDOS ÚTILES:"
    print_status "   - Ver estado: sudo systemctl status $SERVICE_NAME"
    print_status "   - Reiniciar: sudo systemctl restart $SERVICE_NAME"
    print_status "   - Ver logs: sudo journalctl -u $SERVICE_NAME -f"
    print_status "   - Ver logs Nginx: sudo tail -f /var/log/nginx/deudout_error.log"
    
    echo ""
    print_status "📁 ARCHIVOS IMPORTANTES:"
    print_status "   - Configuración: $APP_DIR/.env"
    print_status "   - Base de datos: $APP_DIR/mibasedatos.db"
    print_status "   - Logs: /var/log/flaskapp/"
    
    echo ""
    print_status "🌐 ACCESO A LA APLICACIÓN:"
    print_status "   - URL: http://$DOMAIN/"
    print_status "   - Usuario admin por defecto: admin"
    print_status "   - Contraseña: admin123"
    
    echo ""
    print_warning "⚠️  IMPORTANTE:"
    print_warning "   - Cambia la contraseña del admin por defecto"
    print_warning "   - Revisa la configuración en $APP_DIR/.env"
    print_warning "   - Configura SSL si es necesario"
    
    echo ""
    print_success "✅ La instalación está completa y lista para usar"
}

# Función principal
main() {
    print_header "INSTALADOR OPTIMIZADO DE DEUDOUT"
    print_status "Este script instalará Deudout en Ubuntu 24.04 con todas las optimizaciones"
    
    # Verificar sistema
    check_system
    
    # Obtener información del usuario
    get_user_input
    
    # Confirmar instalación
    echo ""
    read -p "¿Deseas continuar con la instalación? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Instalación cancelada"
        exit 0
    fi
    
    # Ejecutar pasos de instalación
    update_system
    setup_user_and_dirs
    setup_python_env
    setup_app_files
    setup_database
    setup_gunicorn
    setup_nginx
    setup_firewall
    setup_logging
    setup_ssl
    start_services
    verify_installation
    show_final_info
}

# Ejecutar función principal
main "$@"