from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from db import get_db, engine
from models import Base
import auth_endpoints
import me
from admin import admin_users, admin_upload, admin_download

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Backend API",
    description="FastAPI Backend Application",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_endpoints.router, prefix="/auth", tags=["Authentication"])
app.include_router(me.router, prefix="/me", tags=["User Profile"])
app.include_router(admin_users.router, prefix="/admin", tags=["Admin - Users"])
app.include_router(admin_upload.router, prefix="/admin", tags=["Admin - Upload"])
app.include_router(admin_download.router, prefix="/admin", tags=["Admin - Download"])

@app.get("/")
async def root():
    return {"message": "Backend API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}