from werkzeug.security import generate_password_hash
from app import app
from models import db, User

USERNAME = "pedro"
PASSWORD = "admin1234"  # Cambia por la contraseña que quieras
ROLE = "admin"

with app.app_context():
    user = User.query.filter_by(username=USERNAME).first()
    if user:
        print(f"El usuario '{USERNAME}' ya existe.")
    else:
        user = User(
            username=USERNAME,
            password_hash=generate_password_hash(PASSWORD),
            role=ROLE,
            is_enabled=True
        )
        db.session.add(user)
        db.session.commit()
        print(f"Usuario '{USERNAME}' creado correctamente como administrador.")