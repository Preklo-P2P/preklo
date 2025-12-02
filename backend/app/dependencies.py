"""
FastAPI Dependencies
Authentication, rate limiting, and other request dependencies
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import time
from collections import defaultdict, deque

from .database import get_db
from .models import User
from .services.auth_service import auth_service


# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)

# In-memory rate limiting (use Redis in production)
rate_limit_storage = defaultdict(lambda: deque())


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current authenticated user from JWT token
    Returns None if no valid token is provided (for optional authentication)
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return None
    
    return user


async def require_authentication(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Require authentication and return the current user
    Raises HTTPException if no valid token is provided
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_or_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from JWT token or API key
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # First try as JWT token
    user = await get_current_user(credentials, db)
    if user:
        return user
    
    # Then try as API key
    user = auth_service.validate_api_key(token, db)
    return user


def rate_limit(
    max_requests: int = 100, 
    window_seconds: int = 3600,  # 1 hour
    per: str = "ip"  # "ip" or "user"
):
    """
    Rate limiting decorator
    """
    def decorator(request: Request, current_user: Optional[User] = Depends(get_current_user)):
        # Determine the key for rate limiting
        if per == "user" and current_user:
            key = f"user_{current_user.id}"
        else:
            # Use IP address
            client_ip = request.client.host
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                client_ip = forwarded_for.split(",")[0].strip()
            key = f"ip_{client_ip}"
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Clean old requests outside the window
        requests = rate_limit_storage[key]
        while requests and requests[0] < window_start:
            requests.popleft()
        
        # Check if limit is exceeded
        if len(requests) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {max_requests} requests per {window_seconds} seconds",
                headers={"Retry-After": str(window_seconds)}
            )
        
        # Add current request
        requests.append(current_time)
        
        return True
    
    return decorator


async def validate_user_access(
    user_id: str,
    current_user: User = Depends(require_authentication)
) -> bool:
    """
    Validate that the current user has access to the specified user_id
    Users can only access their own data unless they have admin privileges
    """
    if str(current_user.id) == user_id:
        return True
    
    # TODO: Add admin role checking when roles are implemented
    # if current_user.role == "admin":
    #     return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: You can only access your own data"
    )


async def validate_payment_access(
    payment_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
) -> bool:
    """
    Validate that the current user has access to a payment request
    """
    from .models import PaymentRequest
    
    payment_request = db.query(PaymentRequest).filter(
        PaymentRequest.payment_id == payment_id
    ).first()
    
    if not payment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment request not found"
        )
    
    # Users can access payments they created or are the recipient of
    if str(payment_request.recipient_id) == str(current_user.id):
        return True
    
    # TODO: Add check for sender when sender tracking is added
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: You don't have permission to access this payment"
    )


class RateLimitMiddleware:
    """
    Rate limiting middleware for global API protection
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
    
    async def __call__(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Allow tests or specific contexts to override/disable the global limit
        override_limit = None
        override_window = None
        if request.app:
            override_limit = getattr(request.app.state, "global_rate_limit_override", None)
            override_window = getattr(request.app.state, "global_rate_limit_window_override", None)

        # If explicitly disabled, skip
        if override_limit is not None and override_limit <= 0:
            return await call_next(request)

        effective_limit = override_limit if override_limit is not None else self.requests_per_minute
        effective_window = override_window if override_window is not None else self.window_seconds
        
        # Get client IP
        client_ip = request.client.host
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        key = f"global_ip_{client_ip}"
        current_time = time.time()
        window_start = current_time - effective_window
        
        # Clean old requests
        requests = rate_limit_storage[key]
        while requests and requests[0] < window_start:
            requests.popleft()
        
        # Check limit
        if effective_limit and len(requests) >= effective_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {effective_limit} requests per minute",
                headers={"Retry-After": str(effective_window)}
            )
        
        # Add request
        requests.append(current_time)
        
        response = await call_next(request)
        return response
