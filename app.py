from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
from models import db, User, Banco, AccessLog, FormularioRPC, DatosLector, Procedimiento, EntidadFinanciera, TipoVia
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import json
import requests
import os
from utils.pdf_generator import PDFGenerator
from utils.rgpd_destinatarios import PREDEFINED_DESTINATARIOS
from utils.email_sender import EmailSender
from utils.external_queries import consultar_rpc, consultar_boe_tablon, consulta_total_integrada
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# ===== CONFIGURACIÓN ROBUSTA DE BASE DE DATOS =====
def get_database_config():
    """Obtiene la configuración de base de datos de forma robusta"""
    database_type = os.environ.get('DATABASE_TYPE', 'sqlite').lower()
    
    if database_type == 'sqlite':
        # Configuración SQLite con fallbacks
        base_dir = os.path.abspath(os.path.dirname(__file__))
        instance_dir = os.path.join(base_dir, 'instance')
        
        # Crear directorio instance si no existe
        os.makedirs(instance_dir, exist_ok=True)
        
        # Determinar ruta de la base de datos
        if os.environ.get('FLASK_ENV') == 'production':
            db_path = os.environ.get('DATABASE_URL', os.path.join(instance_dir, 'mibasedatos.db'))
        else:
            db_path = os.environ.get('DATABASE_URL', os.path.join(base_dir, 'mibasedatos.db'))
        
        # Si es una URL completa, usarla; si no, construir la URI
        if db_path.startswith('sqlite:///'):
            return db_path
        else:
            return f'sqlite:///{db_path}'
    
    elif database_type in ['mysql', 'mariadb']:
        # Configuración MySQL/MariaDB
        return os.environ.get('DATABASE_URL', 'mysql://root:password@localhost/deudout_db')
    
    elif database_type == 'postgresql':
        # Configuración PostgreSQL
        return os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost/deudout_db')
    
    else:
        # Fallback a SQLite
        print(f"⚠️  Tipo de base de datos '{database_type}' no soportado, usando SQLite")
        base_dir = os.path.abspath(os.path.dirname(__file__))
        return f'sqlite:///{os.path.join(base_dir, "mibasedatos.db")}'

# ===== CONFIGURACIÓN DE LA APLICACIÓN =====
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_config()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Verificar conexión antes de usar
    'pool_recycle': 300,    # Reciclar conexiones cada 5 minutos
    'pool_timeout': 20,     # Timeout de conexión
    'max_overflow': 10      # Conexiones adicionales permitidas
}

# ===== CONFIGURACIÓN DE SEGURIDAD =====
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    print("⚠️  SECRET_KEY no configurada, generando una temporal")
    import secrets
    secret_key = secrets.token_hex(32)

app.config['SECRET_KEY'] = secret_key

# ===== CONFIGURACIÓN DE SESIÓN =====
app.config['SESSION_COOKIE_NAME'] = 'deudout_session'
app.config['SESSION_COOKIE_SAMESITE'] = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
app.config['SESSION_COOKIE_HTTPONLY'] = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'

# Configuración de seguridad de cookies
force_http = os.environ.get('FORCE_HTTP', '1') == '1'
app.config['SESSION_COOKIE_SECURE'] = not force_http

# Duración de la sesión
session_lifetime = int(os.environ.get('PERMANENT_SESSION_LIFETIME', '604800'))  # 7 días por defecto
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=session_lifetime)

# ===== CONFIGURACIÓN DE PROXY (NGINX) =====
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

# ===== INICIALIZACIÓN DE LA BASE DE DATOS =====
db.init_app(app)

# ===== VERIFICACIÓN DE CONECTIVIDAD DE BASE DE DATOS =====
def test_database_connection():
    """Prueba la conexión a la base de datos"""
    try:
        with app.app_context():
            db.engine.execute('SELECT 1')
            print("✅ Conexión a base de datos exitosa")
            return True
    except Exception as e:
        print(f"❌ Error de conexión a base de datos: {e}")
        return False

# ===== CONFIGURACIÓN DE LOGGING =====
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configura el sistema de logging"""
    if not app.debug:
        # Crear directorio de logs si no existe
        log_dir = os.path.dirname(os.environ.get('LOG_FILE', '/var/log/flaskapp/app.log'))
        os.makedirs(log_dir, exist_ok=True)
        
        # Configurar logging rotativo
        file_handler = RotatingFileHandler(
            os.environ.get('LOG_FILE', '/var/log/flaskapp/app.log'),
            maxBytes=int(os.environ.get('LOG_MAX_SIZE', '10485760')),  # 10MB
            backupCount=int(os.environ.get('LOG_BACKUP_COUNT', '5'))
        )
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Deudout startup')

# Configurar logging
setup_logging()

def get_location_from_ip(ip):
    """Obtiene la ubicación geográfica de una IP"""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return f"{data.get('city', '')}, {data.get('country', '')}"
    except:
        pass
    return "Ubicación desconocida"

def log_access(username, ip, user_agent, success):
    """Registra un intento de acceso"""
    ubicacion = get_location_from_ip(ip)
    log = AccessLog(
        username=username,
        ip_address=ip,
        user_agent=user_agent,
        success=success,
        ubicacion=ubicacion
    )
    db.session.add(log)
    db.session.commit()

def recent_failed_attempts(username: str, window_minutes: int = 15) -> int:
    """Cuenta intentos fallidos consecutivos en la ventana dada.
    Se detiene al encontrar un acceso exitoso o fuera de ventana.
    """
    cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
    logs = AccessLog.query.filter(
        AccessLog.username == username
    ).order_by(AccessLog.fecha.desc()).limit(20).all()
    count = 0
    for l in logs:
        if l.fecha < cutoff:
            break
        if l.success:
            break
        count += 1
    return count

def crear_usuario_admin():
    with app.app_context():
        usuario = User.query.filter_by(username="pedro").first()
        if not usuario:
            usuario = User(
                username="pedro",
                password_hash=generate_password_hash("admin1234"),
                role="admin",
                is_enabled=True,
                nombre="Pedro",
                apellidos="Administrador"
            )
            db.session.add(usuario)
            db.session.commit()
            print("Usuario 'pedro' creado correctamente.")
        else:
            print("El usuario 'pedro' ya existe.")

def check_user_access():
    """Verifica si el usuario tiene acceso válido"""
    if "username" not in session:
        return False, "Debes iniciar sesión para acceder al sistema."
    
    usuario = User.query.filter_by(username=session["username"]).first()
    if not usuario or not usuario.is_enabled:
        session.clear()
        return False, "Usuario no válido o deshabilitado."
    
    if usuario.role == "lector" and usuario.is_expired():
        session.clear()
        return False, "Tu acceso ha expirado. Contacta al administrador."
    
    return True, usuario

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("menu"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("menu"))
    
    if request.method == "POST":
        username = request.form.get("usuario")
        password = request.form.get("clave")
        
        if not username or not password:
            flash("Por favor, introduce usuario y contraseña.", "warning")
            return render_template("login.html")
        
        usuario = User.query.filter_by(username=username).first()

        # Bloqueo tras 3 intentos fallidos en 15 minutos
        if usuario:
            fails = recent_failed_attempts(username, window_minutes=15)
            if fails >= 3:
                flash("Cuenta bloqueada temporalmente por intentos fallidos. Inténtalo más tarde.", "danger")
                return render_template("login.html")
        
        if usuario and usuario.is_enabled and check_password_hash(usuario.password_hash, password):
            # Verificar expiración para lectores
            if usuario.role == "lector" and usuario.is_expired():
                flash("Tu acceso ha expirado. Contacta al administrador.", "danger")
                return render_template("login.html")
            
            # Para lectores, verificar que tienen datos asociados
            if usuario.role == "lector":
                if not usuario.dni_nie:
                    flash("Tu cuenta de lector no tiene DNI/NIE asociado. Contacta al administrador.", "danger")
                    return render_template("login.html")
                
                # Buscar datos asociados al DNI/NIE
                datos_lector = DatosLector.query.filter_by(dni_nie=usuario.dni_nie).first()
                if not datos_lector:
                    flash("No se encontraron datos asociados a tu DNI/NIE. Contacta al administrador.", "danger")
                    return render_template("login.html")
                
                # Guardar datos del lector en la sesión
                session["datos_lector"] = {
                    "nombre": datos_lector.nombre,
                    "apellidos": datos_lector.apellidos,
                    "email": datos_lector.email,
                    "telefono": datos_lector.telefono,
                    "direccion": datos_lector.direccion,
                    "datos_adicionales": datos_lector.datos_adicionales
                }
            
            session["username"] = usuario.username
            session["role"] = usuario.role
            session["user_id"] = usuario.id
            
            # Log del acceso exitoso
            log_access(username, request.remote_addr, request.headers.get('User-Agent'), True)
            
            flash(f"¡Bienvenido, {usuario.nombre or usuario.username}!", "success")
            return redirect(url_for("menu"))
        else:
            # Log de intento fallido real
            log_access(username or "", request.remote_addr, request.headers.get('User-Agent'), False)
            # Calcular intentos restantes tras registrar este fallo
            remaining = 0
            try:
                fails_now = recent_failed_attempts(username or "", window_minutes=15)
                remaining = max(0, 3 - fails_now)
            except Exception:
                remaining = 0
            msg = "Usuario o contraseña incorrectos, o usuario deshabilitado."
            if remaining > 0:
                msg += f" Intentos restantes: {remaining}."
            else:
                msg += " Cuenta bloqueada temporalmente tras múltiples intentos."
            # Calcular para mostrar en plantilla
            intentos_restantes = remaining
            return render_template("login.html", intentos_restantes=intentos_restantes)
    
    # GET o sin POST válido: mostrar si hay contador aplicado recientemente no tiene sentido; solo render básico
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("login"))

@app.route("/menu")
def menu():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    return render_template("menu.html", usuario=usuario)

@app.route("/cambiar_password", methods=["GET", "POST"])
def cambiar_password():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))

    usuario = result
    if request.method == "POST":
        actual = request.form.get('password_actual', '')
        nueva = request.form.get('password_nueva', '')
        confirmar = request.form.get('password_confirmar', '')

        # Validaciones básicas
        if not actual or not nueva or not confirmar:
            flash("Todos los campos son obligatorios.", "warning")
            return render_template("cambiar_password.html")

        if not check_password_hash(usuario.password_hash, actual):
            flash("La contraseña actual no es correcta.", "danger")
            return render_template("cambiar_password.html")

        if len(nueva) < 8:
            flash("La nueva contraseña debe tener al menos 8 caracteres.", "danger")
            return render_template("cambiar_password.html")

        if nueva != confirmar:
            flash("La confirmación de contraseña no coincide.", "danger")
            return render_template("cambiar_password.html")

        try:
            usuario.password_hash = generate_password_hash(nueva)
            db.session.commit()
            flash("Contraseña actualizada correctamente.", "success")
            return redirect(url_for("menu"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar la contraseña: {str(e)}", "danger")
            return render_template("cambiar_password.html")

    return render_template("cambiar_password.html")

@app.route("/formulario", methods=["GET", "POST"])
def formulario_generico():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    datos = {"nombre": "", "apellidos": "", "dni": "", "email": "", "direccion": "", "telefono": ""}
    
    # Para lectores, usar datos precargados
    if usuario.role == "lector" and usuario.datos_precargados:
        try:
            datos_precargados = json.loads(usuario.datos_precargados)
            datos.update(datos_precargados)
        except:
            pass
    
    if request.method == "POST":
        for campo in datos:
            datos[campo] = request.form.get(campo, "")
        
        # Generar PDF
        try:
            pdf_filename = pdf_generator.generate_form_generic_pdf(datos)
            flash(f"Formulario guardado y PDF generado: {pdf_filename}", "success")
            
            # Guardar nombre del PDF en sesión para posible descarga
            session['last_generated_pdf'] = pdf_filename
            
        except Exception as e:
            flash(f"Formulario guardado pero error al generar PDF: {str(e)}", "warning")
    
    return render_template("formulario_generico.html", datos=datos)

# Rutas específicas para administradores
@app.route("/admin/usuarios")
def admin_usuarios():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    if usuario.role != "admin":
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for("menu"))
    
    # Filtros y paginación
    role = request.args.get('role', '').strip()
    status = request.args.get('status', '').strip()
    q = request.args.get('q', '').strip()
    try:
        page = int(request.args.get('page', '1'))
    except Exception:
        page = 1
    try:
        per_page = int(request.args.get('per_page', '20'))
    except Exception:
        per_page = 20
    per_page = max(5, min(per_page, 100))

    query = User.query
    if role in ("admin", "usuario", "lector"):
        query = query.filter(User.role == role)
    if status == 'activo':
        query = query.filter(User.is_enabled.is_(True))
    elif status == 'inactivo':
        query = query.filter(User.is_enabled.is_(False))
    if q:
        like = f"%{q}%"
        query = query.filter(
            (User.username.ilike(like)) |
            (User.nombre.ilike(like)) |
            (User.apellidos.ilike(like))
        )

    total = query.count()
    pages = (total + per_page - 1) // per_page if per_page else 1
    page = max(1, min(page, pages if pages else 1))
    usuarios = query.order_by(User.created_at.desc()).limit(per_page).offset((page - 1) * per_page).all()

    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': pages,
        'has_prev': page > 1,
        'has_next': page < pages,
    }

    return render_template(
        "admin_usuarios.html",
        usuarios=usuarios,
        pagination=pagination,
        filter_role=role,
        filter_status=status,
        filter_q=q,
    )

@app.route("/admin/bancos")
def admin_bancos():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    if usuario.role != "admin":
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for("menu"))
    
    entidades = EntidadFinanciera.query.order_by(EntidadFinanciera.nombre.asc()).all()
    return render_template("admin_bancos.html", bancos=entidades)


def _get_entidad_form_from_request(req):
    return {
        'nombre': req.form.get('nombre', '').strip(),
        'nombre_comercial': req.form.get('nombre_comercial', '').strip(),
        'tipo_entidad': req.form.get('tipo_entidad', '').strip() or 'Banco',
        'codigo_entidad': req.form.get('codigo_entidad', '').strip(),
        'direccion': req.form.get('direccion', '').strip(),
        'numero': req.form.get('numero', '').strip(),
        'codigo_postal': req.form.get('codigo_postal', '').strip() or req.form.get('cp', '').strip(),
        'localidad': req.form.get('localidad', '').strip(),
        'provincia': req.form.get('provincia', '').strip(),
        'comunidad_autonoma': req.form.get('comunidad_autonoma', '').strip() or req.form.get('ccaa', '').strip(),
        'telefono': req.form.get('telefono', '').strip(),
        'web': req.form.get('web', '').strip(),
        'email_doc9': req.form.get('email_doc9', '').strip(),
        'email_rgpd': req.form.get('email_rgpd', '').strip(),
        'email_general': req.form.get('email_general', '').strip(),
    }


@app.route('/admin/entidades/crear', methods=['POST'])
def admin_crear_banco():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, 'warning')
        return redirect(url_for('login'))
    if result.role != 'admin':
        flash('No tienes permisos.', 'danger')
        return redirect(url_for('menu'))

    data = _get_entidad_form_from_request(request)
    try:
        entidad = EntidadFinanciera(**data)
        # Dirección completa auxiliar
        parts = [data.get('direccion'), data.get('numero'), data.get('codigo_postal'), data.get('localidad'), data.get('provincia'), data.get('comunidad_autonoma')]
        entidad.direccion_completa = ', '.join([p for p in parts if p])
        db.session.add(entidad)
        db.session.commit()
        flash('Entidad creada correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al crear entidad: {str(e)}', 'danger')
    return redirect(url_for('admin_bancos'))


@app.route('/admin/entidades/<int:entidad_id>/editar', methods=['POST'])
def admin_editar_banco(entidad_id):
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, 'warning')
        return redirect(url_for('login'))
    if result.role != 'admin':
        flash('No tienes permisos.', 'danger')
        return redirect(url_for('menu'))

    entidad = EntidadFinanciera.query.get_or_404(entidad_id)
    data = _get_entidad_form_from_request(request)
    try:
        for k, v in data.items():
            setattr(entidad, k, v)
        parts = [data.get('direccion'), data.get('numero'), data.get('codigo_postal'), data.get('localidad'), data.get('provincia'), data.get('comunidad_autonoma')]
        entidad.direccion_completa = ', '.join([p for p in parts if p])
        db.session.commit()
        flash('Entidad actualizada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar: {str(e)}', 'danger')
    return redirect(url_for('admin_bancos'))


@app.route('/admin/entidades/<int:entidad_id>/eliminar', methods=['POST'])
def admin_eliminar_banco(entidad_id):
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, 'warning')
        return redirect(url_for('login'))
    if result.role != 'admin':
        flash('No tienes permisos.', 'danger')
        return redirect(url_for('menu'))

    try:
        entidad = EntidadFinanciera.query.get_or_404(entidad_id)
        db.session.delete(entidad)
        db.session.commit()
        flash('Entidad eliminada.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    return redirect(url_for('admin_bancos'))


@app.route('/admin/entidades/export')
def admin_export_entidades():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, 'warning')
        return redirect(url_for('login'))
    if result.role != 'admin':
        flash('No tienes permisos.', 'danger')
        return redirect(url_for('menu'))

    entidades = EntidadFinanciera.query.order_by(EntidadFinanciera.nombre.asc()).all()
    from io import BytesIO
    import pandas as pd
    buffer = BytesIO()
    rows = []
    for e in entidades:
        rows.append({
            'NOMBRE': e.nombre,
            'NOMBRE_COMERCIAL': e.nombre_comercial,
            'TIPO_ENTIDAD': e.tipo_entidad,
            'CODIGO_ENTIDAD': e.codigo_entidad,
            'DIRECCION': e.direccion,
            'NUMERO': e.numero,
            'CODIGO_POSTAL': e.codigo_postal,
            'LOCALIDAD': e.localidad,
            'PROVINCIA': e.provincia,
            'CCAA': e.comunidad_autonoma,
            'TELEFONO': e.telefono,
            'WEB': e.web,
            'EMAIL_DOC9': e.email_doc9,
            'EMAIL_RGPD': e.email_rgpd,
            'EMAIL_GENERAL': e.email_general,
            'ESTADO': e.estado,
            'SUPERVISOR': e.supervisor_principal,
        })

    df = pd.DataFrame(rows)
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='ENTIDADES')
        ws = writer.sheets['ENTIDADES']
        for col in ws.iter_cols(min_row=1, max_row=1):
            for cell in col:
                cell.font = cell.font.copy(bold=True)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='entidades_financieras.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@app.route("/admin/doc9")
def admin_doc9():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    if usuario.role != "admin":
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for("menu"))
    
    return render_template("admin_doc9.html")

@app.route("/admin/logs")
def admin_logs():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    if usuario.role != "admin":
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for("menu"))
    
    logs = AccessLog.query.order_by(AccessLog.fecha.desc()).limit(100).all()
    return render_template("admin_logs.html", logs=logs)

# Panel de administración
@app.route("/panel_admin")
def panel_admin():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))

    usuario = result
    if usuario.role != "admin":
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for("menu"))

    formularios = FormularioRPC.query.order_by(FormularioRPC.created_at.desc()).all()
    return render_template("panel_admin.html", formularios=formularios)

# Rutas para formularios RPC
@app.route("/rpc", methods=["GET", "POST"])
def formulario_rpc():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    
    # Verificar permisos para lectores
    if usuario.role == "lector":
        formularios_permitidos = usuario.get_formularios_permitidos()
        if "rpc" not in formularios_permitidos:
            flash("No tienes permisos para acceder a este formulario.", "danger")
            return redirect(url_for("menu"))
    
    if request.method == "POST":
        # Recopilar datos del formulario
        form_data = {
            "nombre": request.form.get("nombre"),
            "apellidos": request.form.get("apellidos"),
            "dni_nie": request.form.get("dni_nie"),
            "observaciones": request.form.get("observaciones"),
            "tipo_concurso": request.form.get("tipo_concurso") if usuario.role == "admin" else "",
            "fecha_presentacion": request.form.get("fecha_presentacion") if usuario.role == "admin" else ""
        }
        
        # Guardar en base de datos
        formulario = FormularioRPC(
            nombre=form_data["nombre"],
            apellidos=form_data["apellidos"],
            dni_nie=form_data["dni_nie"],
            observaciones=form_data["observaciones"],
            usuario_id=usuario.id
        )
        
        if usuario.role == "admin":
            formulario.tipo_concurso = form_data["tipo_concurso"]
            fecha_presentacion = form_data["fecha_presentacion"]
            if fecha_presentacion:
                formulario.fecha_presentacion = datetime.strptime(fecha_presentacion, "%Y-%m-%d").date()
        
        db.session.add(formulario)
        db.session.commit()
        
        # Generar PDF
        try:
            pdf_filename = pdf_generator.generate_form_rpc_pdf(form_data)
            flash(f"Formulario RPC guardado y PDF generado: {pdf_filename}", "success")
            
            # Guardar nombre del PDF en sesión para posible descarga
            session['last_generated_pdf'] = pdf_filename
            
        except Exception as e:
            flash(f"Formulario guardado pero error al generar PDF: {str(e)}", "warning")
        
        return redirect(url_for("menu"))
    
    return render_template("formulario_rpc.html", usuario=usuario)

# Rutas para Documento 9
@app.route("/documento9")
def documento9():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    
    # Verificar permisos para lectores
    if usuario.role == "lector":
        formularios_permitidos = usuario.get_formularios_permitidos()
        if "doc9" not in formularios_permitidos:
            flash("No tienes permisos para acceder a este formulario.", "danger")
            return redirect(url_for("menu"))
    
    return render_template("documento9.html")

@app.route("/doc9", methods=["GET", "POST"])
def doc9():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    
    # Verificar permisos para lectores
    if usuario.role == "lector":
        formularios_permitidos = usuario.get_formularios_permitidos()
        if "doc9" not in formularios_permitidos:
            flash("No tienes permisos para acceder a este formulario.", "danger")
            return redirect(url_for("menu"))
    
    if request.method == "POST":
        # Lógica para procesar el formulario Doc 9
        flash("Documento 9 procesado correctamente.", "success")
        return redirect(url_for("menu"))
    
    return render_template("doc9.html")

@app.route("/doc9_form", methods=["GET", "POST"])
def doc9_form():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    
    # Verificar permisos para lectores
    if usuario.role == "lector":
        formularios_permitidos = usuario.get_formularios_permitidos()
        if "doc9" not in formularios_permitidos:
            flash("No tienes permisos para acceder a este formulario.", "danger")
            return redirect(url_for("menu"))
    
    # Preparar listas y bancos
    bancos = EntidadFinanciera.query.order_by(EntidadFinanciera.nombre.asc()).all()
    bancos_ctx = [{
        'nombre': b.nombre,
        'direccion': b.direccion or '',
        'num': (b.numero if hasattr(b, 'numero') else None) or (b.num if hasattr(b, 'num') else ''),
        'cp': (b.codigo_postal if hasattr(b, 'codigo_postal') else None) or (b.cp if hasattr(b, 'cp') else ''),
        'localidad': b.localidad or '',
        'provincia': b.provincia or '',
        'ccaa': (b.comunidad_autonoma if hasattr(b, 'comunidad_autonoma') else None) or (b.ccaa if hasattr(b, 'ccaa') else ''),
        'email_general': (b.email_general or '') or (b.email_doc9 or '')
    } for b in bancos]

    tipos_deuda = [
        "Tarjeta de crédito",
        "Préstamo personal",
        "Préstamo financiación vehículo",
        "Préstamo hipotecario/Deudor solidario",
        "Descubierto en cuenta",
        "Línea de crédito",
    ]
    cuotas_opciones = ["SI", "NO"]
    garantias_opciones = ["SI", "NO", "Otros"]

    registros = session.get('doc9_registros', [])

    if request.method == "POST":
        action = request.form.get('action', 'add')
        if action == 'add':
            acreedor = request.form.get('acreedor', '').strip()
            domicilio = request.form.get('domicilio', '').strip()
            credito = request.form.get('credito', '').strip()
            importe = request.form.get('importe', '').strip()
            cuotas = request.form.get('cuotas', '').strip()
            garantias = request.form.get('garantias', '').strip()
            texto_libre = request.form.get('texto_libre', '').strip()

            if garantias == 'Otros' and texto_libre:
                garantias_valor = f"Otros: {texto_libre}"
            else:
                garantias_valor = garantias

            if not acreedor or not credito or not importe:
                flash("Completa los campos obligatorios.", "warning")
                return redirect(url_for('doc9_form'))

            try:
                # normalizar importe a número con punto decimal
                importe_num = float(str(importe).replace(',', '.'))
            except Exception:
                flash("Importe inválido.", "warning")
                return redirect(url_for('doc9_form'))

            nuevo = {
                "Acreedor": acreedor,
                "Domicilio y correo electrónico": domicilio,
                "Naturaleza del crédito": credito,
                "Crédito pendiente": f"{importe_num:.2f}",
                "Cuotas vencidas": cuotas or "",
                "Garantías": garantias_valor or "",
            }
            registros.append(nuevo)
            session['doc9_registros'] = registros
            flash("Acreedor añadido al Documento 9.", "success")
            return redirect(url_for('doc9_form'))

    return render_template(
        "doc9_form.html",
        bancos=bancos_ctx,
        tipos_deuda=tipos_deuda,
        cuotas_opciones=cuotas_opciones,
        garantias_opciones=garantias_opciones,
        registros=registros
    )

@app.route('/doc9_export')
def doc9_export():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))

    registros = session.get('doc9_registros', [])
    if not registros:
        flash("No hay registros para exportar.", "warning")
        return redirect(url_for('doc9_form'))

    # Patrón fijo de columnas y normalización de datos
    columnas = [
        "ACREEDOR",
        "DOMICILIO Y CORREO ELECTRÓNICO",
        "NATURALEZA DEL CRÉDITO",
        "CRÉDITO PENDIENTE",
        "CUOTAS VENCIDAS",
        "GARANTÍAS",
    ]

    filas = []
    for r in registros:
        # Convertir importe a número
        importe_raw = (
            r.get("Crédito pendiente")
            or r.get("CRÉDITO PENDIENTE")
            or r.get("Crédito pendiente (€)")
            or r.get("CRÉDITO PENDIENTE (€)")
            or "0"
        )
        try:
            importe_val = float(str(importe_raw).replace('.', '').replace(',', '.'))
        except Exception:
            importe_val = 0.0
        filas.append({
            "ACREEDOR": r.get("Acreedor") or r.get("ACREEDOR", ""),
            "DOMICILIO Y CORREO ELECTRÓNICO": r.get("Domicilio y correo electrónico") or r.get("DOMICILIO Y CORREO ELECTRÓNICO", ""),
            "NATURALEZA DEL CRÉDITO": r.get("Naturaleza del crédito") or r.get("NATURALEZA DEL CRÉDITO", ""),
            "CRÉDITO PENDIENTE": importe_val,
            "CUOTAS VENCIDAS": r.get("Cuotas vencidas") or r.get("CUOTAS VENCIDAS", ""),
            "GARANTÍAS": r.get("Garantías") or r.get("GARANTÍAS", ""),
        })

    # Exportar a Excel (XLSX)
    from io import BytesIO
    import pandas as pd
    output = BytesIO()
    df = pd.DataFrame(filas, columns=columnas)
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='DOC9')
        # Formatos y anchos básicos
        ws = writer.sheets['DOC9']
        for col_cells in ws.iter_cols(min_row=1, max_row=1):
            for cell in col_cells:
                cell.font = cell.font.copy(bold=True)
        # Anchos aproximados
        widths = [28, 46, 30, 20, 18, 22]
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[chr(64+i)].width = w

        # Formato numérico para importe (columna D)
        for cell in ws['D'][1:]:  # excepto cabecera
            cell.number_format = '#,##0.00'

        # Fila de TOTAL PASIVO
        total_row = len(filas) + 2  # +1 cabecera, +1 porque Excel es 1-based
        ws.cell(row=total_row, column=3, value='TOTAL PASIVO')
        total_cell = ws.cell(row=total_row, column=4)
        total_cell.value = f"=SUM(D2:D{len(filas)+1})"
        total_cell.number_format = '#,##0.00'
        # Negrita en total
        ws.cell(row=total_row, column=3).font = ws.cell(row=1, column=1).font.copy(bold=True)
        ws.cell(row=total_row, column=4).font = ws.cell(row=1, column=1).font.copy(bold=True)

    output.seek(0)
    from flask import send_file
    filename = "DOC. 9 Lista Acreedores.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/doc9_clear')
def doc9_clear():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    session.pop('doc9_registros', None)
    flash("Lista del Documento 9 vaciada.", "info")
    return redirect(url_for('doc9_form'))

# Rutas para gestión de derechos
@app.route("/gestion_derechos_step1")
def gestion_derechos_step1():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    return render_template("gestion_derechos_step1.html")

@app.route("/gestion_derechos_solicitante", methods=["GET", "POST"])
def gestion_derechos_solicitante():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    if request.method == "POST":
        # Recopilar datos del formulario
        form_data = {
            "tratamiento": request.form.get("tratamiento"),
            "nombre": request.form.get("nombre"),
            "apellidos": request.form.get("apellidos"),
            "dni": request.form.get("dni"),
            "email": request.form.get("email"),
            "cp": request.form.get("cp"),
            "direccion": request.form.get("direccion"),
            "numero": request.form.get("numero"),
            "localidad": request.form.get("localidad"),
            "provincia": request.form.get("provincia"),
            "ccaa": request.form.get("ccaa"),
            "localidad_firma": request.form.get("localidad_firma"),
            "modelo_destino": request.form.get("modelo_destino")
        }
        
        # Validar DNI/NIE
        dni_nie = form_data.get("dni", "").strip()
        if dni_nie:
            from utils.dni_validator import validar_dni_nie, limpiar_dni_nie
            dni_nie_limpio = limpiar_dni_nie(dni_nie)
            dni_valido, dni_mensaje = validar_dni_nie(dni_nie_limpio)
            
            if not dni_valido:
                flash(f"DNI/NIE inválido: {dni_mensaje}", "danger")
                return render_template("gestion_derechos_solicitante.html", error_dni=dni_mensaje)
            
            # Actualizar con DNI/NIE limpio
            form_data["dni"] = dni_nie_limpio
        
        # Guardar en sesión para uso posterior
        session['rights_form_data'] = form_data
        
        flash("Datos del solicitante guardados correctamente. DNI/NIE validado.", "success")
        return redirect(url_for("datos_procedimiento"))
    
    return render_template("gestion_derechos_solicitante.html")

@app.route("/gestion_derechos_opcion_pdf")
def gestion_derechos_opcion_pdf():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    return render_template("gestion_derechos_opcion_pdf.html")

# Inicializar generadores
pdf_generator = PDFGenerator()
email_sender = EmailSender()

@app.route("/gestion_derechos_enviar_pdf")
def gestion_derechos_enviar_pdf():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    # Obtener datos de la sesión (en una implementación real, estos vendrían de la base de datos)
    form_data = session.get('rights_form_data', {})
    
    if not form_data:
        flash("No hay datos de formulario para procesar", "warning")
        return redirect(url_for("gestion_derechos_step1"))
    
    # Generar PDF
    try:
        pdf_filename = pdf_generator.generate_rights_pdf(form_data)
        
        # Enviar por email
        recipient_email = form_data.get('email', '')
        if recipient_email:
            success, message = email_sender.send_rights_rgpd_email(recipient_email, form_data, pdf_filename)
            if success:
                flash(f"PDF generado y enviado correctamente a {recipient_email}", "success")
            else:
                flash(f"PDF generado pero error al enviar email: {message}", "warning")
        else:
            flash("PDF generado correctamente", "success")
        
        # Limpiar datos de sesión
        session.pop('rights_form_data', None)
        
    except Exception as e:
        flash(f"Error al generar PDF: {str(e)}", "danger")
    
    return render_template("gestion_derechos_enviar_pdf.html")

@app.route("/gestion_derechos_descarga_pdf")
def gestion_derechos_descarga_pdf():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    # Obtener datos de la sesión
    form_data = session.get('rights_form_data', {})
    
    if not form_data:
        flash("No hay datos de formulario para procesar", "warning")
        return redirect(url_for("gestion_derechos_step1"))
    
    # Generar PDF
    try:
        pdf_filename = pdf_generator.generate_rights_pdf(form_data)
        flash("PDF generado correctamente", "success")
        
        # Limpiar datos de sesión
        session.pop('rights_form_data', None)
        
    except Exception as e:
        flash(f"Error al generar PDF: {str(e)}", "danger")
    
    return render_template("gestion_derechos_descarga_pdf.html")

@app.route("/download_pdf/<filename>")
def download_pdf(filename):
    """Descarga un PDF generado"""
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    try:
        file_path = os.path.join("static/pdfs", filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True, download_name=filename)
        else:
            flash("Archivo no encontrado", "danger")
            return redirect(url_for("menu"))
    except Exception as e:
        flash(f"Error al descargar archivo: {str(e)}", "danger")
        return redirect(url_for("menu"))

@app.route("/send_pdf_email/<filename>")
def send_pdf_email(filename):
    """Envía un PDF por email"""
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    try:
        # Obtener email del usuario actual
        user_email = result.email if hasattr(result, 'email') and result.email else None
        
        if not user_email:
            flash("No se encontró email del usuario", "danger")
            return redirect(url_for("menu"))
        
        # Enviar email
        success, message = email_sender.send_pdf_email(
            user_email,
            f"Documento {filename}",
            f"Se adjunta el documento {filename} generado por el sistema.",
            filename
        )
        
        if success:
            flash(f"Email enviado correctamente a {user_email}", "success")
        else:
            flash(f"Error al enviar email: {message}", "danger")
        
    except Exception as e:
        flash(f"Error al enviar email: {str(e)}", "danger")
    
    return redirect(url_for("menu"))

@app.route("/gestion_derechos_error")
def gestion_derechos_error():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    return render_template("gestion_derechos_error.html")

# Rutas para datos de procedimiento
@app.route("/datos_procedimiento", methods=["GET", "POST"])
def datos_procedimiento():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    # Verificar que hay datos del solicitante en sesión
    rights_form_data = session.get('rights_form_data')
    if not rights_form_data:
        flash("Debe completar primero los datos del solicitante.", "warning")
        return redirect(url_for("gestion_derechos_step1"))
    
    if request.method == "POST":
        # Recopilar datos del procedimiento
        procedure_data = {
            "num_procedimiento": request.form.get("num_procedimiento"),
            "juzgado": request.form.get("juzgado"),
            "fecha_epi": request.form.get("fecha_epi"),
            "fecha_testimonio": request.form.get("fecha_testimonio"),
            # Nuevos campos
            "fecha_presentacion_demanda": request.form.get("fecha_presentacion_demanda"),
            "fecha_admision": request.form.get("fecha_admision"),
            "tipo_concurso": request.form.get("tipo_concurso"),
        }

        # Guardar también en BD para analítica
        try:
            proc = Procedimiento(
                num_procedimiento=procedure_data["num_procedimiento"] or "",
                juzgado=procedure_data["juzgado"] or "",
                usuario_id=session.get("user_id")
            )

            # Parseo de fechas soportando DD-MM-AAAA y AAAA-MM-DD
            from datetime import datetime as _dt
            def _parse_date(value):
                if not value:
                    return None
                for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
                    try:
                        return _dt.strptime(value, fmt).date()
                    except Exception:
                        continue
                return None

            proc.fecha_epi = _parse_date(procedure_data["fecha_epi"])
            proc.fecha_testimonio = _parse_date(procedure_data["fecha_testimonio"])
            proc.fecha_presentacion_demanda = _parse_date(procedure_data["fecha_presentacion_demanda"])
            proc.fecha_admision = _parse_date(procedure_data["fecha_admision"])

            # Tipo de concurso
            if procedure_data["tipo_concurso"] in ("Con masa", "Sin masa"):
                proc.tipo_concurso = procedure_data["tipo_concurso"]

            db.session.add(proc)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # No interrumpimos el flujo de RGPD, solo informamos
            flash(f"Aviso: no se pudo registrar el procedimiento para analítica: {str(e)}", "warning")

        # Combinar datos del solicitante y del procedimiento en sesión (para el flujo existente)
        complete_data = {**rights_form_data, **procedure_data}
        session['rights_form_data'] = complete_data

        flash("Datos del procedimiento guardados correctamente.", "success")
        return redirect(url_for("gestion_derechos_opcion_pdf"))
    
    # Importar lista completa de juzgados mercantiles 2025
    from juzgados_mercantil_2025 import JUZGADOS_MERCANTILES_2025
    
    # Lista de juzgados para el formulario (solo mercantiles)
    juzgados = JUZGADOS_MERCANTILES_2025
    
    return render_template("datos_procedimiento.html", juzgados=juzgados)

# Analítica de juzgados (admin)
@app.route("/admin/juzgados_analytics")
def admin_juzgados_analytics():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))

    usuario = result
    if usuario.role != "admin":
        flash("No tienes permisos para acceder a esta sección.", "danger")
        return redirect(url_for("menu"))

    # Filtro por rango de fechas (sobre fecha_presentacion_demanda)
    presentacion_start_str = request.args.get('presentacion_start', '').strip()
    presentacion_end_str = request.args.get('presentacion_end', '').strip()
    admision_start_str = request.args.get('admision_start', '').strip()
    admision_end_str = request.args.get('admision_end', '').strip()

    query = Procedimiento.query.filter(
        Procedimiento.fecha_presentacion_demanda.isnot(None),
        Procedimiento.fecha_admision.isnot(None),
        Procedimiento.juzgado.isnot(None)
    )

    from datetime import datetime as _dt
    filtro_aplicado = False
    presentacion_start = None
    presentacion_end = None
    admision_start = None
    admision_end = None

    try:
        # Parse de fechas soportando DD-MM-AAAA y AAAA-MM-DD
        def _parse_date(value):
            if not value:
                return None
            for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
                try:
                    return _dt.strptime(value, fmt).date()
                except Exception:
                    continue
            return None

        presentacion_start = _parse_date(presentacion_start_str)
        presentacion_end = _parse_date(presentacion_end_str)
        admision_start = _parse_date(admision_start_str)
        admision_end = _parse_date(admision_end_str)

        # Corregir rangos invertidos
        if presentacion_start and presentacion_end and presentacion_start > presentacion_end:
            presentacion_start, presentacion_end = presentacion_end, presentacion_start
        if admision_start and admision_end and admision_start > admision_end:
            admision_start, admision_end = admision_end, admision_start

        # Aplicar filtros independientes
        if presentacion_start:
            query = query.filter(Procedimiento.fecha_presentacion_demanda >= presentacion_start)
            filtro_aplicado = True
        if presentacion_end:
            query = query.filter(Procedimiento.fecha_presentacion_demanda <= presentacion_end)
            filtro_aplicado = True
        if admision_start:
            query = query.filter(Procedimiento.fecha_admision >= admision_start)
            filtro_aplicado = True
        if admision_end:
            query = query.filter(Procedimiento.fecha_admision <= admision_end)
            filtro_aplicado = True
    except Exception:
        flash("Formato de fechas inválido. Use DD-MM-AAAA.", "warning")

    registros = query.all()

    from collections import defaultdict
    import math

    dias_por_juzgado = defaultdict(list)
    for r in registros:
        dias = (r.fecha_admision - r.fecha_presentacion_demanda).days
        if dias is not None and dias >= 0:
            dias_por_juzgado[r.juzgado].append(dias)

    promedios = []
    for juz, lista in dias_por_juzgado.items():
        if lista:
            avg = sum(lista) / len(lista)
            promedios.append({
                "juzgado": juz,
                "promedio_dias": round(avg, 1),
                "muestras": len(lista)
            })

    # Ordenar y seleccionar top 6
    mas_rapidos = sorted(promedios, key=lambda x: x["promedio_dias"])[:6]
    mas_lentos = sorted(promedios, key=lambda x: x["promedio_dias"], reverse=True)[:6]

    return render_template(
        "admin_juzgados_analytics.html",
        mas_rapidos=mas_rapidos,
        mas_lentos=mas_lentos,
        total_registros=len(registros),
        presentacion_start=presentacion_start.strftime('%d-%m-%Y') if presentacion_start else '',
        presentacion_end=presentacion_end.strftime('%d-%m-%Y') if presentacion_end else '',
        admision_start=admision_start.strftime('%d-%m-%Y') if admision_start else '',
        admision_end=admision_end.strftime('%d-%m-%Y') if admision_end else '',
        filtro_aplicado=filtro_aplicado
    )

# Rutas para crear usuario
@app.route("/crear_usuario", methods=["GET", "POST"])
def crear_usuario():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    if usuario.role != "admin":
        flash("No tienes permisos para crear usuarios.", "danger")
        return redirect(url_for("menu"))
    
    if request.method == "POST":
        try:
            # Obtener datos del formulario
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            nombre = request.form.get('nombre', '').strip()
            apellidos = request.form.get('apellidos', '').strip()
            dni_nie = request.form.get('dni_nie', '').strip()
            email = request.form.get('email', '').strip()
            telefono = request.form.get('telefono', '').strip()
            role = request.form.get('rol', 'usuario')
            
            # Validaciones básicas
            if not username or not password or not nombre or not apellidos:
                flash("Todos los campos obligatorios deben estar completos.", "danger")
                return render_template("crear_usuario.html", error="Campos obligatorios incompletos")
            
            if password != confirm_password:
                flash("Las contraseñas no coinciden.", "danger")
                return render_template("crear_usuario.html", error="Contraseñas no coinciden")
            
            if len(password) < 8:
                flash("La contraseña debe tener al menos 6 caracteres.", "danger")
                return render_template("crear_usuario.html", error="Contraseña muy corta")
            
            # Mensaje coherente
            if len(password) < 8:
                return render_template("crear_usuario.html", error="La contraseña debe tener al menos 8 caracteres.")
            
            # Validar DNI/NIE
            from utils.dni_validator import validar_dni_nie, limpiar_dni_nie
            dni_nie_limpio = limpiar_dni_nie(dni_nie)
            if dni_nie_limpio:
                dni_valido, dni_mensaje = validar_dni_nie(dni_nie_limpio)
                if not dni_valido:
                    flash(f"DNI/NIE inválido: {dni_mensaje}", "danger")
                    return render_template("crear_usuario.html", error=f"DNI/NIE inválido: {dni_mensaje}")
            
            # Verificar si el usuario ya existe
            usuario_existente = User.query.filter_by(username=username).first()
            if usuario_existente:
                flash("El nombre de usuario ya existe.", "danger")
                return render_template("crear_usuario.html", error="Usuario ya existe")
            
            # Verificar si el DNI/NIE ya existe
            if dni_nie_limpio:
                dni_existente = User.query.filter_by(dni_nie=dni_nie_limpio).first()
                if dni_existente:
                    flash("El DNI/NIE ya está registrado.", "danger")
                    return render_template("crear_usuario.html", error="DNI/NIE ya registrado")
            
            # Crear nuevo usuario
            nuevo_usuario = User(
                username=username,
                password_hash=generate_password_hash(password),
                role=role,
                nombre=nombre,
                apellidos=apellidos,
                dni_nie=dni_nie_limpio,
                email=email,
                telefono=telefono,
                is_enabled=True
            )
            
            # Configuración específica para lectores
            if role == "lector":
                from datetime import datetime, timedelta
                fecha_expiracion = request.form.get('fecha_expiracion')
                if fecha_expiracion:
                    nuevo_usuario.fecha_expiracion = datetime.strptime(fecha_expiracion, '%Y-%m-%d')
                else:
                    nuevo_usuario.fecha_expiracion = datetime.utcnow() + timedelta(days=10)
                
                formularios_permitidos = request.form.getlist('formularios_permitidos')
                nuevo_usuario.formularios_permitidos = ','.join(formularios_permitidos) if formularios_permitidos else 'generico'
            
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            flash(f"Usuario '{username}' creado correctamente.", "success")
            return redirect(url_for("admin_usuarios"))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear usuario: {str(e)}", "danger")
            return render_template("crear_usuario.html", error=f"Error: {str(e)}")
    
    return render_template("crear_usuario.html")

@app.route("/admin/crear_usuario", methods=["POST"])
def admin_crear_usuario():
    """Ruta para crear usuario desde el modal del panel de administración"""
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    if usuario.role != "admin":
        flash("No tienes permisos para crear usuarios.", "danger")
        return redirect(url_for("admin_usuarios"))
    
    try:
        # Obtener datos del formulario
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        nombre = request.form.get('nombre', '').strip()
        apellidos = request.form.get('apellidos', '').strip()
        dni_nie = request.form.get('dni_nie', '').strip()
        email = request.form.get('email', '').strip()
        telefono = request.form.get('telefono', '').strip()
        role = request.form.get('role', 'lector')
        is_enabled = request.form.get('is_enabled', '1') == '1'
        
        # Validaciones básicas
        if not username or not nombre or not apellidos:
            flash("Usuario, nombre y apellidos son obligatorios.", "danger")
            return redirect(url_for("admin_usuarios"))
        
        # Permitir alta sin contraseña: generar una aleatoria y enviarla por email
        generated_password = None
        if not password:
            import secrets, string
            alphabet = string.ascii_letters + string.digits
            generated_password = ''.join(secrets.choice(alphabet) for _ in range(10))
            password = generated_password
            confirm_password = generated_password
        
        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for("admin_usuarios"))
        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "danger")
            return redirect(url_for("admin_usuarios"))
        
        # Validar DNI/NIE
        from utils.dni_validator import validar_dni_nie, limpiar_dni_nie
        dni_nie_limpio = limpiar_dni_nie(dni_nie)
        if dni_nie_limpio:
            dni_valido, dni_mensaje = validar_dni_nie(dni_nie_limpio)
            if not dni_valido:
                flash(f"DNI/NIE inválido: {dni_mensaje}", "danger")
                return redirect(url_for("admin_usuarios"))
        
        # Verificar si el usuario ya existe
        usuario_existente = User.query.filter_by(username=username).first()
        if usuario_existente:
            flash("El nombre de usuario ya existe.", "danger")
            return redirect(url_for("admin_usuarios"))
        
        # Verificar si el DNI/NIE ya existe
        if dni_nie_limpio:
            dni_existente = User.query.filter_by(dni_nie=dni_nie_limpio).first()
            if dni_existente:
                flash("El DNI/NIE ya está registrado.", "danger")
                return redirect(url_for("admin_usuarios"))
        
        # Crear nuevo usuario
        nuevo_usuario = User(
            username=username,
            password_hash=generate_password_hash(password),
            role=role,
            nombre=nombre,
            apellidos=apellidos,
            dni_nie=dni_nie_limpio,
            email=email,
            telefono=telefono,
            is_enabled=is_enabled
        )
        
        # Configuración específica para lectores
        if role == "lector":
            from datetime import datetime, timedelta
            fecha_expiracion = request.form.get('fecha_expiracion')
            if fecha_expiracion:
                nuevo_usuario.fecha_expiracion = datetime.strptime(fecha_expiracion, '%Y-%m-%d')
            else:
                nuevo_usuario.fecha_expiracion = datetime.utcnow() + timedelta(days=10)
            
            formularios_permitidos = request.form.getlist('formularios_permitidos')
            nuevo_usuario.formularios_permitidos = ','.join(formularios_permitidos) if formularios_permitidos else 'generico'
        
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        flash(f"Usuario '{username}' creado correctamente.", "success")

        # Si se generó contraseña, enviar email de bienvenida
        if generated_password and email:
            subject = "Bienvenido - Credenciales de acceso"
            # Si existe plantilla DOCX, la usamos como HTML
            docx_path = os.path.join(BASE_DIR, 'static', 'email_templates', 'bienvenida.docx')
            try:
                if os.path.exists(docx_path):
                    html, inline_images = email_sender.render_email_from_docx(docx_path, {
                        'nombre': nombre,
                        'apellidos': apellidos,
                        'username': username,
                        'password_temporal': generated_password,
                    })
                    email_sender.send_notification_email(email, subject, html, html=True, inline_images=inline_images)
                else:
                    body = (
                        f"Hola {nombre} {apellidos},\n\n"
                        f"Se ha creado tu usuario en el sistema.\n\n"
                        f"Usuario: {username}\n"
                        f"Contraseña temporal: {generated_password}\n\n"
                        f"Por seguridad, cambia tu contraseña tras iniciar sesión."
                    )
                    email_sender.send_notification_email(email, subject, body)
            except Exception:
                pass
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error al crear usuario: {str(e)}", "danger")
    
    return redirect(url_for("admin_usuarios"))


@app.route("/admin/usuarios/<int:user_id>/editar", methods=["POST"])
def admin_editar_usuario(user_id: int):
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))

    usuario_admin = result
    if usuario_admin.role != "admin":
        flash("No tienes permisos para editar usuarios.", "danger")
        return redirect(url_for("menu"))

    user = User.query.get_or_404(user_id)
    try:
        # Datos básicos
        user.nombre = request.form.get('nombre', '').strip()
        user.apellidos = request.form.get('apellidos', '').strip()
        user.email = request.form.get('email', '').strip()
        user.telefono = request.form.get('telefono', '').strip()
        new_role = request.form.get('role', user.role)
        user.role = new_role if new_role in ("admin", "usuario", "lector") else user.role
        user.is_enabled = request.form.get('is_enabled', '1') == '1'

        # Cambio de contraseña opcional
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if new_password:
            if new_password != confirm_password:
                flash("Las contraseñas no coinciden.", "danger")
                return redirect(url_for('admin_usuarios'))
            if len(new_password) < 6:
                flash("La contraseña debe tener al menos 6 caracteres.", "danger")
                return redirect(url_for('admin_usuarios'))
            user.password_hash = generate_password_hash(new_password)

        # Habilitar usuario (+10 días) para lectores
        habilitar_10 = request.form.get('habilitar_10') == '1'
        if habilitar_10 and user.role == 'lector':
            from datetime import datetime as _dt, timedelta as _td
            base = user.fecha_expiracion if user.fecha_expiracion and user.fecha_expiracion > _dt.utcnow() else _dt.utcnow()
            user.fecha_expiracion = base + _td(days=10)

        db.session.commit()
        flash("Usuario actualizado correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar usuario: {str(e)}", "danger")
    return redirect(url_for('admin_usuarios'))

# Rutas para páginas informativas
@app.route("/bienvenida")
def bienvenida():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    return render_template("bienvenida.html")

@app.route("/consulta")
def consulta():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    return render_template("consulta.html")

@app.route("/derechos_rgpd")
def derechos_rgpd():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    return render_template("derechos_rgpd.html")

@app.route("/derecho_acceso", methods=["GET", "POST"])
def derecho_acceso():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    datos = {
        "nombre": "",
        "apellidos": "",
        "dni_nie": "",
        "email": "",
        "telefono": "",
        "direccion": "",
        "motivo": "acceso",
        # Selección de destino
        "destino_tipo": "",
    }
    
    # Para lectores, usar datos precargados
    if usuario.role == "lector" and "datos_lector" in session:
        datos_lector = session["datos_lector"]
        datos.update({
            "nombre": datos_lector.get("nombre", ""),
            "apellidos": datos_lector.get("apellidos", ""),
            "email": datos_lector.get("email", ""),
            "telefono": datos_lector.get("telefono", ""),
            "direccion": datos_lector.get("direccion", "")
        })
    elif usuario.dni_nie:
        datos["dni_nie"] = usuario.dni_nie
    
    if request.method == "POST":
        for campo in ["nombre","apellidos","dni_nie","email","telefono","direccion"]:
            datos[campo] = request.form.get(campo, "")
        datos["destino_tipo"] = request.form.get("destino_tipo", "")

        # Construir datos de destinatario
        destinatario = {}
        if datos["destino_tipo"] in ("equifax_asnef", "badexcug"):
            destinatario = PREDEFINED_DESTINATARIOS.get(datos["destino_tipo"], {}).copy()
        elif datos["destino_tipo"] == "banco":
            # obtener banco por id
            banco_id = request.form.get("destino_banco")
            try:
                if banco_id:
                    b = EntidadFinanciera.query.get(int(banco_id))
                    if b:
                        destinatario = {
                            "clave": "banco",
                            "nombre": b.nombre,
                            "email": b.email_rgpd or b.email_general or "",
                            "tipo_via": "",
                            "via": b.direccion or b.direccion_completa or "",
                            "numero": b.numero or "",
                            "extras": "",
                            "cp": b.codigo_postal or "",
                            "localidad": b.localidad or "",
                            "provincia": b.provincia or "",
                            "ccaa": b.comunidad_autonoma or "",
                        }
            except Exception:
                pass
        else:
            # Otros: recoger del formulario
            destinatario = {
                "clave": "otros",
                "nombre": request.form.get("dest_nombre", ""),
                "email": request.form.get("dest_email", ""),
                "tipo_via": request.form.get("dest_tipo_via", ""),
                "via": request.form.get("dest_via", ""),
                "numero": request.form.get("dest_numero", ""),
                "extras": request.form.get("dest_extras", ""),
                "cp": request.form.get("dest_cp", ""),
                "localidad": request.form.get("dest_localidad", ""),
                "provincia": request.form.get("dest_provincia", ""),
                "ccaa": request.form.get("dest_ccaa", ""),
            }

        # Generar PDF de derecho de acceso (con destinatario)
        try:
            payload = {**datos, "destinatario": destinatario}
            pdf_filename = pdf_generator.generate_rgpd_acceso_pdf(payload)
            flash(f"Solicitud de derecho de acceso generada: {pdf_filename}", "success")
            return redirect(url_for("derecho_acceso_completado", filename=pdf_filename))
        except Exception as e:
            flash(f"Error al generar PDF: {str(e)}", "danger")
    
    # bancos para selector
    bancos = EntidadFinanciera.query.order_by(EntidadFinanciera.nombre.asc()).all()
    tipos_via = TipoVia.query.filter_by(activo=True).order_by(TipoVia.nombre.asc()).all()
    return render_template("derecho_acceso.html", datos=datos, usuario=usuario, bancos=bancos, tipos_via=tipos_via)

@app.route("/derecho_supresion", methods=["GET", "POST"])
def derecho_supresion():
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    datos = {
        "nombre": "",
        "apellidos": "",
        "dni_nie": "",
        "email": "",
        "telefono": "",
        "direccion": "",
        "motivo": "supresion",
        # Selección de destino
        "destino_tipo": "",
    }
    
    # Para lectores, usar datos precargados
    if usuario.role == "lector" and "datos_lector" in session:
        datos_lector = session["datos_lector"]
        datos.update({
            "nombre": datos_lector.get("nombre", ""),
            "apellidos": datos_lector.get("apellidos", ""),
            "email": datos_lector.get("email", ""),
            "telefono": datos_lector.get("telefono", ""),
            "direccion": datos_lector.get("direccion", "")
        })
    elif usuario.dni_nie:
        datos["dni_nie"] = usuario.dni_nie
    
    if request.method == "POST":
        for campo in ["nombre","apellidos","dni_nie","email","telefono","direccion"]:
            datos[campo] = request.form.get(campo, "")
        datos["destino_tipo"] = request.form.get("destino_tipo", "")

        destinatario = {}
        if datos["destino_tipo"] in ("equifax_asnef", "badexcug"):
            destinatario = PREDEFINED_DESTINATARIOS.get(datos["destino_tipo"], {}).copy()
        elif datos["destino_tipo"] == "banco":
            banco_id = request.form.get("destino_banco")
            try:
                if banco_id:
                    b = EntidadFinanciera.query.get(int(banco_id))
                    if b:
                        destinatario = {
                            "clave": "banco",
                            "nombre": b.nombre,
                            "email": b.email_rgpd or b.email_general or "",
                            "tipo_via": "",
                            "via": b.direccion or b.direccion_completa or "",
                            "numero": b.numero or "",
                            "extras": "",
                            "cp": b.codigo_postal or "",
                            "localidad": b.localidad or "",
                            "provincia": b.provincia or "",
                            "ccaa": b.comunidad_autonoma or "",
                        }
            except Exception:
                pass
        else:
            destinatario = {
                "clave": "otros",
                "nombre": request.form.get("dest_nombre", ""),
                "email": request.form.get("dest_email", ""),
                "tipo_via": request.form.get("dest_tipo_via", ""),
                "via": request.form.get("dest_via", ""),
                "numero": request.form.get("dest_numero", ""),
                "extras": request.form.get("dest_extras", ""),
                "cp": request.form.get("dest_cp", ""),
                "localidad": request.form.get("dest_localidad", ""),
                "provincia": request.form.get("dest_provincia", ""),
                "ccaa": request.form.get("dest_ccaa", ""),
            }
        
        # Generar PDF de derecho de supresión (con destinatario)
        try:
            payload = {**datos, "destinatario": destinatario}
            pdf_filename = pdf_generator.generate_rgpd_supresion_pdf(payload)
            flash(f"Solicitud de derecho de supresión generada: {pdf_filename}", "success")
            return redirect(url_for("derecho_supresion_completado", filename=pdf_filename))
        except Exception as e:
            flash(f"Error al generar PDF: {str(e)}", "danger")
    
    bancos = EntidadFinanciera.query.order_by(EntidadFinanciera.nombre.asc()).all()
    tipos_via = TipoVia.query.filter_by(activo=True).order_by(TipoVia.nombre.asc()).all()
    return render_template("derecho_supresion.html", datos=datos, usuario=usuario, bancos=bancos, tipos_via=tipos_via)

@app.route("/derecho_acceso_completado/<filename>")
def derecho_acceso_completado(filename):
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    return render_template("derecho_completado.html", filename=filename, tipo="acceso")

@app.route("/derecho_supresion_completado/<filename>")
def derecho_supresion_completado(filename):
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    return render_template("derecho_completado.html", filename=filename, tipo="supresion")

@app.route("/registro_concursal", methods=["GET", "POST"])
def registro_concursal():
    """Formulario para solicitud de registro en el Registro Público Concursal"""
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = User.query.filter_by(username=session['username']).first()
    if not usuario:
        flash("Usuario no encontrado", "danger")
        return redirect(url_for("login"))
    
    # Datos por defecto del usuario
    datos = {
        "nombre": usuario.nombre or "",
        "apellidos": usuario.apellidos or "",
        "dni_nie": usuario.dni_nie or "",
        "email": usuario.email or "",
        "telefono": usuario.telefono or "",
        "direccion": usuario.direccion or ""
    }
    
    # Para lectores, usar datos precargados
    if usuario.role == "lector" and "datos_lector" in session:
        datos_lector = session["datos_lector"]
        datos.update({
            "nombre": datos_lector.get("nombre", ""),
            "apellidos": datos_lector.get("apellidos", ""),
            "email": datos_lector.get("email", ""),
            "telefono": datos_lector.get("telefono", ""),
            "direccion": datos_lector.get("direccion", "")
        })
    
    if request.method == "POST":
        # Recoger datos del formulario
        for campo in ["nombre", "apellidos", "dni_nie", "email", "telefono", "direccion"]:
            datos[campo] = request.form.get(campo, "")
        
        # Recoger datos del procedimiento
        datos_procedimiento = {
            "juzgado_id": request.form.get("juzgado_id"),
            "numero_procedimiento": request.form.get("numero_procedimiento"),
            "fecha_epi": request.form.get("fecha_epi"),
            "fecha_testimonio": request.form.get("fecha_testimonio") or ""
        }
        
        # Validar datos obligatorios
        if not all([datos["nombre"], datos["apellidos"], datos["dni_nie"], 
                   datos["email"], datos_procedimiento["juzgado_id"], 
                   datos_procedimiento["numero_procedimiento"], datos_procedimiento["fecha_epi"]]):
            flash("Por favor, completa todos los campos obligatorios", "warning")
        else:
            try:
                # Generar documento DOCX y convertir a PDF
                from utils.docx_generator import DocxGenerator
                docx_generator = DocxGenerator()
                docx_filename, pdf_filename = docx_generator.generate_registro_concursal_docx(datos, datos_procedimiento)
                
                if pdf_filename:
                    flash(f"Documento de registro concursal generado y convertido a PDF: {pdf_filename}", "success")
                    return redirect(url_for("registro_concursal_completado", filename=pdf_filename))
                else:
                    flash(f"Documento DOCX generado pero error en conversión a PDF: {docx_filename}", "warning")
                    return redirect(url_for("registro_concursal_completado", filename=docx_filename))
            except Exception as e:
                flash(f"Error al generar documento: {str(e)}", "danger")
    
    # Obtener juzgados mercantiles
    juzgados = Procedimiento.query.with_entities(
        Procedimiento.juzgado_id, 
        Procedimiento.juzgado_nombre
    ).distinct().filter(
        Procedimiento.juzgado_nombre.isnot(None),
        Procedimiento.juzgado_nombre != ""
    ).order_by(Procedimiento.juzgado_nombre.asc()).all()
    
    return render_template("registro_concursal.html", datos=datos, usuario=usuario, juzgados=juzgados)

@app.route("/registro_concursal_completado/<filename>")
def registro_concursal_completado(filename):
    """Página de confirmación para registro concursal completado"""
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    return render_template("registro_concursal_completado.html", filename=filename)

@app.route("/download_registro_concursal_pdf/<filename>")
def download_registro_concursal_pdf(filename):
    """Descarga un documento PDF de registro concursal"""
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    try:
        # Verificar que el archivo existe y está en la carpeta correcta
        pdf_path = os.path.join(BASE_DIR, 'static', 'generated_docs', filename)
        if not os.path.exists(pdf_path):
            flash("Archivo no encontrado", "danger")
            return redirect(url_for("error"))
        
        return send_file(pdf_path, as_attachment=True, download_name=filename)
    except Exception as e:
        flash(f"Error al descargar archivo: {str(e)}", "danger")
        return redirect(url_for("error"))

@app.route("/send_registro_concursal_pdf_email/<filename>")
def send_registro_concursal_pdf_email(filename):
    """Envía un documento PDF de registro concursal por email al usuario"""
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    try:
        usuario = User.query.filter_by(username=session['username']).first()
        if not usuario or not usuario.email:
            flash("No se puede enviar el email: usuario no encontrado o sin email", "danger")
            return redirect(url_for("error"))
        
        # Verificar que el archivo existe
        pdf_path = os.path.join(BASE_DIR, 'static', 'generated_docs', filename)
        if not os.path.exists(pdf_path):
            flash("Archivo no encontrado", "danger")
            return redirect(url_for("error"))
        
        # Enviar email con el documento adjunto
        email_sender = EmailSender()
        subject = "Documento de Registro Concursal - Deudout Abogados"
        body = f"""
        Hola {usuario.nombre or usuario.username},
        
        Adjunto encontrarás el documento de Registro Público Concursal que solicitaste.
        
        Este documento ha sido generado para tu uso personal. Deberás revisarlo y enviarlo tú mismo al juzgado correspondiente.
        
        Saludos,
        Equipo de Deudout Abogados
        """
        
        success = email_sender.send_notification_email(
            to_email=usuario.email,
            subject=subject,
            body=body,
            attachment_path=pdf_path
        )
        
        if success:
            flash(f"Documento PDF enviado por email a {usuario.email}", "success")
        else:
            flash("Error al enviar el email", "danger")
            
        return redirect(url_for("registro_concursal_completado", filename=filename))
        
    except Exception as e:
        flash(f"Error al enviar email: {str(e)}", "danger")
        return redirect(url_for("error"))

@app.route("/consulta_cliente", methods=["GET", "POST"])
def consulta_cliente():
    """Consulta de clientes en base de datos local y externa"""
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    
    # RESTRICCIÓN: Solo administradores y usuarios pueden acceder
    if usuario.role == "lector":
        flash("No tienes permisos para acceder a esta funcionalidad. Solo administradores y usuarios pueden consultar clientes.", "danger")
        return redirect(url_for("menu"))
    
    resultados_local = []
    resultados_rpc = []
    resultados_boe = []
    mensaje_rpc = ""
    mensaje_boe = ""
    dni_busqueda = ""
    
    if request.method == "POST":
        dni_busqueda = request.form.get('dni_nie', '').strip().upper()
        
        if dni_busqueda:
            # 1. Búsqueda en base de datos local
            resultados_local = buscar_en_base_local(dni_busqueda)
            
            # 2. Consulta al RPC
            resultados_rpc, mensaje_rpc = consultar_rpc(dni_busqueda)
            
            # 3. Consulta BOE y Tablón Edictal
            resultados_boe, mensaje_boe = consultar_boe_tablón(dni_busqueda)
    
    return render_template("consulta_cliente.html", 
                         usuario=usuario,
                         resultados_local=resultados_local,
                         resultados_rpc=resultados_rpc,
                         resultados_boe=resultados_boe,
                         mensaje_rpc=mensaje_rpc,
                         mensaje_boe=mensaje_boe,
                         dni_busqueda=dni_busqueda)

@app.route("/consulta_total", methods=["GET", "POST"])
def consulta_total():
    """Consulta total integrada a todas las fuentes públicas disponibles"""
    access_valid, result = check_user_access()
    if not access_valid:
        flash(result, "warning")
        return redirect(url_for("login"))
    
    usuario = result
    
    # RESTRICCIÓN: Solo administradores y usuarios pueden acceder
    if usuario.role == "lector":
        flash("No tienes permisos para acceder a esta funcionalidad. Solo administradores y usuarios pueden realizar consultas totales.", "danger")
        return redirect(url_for("menu"))
    
    from utils.external_queries import consulta_total_integrada, consultar_rpc, consultar_boe_tablon
    
    resultados_local = []
    resultados_total = {}
    mensajes_total = {}
    dni_busqueda = ""
    
    if request.method == "POST":
        dni_busqueda = request.form.get('dni_nie', '').strip().upper()
        
        if dni_busqueda:
            # 1. Búsqueda en base de datos local
            resultados_local = buscar_en_base_local(dni_busqueda)
            
            # 2. Consulta total integrada a todas las fuentes
            resultados_total, mensajes_total = consulta_total_integrada(dni_busqueda)
    
    return render_template("consulta_total.html", 
                         usuario=usuario,
                         resultados_local=resultados_local,
                         resultados_total=resultados_total,
                         mensajes_total=mensajes_total,
                         dni_busqueda=dni_busqueda)

def buscar_en_base_local(dni_nie):
    """Busca en todos los formularios de la base de datos local"""
    resultados = []
    
    # Buscar en FormularioRPC
    formularios_rpc = FormularioRPC.query.filter_by(dni_nie=dni_nie).all()
    for form in formularios_rpc:
        resultados.append({
            'tipo': 'Registro Público Concursal',
            'datos': {
                'nombre': form.nombre,
                'apellidos': form.apellidos,
                'dni_nie': form.dni_nie,
                'tipo_concurso': form.tipo_concurso,
                'fecha_presentacion': form.fecha_presentacion,
                'observaciones': form.observaciones,
                'fecha_creacion': form.created_at
            }
        })
    
    # Buscar en DatosLector
    datos_lector = DatosLector.query.filter_by(dni_nie=dni_nie).all()
    for dato in datos_lector:
        resultados.append({
            'tipo': 'Datos de Lector',
            'datos': {
                'nombre': dato.nombre,
                'apellidos': dato.apellidos,
                'dni_nie': dato.dni_nie,
                'email': dato.email,
                'telefono': dato.telefono,
                'direccion': dato.direccion,
                'datos_adicionales': dato.datos_adicionales,
                'fecha_creacion': dato.created_at,
                'ultima_actualizacion': dato.updated_at
            }
        })
    
    # Buscar en User (usuarios registrados)
    usuarios = User.query.filter_by(dni_nie=dni_nie).all()
    for user in usuarios:
        resultados.append({
            'tipo': 'Usuario del Sistema',
            'datos': {
                'username': user.username,
                'nombre': user.nombre,
                'apellidos': user.apellidos,
                'dni_nie': user.dni_nie,
                'email': user.email,
                'telefono': user.telefono,
                'role': user.role,
                'fecha_creacion': user.created_at
            }
        })
    
    return resultados

@app.route("/error")
def error():
    return render_template("error.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        crear_usuario_admin()
    
    # En desarrollo
    if os.environ.get('FLASK_ENV') != 'production':
        app.run(host="0.0.0.0", port=5000, debug=True)