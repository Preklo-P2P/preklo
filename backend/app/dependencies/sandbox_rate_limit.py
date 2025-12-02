"""
Sandbox API Key Rate Limiting
Implements rate limiting for sandbox API keys: 1,000 requests/day, 100 requests/minute
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import time
from collections import defaultdict, deque
from datetime import datetime

from ..database import get_db
from ..models.sandbox import SandboxAPIKey
from ..dependencies.sandbox_auth import get_sandbox_user_from_api_key


# In-memory rate limiting storage (use Redis in production)
# Structure: {api_key_id: {"daily": deque, "minute": deque}}
sandbox_rate_limit_storage = defaultdict(lambda: {"daily": deque(), "minute": deque()})


def _check_rate_limit(
    current_api_key: SandboxAPIKey,
    db: Session,
    max_requests_daily: int = 1000,
    max_requests_minute: int = 100
) -> bool:
    """
    Internal function to check rate limits (called from unified_auth).
    """
    api_key_id = str(current_api_key.id)
    current_time = time.time()
    
    # Get rate limit data for this API key
    rate_data = sandbox_rate_limit_storage[api_key_id]
    
    # Daily limit (rolling 24-hour window)
    daily_window_start = current_time - (24 * 3600)  # 24 hours ago
    daily_requests = rate_data["daily"]
    
    # Clean old requests outside the daily window
    while daily_requests and daily_requests[0] < daily_window_start:
        daily_requests.popleft()
    
    # Check daily limit
    if len(daily_requests) >= max_requests_daily:
        # Calculate retry after (seconds until oldest request expires)
        if daily_requests:
            oldest_request = daily_requests[0]
            retry_after = int(oldest_request + (24 * 3600) - current_time)
            retry_after = max(retry_after, 60)  # Minimum 60 seconds
        else:
            retry_after = 3600  # 1 hour default
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily rate limit exceeded: {max_requests_daily} requests per day",
            headers={
                "X-RateLimit-Limit": str(max_requests_daily),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(current_time + retry_after)),
                "Retry-After": str(retry_after)
            }
        )
    
    # Minute limit (rolling 60-second window)
    minute_window_start = current_time - 60  # 60 seconds ago
    minute_requests = rate_data["minute"]
    
    # Clean old requests outside the minute window
    while minute_requests and minute_requests[0] < minute_window_start:
        minute_requests.popleft()
    
    # Check minute limit
    if len(minute_requests) >= max_requests_minute:
        # Calculate retry after (seconds until oldest request expires)
        if minute_requests:
            oldest_request = minute_requests[0]
            retry_after = int(oldest_request + 60 - current_time)
            retry_after = max(retry_after, 1)  # Minimum 1 second
        else:
            retry_after = 60  # 1 minute default
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Burst rate limit exceeded: {max_requests_minute} requests per minute",
            headers={
                "X-RateLimit-Limit": str(max_requests_minute),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(current_time + retry_after)),
                "Retry-After": str(retry_after)
            }
        )
    
    # Add current request to both windows
    daily_requests.append(current_time)
    minute_requests.append(current_time)
    
    # Update last_used_at in database
    try:
        current_api_key.last_used_at = datetime.utcnow()
        db.commit()
    except Exception:
        # Don't fail request if database update fails
        db.rollback()
        pass
    
    return True


def sandbox_rate_limit(
    current_api_key: SandboxAPIKey = Depends(get_sandbox_user_from_api_key),
    db: Session = Depends(get_db),
    max_requests_daily: int = 1000,
    max_requests_minute: int = 100
) -> bool:
    """
    Rate limiting dependency for sandbox API keys.
    Use this as a FastAPI dependency.
    
    Limits:
    - 1,000 requests per day (rolling 24-hour window)
    - 100 requests per minute (rolling 60-second window)
    """
    return _check_rate_limit(current_api_key, db, max_requests_daily, max_requests_minute)


def get_rate_limit_headers(
    api_key_id: str,
    max_requests_daily: int = 1000,
    max_requests_minute: int = 100
) -> dict:
    """
    Get rate limit headers for a given API key.
    
    Returns:
        dict: Rate limit headers
    """
    current_time = time.time()
    rate_data = sandbox_rate_limit_storage.get(api_key_id, {"daily": deque(), "minute": deque()})
    
    # Calculate daily remaining
    daily_window_start = current_time - (24 * 3600)
    daily_requests = rate_data["daily"]
    while daily_requests and daily_requests[0] < daily_window_start:
        daily_requests.popleft()
    daily_remaining = max(0, max_requests_daily - len(daily_requests))
    
    # Calculate minute remaining
    minute_window_start = current_time - 60
    minute_requests = rate_data["minute"]
    while minute_requests and minute_requests[0] < minute_window_start:
        minute_requests.popleft()
    minute_remaining = max(0, max_requests_minute - len(minute_requests))
    
    return {
        "X-RateLimit-Limit-Daily": str(max_requests_daily),
        "X-RateLimit-Remaining-Daily": str(daily_remaining),
        "X-RateLimit-Limit-Minute": str(max_requests_minute),
        "X-RateLimit-Remaining-Minute": str(minute_remaining),
        "X-RateLimit-Reset": str(int(current_time + 60))  # Reset in 1 minute
    }
