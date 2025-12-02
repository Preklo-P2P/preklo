"""
Security Middleware
Adds security headers and request tracking
"""

import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

from ..utils.logging import request_logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Content Security Policy (basic)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "font-src 'self' https://cdn.jsdelivr.net;"
        )
        
        return response


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Track requests with unique IDs and logging
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start time
        start_time = time.time()
        
        # Log request start
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(request.state.user.id)
        
        request_logger.log_request(request, request_id, user_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            # Log successful response
            request_logger.log_response(
                request, request_id, response.status_code, duration_ms, user_id
            )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            request_logger.log_error(request, request_id, e, user_id)
            
            # Re-raise the exception
            raise


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Add user context to request state for logging
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract user info from Authorization header if present
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from ..services.auth_service import auth_service
                from ..database import SessionLocal, get_session_local
                
                token = auth_header.split(" ")[1]
                payload = auth_service.verify_token(token)
                
                if payload and payload.get("sub"):
                    # Get user from database
                    session_local = SessionLocal if SessionLocal is not None else get_session_local()
                    db = session_local()
                    try:
                        from ..models import User
                        user = db.query(User).filter(User.id == payload["sub"]).first()
                        if user:
                            request.state.user = user
                    finally:
                        db.close()
            except:
                # Ignore errors in user context extraction
                pass
        
        return await call_next(request)
