from app import app, db
from models import User, DatosLector, TipoVia
from werkzeug.security import generate_password_hash
from datetime import datetime

with app.app_context():
    db.create_all()
    # Crea un usuario admin si no existe
    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            nombre="Administrador",
            apellidos="Sistema",
            email="admin@sistema.com",
            is_enabled=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Usuario admin creado: admin / admin123")
    else:
        print("Usuario admin ya existe.")
    
    # Crear algunos datos de ejemplo para lectores
    if not DatosLector.query.filter_by(dni_nie="12345678A").first():
        lector1 = DatosLector(
            dni_nie="12345678A",
            nombre="Juan",
            apellidos="Pérez García",
            email="juan.perez@email.com",
            telefono="600123456",
            direccion="Calle Mayor 123, Madrid",
            datos_adicionales='{"empresa": "Empresa ABC", "cargo": "Empleado"}'
        )
        db.session.add(lector1)
        print("Datos de lector de ejemplo creados: 12345678A")
    
    if not DatosLector.query.filter_by(dni_nie="87654321B").first():
        lector2 = DatosLector(
            dni_nie="87654321B",
            nombre="María",
            apellidos="González López",
            email="maria.gonzalez@email.com",
            telefono="600654321",
            direccion="Avenida Principal 456, Barcelona",
            datos_adicionales='{"empresa": "Empresa XYZ", "cargo": "Directivo"}'
        )
        db.session.add(lector2)
        print("Datos de lector de ejemplo creados: 87654321B")
    
    db.session.commit()
    print("Base de datos inicializada correctamente.")

    # Poblar catálogo de tipos de vía si está vacío
    tipos_base = [
        ("Calle", "C/"),
        ("Avenida", "Avda."),
        ("Plaza", "Pl."),
        ("Camino", "Cno."),
        ("Carretera", "Ctra."),
        ("Pasaje", "Pje."),
        ("Paseo", "Pº"),
        ("Ronda", "Rda."),
        ("Travesía", "Trva."),
        ("Urbanización", "Urb."),
        ("Polígono", "Pol."),
        ("Apartado de Correos", "Aptdo.")
    ]
    if not TipoVia.query.first():
        for nombre, abrev in tipos_base:
            db.session.add(TipoVia(nombre=nombre, abreviatura=abrev))
        db.session.commit()
        print("Tipos de vía cargados (incluido 'Apartado de Correos').")