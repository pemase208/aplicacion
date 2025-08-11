# 🚀 DESPLIEGUE SFTP DE DEUDOUT

## 📋 **OPCIONES DE DESPLIEGUE**

### **Opción 1: Despliegue Automático Completo**
```bash
# Ejecutar desde el directorio del proyecto
chmod +x deploy_sftp.sh
./deploy_sftp.sh
```

**Características:**
- ✅ Subida automática de todos los archivos
- ✅ Verificación de conectividad
- ✅ Script de instalación remota
- ✅ Limpieza automática de archivos temporales
- ✅ Configuración completa del despliegue

### **Opción 2: Subida Rápida Simple**
```bash
# Para despliegues rápidos
chmod +x upload_sftp.sh
./upload_sftp.sh
```

**Características:**
- ⚡ Subida directa sin verificaciones adicionales
- 📁 Solo archivos esenciales
- 🔧 Instrucciones manuales post-subida

## 🔧 **PREPARACIÓN PREVIA**

### **1. Verificar Archivos del Proyecto**
```bash
# Asegúrate de tener estos archivos en tu directorio:
ls -la
# Debe incluir: app.py, models.py, requirements.txt, etc.
```

### **2. Configurar Acceso SSH**
```bash
# Opción A: Claves SSH (recomendado)
ssh-keygen -t rsa -b 4096
ssh-copy-id root@tu-ip-del-vps

# Opción B: Contraseña (menos seguro)
# El script te pedirá la contraseña durante la ejecución
```

### **3. Verificar Conectividad**
```bash
# Probar conexión SSH
ssh root@tu-ip-del-vps

# Probar SFTP
sftp root@tu-ip-del-vps
```

## 📤 **PROCESO DE DESPLIEGUE**

### **Paso 1: Ejecutar Script de Despliegue**
```bash
./deploy_sftp.sh
```

**El script te pedirá:**
- IP del VPS
- Usuario (normalmente `root`)
- Puerto SSH (normalmente `22`)

### **Paso 2: Verificar Subida**
```bash
# Conectarse al VPS
ssh root@tu-ip-del-vps

# Verificar archivos subidos
cd /tmp/deudout_deploy
ls -la
```

### **Paso 3: Ejecutar Instalación**
```bash
# Opción A: Instalación automática
./remote_install.sh

# Opción B: Instalación manual
chmod +x install_ubuntu24_optimized.sh
./install_ubuntu24_optimized.sh
```

## 📁 **ESTRUCTURA DE ARCHIVOS DESPLEGADOS**

```
/tmp/deudout_deploy/
├── app.py                              # Aplicación principal
├── models.py                           # Modelos de base de datos
├── requirements.txt                    # Dependencias Python
├── init_db.py                         # Inicialización de BD
├── crear_admin.py                     # Creación de usuario admin
├── poblar_entidades_financieras.py    # Datos iniciales
├── utils/                             # Utilidades
├── static/                            # Archivos estáticos
├── templates/                         # Plantillas HTML
├── instance/                          # Base de datos
├── .env.example                       # Variables de entorno
├── README.txt                         # Documentación
├── gunicorn.conf.py                   # Configuración Gunicorn
├── nginx.conf                         # Configuración Nginx
├── install_ubuntu24_optimized.sh      # Script de instalación
├── remote_install.sh                  # Instalación remota
└── deploy_config.txt                  # Configuración del despliegue
```

## 🔍 **VERIFICACIÓN POST-DESPLIEGUE**

### **1. Verificar Servicios**
```bash
# Estado de la aplicación
systemctl status deudout

# Estado de Nginx
systemctl status nginx

# Verificar puertos
netstat -tlnp | grep -E ':(80|443)'
```

### **2. Verificar Logs**
```bash
# Logs de la aplicación
journalctl -u deudout -f

# Logs de Nginx
tail -f /home/deudout/logs/nginx_access.log
tail -f /home/deudout/logs/nginx_error.log
```

### **3. Script de Verificación de Salud**
```bash
# Ejecutar verificación automática
/home/deudout/health_check.sh
```

## 🚨 **SOLUCIÓN DE PROBLEMAS**

### **Error: "Permission denied"**
```bash
# Verificar permisos SSH
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Verificar permisos en el VPS
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### **Error: "Connection refused"**
```bash
# Verificar que SSH esté activo en el VPS
systemctl status ssh

# Verificar firewall
ufw status
```

### **Error: "No such file or directory"**
```bash
# Verificar que estés en el directorio correcto
pwd
ls -la

# Asegúrate de ejecutar desde el directorio del proyecto
cd /ruta/a/tu/proyecto/deudout
```

## 📝 **NOTAS IMPORTANTES**

### **Seguridad**
- 🔐 Cambia la contraseña del admin después de la instalación
- 🔒 Configura las variables de email en `.env`
- 🛡️ Considera configurar SSL/HTTPS para producción
- 🔑 Usa claves SSH en lugar de contraseñas

### **Mantenimiento**
- 📊 Revisa los logs regularmente
- 🔄 Actualiza el sistema periódicamente
- 💾 Haz backups de la base de datos
- 📈 Monitorea el rendimiento

### **Escalabilidad**
- 🚀 El script está optimizado para Ubuntu 24.04
- 📦 Incluye todas las dependencias necesarias
- 🔧 Configuración de producción lista
- 📱 Interfaz responsive y moderna

## 🎯 **COMANDOS RÁPIDOS**

```bash
# Despliegue completo
./deploy_sftp.sh

# Subida rápida
./upload_sftp.sh

# Verificar estado en el VPS
ssh root@tu-ip-del-vps "systemctl status deudout"

# Reiniciar aplicación
ssh root@tu-ip-del-vps "systemctl restart deudout"

# Ver logs en tiempo real
ssh root@tu-ip-del-vps "journalctl -u deudout -f"
```

---

**¡Tu aplicación DEUDOUT estará lista para producción en minutos!** 🎉


