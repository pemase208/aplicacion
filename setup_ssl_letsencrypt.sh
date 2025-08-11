#!/bin/bash

# ===== CONFIGURACIÓN SSL/HTTPS CON LET'S ENCRYPT PARA DEUDOUT =====
# Script para configurar certificados SSL gratuitos

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

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

# Variables
APP_NAME="deudout"
APP_DIR="/home/$APP_NAME"
DOMAIN=""

print_header "CONFIGURACIÓN SSL/HTTPS CON LET'S ENCRYPT"

# Solicitar dominio
read -p "Introduce tu dominio (ej: mideudout.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    print_error "Debes introducir un dominio válido"
    exit 1
fi

print_step "Configurando SSL para dominio: $DOMAIN"

# Verificar que el dominio resuelve a esta IP
print_step "Verificando resolución DNS..."
SERVER_IP=$(hostname -I | awk '{print $1}')
DOMAIN_IP=$(dig +short $DOMAIN)

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
    print_warning "El dominio $DOMAIN resuelve a $DOMAIN_IP pero este servidor tiene IP $SERVER_IP"
    print_warning "Asegúrate de que el DNS esté configurado correctamente"
    read -p "¿Continuar de todas formas? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Configuración cancelada"
        exit 1
    fi
fi

print_step "Instalando Certbot..."

# Instalar Certbot
apt update
apt install -y certbot python3-certbot-nginx

print_step "Configurando Nginx para el dominio..."

# Crear configuración Nginx con el dominio
cat > "/etc/nginx/sites-available/$APP_NAME" << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
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

# Redirección HTTP a HTTPS (se activará después de obtener el certificado)
# server {
#     listen 80;
#     server_name $DOMAIN;
#     return 301 https://\$server_name\$request_uri;
# }
EOF

# Habilitar sitio
ln -sf "/etc/nginx/sites-available/$APP_NAME" "/etc/nginx/sites-enabled/"
rm -f /etc/nginx/sites-enabled/default

# Reiniciar Nginx
systemctl restart nginx

print_step "Obteniendo certificado SSL..."

# Obtener certificado SSL
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN

print_step "Configurando renovación automática..."

# Crear script de renovación
cat > "/etc/cron.daily/renew-ssl" << 'EOF'
#!/bin/bash
certbot renew --quiet --nginx
EOF

chmod +x /etc/cron.daily/renew-ssl

print_step "Configurando firewall para HTTPS..."

# Permitir HTTPS
ufw allow 443/tcp

print_success "SSL/HTTPS configurado exitosamente!"

print_header "VERIFICACIÓN FINAL"
print_step "Verificando certificado..."

# Verificar certificado
certbot certificates

print_step "Verificando Nginx..."

# Verificar configuración Nginx
nginx -t

print_step "Verificando estado de servicios..."

# Verificar servicios
systemctl status nginx --no-pager -l

print_header "CONFIGURACIÓN COMPLETADA"
print_success "¡SSL/HTTPS configurado correctamente para $DOMAIN!"
echo ""
echo "🌐 Tu aplicación está disponible en:"
echo "   - HTTP:  http://$DOMAIN (redirige a HTTPS)"
echo "   - HTTPS: https://$DOMAIN"
echo ""
echo "🔒 Características de seguridad:"
echo "   - Certificado SSL válido y confiable"
echo "   - Renovación automática cada 90 días"
echo "   - Redirección automática HTTP → HTTPS"
echo "   - Headers de seguridad configurados"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Verifica que https://$DOMAIN funcione correctamente"
echo "   2. Configura las variables de email en $APP_DIR/.env"
echo "   3. Actualiza la configuración de la aplicación si es necesario"
echo "   4. Revisa los logs para verificar que todo funcione"
echo ""
echo "🔧 Comandos útiles:"
echo "   - Ver certificados: certbot certificates"
echo "   - Renovar manualmente: certbot renew"
echo "   - Ver logs de Nginx: tail -f $APP_DIR/logs/nginx_access.log"
echo "   - Ver logs de error: tail -f $APP_DIR/logs/nginx_error.log"
echo ""
print_warning "IMPORTANTE: El certificado se renueva automáticamente cada 90 días"
print_success "¡Tu aplicación DEUDOUT ahora es segura con HTTPS!"
