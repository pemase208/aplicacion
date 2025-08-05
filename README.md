# Aplicacion API

A FastAPI backend application with authentication, admin features, and file management.

## Features

- **Authentication**: JWT-based authentication with admin and user roles
- **User Management**: Admin endpoints for managing users
- **Procedure Management**: CRUD operations for procedures
- **File Upload/Download**: File management with admin controls
- **Audit Logging**: Request tracking and user activity logging
- **Email Utilities**: Email notification system
- **Database**: SQLAlchemy with SQLite (configurable)

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd aplicacion
```

2. Start the application:
```bash
docker-compose up --build
```

3. Access the API:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Manual Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python init_db.py
```

4. Start the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Default Credentials

- **Admin User**: username: `admin`, password: `admin123`
- **Test User**: username: `testuser`, password: `test123`

⚠️ **Important**: Change default passwords in production!

## API Endpoints

### Authentication
- `POST /auth/login` - Login with form data
- `POST /auth/login/json` - Login with JSON
- `POST /auth/register` - Register new user

### User Profile
- `GET /me/profile` - Get current user profile
- `PUT /me/profile` - Update current user profile
- `GET /me/settings` - Get user settings
- `GET /me/activity` - Get user activity logs

### Admin - Users
- `GET /admin/users/` - List all users
- `GET /admin/users/{user_id}` - Get user by ID
- `POST /admin/users/` - Create new user
- `PUT /admin/users/{user_id}` - Update user
- `DELETE /admin/users/{user_id}` - Delete user

### Admin - Procedures
- `GET /admin/procedures/` - List all procedures
- `GET /admin/procedures/{procedure_id}` - Get procedure by ID
- `POST /admin/procedures/` - Create new procedure
- `PUT /admin/procedures/{procedure_id}` - Update procedure
- `DELETE /admin/procedures/{procedure_id}` - Delete procedure

### Admin - File Management
- `POST /admin/upload/file` - Upload single file
- `POST /admin/upload/multiple` - Upload multiple files
- `GET /admin/upload/files` - List uploaded files
- `GET /admin/download/file/{file_id}` - Download file
- `GET /admin/download/files/procedure/{procedure_id}` - Get procedure files

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./aplicacion.db` | Database connection string |
| `SECRET_KEY` | `your-secret-key-change-in-production` | JWT secret key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Token expiration time |
| `SMTP_SERVER` | `localhost` | Email server |
| `SMTP_PORT` | `587` | Email server port |

## File Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── models.py              # Database models
├── schemas.py             # Pydantic schemas
├── db.py                  # Database configuration
├── auth.py                # Authentication utilities
├── auth_endpoints.py      # Authentication endpoints
├── me.py                  # User profile endpoints
├── dependencies.py        # FastAPI dependencies
├── audit.py               # Audit logging middleware
├── email_utils.py         # Email utilities
├── init_db.py            # Database initialization
├── admin/                 # Admin module
│   ├── __init__.py
│   ├── admin_users.py     # User management endpoints
│   ├── admin_procedures.py # Procedure management endpoints
│   ├── admin_upload.py    # File upload endpoints
│   └── admin_download.py  # File download endpoints
├── docs/                  # File upload directory
├── requirements.txt       # Python dependencies
└── Dockerfile            # Docker configuration
```

## Development

### Adding New Endpoints

1. Create new router in appropriate module
2. Import and include in `main.py`
3. Add authentication dependencies as needed
4. Update API documentation

### Database Changes

1. Update models in `models.py`
2. Update schemas in `schemas.py`
3. Recreate database: `python init_db.py --reset`

### Testing

Access the interactive API documentation at http://localhost:8000/docs to test endpoints.

## Security Notes

- Change default passwords in production
- Set strong `SECRET_KEY` in production
- Configure proper CORS origins
- Use HTTPS in production
- Regularly rotate JWT secret keys
- Implement rate limiting for production use

## License

This project is for educational/internal use.