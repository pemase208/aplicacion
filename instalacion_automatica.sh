#!/bin/bash

# 🎁 Script de Instalación Automática - Ubuntu 24.04 + Flask App
# Para usuarios sin conocimientos técnicos

echo "🎁 ========================================="
echo "   INSTALACIÓN AUTOMÁTICA UBUNTU 24.04"
echo "   APLICACIÓN FLASK PARA ABOGADOS"
echo " ========================================="
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Verificar si se ejecuta como root
if [ "$EUID" -ne 0 ]; then
    print_error "Este script debe ejecutarse como root (sudo)"
    exit 1
fi

# PASO 1: Actualizar sistema
print_status "Paso 1/11: Actualizando sistema..."
apt update && apt upgrade -y
print_success "Sistema actualizado"

# PASO 2: Instalar Python y dependencias
print_status "Paso 2/11: Instalando Python y herramientas..."
apt install -y python3 python3-pip python3-venv python3-dev build-essential libssl-dev libffi-dev python3-setuptools unzip curl wget git
print_success "Python y herramientas instaladas"

# PASO 3: Crear alias para python
print_status "Paso 3/11: Configurando alias de Python..."
echo "alias python=python3" >> ~/.bashrc
echo "alias pip=pip3" >> ~/.bashrc
source ~/.bashrc
print_success "Alias de Python configurado"

# PASO 4: Crear usuario y directorio para la aplicación
print_status "Paso 4/11: Creando usuario y directorio para la aplicación..."
useradd -m -s /bin/bash flaskapp
mkdir -p /home/flaskapp
chown flaskapp:flaskapp /home/flaskapp
print_success "Usuario y directorio creados"

# PASO 5: Verificar si existe el archivo ZIP
print_status "Paso 5/11: Verificando archivo de la aplicación..."
if [ ! -f "/home/flaskapp/flask_app_clean.zip" ]; then
    print_warning "No se encontró flask_app_clean.zip en /home/flaskapp/"
    print_warning "Por favor, sube el archivo antes de continuar"
    print_warning "Puedes usar: scp flask_app_clean.zip root@TU_IP:/home/flaskapp/"
    exit 1
fi
print_success "Archivo de aplicación encontrado"

# PASO 6: Descomprimir aplicación
print_status "Paso 6/11: Descomprimiendo aplicación..."
cd /home/flaskapp
unzip -o flask_app_clean.zip
chown -R flaskapp:flaskapp /home/flaskapp
print_success "Aplicación descomprimida"

# PASO 7: Configurar entorno virtual
print_status "Paso 7/11: Configurando entorno virtual..."
cd /home/flaskapp/flask_app_clean
sudo -u flaskapp python3 -m venv venv
print_success "Entorno virtual creado"

# PASO 8: Instalar dependencias
print_status "Paso 8/11: Instalando dependencias de Python..."
sudo -u flaskapp /home/flaskapp/flask_app_clean/venv/bin/pip install --upgrade pip
sudo -u flaskapp /home/flaskapp/flask_app_clean/venv/bin/pip install -r requirements.txt
sudo -u flaskapp /home/flaskapp/flask_app_clean/venv/bin/pip install gunicorn
print_success "Dependencias instaladas"

# PASO 9: Configurar variables de entorno
print_status "Paso 9/11: Configurando variables de entorno..."
cd /home/flaskapp/flask_app_clean
sudo -u flaskapp cp config.env.example .env

# Generar clave secreta aleatoria
SECRET_KEY=$(openssl rand -hex 32)
sudo -u flaskapp sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
sudo -u flaskapp sed -i "s/FLASK_ENV=.*/FLASK_ENV=production/" .env

print_warning "IMPORTANTE: Edita el archivo .env para configurar email:"
print_warning "nano /home/flaskapp/flask_app_clean/.env"
print_warning "Configura EMAIL_USER y EMAIL_PASS con tus credenciales de Gmail"
print_success "Variables de entorno configuradas"

# PASO 10: Inicializar base de datos
print_status "Paso 10/11: Inicializando base de datos..."
cd /home/flaskapp/flask_app_clean
sudo -u flaskapp /home/flaskapp/flask_app_clean/venv/bin/python init_db.py
print_success "Base de datos inicializada"

# PASO 11: Configurar servicios
print_status "Paso 11/11: Configurando servicios..."

# Configurar servicio systemd
cp flaskapp.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable flaskapp
systemctl start flaskapp

# Instalar y configurar Nginx
apt install -y nginx
cp nginx.conf /etc/nginx/sites-available/flaskapp
ln -sf /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl enable nginx
systemctl start nginx

# Configurar firewall
apt install -y ufw
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

print_success "Servicios configurados"

# Verificar servicios
print_status "Verificando servicios..."
if systemctl is-active --quiet flaskapp; then
    print_success "Servicio Flask: ACTIVO"
else
    print_error "Servicio Flask: INACTIVO"
fi

if systemctl is-active --quiet nginx; then
    print_success "Servicio Nginx: ACTIVO"
else
    print_error "Servicio Nginx: INACTIVO"
fi

if ufw status | grep -q "Status: active"; then
    print_success "Firewall: ACTIVO"
else
    print_error "Firewall: INACTIVO"
fi

# Obtener IP del servidor
SERVER_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "🎉 ========================================="
echo "   ¡INSTALACIÓN COMPLETADA EXITOSAMENTE!"
echo " ========================================="
echo ""
echo "📋 INFORMACIÓN IMPORTANTE:"
echo "   URL de acceso: http://$SERVER_IP"
echo "   Usuario admin: admin"
echo "   Contraseña: admin123"
echo ""
echo "🔧 PRÓXIMOS PASOS:"
echo "   1. Edita la configuración de email:"
echo "      nano /home/flaskapp/flask_app_clean/.env"
echo ""
echo "   2. Cambia la contraseña del admin:"
echo "      cd /home/flaskapp/flask_app_clean"
echo "      source venv/bin/activate"
echo "      python crear_admin.py"
echo ""
echo "   3. Accede a la aplicación:"
echo "      http://$SERVER_IP"
echo ""
echo "📞 COMANDOS ÚTILES:"
echo "   Ver logs: sudo journalctl -u flaskapp -f"
echo "   Reiniciar: sudo systemctl restart flaskapp"
echo "   Estado: sudo systemctl status flaskapp"
echo ""
echo "🎁 ¡Tu aplicación está lista para tu abogado!"
echo " ========================================="







