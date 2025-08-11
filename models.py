from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(16), nullable=False)  # 'admin', 'usuario', 'lector'
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Campos específicos para usuarios
    nombre = db.Column(db.String(100))
    apellidos = db.Column(db.String(100))
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(20))
    dni_nie = db.Column(db.String(20))  # Campo para DNI/NIE
    
    # Campos específicos para lectores
    formularios_permitidos = db.Column(db.Text)  # JSON string con formularios permitidos
    fecha_expiracion = db.Column(db.DateTime)
    datos_precargados = db.Column(db.Text)  # JSON string con datos precargados
    
    def is_expired(self):
        """Verifica si el usuario lector ha expirado (10 días)"""
        if self.role == 'lector' and self.fecha_expiracion:
            return datetime.utcnow() > self.fecha_expiracion
        return False
    
    def get_formularios_permitidos(self):
        """Obtiene la lista de formularios permitidos para lectores"""
        import json
        if self.formularios_permitidos:
            return json.loads(self.formularios_permitidos)
        return []

class CodigoPostal(db.Model):
    """Modelo para códigos postales de España"""
    id = db.Column(db.Integer, primary_key=True)
    codigo_postal = db.Column(db.String(5), nullable=False, index=True)
    localidad = db.Column(db.String(100), nullable=False)
    provincia = db.Column(db.String(100), nullable=False)
    comunidad_autonoma = db.Column(db.String(100), nullable=False)
    pais = db.Column(db.String(50), default='España')
    
    # Campos de búsqueda optimizados
    localidad_busqueda = db.Column(db.String(100))  # Para búsquedas sin acentos
    provincia_busqueda = db.Column(db.String(100))  # Para búsquedas sin acentos
    
    # Metadatos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fuente_datos = db.Column(db.String(50), default='Correos España')
    version_datos = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<CodigoPostal {self.codigo_postal} - {self.localidad}, {self.provincia}>'
    
    def to_dict(self):
        """Convierte el código postal a diccionario para JSON"""
        return {
            'id': self.id,
            'codigo_postal': self.codigo_postal,
            'localidad': self.localidad,
            'provincia': self.provincia,
            'comunidad_autonoma': self.comunidad_autonoma,
            'pais': self.pais
        }

class EntidadFinanciera(db.Model):
    """Modelo mejorado para entidades financieras basado en el Banco de España"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Información básica
    nombre = db.Column(db.String(200), nullable=False)
    nombre_comercial = db.Column(db.String(200))  # Nombre comercial si es diferente
    tipo_entidad = db.Column(db.String(50), nullable=False)  # 'Banco', 'EFC', 'Caja de Ahorros', etc.
    codigo_entidad = db.Column(db.String(10), unique=True)  # Código oficial del BdE
    
    # Estado operativo
    estado = db.Column(db.String(20), default='Activo')  # Activo, Inactivo, En Liquidación
    fecha_autorizacion = db.Column(db.Date)
    fecha_ultima_actualizacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Información de contacto postal completa
    direccion_completa = db.Column(db.Text)  # Dirección completa para Doc. 9
    direccion = db.Column(db.String(200))
    numero = db.Column(db.String(10))
    codigo_postal = db.Column(db.String(10))
    localidad = db.Column(db.String(100))
    provincia = db.Column(db.String(100))
    comunidad_autonoma = db.Column(db.String(100))
    pais = db.Column(db.String(50), default='España')
    
    # Información de contacto adicional
    telefono = db.Column(db.String(20))
    fax = db.Column(db.String(20))
    web = db.Column(db.String(200))
    
    # Emails específicos por tipo de documento
    email_doc9 = db.Column(db.String(120))  # Email genérico para Doc. 9 (ej: info@banco.com)
    email_rgpd = db.Column(db.String(120))  # Email específico para RGPD (ej: protecciondatos@banco.com)
    email_general = db.Column(db.String(120))  # Email general de contacto
    
    # Información fiscal y legal
    cif_nif = db.Column(db.String(20))
    registro_mercantil = db.Column(db.String(100))
    numero_registro = db.Column(db.String(50))
    
    # Información del BdE
    supervisor_principal = db.Column(db.String(100), default='Banco de España')
    codigo_supervisor = db.Column(db.String(20))
    
    # Metadatos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fuente_datos = db.Column(db.String(50), default='Banco de España')
    version_datos = db.Column(db.String(20))
    
    # Campos de búsqueda optimizados
    nombre_busqueda = db.Column(db.String(200))  # Para búsquedas sin acentos
    localidad_busqueda = db.Column(db.String(100))  # Para búsquedas sin acentos
    provincia_busqueda = db.Column(db.String(100))  # Para búsquedas sin acentos
    
    def __repr__(self):
        return f'<EntidadFinanciera {self.codigo_entidad} - {self.nombre}>'
    
    def to_dict(self):
        """Convierte la entidad a diccionario para JSON"""
        return {
            'id': self.id,
            'nombre': self.nombre,
            'nombre_comercial': self.nombre_comercial,
            'tipo_entidad': self.tipo_entidad,
            'codigo_entidad': self.codigo_entidad,
            'estado': self.estado,
            'direccion_completa': self.direccion_completa,
            'localidad': self.localidad,
            'provincia': self.provincia,
            'comunidad_autonoma': self.comunidad_autonoma,
            'telefono': self.telefono,
            'email_doc9': self.email_doc9,
            'email_rgpd': self.email_rgpd,
            'email_general': self.email_general,
            'web': self.web
        }
    
    def get_email_para_documento(self, tipo_documento):
        """Obtiene el email apropiado según el tipo de documento"""
        if tipo_documento == 'doc9':
            return self.email_doc9 or self.email_general
        elif tipo_documento == 'rgpd':
            return self.email_rgpd or self.email_general
        else:
            return self.email_general


class TipoVia(db.Model):
    """Catálogo de tipos de vía (Calle, Avenida, Apartado de Correos, etc.)."""
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    abreviatura = db.Column(db.String(20))  # Ej.: C/, Avda., Aptdo.
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TipoVia {self.nombre}>'

class Banco(db.Model):
    """Modelo legacy para compatibilidad - será reemplazado por EntidadFinanciera"""
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    direccion = db.Column(db.String(200))
    num = db.Column(db.String(10))
    cp = db.Column(db.String(10))
    localidad = db.Column(db.String(100))
    provincia = db.Column(db.String(100))
    ccaa = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AccessLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    success = db.Column(db.Boolean, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    ubicacion = db.Column(db.String(200))  # País, ciudad según IP
    
    def __repr__(self):
        return f'<AccessLog {self.username} - {self.ip_address} - {self.success}>'

class FormularioRPC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    dni_nie = db.Column(db.String(20), nullable=False)
    observaciones = db.Column(db.Text)
    tipo_concurso = db.Column(db.String(100))
    fecha_presentacion = db.Column(db.Date)
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('User', backref='formularios_rpc')

class Procedimiento(db.Model):
    """Almacena datos de procedimiento por juzgado para métricas."""
    id = db.Column(db.Integer, primary_key=True)
    num_procedimiento = db.Column(db.String(50), nullable=False)
    juzgado = db.Column(db.String(200), nullable=False)

    # Fechas clave del procedimiento
    fecha_epi = db.Column(db.Date)  # Ya existente en el formulario
    fecha_testimonio = db.Column(db.Date)
    fecha_presentacion_demanda = db.Column(db.Date)
    fecha_admision = db.Column(db.Date)

    # Clasificación del concurso
    tipo_concurso = db.Column(db.String(20))  # "Con masa" | "Sin masa"

    # Relación con usuario
    usuario_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('User', backref='procedimientos')

    def tiempo_admision_dias(self):
        """Retorna días entre presentación de demanda y admisión, si ambas existen."""
        if self.fecha_presentacion_demanda and self.fecha_admision:
            return (self.fecha_admision - self.fecha_presentacion_demanda).days
        return None

class DatosLector(db.Model):
    """Modelo para almacenar los datos de los lectores filtrados por DNI/NIE"""
    id = db.Column(db.Integer, primary_key=True)
    dni_nie = db.Column(db.String(20), nullable=False, unique=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(200))
    datos_adicionales = db.Column(db.Text)  # JSON con datos adicionales
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DatosLector {self.dni_nie} - {self.nombre} {self.apellidos}>'