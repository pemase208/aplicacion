#!/bin/bash

# ===== SCRIPT SIMPLE DE SUBIDA SFTP =====
# Sube archivos específicos vía SFTP de forma rápida

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Subida SFTP Rápida para DEUDOUT${NC}"
echo "=================================="

# Configuración rápida
read -p "IP del VPS: " VPS_IP
read -p "Usuario (root): " VPS_USER
read -p "Puerto (22): " VPS_PORT
VPS_PORT=${VPS_PORT:-22}

echo ""
echo -e "${BLUE}📁 Subiendo archivos...${NC}"

# Crear directorio remoto y subir archivos
sftp -P "$VPS_PORT" "$VPS_USER@$VPS_IP" << EOF
cd /tmp
mkdir -p deudout_deploy
cd deudout_deploy
put app.py
put models.py
put requirements.txt
put init_db.py
put crear_admin.py
put poblar_entidades_financieras.py
put -r utils/
put -r static/
put -r templates/
put -r instance/
put .env.example
put README.txt
put gunicorn.conf.py
put nginx.conf
put install_ubuntu24_optimized.sh
bye
EOF

echo ""
echo -e "${GREEN}✅ Archivos subidos exitosamente${NC}"
echo ""
echo "🔧 Próximos pasos en el VPS:"
echo "   cd /tmp/deudout_deploy"
echo "   chmod +x install_ubuntu24_optimized.sh"
echo "   ./install_ubuntu24_optimized.sh"
echo ""
echo -e "${BLUE}🌐 La aplicación estará disponible en: http://$VPS_IP${NC}"


