#!/bin/bash

# ===== VERIFICACIÓN RÁPIDA DE SALUD DEUDOUT =====
# Script para verificar que la aplicación esté funcionando correctamente

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
SERVER_IP=$(hostname -I | awk '{print $1}')
HEALTH_SCORE=0
TOTAL_CHECKS=0

# Función para incrementar puntuación
increment_score() {
    HEALTH_SCORE=$((HEALTH_SCORE + 1))
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
}

print_header "VERIFICACIÓN DE SALUD DEUDOUT"
echo "Servidor: $SERVER_IP"
echo "Fecha: $(date)"
echo ""

# 1. Verificar que la aplicación esté instalada
print_status "1. Verificando instalación..."
if [ -d "$APP_DIR" ]; then
    print_success "✓ Directorio de aplicación encontrado: $APP_DIR"
    increment_score
else
    print_error "✗ Directorio de aplicación no encontrado: $APP_DIR"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# 2. Verificar archivos principales
print_status "2. Verificando archivos principales..."
if [ -f "$APP_DIR/app.py" ]; then
    print_success "✓ app.py encontrado"
    increment_score
else
    print_error "✗ app.py no encontrado"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

if [ -f "$APP_DIR/requirements.txt" ]; then
    print_success "✓ requirements.txt encontrado"
    increment_score
else
    print_error "✗ requirements.txt no encontrado"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

if [ -f "$APP_DIR/.env" ]; then
    print_success "✓ .env encontrado"
    increment_score
else
    print_error "✗ .env no encontrado"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# 3. Verificar entorno virtual
print_status "3. Verificando entorno virtual..."
if [ -d "$APP_DIR/venv" ]; then
    print_success "✓ Entorno virtual encontrado"
    increment_score
else
    print_error "✗ Entorno virtual no encontrado"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# 4. Verificar servicios del sistema
print_status "4. Verificando servicios del sistema..."

# Verificar servicio deudout
if systemctl is-active --quiet "$APP_NAME"; then
    print_success "✓ Servicio $APP_NAME está activo"
    increment_score
else
    print_error "✗ Servicio $APP_NAME no está activo"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# Verificar Nginx
if systemctl is-active --quiet nginx; then
    print_success "✓ Servicio Nginx está activo"
    increment_score
else
    print_error "✗ Servicio Nginx no está activo"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# Verificar Supervisor
if systemctl is-active --quiet supervisor; then
    print_success "✓ Servicio Supervisor está activo"
    increment_score
else
    print_warning "⚠ Servicio Supervisor no está activo (opcional)"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# 5. Verificar puertos
print_status "5. Verificando puertos..."

# Verificar puerto 80 (HTTP)
if netstat -tlnp | grep -q ":80 "; then
    print_success "✓ Puerto 80 (HTTP) abierto"
    increment_score
else
    print_error "✗ Puerto 80 (HTTP) no está abierto"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# Verificar puerto 443 (HTTPS) si existe
if netstat -tlnp | grep -q ":443 "; then
    print_success "✓ Puerto 443 (HTTPS) abierto"
    increment_score
else
    print_warning "⚠ Puerto 443 (HTTPS) no está abierto (normal si no hay SSL)"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# 6. Verificar base de datos
print_status "6. Verificando base de datos..."
DB_FILES=$(find "$APP_DIR" -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" 2>/dev/null)
if [ -n "$DB_FILES" ]; then
    print_success "✓ Archivos de base de datos encontrados"
    increment_score
else
    print_error "✗ No se encontraron archivos de base de datos"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# 7. Verificar directorios importantes
print_status "7. Verificando directorios importantes..."
if [ -d "$APP_DIR/static" ]; then
    print_success "✓ Directorio static encontrado"
    increment_score
else
    print_error "✗ Directorio static no encontrado"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

if [ -d "$APP_DIR/templates" ]; then
    print_success "✓ Directorio templates encontrado"
    increment_score
else
    print_error "✗ Directorio templates no encontrado"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

if [ -d "$APP_DIR/utils" ]; then
    print_success "✓ Directorio utils encontrado"
    increment_score
else
    print_error "✗ Directorio utils no encontrado"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# 8. Verificar logs
print_status "8. Verificando logs..."
if [ -d "$APP_DIR/logs" ]; then
    print_success "✓ Directorio de logs encontrado"
    increment_score
else
    print_warning "⚠ Directorio de logs no encontrado (se creará automáticamente)"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# 9. Verificar firewall
print_status "9. Verificando firewall..."
if ufw status | grep -q "Status: active"; then
    print_success "✓ Firewall UFW activo"
    increment_score
else
    print_warning "⚠ Firewall UFW no está activo"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# 10. Verificar conectividad web
print_status "10. Verificando conectividad web..."
if curl -s -o /dev/null -w "%{http_code}" "http://localhost" | grep -q "200\|302"; then
    print_success "✓ Aplicación responde en localhost"
    increment_score
else
    print_error "✗ Aplicación no responde en localhost"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# 11. Verificar certificados SSL (si existen)
print_status "11. Verificando certificados SSL..."
if command -v certbot &> /dev/null; then
    SSL_CERTS=$(certbot certificates 2>/dev/null | grep -c "VALID" || echo "0")
    if [ "$SSL_CERTS" -gt 0 ]; then
        print_success "✓ Certificados SSL válidos encontrados: $SSL_CERTS"
        increment_score
    else
        print_warning "⚠ No hay certificados SSL válidos (normal si no se configuró)"
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    fi
else
    print_warning "⚠ Certbot no está instalado (normal si no se configuró SSL)"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# 12. Verificar permisos
print_status "12. Verificando permisos..."
if [ -r "$APP_DIR" ] && [ -w "$APP_DIR" ]; then
    print_success "✓ Permisos de directorio correctos"
    increment_score
else
    print_error "✗ Problemas con permisos del directorio"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
fi

# Calcular puntuación final
PERCENTAGE=$((HEALTH_SCORE * 100 / TOTAL_CHECKS))

print_header "RESULTADO FINAL"
echo "Puntuación: $HEALTH_SCORE/$TOTAL_CHECKS ($PERCENTAGE%)"
echo ""

if [ $PERCENTAGE -ge 90 ]; then
    print_success "🎉 ¡EXCELENTE! Tu aplicación DEUDOUT está funcionando perfectamente"
    echo "   - Todos los servicios están activos"
    echo "   - La aplicación responde correctamente"
    echo "   - La configuración es óptima"
elif [ $PERCENTAGE -ge 75 ]; then
    print_success "✅ ¡BUENO! Tu aplicación DEUDOUT está funcionando bien"
    echo "   - La mayoría de servicios están activos"
    echo "   - La aplicación responde correctamente"
    echo "   - Algunas configuraciones opcionales faltan"
elif [ $PERCENTAGE -ge 50 ]; then
    print_warning "⚠️  ¡ATENCIÓN! Tu aplicación DEUDOUT tiene algunos problemas"
    echo "   - Algunos servicios no están funcionando"
    echo "   - La aplicación puede no responder correctamente"
    echo "   - Revisa los errores mostrados arriba"
else
    print_error "❌ ¡CRÍTICO! Tu aplicación DEUDOUT tiene problemas graves"
    echo "   - Muchos servicios no están funcionando"
    echo "   - La aplicación no responde"
    echo "   - Revisa urgentemente la instalación"
fi

echo ""
print_header "INFORMACIÓN DE ACCESO"
echo "🌐 URL de acceso: http://$SERVER_IP"
echo "👤 Usuario admin: admin"
echo "🔑 Contraseña: admin123"
echo ""

print_header "PRÓXIMOS PASOS"
if [ $PERCENTAGE -ge 75 ]; then
    echo "✅ Tu aplicación está lista para usar"
    echo "📝 Recomendaciones:"
    echo "   1. Accede a la aplicación y cambia la contraseña del admin"
    echo "   2. Configura las variables de email en $APP_DIR/.env"
    echo "   3. Haz un backup inicial"
    echo "   4. Configura SSL si tienes dominio"
else
    echo "🔧 Tu aplicación necesita atención"
    echo "📝 Acciones requeridas:"
    echo "   1. Revisa los errores mostrados arriba"
    echo "   2. Ejecuta: sudo systemctl status $APP_NAME"
    echo "   3. Verifica los logs: sudo journalctl -u $APP_NAME -f"
    echo "   4. Considera reinstalar si los problemas persisten"
fi

echo ""
print_header "COMANDOS ÚTILES"
echo "🔍 Ver estado: sudo systemctl status $APP_NAME"
echo "📋 Ver logs: sudo journalctl -u $APP_NAME -f"
echo "🚀 Reiniciar: sudo systemctl restart $APP_NAME"
echo "🛠️  Mantenimiento: sudo ./maintenance_backup.sh"
echo ""

if [ $PERCENTAGE -ge 75 ]; then
    print_success "¡Tu aplicación DEUDOUT está lista para usar! 🚀"
else
    print_warning "Revisa y corrige los problemas antes de usar la aplicación"
fi
