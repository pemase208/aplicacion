#!/bin/bash

# ===== SCRIPT DE MANTENIMIENTO Y BACKUP PARA DEUDOUT =====
# Script para realizar tareas de mantenimiento y backup automático

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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
BACKUP_DIR="$APP_DIR/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="deudout_backup_$DATE.tar.gz"

# Función para mostrar menú
show_menu() {
    clear
    print_header "MANTENIMIENTO Y BACKUP DEUDOUT"
    echo ""
    echo "1. 🔄 Backup completo de la aplicación"
    echo "2. 🗄️  Backup solo de la base de datos"
    echo "3. 🧹 Limpieza de logs antiguos"
    echo "4. 🔍 Verificar estado de servicios"
    echo "5. 📊 Ver estadísticas del sistema"
    echo "6. 🚀 Reiniciar servicios"
    echo "7. 📋 Ver logs recientes"
    echo "8. 🔐 Verificar certificados SSL"
    echo "9. 🗂️  Gestionar backups"
    echo "10. ❌ Salir"
    echo ""
    read -p "Selecciona una opción (1-10): " choice
}

# Función para hacer backup completo
backup_complete() {
    print_header "BACKUP COMPLETO DE LA APLICACIÓN"
    
    # Crear directorio de backup si no existe
    mkdir -p "$BACKUP_DIR"
    
    print_step "Creando backup completo..."
    
    # Crear backup excluyendo archivos innecesarios
    tar --exclude="$APP_DIR/venv" \
        --exclude="$APP_DIR/backups" \
        --exclude="$APP_DIR/logs" \
        --exclude="$APP_DIR/__pycache__" \
        --exclude="$APP_DIR/static/generated_docs" \
        --exclude="$APP_DIR/uploads" \
        -czf "$BACKUP_DIR/$BACKUP_FILE" \
        -C "$APP_DIR" .
    
    if [ $? -eq 0 ]; then
        print_success "Backup completo creado: $BACKUP_FILE"
        print_step "Tamaño del backup: $(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)"
        
        # Limpiar backups antiguos (mantener solo los últimos 10)
        cd "$BACKUP_DIR"
        ls -t deudout_backup_*.tar.gz | tail -n +11 | xargs -r rm -f
        print_success "Backups antiguos limpiados"
    else
        print_error "Error al crear el backup"
        return 1
    fi
    
    read -p "Presiona Enter para continuar..."
}

# Función para hacer backup de la base de datos
backup_database() {
    print_header "BACKUP DE LA BASE DE DATOS"
    
    mkdir -p "$BACKUP_DIR"
    
    print_step "Creando backup de la base de datos..."
    
    # Buscar archivos de base de datos
    DB_FILES=$(find "$APP_DIR" -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" 2>/dev/null)
    
    if [ -z "$DB_FILES" ]; then
        print_warning "No se encontraron archivos de base de datos"
        return 1
    fi
    
    for db_file in $DB_FILES; do
        db_name=$(basename "$db_file")
        backup_name="db_${db_name%.*}_$DATE.sql"
        
        print_step "Backup de $db_name..."
        
        # Crear backup SQL
        sqlite3 "$db_file" .dump > "$BACKUP_DIR/$backup_name"
        
        if [ $? -eq 0 ]; then
            print_success "Backup de $db_name creado: $backup_name"
        else
            print_error "Error al crear backup de $db_name"
        fi
    done
    
    read -p "Presiona Enter para continuar..."
}

# Función para limpiar logs antiguos
clean_logs() {
    print_header "LIMPIEZA DE LOGS ANTIGUOS"
    
    print_step "Limpiando logs antiguos..."
    
    # Limpiar logs de la aplicación
    if [ -d "$APP_DIR/logs" ]; then
        find "$APP_DIR/logs" -name "*.log" -mtime +30 -delete
        print_success "Logs de aplicación limpiados (más de 30 días)"
    fi
    
    # Limpiar logs del sistema
    journalctl --vacuum-time=30d
    print_success "Logs del sistema limpiados (más de 30 días)"
    
    # Limpiar logs de Nginx
    if [ -f "/var/log/nginx/access.log" ]; then
        truncate -s 0 /var/log/nginx/access.log
        print_success "Logs de Nginx limpiados"
    fi
    
    read -p "Presiona Enter para continuar..."
}

# Función para verificar estado de servicios
check_services() {
    print_header "VERIFICACIÓN DE ESTADO DE SERVICIOS"
    
    print_step "Verificando servicios principales..."
    
    echo ""
    echo "Estado de $APP_NAME:"
    systemctl status "$APP_NAME" --no-pager -l | head -20
    
    echo ""
    echo "Estado de Nginx:"
    systemctl status nginx --no-pager -l | head -20
    
    echo ""
    echo "Estado de Supervisor:"
    systemctl status supervisor --no-pager -l | head -20
    
    echo ""
    print_step "Verificando puertos..."
    netstat -tlnp | grep -E ':(80|443|5000)'
    
    echo ""
    print_step "Verificando uso de disco..."
    df -h
    
    echo ""
    print_step "Verificando uso de memoria..."
    free -h
    
    read -p "Presiona Enter para continuar..."
}

# Función para ver estadísticas del sistema
system_stats() {
    print_header "ESTADÍSTICAS DEL SISTEMA"
    
    print_step "Información del sistema..."
    
    echo ""
    echo "🖥️  Información del sistema:"
    echo "   - OS: $(lsb_release -d | cut -f2)"
    echo "   - Kernel: $(uname -r)"
    echo "   - Arquitectura: $(uname -m)"
    echo "   - Uptime: $(uptime -p)"
    
    echo ""
    echo "💾 Uso de disco:"
    df -h | grep -E '^/dev/'
    
    echo ""
    echo "🧠 Uso de memoria:"
    free -h
    
    echo ""
    echo "🔥 Uso de CPU:"
    top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1
    
    echo ""
    echo "🌐 Información de red:"
    echo "   - IP local: $(hostname -I | awk '{print $1}')"
    echo "   - Hostname: $(hostname)"
    
    echo ""
    echo "📊 Procesos activos:"
    ps aux | grep -E "(deudout|nginx|gunicorn)" | grep -v grep | wc -l
    
    read -p "Presiona Enter para continuar..."
}

# Función para reiniciar servicios
restart_services() {
    print_header "REINICIO DE SERVICIOS"
    
    print_step "Reiniciando servicios..."
    
    systemctl restart "$APP_NAME"
    print_success "$APP_NAME reiniciado"
    
    systemctl restart nginx
    print_success "Nginx reiniciado"
    
    systemctl restart supervisor
    print_success "Supervisor reiniciado"
    
    print_step "Verificando estado..."
    sleep 3
    
    systemctl status "$APP_NAME" --no-pager -l | head -10
    systemctl status nginx --no-pager -l | head -10
    
    read -p "Presiona Enter para continuar..."
}

# Función para ver logs recientes
view_logs() {
    print_header "VISUALIZACIÓN DE LOGS"
    
    print_step "Seleccionando archivo de log..."
    
    echo ""
    echo "1. Logs de la aplicación ($APP_DIR/logs/)"
    echo "2. Logs del sistema (journalctl)"
    echo "3. Logs de Nginx"
    echo "4. Logs de Gunicorn"
    echo ""
    read -p "Selecciona tipo de log (1-4): " log_choice
    
    case $log_choice in
        1)
            if [ -d "$APP_DIR/logs" ]; then
                echo ""
                echo "Archivos de log disponibles:"
                ls -la "$APP_DIR/logs/"
                echo ""
                read -p "Introduce nombre del archivo: " log_file
                if [ -f "$APP_DIR/logs/$log_file" ]; then
                    tail -50 "$APP_DIR/logs/$log_file"
                else
                    print_error "Archivo no encontrado"
                fi
            else
                print_warning "Directorio de logs no encontrado"
            fi
            ;;
        2)
            echo ""
            journalctl -u "$APP_NAME" -n 50 --no-pager
            ;;
        3)
            echo ""
            tail -50 /var/log/nginx/error.log
            ;;
        4)
            if [ -f "$APP_DIR/logs/gunicorn.log" ]; then
                tail -50 "$APP_DIR/logs/gunicorn.log"
            else
                print_warning "Log de Gunicorn no encontrado"
            fi
            ;;
        *)
            print_error "Opción no válida"
            ;;
    esac
    
    read -p "Presiona Enter para continuar..."
}

# Función para verificar certificados SSL
check_ssl() {
    print_header "VERIFICACIÓN DE CERTIFICADOS SSL"
    
    print_step "Verificando certificados..."
    
    if command -v certbot &> /dev/null; then
        certbot certificates
    else
        print_warning "Certbot no está instalado"
    fi
    
    echo ""
    print_step "Verificando configuración Nginx..."
    nginx -t
    
    echo ""
    print_step "Verificando puertos SSL..."
    netstat -tlnp | grep :443
    
    read -p "Presiona Enter para continuar..."
}

# Función para gestionar backups
manage_backups() {
    print_header "GESTIÓN DE BACKUPS"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        print_warning "Directorio de backups no encontrado"
        read -p "Presiona Enter para continuar..."
        return
    fi
    
    print_step "Backups disponibles:"
    echo ""
    
    if [ -z "$(ls -A "$BACKUP_DIR")" ]; then
        print_warning "No hay backups disponibles"
    else
        ls -lah "$BACKUP_DIR"
        
        echo ""
        echo "1. 📥 Descargar backup"
        echo "2. 🗑️  Eliminar backup"
        echo "3. 🔍 Ver contenido de backup"
        echo "4. ↩️  Volver"
        echo ""
        read -p "Selecciona opción (1-4): " backup_choice
        
        case $backup_choice in
            1)
                read -p "Introduce nombre del archivo: " backup_file
                if [ -f "$BACKUP_DIR/$backup_file" ]; then
                    print_step "Backup disponible en: $BACKUP_DIR/$backup_file"
                    print_step "Para descargar, usa SCP desde tu máquina local:"
                    echo "scp usuario@$(hostname -I | awk '{print $1}'):$BACKUP_DIR/$backup_file ."
                else
                    print_error "Archivo no encontrado"
                fi
                ;;
            2)
                read -p "Introduce nombre del archivo: " backup_file
                if [ -f "$BACKUP_DIR/$backup_file" ]; then
                    read -p "¿Estás seguro de eliminar $backup_file? (y/N): " -n 1 -r
                    echo
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        rm -f "$BACKUP_DIR/$backup_file"
                        print_success "Backup eliminado"
                    fi
                else
                    print_error "Archivo no encontrado"
                fi
                ;;
            3)
                read -p "Introduce nombre del archivo: " backup_file
                if [ -f "$BACKUP_DIR/$backup_file" ]; then
                    tar -tzf "$BACKUP_DIR/$backup_file" | head -20
                    echo "..."
                else
                    print_error "Archivo no encontrado"
                fi
                ;;
        esac
    fi
    
    read -p "Presiona Enter para continuar..."
}

# Función principal
main() {
    while true; do
        show_menu
        
        case $choice in
            1) backup_complete ;;
            2) backup_database ;;
            3) clean_logs ;;
            4) check_services ;;
            5) system_stats ;;
            6) restart_services ;;
            7) view_logs ;;
            8) check_ssl ;;
            9) manage_backups ;;
            10) 
                print_success "¡Hasta luego!"
                exit 0
                ;;
            *) 
                print_error "Opción no válida"
                read -p "Presiona Enter para continuar..."
                ;;
        esac
    done
}

# Verificar que estamos ejecutando como root
if [ "$EUID" -ne 0 ]; then
    print_error "Este script debe ejecutarse como root"
    print_error "Usa: sudo $0"
    exit 1
fi

# Verificar que la aplicación existe
if [ ! -d "$APP_DIR" ]; then
    print_error "La aplicación DEUDOUT no está instalada en $APP_DIR"
    exit 1
fi

# Ejecutar función principal
main
