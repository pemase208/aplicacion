# 🚀 INSTALACIÓN DEUDOUT - UBUNTU 24.04

## 📋 REQUISITOS PREVIOS

- **VPS con Ubuntu 24.04** (limpio, recién instalado)
- **Acceso root** al servidor
- **Conexión a internet** estable
- **Archivos del proyecto** DeudOut

## 🔧 INSTALACIÓN PASO A PASO

### **PASO 1: Preparar el VPS**

```bash
# Conectarse al VPS como root
ssh root@TU_IP_DEL_VPS

# Actualizar el sistema
apt update && apt upgrade -y

# Instalar dependencias básicas
apt install -y curl wget git unzip
```

### **PASO 2: Subir archivos del proyecto**

```bash
# Crear directorio temporal
mkdir -p /tmp/deudout_install
cd /tmp/deudout_install

# Subir archivos vía SFTP desde tu computadora
# O usar git clone si tienes repositorio
```

### **PASO 3: Ejecutar instalación automática**

```bash
# Dar permisos de ejecución
chmod +x install_ubuntu24_optimized.sh

# Ejecutar instalación (primera fase)
sudo bash install_ubuntu24_optimized.sh
```

### **PASO 4: Copiar archivos de la aplicación**

```bash
# Copiar todos los archivos del proyecto
cp -r /tmp/deudout_install/* /var/www/flaskapp/

# Dar permisos correctos
chown -R www-data:www-data /var/www/flaskapp
chmod -R 755 /var/www/flaskapp
```

### **PASO 5: Completar instalación**

```bash
# Ejecutar segunda fase de instalación
sudo bash install_ubuntu24_optimized.sh --continue
```

## 📁 ESTRUCTURA FINAL

```
/var/www/flaskapp/
├── app.py                 # Aplicación principal
├── models.py             # Modelos de base de datos
├── requirements.txt      # Dependencias Python
├── gunicorn.conf.py     # Configuración Gunicorn
├── nginx.conf           # Configuración Nginx
├── venv/                # Entorno virtual Python
├── static/              # Archivos estáticos
├── templates/           # Plantillas HTML
├── instance/            # Base de datos SQLite
└── uploads/             # Archivos subidos
```

## 🌐 ACCESO A LA APLICACIÓN

- **URL**: `http://TU_IP_DEL_VPS`
- **Usuario admin**: `pedro`
- **Contraseña**: `admin1234`

## 🔧 COMANDOS ÚTILES

### **Ver estado de servicios**
```bash
# Estado de Flask
sudo systemctl status flaskapp

# Estado de Nginx
sudo systemctl status nginx

# Ver logs en tiempo real
sudo journalctl -u flaskapp -f
```

### **Reiniciar servicios**
```bash
# Reiniciar aplicación
sudo systemctl restart flaskapp

# Reiniciar Nginx
sudo systemctl restart nginx

# Recargar configuración
sudo systemctl reload nginx
```

### **Ver logs**
```bash
# Logs de Flask
sudo tail -f /var/log/flaskapp/app.log

# Logs de Nginx
sudo tail -f /var/log/nginx/error.log

# Logs de Gunicorn
sudo tail -f /var/log/gunicorn/error.log
```

## 📝 CONFIGURACIÓN AVANZADA

### **Variables de entorno**
```bash
# Editar configuración
sudo nano /etc/flaskapp.env

# Variables disponibles:
SECRET_KEY=tu_clave_secreta
FLASK_ENV=production
DATABASE_URL=sqlite:////var/www/flaskapp/mibasedatos.db
SESSION_COOKIE_SECURE=False
FORCE_HTTP=1
```

### **Configurar SSL/HTTPS**
```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tudominio.com

# Renovar automáticamente
sudo crontab -e
# Añadir: 0 12 * * * /usr/bin/certbot renew --quiet
```

### **Configurar firewall**
```bash
# Ver estado
sudo ufw status

# Abrir puertos adicionales
sudo ufw allow 8000  # Si usas puerto personalizado

# Ver reglas
sudo ufw status numbered
```

## 🚨 SOLUCIÓN DE PROBLEMAS

### **Error: "Unit flaskapp.service not found"**
```bash
# Verificar que el archivo existe
ls -la /etc/systemd/system/flaskapp.service

# Si no existe, recrear el servicio
sudo bash install_ubuntu24_optimized.sh
```

### **Error: "No such user: flaskapp"**
```bash
# El archivo del servicio tiene usuario incorrecto
# Verificar contenido:
sudo cat /etc/systemd/system/flaskapp.service

# Debe tener: User=www-data, Group=www-data
```

### **Error: "ModuleNotFoundError"**
```bash
# Activar entorno virtual y reinstalar dependencias
cd /var/www/flaskapp
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

### **Error: "Permission denied"**
```bash
# Corregir permisos
sudo chown -R www-data:www-data /var/www/flaskapp
sudo chmod -R 755 /var/www/flaskapp
```

### **Nginx no funciona**
```bash
# Verificar configuración
sudo nginx -t

# Ver logs de error
sudo tail -f /var/log/nginx/error.log

# Reiniciar Nginx
sudo systemctl restart nginx
```

## 📊 MONITOREO Y MANTENIMIENTO

### **Verificar salud del sistema**
```bash
# Estado de todos los servicios
sudo systemctl status flaskapp nginx

# Uso de recursos
htop
df -h
free -h

# Puertos abiertos
sudo netstat -tlnp
```

### **Backup de base de datos**
```bash
# Crear backup
sudo cp /var/www/flaskapp/mibasedatos.db /backup/deudout_$(date +%Y%m%d_%H%M%S).db

# Restaurar backup
sudo cp /backup/deudout_20241201_120000.db /var/www/flaskapp/mibasedatos.db
sudo chown www-data:www-data /var/www/flaskapp/mibasedatos.db
```

### **Actualizar aplicación**
```bash
# Detener servicio
sudo systemctl stop flaskapp

# Hacer backup
sudo cp -r /var/www/flaskapp /backup/flaskapp_$(date +%Y%m%d_%H%M%S)

# Copiar nuevos archivos
sudo cp -r /ruta/nuevos/archivos/* /var/www/flaskapp/

# Corregir permisos
sudo chown -R www-data:www-data /var/www/flaskapp

# Reiniciar servicio
sudo systemctl start flaskapp
```

## 🔒 SEGURIDAD

### **Cambiar contraseña admin**
1. Acceder a la aplicación
2. Ir a "Cambiar Contraseña"
3. Usar contraseña fuerte

### **Configurar firewall**
```bash
# Solo permitir SSH, HTTP y HTTPS
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### **Actualizar sistema regularmente**
```bash
# Actualizar semanalmente
sudo apt update && apt upgrade -y

# Reiniciar si es necesario
sudo reboot
```

## 📞 SOPORTE

### **Logs importantes**
- **Flask**: `/var/log/flaskapp/app.log`
- **Nginx**: `/var/log/nginx/error.log`
- **Systemd**: `sudo journalctl -u flaskapp`

### **Comandos de diagnóstico**
```bash
# Verificar servicios
sudo systemctl list-units --failed

# Verificar puertos
sudo ss -tlnp

# Verificar permisos
ls -la /var/www/flaskapp/
```

## ✅ VERIFICACIÓN FINAL

Después de la instalación, verifica:

1. ✅ **Servicio Flask activo**: `sudo systemctl status flaskapp`
2. ✅ **Nginx funcionando**: `sudo systemctl status nginx`
3. ✅ **Puerto 80 abierto**: `sudo netstat -tlnp | grep :80`
4. ✅ **Aplicación accesible**: `http://TU_IP_DEL_VPS`
5. ✅ **Login admin funciona**: Usuario `pedro`, Password `admin1234`

## 🎯 PRÓXIMOS PASOS

1. **Cambiar contraseña del admin** inmediatamente
2. **Configurar dominio** si tienes uno
3. **Configurar SSL/HTTPS** para producción
4. **Configurar backup automático** de la base de datos
5. **Monitorear logs** regularmente

---

**¡DeudOut está listo para usar en producción! 🚀**


