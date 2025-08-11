# ===== CONFIGURACIÓN OPTIMIZADA DE GUNICORN PARA DEUDOUT =====
# Configuración para producción en Ubuntu 24.04

import multiprocessing
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ===== CONFIGURACIÓN DEL SERVIDOR =====
bind = os.environ.get('GUNICORN_BIND', "127.0.0.1:8000")
workers = int(os.environ.get('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = os.environ.get('WORKER_CLASS', "sync")
worker_connections = int(os.environ.get('WORKER_CONNECTIONS', '1000'))
max_requests = int(os.environ.get('MAX_REQUESTS', '1000'))
max_requests_jitter = int(os.environ.get('MAX_REQUESTS_JITTER', '50'))

# ===== CONFIGURACIÓN DE LOGGING =====
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', "/var/log/gunicorn/access.log")
errorlog = os.environ.get('GUNICORN_ERROR_LOG', "/var/log/gunicorn/error.log")
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', "info")

# ===== CONFIGURACIÓN DE SEGURIDAD =====
preload_app = True
timeout = int(os.environ.get('TIMEOUT', '30'))
keepalive = int(os.environ.get('KEEPALIVE', '2'))

# ===== CONFIGURACIÓN DE ARCHIVOS =====
pidfile = os.environ.get('GUNICORN_PIDFILE', "/var/run/gunicorn/flaskapp.pid")
tmp_upload_dir = None

# ===== CONFIGURACIÓN DE WORKERS =====
# Configuración específica para diferentes tipos de worker
if worker_class == "gevent":
    worker_connections = 1000
    max_requests = 1000
elif worker_class == "eventlet":
    worker_connections = 1000
    max_requests = 1000
elif worker_class == "tornado":
    worker_connections = 1000
    max_requests = 1000

# ===== CONFIGURACIÓN DE BUFFERS =====
# Optimizar para aplicaciones web
max_requests_jitter = 50
graceful_timeout = 30
worker_tmp_dir = "/dev/shm"  # Usar memoria compartida si está disponible

# ===== CONFIGURACIÓN DE SSL (SI ES NECESARIO) =====
# keyfile = os.environ.get('SSL_KEYFILE', "/path/to/keyfile")
# certfile = os.environ.get('SSL_CERTFILE', "/path/to/certfile")

# ===== CONFIGURACIÓN DE MONITOREO =====
# Habilitar estadísticas de workers
statsd_host = os.environ.get('STATSD_HOST', None)
statsd_port = os.environ.get('STATSD_PORT', None)
statsd_prefix = os.environ.get('STATSD_PREFIX', 'gunicorn')

# ===== CONFIGURACIÓN DE LIMPIEZA =====
# Limpiar archivos temporales
cleanup_on_exit = True

# ===== CONFIGURACIÓN DE ENTORNO =====
# Variables de entorno para la aplicación
raw_env = [
    f"FLASK_ENV={os.environ.get('FLASK_ENV', 'production')}",
    f"FLASK_APP={os.environ.get('FLASK_APP', 'app.py')}",
]

# ===== CONFIGURACIÓN DE PROCESOS =====
# Configuración de procesos para evitar zombies
daemon = False
user = os.environ.get('GUNICORN_USER', 'www-data')
group = os.environ.get('GUNICORN_GROUP', 'www-data')

# ===== CONFIGURACIÓN DE LIMITES =====
# Límites de recursos
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# ===== CONFIGURACIÓN DE COMPRESIÓN =====
# Comprimir respuestas
compress_level = 6
compress_min_len = 500

# ===== CONFIGURACIÓN DE CACHE =====
# Cache de archivos estáticos
static_cache_timeout = 86400  # 24 horas
