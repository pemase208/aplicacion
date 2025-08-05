from fastapi import Request, Response
from sqlalchemy.orm import Session
import json
from datetime import datetime

from db import SessionLocal
from models import AuditLog

async def audit_middleware(request: Request, call_next):
    """Middleware to log API requests for audit purposes"""
    
    # Get request details
    start_time = datetime.utcnow()
    method = request.method
    url = str(request.url)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Process the request
    response = await call_next(request)
    
    # Calculate response time
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    # Log the request (in background to avoid slowing down the response)
    try:
        # Only log certain endpoints to avoid noise
        if should_audit_request(url, method):
            db = SessionLocal()
            try:
                # Try to get user ID from request state (set by auth middleware)
                user_id = getattr(request.state, 'user_id', None) if hasattr(request.state, 'user_id') else None
                
                audit_log = AuditLog(
                    user_id=user_id,
                    action=f"{method} {url}",
                    resource=extract_resource_from_url(url),
                    details=json.dumps({
                        "method": method,
                        "url": url,
                        "status_code": response.status_code,
                        "process_time": process_time,
                        "response_size": response.headers.get("content-length")
                    }),
                    ip_address=client_ip,
                    user_agent=user_agent
                )
                
                db.add(audit_log)
                db.commit()
            except Exception as e:
                # Don't let audit logging break the request
                print(f"Audit logging failed: {e}")
            finally:
                db.close()
    except Exception as e:
        # Don't let audit logging break the request
        print(f"Audit middleware error: {e}")
    
    return response

def should_audit_request(url: str, method: str) -> bool:
    """Determine if a request should be audited"""
    # Skip health checks and static files
    skip_patterns = ["/health", "/docs", "/static", "/favicon.ico"]
    
    for pattern in skip_patterns:
        if pattern in url:
            return False
    
    # Audit all POST, PUT, DELETE requests
    if method in ["POST", "PUT", "DELETE"]:
        return True
    
    # Audit GET requests to sensitive endpoints
    sensitive_patterns = ["/admin", "/me", "/users"]
    for pattern in sensitive_patterns:
        if pattern in url:
            return True
    
    return False

def extract_resource_from_url(url: str) -> str:
    """Extract resource name from URL for audit logging"""
    try:
        # Remove query parameters and extract path
        path = url.split("?")[0].split("/")
        
        # Find the main resource
        if len(path) >= 2:
            if "admin" in path:
                return f"admin/{path[-1]}" if len(path) > 2 else "admin"
            elif "auth" in path:
                return "auth"
            elif "me" in path:
                return "user_profile"
            else:
                return path[1] if path[1] else "root"
        
        return "unknown"
    except Exception:
        return "unknown"