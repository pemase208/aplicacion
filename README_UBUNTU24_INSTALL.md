# 🚀 INSTALACIÓN COMPLETA DEUDOUT EN UBUNTU 24.04

## 📋 Descripción

Este documento contiene las instrucciones completas para instalar la aplicación DEUDOUT desde cero en un entorno Ubuntu 24.04 limpio. La aplicación incluye:

- **Sistema de roles** (admin, usuario, lector)
- **Gestión de usuarios y bancos**
- **Formularios RPC, Doc9, y gestión de derechos RGPD**
- **Consultas externas** a BOE, TEU, RPC
- **Generación de PDFs y documentos Word**
- **Sistema de logging y analytics**
- **Interfaz moderna** con Bootstrap 5
- **Consulta Total Integrada** (nueva funcionalidad)

## 🎯 Requisitos Previos

### Sistema Operativo
- **Ubuntu 24.04 LTS** (recomendado)
- **Ubuntu 22.04 LTS** (compatible)
- **Ubuntu 20.04 LTS** (compatible con limitaciones)

### Hardware Mínimo
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disco**: 20 GB de espacio libre
- **Red**: Conexión a Internet

### Software Requerido
- **Python 3.10+** (se instala automáticamente)
- **Nginx** (se instala automáticamente)
- **SQLite** (incluido con Python)

## 🛠️ Instalación Automática

### Opción 1: Instalación Completa (Recomendada)

1. **Descargar el script de instalación:**
   ```bash
   wget https://raw.githubusercontent.com/tu-usuario/deudout/main/install_ubuntu24_clean.sh
   ```

2. **Dar permisos de ejecución:**
   ```bash
   chmod +x install_ubuntu24_clean.sh
   ```

3. **Ejecutar como root:**
   ```bash
   sudo ./install_ubuntu24_clean.sh
   ```

### Opción 2: Instalación Manual

Si prefieres instalar paso a paso, sigue las instrucciones en la sección [Instalación Manual](#instalación-manual).

## 📁 Estructura de Archivos

```
/home/deudout/
├── app.py                          # Aplicación principal Flask
├── models.py                       # Modelos de base de datos
├── requirements.txt                # Dependencias Python
├── .env                           # Variables de entorno
├── venv/                          # Entorno virtual Python
├── static/                        # Archivos estáticos
│   ├── deudout_style.css
│   ├── deudout_components.css
│   └── deudout_components.js
├── templates/                     # Plantillas HTML
├── utils/                         # Utilidades
├── logs/                          # Logs de la aplicación
├── backups/                       # Backups automáticos
├── uploads/                       # Archivos subidos
└── instance/                      # Base de datos SQLite
```

## 🔧 Configuración Post-Instalación

### 1. Acceder a la Aplicación

- **URL**: `http://TU_IP_DEL_SERVIDOR`
- **Usuario admin**: `admin`
- **Contraseña**: `admin123`

### 2. Cambiar Contraseña del Admin

**IMPORTANTE**: Cambia la contraseña del admin inmediatamente después de la instalación.

### 3. Configurar Variables de Email

Edita el archivo `.env`:
```bash
sudo nano /home/deudout/.env
```

Configura:
```env
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password
```

### 4. Configurar Dominio (Opcional)

Si tienes un dominio, ejecuta:
```bash
sudo ./setup_ssl_letsencrypt.sh
```

## 🌐 Configuración de Red

### Firewall
El script configura automáticamente:
- **Puerto 22**: SSH
- **Puerto 80**: HTTP
- **Puerto 443**: HTTPS (si configuras SSL)

### Verificar Puertos
```bash
sudo ufw status
```

## 📊 Monitoreo y Mantenimiento

### Script de Mantenimiento
```bash
sudo ./maintenance_backup.sh
```

**Funcionalidades:**
- 🔄 Backup completo de la aplicación
- 🗄️ Backup de base de datos
- 🧹 Limpieza de logs
- 🔍 Verificación de servicios
- 📊 Estadísticas del sistema
- 🚀 Reinicio de servicios
- 📋 Visualización de logs
- 🔐 Verificación de SSL
- 🗂️ Gestión de backups

### Comandos Útiles

#### Ver Estado de Servicios
```bash
sudo systemctl status deudout
sudo systemctl status nginx
sudo systemctl status supervisor
```

#### Ver Logs
```bash
# Logs de la aplicación
sudo journalctl -u deudout -f

# Logs de Nginx
sudo tail -f /home/deudout/logs/nginx_access.log
sudo tail -f /home/deudout/logs/nginx_error.log

# Logs de Gunicorn
sudo tail -f /home/deudout/logs/gunicorn.log
```

#### Reiniciar Servicios
```bash
sudo systemctl restart deudout
sudo systemctl restart nginx
sudo systemctl restart supervisor
```

#### Backup Manual
```bash
# Backup completo
sudo tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz /home/deudout --exclude=/home/deudout/venv --exclude=/home/deudout/backups --exclude=/home/deudout/logs

# Backup de base de datos
sudo sqlite3 /home/deudout/instance/deudout.db .dump > backup_db_$(date +%Y%m%d_%H%M%S).sql
```

## 🔒 Seguridad

### Headers de Seguridad
La aplicación incluye automáticamente:
- **X-Content-Type-Options**: nosniff
- **X-Frame-Options**: DENY
- **X-XSS-Protection**: 1; mode=block
- **Referrer-Policy**: strict-origin-when-cross-origin
- **Content-Security-Policy**: Configurado para prevenir XSS

### Rate Limiting
- **API**: 10 requests/segundo por IP
- **Login**: 1 request/segundo por IP

### Firewall
- **UFW** configurado automáticamente
- Solo puertos necesarios abiertos
- Acceso SSH restringido

## 📈 Escalabilidad

### Configuración de Gunicorn
- **Workers**: `(CPU cores × 2) + 1`
- **Worker connections**: 1000
- **Timeout**: 30 segundos
- **Max requests**: 1000 por worker

### Nginx
- **Gzip compression** habilitado
- **Caching** para archivos estáticos
- **Proxy buffering** optimizado
- **Load balancing** preparado

## 🚨 Solución de Problemas

### Problemas Comunes

#### 1. La aplicación no inicia
```bash
# Ver logs
sudo journalctl -u deudout -f

# Verificar permisos
sudo chown -R deudout:deudout /home/deudout
sudo chmod -R 755 /home/deudout
```

#### 2. Error de base de datos
```bash
# Verificar archivo de base de datos
ls -la /home/deudout/instance/

# Recrear base de datos
cd /home/deudout
source venv/bin/activate
python init_db.py
```

#### 3. Error de Nginx
```bash
# Verificar configuración
sudo nginx -t

# Ver logs
sudo tail -f /var/log/nginx/error.log
```

#### 4. Problemas de permisos
```bash
# Corregir permisos
sudo chown -R deudout:deudout /home/deudout
sudo chmod -R 755 /home/deudout
sudo chmod 640 /home/deudout/.env
```

### Logs de Diagnóstico

#### Verificar Estado del Sistema
```bash
# Uso de recursos
htop
df -h
free -h

# Procesos activos
ps aux | grep -E "(deudout|nginx|gunicorn)"

# Puertos abiertos
netstat -tlnp
```

#### Verificar Servicios
```bash
# Estado de todos los servicios
sudo systemctl list-units --type=service --state=failed

# Verificar dependencias
sudo systemctl list-dependencies deudout
```

## 🔄 Actualizaciones

### Actualizar la Aplicación
```bash
cd /home/deudout
sudo -u deudout git pull origin main
sudo -u deudout source venv/bin/activate && pip install -r requirements.txt
sudo systemctl restart deudout
```

### Actualizar Dependencias del Sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### Actualizar Python
```bash
# Verificar versión actual
python3 --version

# Actualizar si es necesario
sudo apt install python3.12 python3.12-venv python3.12-dev
```

## 📚 Documentación Adicional

### Archivos de Configuración
- **Nginx**: `/etc/nginx/sites-available/deudout`
- **Systemd**: `/etc/systemd/system/deudout.service`
- **Supervisor**: `/etc/supervisor/conf.d/deudout.conf`
- **Logrotate**: `/etc/logrotate.d/deudout`

### Variables de Entorno
```env
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=tu_clave_secreta
DATABASE_URL=sqlite:///deudout.db
EMAIL_SERVER=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password
UPLOAD_FOLDER=/home/deudout/uploads
MAX_CONTENT_LENGTH=16777216
```

## 🤝 Soporte

### Canales de Ayuda
- **Issues**: GitHub Issues
- **Documentación**: README.md
- **Logs**: `/home/deudout/logs/`

### Información del Sistema
```bash
# Información completa del sistema
sudo ./maintenance_backup.sh

# Seleccionar opción 5: Ver estadísticas del sistema
```

## 📝 Notas Importantes

### Antes de la Instalación
1. ✅ Asegúrate de tener Ubuntu 24.04
2. ✅ Ejecuta como usuario root
3. ✅ Ten conexión a Internet estable
4. ✅ Verifica espacio en disco (mínimo 20 GB)

### Después de la Instalación
1. ✅ Cambia la contraseña del admin
2. ✅ Configura las variables de email
3. ✅ Verifica que todos los servicios estén funcionando
4. ✅ Haz un backup inicial
5. ✅ Configura SSL si tienes dominio

### Mantenimiento Regular
1. 🔄 Hacer backups semanales
2. 🧹 Limpiar logs mensualmente
3. 🔍 Verificar estado de servicios semanalmente
4. 📊 Monitorear uso de recursos
5. 🔒 Mantener actualizado el sistema

## 🎉 ¡Listo!

Tu aplicación DEUDOUT está ahora completamente instalada y configurada en Ubuntu 24.04. 

**URL de acceso**: `http://TU_IP_DEL_SERVIDOR`
**Usuario**: `admin`
**Contraseña**: `admin123`

¡Disfruta usando tu nueva aplicación DEUDOUT! 🚀
