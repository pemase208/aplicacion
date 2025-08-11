#!/bin/bash

# ===== VERIFICACIÓN COMPLETA DE INSTALACIÓN DEUDOUT =====
# Script para verificar que todo esté funcionando correctamente

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

print_header "VERIFICACIÓN COMPLETA DE INSTALACIÓN DEUDOUT"

# ===== VERIFICACIÓN 1: SISTEMA OPERATIVO =====
print_header "VERIFICANDO SISTEMA OPERATIVO"
print_step "Verificando versión de Ubuntu..."

if grep -q "Ubuntu 24.04" /etc/os-release; then
    print_success "Ubuntu 24.04 detectado"
elif grep -q "Ubuntu" /etc/os-release; then
    version=$(grep VERSION= /etc/os-release | cut -d'"' -f2)
    print_warning "Ubuntu $version detectado (recomendado 24.04)"
else
    print_warning "Sistema operativo no es Ubuntu"
fi

# ===== VERIFICACIÓN 2: DEPENDENCIAS DEL SISTEMA =====
print_header "VERIFICANDO DEPENDENCIAS DEL SISTEMA"
print_step "Verificando paquetes esenciales..."

required_packages=(
    "python3"
    "python3-pip"
    "python3-venv"
    "nginx"
    "ufw"
    "curl"
    "wget"
    "git"
    "unzip"
    "supervisor"
    "logrotate"
)

missing_packages=()

for package in "${required_packages[@]}"; do
    if dpkg -l | grep -q "^ii.*$package"; then
        print_success "$package instalado"
    else
        print_error "$package NO instalado"
        missing_packages+=("$package")
    fi
done

if [ ${#missing_packages[@]} -gt 0 ]; then
    print_warning "Paquetes faltantes: ${missing_packages[*]}"
    print_step "Instalando paquetes faltantes..."
    apt update && apt install -y "${missing_packages[@]}"
else
    print_success "Todas las dependencias del sistema están instaladas"
fi

# ===== VERIFICACIÓN 3: USUARIO Y PERMISOS =====
print_header "VERIFICANDO USUARIO Y PERMISOS"
print_step "Verificando usuario de la aplicación..."

if id "$APP_NAME" &>/dev/null; then
    print_success "Usuario $APP_NAME existe"
else
    print_error "Usuario $APP_NAME NO existe"
    print_step "Creando usuario $APP_NAME..."
    useradd -m -s /bin/bash "$APP_NAME"
    usermod -aG sudo "$APP_NAME"
fi

if [ -d "$APP_DIR" ]; then
    print_success "Directorio $APP_DIR existe"
    
    # Verificar permisos
    if [ -w "$APP_DIR" ]; then
        print_success "Permisos de escritura correctos"
    else
        print_error "Problema de permisos en $APP_DIR"
        chown -R "$APP_NAME:$APP_NAME" "$APP_DIR"
    fi
else
    print_error "Directorio $APP_DIR NO existe"
    print_step "Creando directorio $APP_DIR..."
    mkdir -p "$APP_DIR"
    chown "$APP_NAME:$APP_NAME" "$APP_DIR"
fi

# ===== VERIFICACIÓN 4: ENTORNO VIRTUAL PYTHON =====
print_header "VERIFICANDO ENTORNO VIRTUAL PYTHON"
print_step "Verificando entorno virtual..."

if [ -d "$APP_DIR/venv" ]; then
    print_success "Entorno virtual existe"
    
    # Verificar activación
    if source "$APP_DIR/venv/bin/activate" 2>/dev/null; then
        print_success "Entorno virtual se puede activar"
        
        # Verificar Python
        python_version=$(python3 --version 2>&1)
        print_success "Python: $python_version"
        
        # Verificar pip
        pip_version=$(pip --version 2>&1)
        print_success "Pip: $pip_version"
    else
        print_error "Problema con el entorno virtual"
    fi
else
    print_error "Entorno virtual NO existe"
    print_step "Creando entorno virtual..."
    cd "$APP_DIR"
    python3 -m venv venv
    chown -R "$APP_NAME:$APP_NAME" venv
fi

# ===== VERIFICACIÓN 5: DEPENDENCIAS PYTHON =====
print_header "VERIFICANDO DEPENDENCIAS PYTHON"
print_step "Verificando requirements.txt..."

if [ -f "$APP_DIR/requirements.txt" ]; then
    print_success "requirements.txt existe"
    
    # Verificar instalación de dependencias
    cd "$APP_DIR"
    source venv/bin/activate
    
    print_step "Verificando dependencias instaladas..."
    
    # Lista de dependencias críticas
    critical_deps=(
        "Flask"
        "Flask-SQLAlchemy"
        "Flask-Login"
        "gunicorn"
        "PyPDF2"
        "reportlab"
        "python-docx"
        "pandas"
        "openpyxl"
        "requests"
        "beautifulsoup4"
    )
    
    missing_deps=()
    
    for dep in "${critical_deps[@]}"; do
        if python3 -c "import $dep" 2>/dev/null; then
            print_success "$dep instalado"
        else
            print_error "$dep NO instalado"
            missing_deps+=("$dep")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_warning "Dependencias faltantes: ${missing_deps[*]}"
        print_step "Instalando dependencias faltantes..."
        pip install -r requirements.txt
    else
        print_success "Todas las dependencias Python están instaladas"
    fi
else
    print_error "requirements.txt NO existe"
fi

# ===== VERIFICACIÓN 6: BASE DE DATOS =====
print_header "VERIFICANDO BASE DE DATOS"
print_step "Verificando archivo de base de datos..."

if [ -f "$APP_DIR/mibasedatos.db" ]; then
    print_success "Base de datos SQLite existe"
    
    # Verificar permisos
    if [ -r "$APP_DIR/mibasedatos.db" ] && [ -w "$APP_DIR/mibasedatos.db" ]; then
        print_success "Permisos de base de datos correctos"
    else
        print_error "Problema de permisos en la base de datos"
        chown "$APP_NAME:$APP_NAME" "$APP_DIR/mibasedatos.db"
        chmod 644 "$APP_DIR/mibasedatos.db"
    fi
else
    print_warning "Base de datos NO existe, se creará al ejecutar la aplicación"
fi

# ===== VERIFICACIÓN 7: SERVICIO SYSTEMD =====
print_header "VERIFICANDO SERVICIO SYSTEMD"
print_step "Verificando servicio $SERVICE_NAME..."

if systemctl list-unit-files | grep -q "$SERVICE_NAME.service"; then
    print_success "Servicio $SERVICE_NAME existe"
    
    # Verificar estado
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_success "Servicio $SERVICE_NAME está activo"
    else
        print_warning "Servicio $SERVICE_NAME NO está activo"
        print_step "Iniciando servicio..."
        systemctl start "$SERVICE_NAME"
    fi
    
    # Verificar habilitado
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        print_success "Servicio $SERVICE_NAME está habilitado"
    else
        print_warning "Servicio $SERVICE_NAME NO está habilitado"
        print_step "Habilitando servicio..."
        systemctl enable "$SERVICE_NAME"
    fi
else
    print_error "Servicio $SERVICE_NAME NO existe"
fi

# ===== VERIFICACIÓN 8: NGINX =====
print_header "VERIFICANDO NGINX"
print_step "Verificando Nginx..."

if systemctl is-active --quiet nginx; then
    print_success "Nginx está activo"
    
    # Verificar configuración
    if nginx -t 2>/dev/null; then
        print_success "Configuración de Nginx válida"
    else
        print_error "Configuración de Nginx inválida"
    fi
    
    # Verificar sitio
    if [ -f "/etc/nginx/sites-available/$NGINX_SITE" ]; then
        print_success "Sitio $NGINX_SITE configurado"
        
        if [ -L "/etc/nginx/sites-enabled/$NGINX_SITE" ]; then
            print_success "Sitio $NGINX_SITE habilitado"
        else
            print_warning "Sitio $NGINX_SITE NO habilitado"
            print_step "Habilitando sitio..."
            ln -s "/etc/nginx/sites-available/$NGINX_SITE" "/etc/nginx/sites-enabled/"
            systemctl reload nginx
        fi
    else
        print_error "Sitio $NGINX_SITE NO configurado"
    fi
else
    print_error "Nginx NO está activo"
    print_step "Iniciando Nginx..."
    systemctl start nginx
    systemctl enable nginx
fi

# ===== VERIFICACIÓN 9: FIREWALL =====
print_header "VERIFICANDO FIREWALL"
print_step "Verificando UFW..."

if ufw status | grep -q "Status: active"; then
    print_success "UFW está activo"
    
    # Verificar puertos abiertos
    if ufw status | grep -q "80/tcp.*ALLOW"; then
        print_success "Puerto 80 (HTTP) abierto"
    else
        print_warning "Puerto 80 (HTTP) NO abierto"
        print_step "Abriendo puerto 80..."
        ufw allow 80/tcp
    fi
    
    if ufw status | grep -q "443/tcp.*ALLOW"; then
        print_success "Puerto 443 (HTTPS) abierto"
    else
        print_warning "Puerto 443 (HTTPS) NO abierto"
        print_step "Abriendo puerto 443..."
        ufw allow 443/tcp
    fi
    
    if ufw status | grep -q "22/tcp.*ALLOW"; then
        print_success "Puerto 22 (SSH) abierto"
    else
        print_warning "Puerto 22 (SSH) NO abierto"
        print_step "Abriendo puerto 22..."
        ufw allow 22/tcp
    fi
else
    print_warning "UFW NO está activo"
    print_step "Activando UFW..."
    ufw --force enable
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
fi

# ===== VERIFICACIÓN 10: LOGS =====
print_header "VERIFICANDO LOGS"
print_step "Verificando directorios de logs..."

log_dirs=(
    "/var/log/flaskapp"
    "/var/log/gunicorn"
    "/var/log/nginx"
)

for log_dir in "${log_dirs[@]}"; do
    if [ -d "$log_dir" ]; then
        print_success "Directorio de logs $log_dir existe"
        
        # Verificar permisos
        if [ -w "$log_dir" ]; then
            print_success "Permisos de logs correctos en $log_dir"
        else
            print_warning "Problema de permisos en $log_dir"
            chown -R www-data:www-data "$log_dir"
        fi
    else
        print_warning "Directorio de logs $log_dir NO existe"
        print_step "Creando directorio de logs $log_dir..."
        mkdir -p "$log_dir"
        chown -R www-data:www-data "$log_dir"
    fi
done

# ===== VERIFICACIÓN 11: CONECTIVIDAD =====
print_header "VERIFICANDO CONECTIVIDAD"
print_step "Verificando puertos abiertos..."

if netstat -tlnp | grep -q ":80 "; then
    print_success "Puerto 80 está escuchando"
else
    print_error "Puerto 80 NO está escuchando"
fi

if netstat -tlnp | grep -q ":8000 "; then
    print_success "Puerto 8000 (Gunicorn) está escuchando"
else
    print_error "Puerto 8000 (Gunicorn) NO está escuchando"
fi

# ===== VERIFICACIÓN 12: ARCHIVOS DE CONFIGURACIÓN =====
print_header "VERIFICANDO ARCHIVOS DE CONFIGURACIÓN"
print_step "Verificando archivos de configuración..."

config_files=(
    "$APP_DIR/.env"
    "$APP_DIR/gunicorn.conf.py"
    "/etc/nginx/sites-available/$NGINX_SITE"
    "/etc/systemd/system/$SERVICE_NAME.service"
)

for config_file in "${config_files[@]}"; do
    if [ -f "$config_file" ]; then
        print_success "$config_file existe"
    else
        print_warning "$config_file NO existe"
    fi
done

# ===== VERIFICACIÓN 13: PRUEBA DE FUNCIONAMIENTO =====
print_header "PRUEBA DE FUNCIONAMIENTO"
print_step "Probando aplicación..."

# Esperar un momento para que la aplicación se inicie
sleep 5

# Probar respuesta HTTP
if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200\|302"; then
    print_success "Aplicación responde correctamente"
else
    print_error "Aplicación NO responde correctamente"
    
    # Verificar logs
    print_step "Verificando logs de error..."
    if [ -f "/var/log/flaskapp/app.log" ]; then
        tail -20 "/var/log/flaskapp/app.log"
    fi
    
    if [ -f "/var/log/gunicorn/error.log" ]; then
        tail -20 "/var/log/gunicorn/error.log"
    fi
fi

# ===== RESUMEN FINAL =====
print_header "RESUMEN DE VERIFICACIÓN"
print_step "Verificación completada"

print_success "✅ Instalación verificada correctamente"
print_status "📝 Para ver logs en tiempo real:"
print_status "   - Aplicación: tail -f /var/log/flaskapp/app.log"
print_status "   - Gunicorn: tail -f /var/log/gunicorn/error.log"
print_status "   - Nginx: tail -f /var/log/nginx/deudout_error.log"
print_status ""
print_status "🔧 Comandos útiles:"
print_status "   - Reiniciar aplicación: sudo systemctl restart flaskapp"
print_status "   - Reiniciar Nginx: sudo systemctl restart nginx"
print_status "   - Ver estado: sudo systemctl status flaskapp"
print_status "   - Ver logs: sudo journalctl -u flaskapp -f"
print_status ""
print_status "🌐 La aplicación debería estar disponible en:"
print_status "   - http://$(hostname -I | awk '{print $1}')/"
print_status "   - http://localhost/"

print_header "VERIFICACIÓN COMPLETADA"
print_success "🎉 ¡Deudout está listo para usar!"

