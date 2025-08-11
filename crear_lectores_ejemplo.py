from app import app, db
from models import User, DatosLector
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

with app.app_context():
    # Crear usuario lector 1
    if not User.query.filter_by(username="lector1").first():
        lector1 = User(
            username="lector1",
            password_hash=generate_password_hash("lector123"),
            role="lector",
            nombre="Juan",
            apellidos="Pérez García",
            email="juan.perez@email.com",
            dni_nie="12345678A",
            fecha_expiracion=datetime.utcnow() + timedelta(days=10),
            formularios_permitidos='["rpc", "generico"]',
            is_enabled=True
        )
        db.session.add(lector1)
        print("Usuario lector1 creado: lector1 / lector123")
    
    # Crear usuario lector 2
    if not User.query.filter_by(username="lector2").first():
        lector2 = User(
            username="lector2",
            password_hash=generate_password_hash("lector123"),
            role="lector",
            nombre="María",
            apellidos="González López",
            email="maria.gonzalez@email.com",
            dni_nie="87654321B",
            fecha_expiracion=datetime.utcnow() + timedelta(days=10),
            formularios_permitidos='["generico"]',
            is_enabled=True
        )
        db.session.add(lector2)
        print("Usuario lector2 creado: lector2 / lector123")
    
    # Crear usuario normal
    if not User.query.filter_by(username="usuario1").first():
        usuario1 = User(
            username="usuario1",
            password_hash=generate_password_hash("usuario123"),
            role="usuario",
            nombre="Carlos",
            apellidos="Rodríguez Martín",
            email="carlos.rodriguez@email.com",
            is_enabled=True
        )
        db.session.add(usuario1)
        print("Usuario normal creado: usuario1 / usuario123")
    
    db.session.commit()
    print("Usuarios de ejemplo creados correctamente.")
    print("\nCredenciales de acceso:")
    print("- Admin: admin / admin123")
    print("- Usuario: usuario1 / usuario123")
    print("- Lector 1: lector1 / lector123 (acceso a RPC y genérico)")
    print("- Lector 2: lector2 / lector123 (acceso solo a genérico)")







