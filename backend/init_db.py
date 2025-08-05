"""
Database initialization script
"""
import os
import sys
from sqlalchemy.orm import Session

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import engine, SessionLocal, create_tables
from models import User, Procedure, FileUpload, AuditLog
from auth import create_user

def init_database():
    """Initialize the database with tables and default data"""
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully!")
    
    # Create default admin user if it doesn't exist
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("Creating default admin user...")
            admin_user = create_user(
                db=db,
                username="admin",
                email="admin@aplicacion.com",
                password="admin123",  # Change this in production!
                full_name="System Administrator",
                is_admin=True
            )
            print(f"Admin user created with ID: {admin_user.id}")
        else:
            print("Admin user already exists")
        
        # Create a test regular user if it doesn't exist
        test_user = db.query(User).filter(User.username == "testuser").first()
        if not test_user:
            print("Creating test user...")
            test_user = create_user(
                db=db,
                username="testuser",
                email="test@aplicacion.com",
                password="test123",
                full_name="Test User",
                is_admin=False
            )
            print(f"Test user created with ID: {test_user.id}")
        else:
            print("Test user already exists")
            
    except Exception as e:
        print(f"Error creating default users: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("Database initialization completed!")

def reset_database():
    """Reset the database by dropping and recreating all tables"""
    print("WARNING: This will delete all data in the database!")
    confirm = input("Are you sure you want to continue? (yes/no): ")
    
    if confirm.lower() == 'yes':
        from db import drop_tables
        print("Dropping all tables...")
        drop_tables()
        print("Reinitializing database...")
        init_database()
        print("Database reset completed!")
    else:
        print("Database reset cancelled.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument("--reset", action="store_true", help="Reset the database (WARNING: deletes all data)")
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database()
    else:
        init_database()