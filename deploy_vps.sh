#!/bin/bash

# ===== SCRIPT DE DESPLIEGUE DEUDOUT VPS =====
# Script simplificado para desplegar la aplicación en VPS

echo "🚀 Iniciando despliegue de DEUDOUT en VPS..."
echo "=========================================="

# Variables configurables
VPS_IP="TU_IP_DEL_VPS"
VPS_USER="root"
APP_NAME="deudout"
APP_DIR="/home/${APP_NAME}"

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

# Verificar conexión SSH
print_status "Verificando conexión SSH..."
if ! ssh -o ConnectTimeout=10 ${VPS_USER}@${VPS_IP} "echo 'Conexión SSH exitosa'" 2>/dev/null; then
    print_error "No se puede conectar al VPS. Verifica:"
    echo "  1. La IP del VPS es correcta"
    echo "  2. El usuario SSH es correcto"
    echo "  3. Las claves SSH están configuradas"
    echo "  4. El firewall permite conexiones SSH"
    exit 1
fi

print_success "Conexión SSH establecida"

# Crear directorio de la aplicación
print_status "Creando directorio de la aplicación..."
ssh ${VPS_USER}@${VPS_IP} "mkdir -p ${APP_DIR}"

# Crear usuario deudout si no existe
print_status "Configurando usuario deudout..."
ssh ${VPS_USER}@${VPS_IP} "
if ! id 'deudout' &>/dev/null; then
    useradd -m -s /bin/bash deudout
    echo 'Usuario deudout creado'
else
    echo 'Usuario deudout ya existe'
fi
"

# Cambiar propietario del directorio
ssh ${VPS_USER}@${VPS_IP} "chown -R deudout:deudout ${APP_DIR}"

# Instalar dependencias del sistema
print_status "Instalando dependencias del sistema..."
ssh ${VPS_USER}@${VPS_IP} "
apt update && apt install -y python3 python3-pip python3-venv nginx supervisor
"

# Crear entorno virtual
print_status "Creando entorno virtual..."
ssh ${VPS_USER}@${VPS_IP} "
cd ${APP_DIR}
python3 -m venv venv
chown -R deudout:deudout venv
"

# Copiar archivos de la aplicación
print_status "Copiando archivos de la aplicación..."
scp -r ./* ${VPS_USER}@${VPS_IP}:${APP_DIR}/

# Instalar dependencias Python
print_status "Instalando dependencias Python..."
ssh ${VPS_USER}@${VPS_IP} "
cd ${APP_DIR}
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
"

# Configurar variables de entorno
print_status "Configurando variables de entorno..."
ssh ${VPS_USER}@${VPS_IP} "
cd ${APP_DIR}
cat > .env << 'EOF'
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=X0001388ed0&
DATABASE_URL=sqlite:///deudout.db
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password
EOF
chown deudout:deudout .env
"

# Inicializar base de datos
print_status "Inicializando base de datos..."
ssh ${VPS_USER}@${VPS_IP} "
cd ${APP_DIR}
source venv/bin/activate
python init_db.py
python poblar_entidades_financieras.py
chown -R deudout:deudout instance/
"

# Configurar Gunicorn
print_status "Configurando Gunicorn..."
ssh ${VPS_USER}@${VPS_IP} "
systemctl cat deudout
ls -l /etc/systemd/system/deudout.service
systemctl list-unit-files | grep deudout
[Service]
User=deudout
Group=deudout
WorkingDirectory=${APP_DIR}
Environment=PATH=${APP_DIR}/venv/bin
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers 3 --bind unix:deudout.sock -m 007 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF
"

# Configurar Nginx
print_status "Configurando Nginx..."
ssh ${VPS_USER}@${VPS_IP} "
cat > /etc/nginx/sites-available/deudout << 'EOF'
server {
    listen 80;
    server_name ${VPS_IP};

    location / {
        include proxy_params;
        proxy_pass http://unix:${APP_DIR}/deudout.sock;
    }

    location /static {
        alias ${APP_DIR}/static;
    }
}
EOF

ln -sf /etc/nginx/sites-available/deudout /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
"

# Iniciar servicios
print_status "Iniciando servicios..."
ssh ${VPS_USER}@${VPS_IP} "
systemctl daemon-reload
systemctl enable deudout
systemctl start deudout
systemctl restart nginx
"

# Configurar firewall
print_status "Configurando firewall..."
ssh ${VPS_USER}@${VPS_IP} "
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable
"

# Verificar estado
print_status "Verificando estado de los servicios..."
ssh ${VPS_USER}@${VPS_IP} "
echo 'Estado de DEUDOUT:'
systemctl status deudout --no-pager -l
echo ''
echo 'Estado de Nginx:'
systemctl status nginx --no-pager -l
echo ''
echo 'Puertos abiertos:'
ufw status
"

print_success "¡Despliegue completado!"
echo ""
echo "🌐 Tu aplicación está disponible en: http://${VPS_IP}"
echo ""
echo "📋 Próximos pasos:"
echo "  1. Accede a http://${VPS_IP}"
echo "  2. Usuario admin: admin"
echo "  3. Contraseña: admin123"
echo "  4. Cambia la contraseña del admin inmediatamente"
echo ""
echo "🔧 Comandos útiles:"
echo "  - Ver logs: ssh ${VPS_USER}@${VPS_IP} 'journalctl -u deudout -f'"
echo "  - Reiniciar app: ssh ${VPS_USER}@${VPS_IP} 'systemctl restart deudout'"
echo "  - Ver estado: ssh ${VPS_USER}@${VPS_IP} 'systemctl status deudout'"
echo ""
print_warning "IMPORTANTE: Configura las variables de email en ${APP_DIR}/.env"
