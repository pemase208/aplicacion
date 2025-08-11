#!/bin/bash

# ===== INSTALACIÓN COMPLETA DEUDOUT EN UBUNTU 24.04 LIMPIO =====
# Script para montar toda la aplicación desde cero en un entorno limpio

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

# Verificar que estamos en Ubuntu 24.04
print_header "VERIFICANDO SISTEMA OPERATIVO"
print_step "Verificando versión de Ubuntu..."

if ! grep -q "Ubuntu 24.04" /etc/os-release; then
    print_warning "Este script está optimizado para Ubuntu 24.04"
    print_warning "Versión detectada: $(grep VERSION= /etc/os-release | cut -d'"' -f2)"
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Instalación cancelada"
        exit 1
    fi
fi

print_success "Sistema operativo verificado"

# Variables de configuración
APP_NAME="deudout"
APP_DIR="/home/$APP_NAME"
APP_USER="$APP_NAME"
APP_GROUP="$APP_NAME"
PYTHON_VERSION="3.12"
NGINX_SITE="deudout"

print_header "CONFIGURACIÓN INICIAL"
print_step "Actualizando sistema..."

# Actualizar sistema
apt update && apt upgrade -y

print_step "Instalando dependencias del sistema..."

# Instalar dependencias esenciales
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
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    supervisor \
    logrotate \
    htop \
    nano \
    vim \
    tree

print_success "Dependencias del sistema instaladas"

print_header "CONFIGURACIÓN DE USUARIO Y DIRECTORIOS"
print_step "Creando usuario y directorios..."

# Crear usuario si no existe
if ! id "$APP_USER" &>/dev/null; then
    useradd -m -s /bin/bash -G sudo "$APP_USER"
    echo "$APP_USER:$APP_USER" | chpasswd
    print_success "Usuario $APP_USER creado"
else
    print_warning "Usuario $APP_USER ya existe"
fi

# Crear directorios
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/backups"
mkdir -p "$APP_DIR/uploads"
mkdir -p "$APP_DIR/static/generated_docs"
mkdir -p "$APP_DIR/static/docx_templates"

# Cambiar propietario
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"

print_success "Directorios creados y configurados"

print_header "CONFIGURACIÓN DE PYTHON"
print_step "Configurando Python $PYTHON_VERSION..."

# Crear entorno virtual
cd "$APP_DIR"
sudo -u "$APP_USER" python3 -m venv venv

# Activar entorno virtual y actualizar pip
sudo -u "$APP_USER" bash -c "source venv/bin/activate && pip install --upgrade pip"

print_success "Entorno virtual Python configurado"

print_header "INSTALACIÓN DE LA APLICACIÓN"
print_step "Copiando archivos de la aplicación..."

# Si estamos ejecutando desde el directorio del proyecto, copiar archivos
if [ -f "app.py" ]; then
    cp -r . "$APP_DIR/"
    chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
    print_success "Archivos copiados desde directorio actual"
else
    print_warning "No se encontró app.py en el directorio actual"
    print_step "Descargando aplicación desde repositorio..."
    
    # Aquí podrías clonar desde un repositorio Git
    # sudo -u "$APP_USER" git clone https://github.com/tu-usuario/deudout.git "$APP_DIR"
    
    print_warning "Por favor, copia manualmente los archivos de la aplicación a $APP_DIR"
    print_warning "O configura un repositorio Git y ejecuta:"
    print_warning "sudo -u $APP_USER git clone <tu-repo> $APP_DIR"
fi

print_header "INSTALACIÓN DE DEPENDENCIAS PYTHON"
print_step "Instalando dependencias Python..."

cd "$APP_DIR"
sudo -u "$APP_USER" bash -c "source venv/bin/activate && pip install -r requirements.txt"

print_success "Dependencias Python instaladas"

print_header "CONFIGURACIÓN DE BASE DE DATOS"
print_step "Inicializando base de datos..."

# Crear archivo de configuración
sudo -u "$APP_USER" bash -c "cat > $APP_DIR/.env << 'EOF'
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///deudout.db
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password
UPLOAD_FOLDER=$APP_DIR/uploads
MAX_CONTENT_LENGTH=16777216
EOF"

# Inicializar base de datos
sudo -u "$APP_USER" bash -c "cd $APP_DIR && source venv/bin/activate && python init_db.py"

# Poblar datos iniciales
if [ -f "poblar_entidades_financieras.py" ]; then
    sudo -u "$APP_USER" bash -c "cd $APP_DIR && source venv/bin/activate && python poblar_entidades_financieras.py"
fi

# Crear usuario admin
if [ -f "crear_admin.py" ]; then
    sudo -u "$APP_USER" bash -c "cd $APP_DIR && source venv/bin/activate && python crear_admin.py"
fi

print_success "Base de datos inicializada"

print_header "CONFIGURACIÓN DE GUNICORN"
print_step "Configurando Gunicorn..."

# Crear archivo de configuración de Gunicorn
cat > "$APP_DIR/gunicorn.conf.py" << 'EOF'
import multiprocessing

bind = "unix:$APP_DIR/deudout.sock"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
reload = False
daemon = False
user = "$APP_USER"
group = "$APP_GROUP"
tmp_upload_dir = None
EOF

# Crear servicio systemd
cat > "/etc/systemd/system/$APP_NAME.service" << EOF
[Unit]
Description=DEUDOUT Flask Application
After=network.target
Wants=network.target

[Service]
Type=notify
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=FLASK_APP=app.py
Environment=FLASK_ENV=production
ExecStart=$APP_DIR/venv/bin/gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$APP_NAME

[Install]
WantedBy=multi-user.target
EOF

print_success "Gunicorn configurado"

print_header "CONFIGURACIÓN DE NGINX"
print_step "Configurando Nginx..."

# Crear configuración de sitio
cat > "/etc/nginx/sites-available/$NGINX_SITE" << EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 16M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    # Logs
    access_log $APP_DIR/logs/nginx_access.log;
    error_log $APP_DIR/logs/nginx_error.log;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/deudout.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /static {
        alias $APP_DIR/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";
    }
    
    location /uploads {
        alias $APP_DIR/uploads;
        internal;
    }
    
    # Security headers
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';" always;
}
EOF

# Habilitar sitio y deshabilitar default
ln -sf "/etc/nginx/sites-available/$NGINX_SITE" "/etc/nginx/sites-enabled/"
rm -f /etc/nginx/sites-enabled/default

# Configurar Nginx principal
cat > "/etc/nginx/nginx.conf" << 'EOF'
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 768;
    multi_accept on;
    use epoll;
}

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;
    
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

print_success "Nginx configurado"

print_header "CONFIGURACIÓN DE SUPERVISOR"
print_step "Configurando Supervisor..."

# Crear configuración de Supervisor
cat > "/etc/supervisor/conf.d/$APP_NAME.conf" << EOF
[program:$APP_NAME]
command=$APP_DIR/venv/bin/gunicorn --config gunicorn.conf.py app:app
directory=$APP_DIR
user=$APP_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$APP_DIR/logs/gunicorn.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
EOF

print_success "Supervisor configurado"

print_header "CONFIGURACIÓN DE LOGROTATE"
print_step "Configurando logrotate..."

# Crear configuración de logrotate
cat > "/etc/logrotate.d/$APP_NAME" << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_GROUP
    postrotate
        systemctl reload $APP_NAME > /dev/null 2>&1 || true
    endscript
}
EOF

print_success "Logrotate configurado"

print_header "CONFIGURACIÓN DE FIREWALL"
print_step "Configurando firewall..."

# Configurar UFW
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

print_success "Firewall configurado"

print_header "CONFIGURACIÓN DE PERMISOS"
print_step "Configurando permisos..."

# Configurar permisos
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod 640 "$APP_DIR/.env"
chmod 755 "$APP_DIR/venv/bin/activate"

# Crear directorio de logs si no existe
mkdir -p "$APP_DIR/logs"
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR/logs"

print_success "Permisos configurados"

print_header "INICIO DE SERVICIOS"
print_step "Iniciando servicios..."

# Recargar systemd y habilitar servicios
systemctl daemon-reload
systemctl enable "$APP_NAME"
systemctl start "$APP_NAME"

# Reiniciar Nginx
systemctl restart nginx

# Reiniciar Supervisor
systemctl restart supervisor

print_success "Servicios iniciados"

print_header "VERIFICACIÓN FINAL"
print_step "Verificando estado de los servicios..."

# Verificar estado
echo ""
echo "Estado de $APP_NAME:"
systemctl status "$APP_NAME" --no-pager -l

echo ""
echo "Estado de Nginx:"
systemctl status nginx --no-pager -l

echo ""
echo "Estado de Supervisor:"
systemctl status supervisor --no-pager -l

echo ""
echo "Puertos abiertos:"
ufw status

echo ""
echo "Verificación de archivos:"
ls -la "$APP_DIR/"

echo ""
echo "Verificación de logs:"
ls -la "$APP_DIR/logs/"

print_header "INSTALACIÓN COMPLETADA"
print_success "¡DEUDOUT ha sido instalado exitosamente en Ubuntu 24.04!"
echo ""
echo "🌐 Tu aplicación está disponible en: http://$(hostname -I | awk '{print $1}')"
echo ""
echo "📋 Información de acceso:"
echo "   - Usuario admin: admin"
echo "   - Contraseña: admin123"
echo "   - IMPORTANTE: Cambia la contraseña del admin inmediatamente"
echo ""
echo "📁 Directorios importantes:"
echo "   - Aplicación: $APP_DIR"
echo "   - Logs: $APP_DIR/logs"
echo "   - Base de datos: $APP_DIR/instance/"
echo "   - Archivos estáticos: $APP_DIR/static"
echo ""
echo "🔧 Comandos útiles:"
echo "   - Ver logs: journalctl -u $APP_NAME -f"
echo "   - Reiniciar app: systemctl restart $APP_NAME"
echo "   - Ver estado: systemctl status $APP_NAME"
echo "   - Acceder al directorio: cd $APP_DIR"
echo "   - Activar entorno virtual: source $APP_DIR/venv/bin/activate"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Accede a la aplicación y cambia la contraseña del admin"
echo "   2. Configura las variables de email en $APP_DIR/.env"
echo "   3. Configura SSL/HTTPS si es necesario"
echo "   4. Revisa los logs para verificar que todo funcione correctamente"
echo ""
print_warning "IMPORTANTE: Revisa y configura las variables de email en $APP_DIR/.env"
print_warning "IMPORTANTE: Cambia la contraseña del admin por seguridad"
echo ""
print_success "¡Ubuntu 24.04 configurado correctamente para DEUDOUT!"
print_success "La aplicación está lista para usar en producción"
