from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from auth_endpoints import router as auth_router
from me import router as me_router
from admin.admin_users import router as admin_users_router
from admin.admin_procedures import router as admin_procedures_router
from admin.admin_upload import router as admin_upload_router
from admin.admin_download import router as admin_download_router
from dependencies import get_current_user
from audit import audit_middleware

app = FastAPI(
    title="Aplicacion API",
    description="FastAPI backend application",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
app.mount("/docs", StaticFiles(directory="docs"), name="docs")

# Add audit middleware
app.middleware("http")(audit_middleware)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(me_router, prefix="/me", tags=["user profile"])
app.include_router(admin_users_router, prefix="/admin/users", tags=["admin - users"])
app.include_router(admin_procedures_router, prefix="/admin/procedures", tags=["admin - procedures"])
app.include_router(admin_upload_router, prefix="/admin/upload", tags=["admin - upload"])
app.include_router(admin_download_router, prefix="/admin/download", tags=["admin - download"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Aplicacion API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)