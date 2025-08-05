from sqlalchemy.orm import Session
from db import SessionLocal, engine
from models import Base, User
from auth import get_password_hash

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def create_admin_user():
    """Create default admin user if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="System Administrator",
                is_active=True,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
            print("Email: admin@example.com")
        else:
            print("Admin user already exists!")
            
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def init_database():
    """Initialize database with tables and default data"""
    print("Initializing database...")
    
    # Create tables
    create_tables()
    
    # Create admin user
    create_admin_user()
    
    print("Database initialization completed!")

if __name__ == "__main__":
    init_database()