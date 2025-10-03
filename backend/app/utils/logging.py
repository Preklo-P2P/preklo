"""
Production Logging Configuration
Structured logging with JSON format and proper log levels
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid
from fastapi import Request

class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, "endpoint"):
            log_entry["endpoint"] = record.endpoint
        
        if hasattr(record, "method"):
            log_entry["method"] = record.method
        
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        
        if hasattr(record, "duration"):
            log_entry["duration_ms"] = record.duration
        
        return json.dumps(log_entry, default=str)


class RequestLogger:
    """
    Request logging utility for tracking API calls
    """
    
    def __init__(self):
        self.logger = logging.getLogger("preklo.requests")
    
    def log_request(
        self,
        request: Request,
        request_id: str,
        user_id: Optional[str] = None
    ):
        """Log incoming request"""
        self.logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "endpoint": request.url.path,
                "method": request.method,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent", ""),
            }
        )
    
    def log_response(
        self,
        request: Request,
        request_id: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None
    ):
        """Log response"""
        self.logger.info(
            f"Request completed: {request.method} {request.url.path} - {status_code}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": status_code,
                "duration": duration_ms,
            }
        )
    
    def log_error(
        self,
        request: Request,
        request_id: str,
        error: Exception,
        user_id: Optional[str] = None
    ):
        """Log error"""
        self.logger.error(
            f"Request error: {request.method} {request.url.path} - {type(error).__name__}",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "endpoint": request.url.path,
                "method": request.method,
                "error_type": type(error).__name__,
                "error_message": str(error),
            },
            exc_info=True
        )


class BusinessLogger:
    """
    Business logic logging for important events
    """
    
    def __init__(self):
        self.logger = logging.getLogger("preklo.business")
    
    def log_user_registration(self, user_id: str, username: str, email: str):
        """Log user registration"""
        self.logger.info(
            f"User registered: {username}",
            extra={
                "event": "user_registration",
                "user_id": user_id,
                "username": username,
                "email": email,
            }
        )
    
    def log_transaction(
        self,
        transaction_id: str,
        sender_id: str,
        recipient_id: str,
        amount: str,
        currency: str,
        transaction_type: str
    ):
        """Log transaction"""
        self.logger.info(
            f"Transaction: {amount} {currency} from {sender_id} to {recipient_id}",
            extra={
                "event": "transaction",
                "transaction_id": transaction_id,
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "amount": amount,
                "currency": currency,
                "transaction_type": transaction_type,
            }
        )
    
    def log_payment_request(
        self,
        payment_id: str,
        recipient_id: str,
        amount: str,
        currency: str
    ):
        """Log payment request creation"""
        self.logger.info(
            f"Payment request created: {amount} {currency}",
            extra={
                "event": "payment_request_created",
                "payment_id": payment_id,
                "recipient_id": recipient_id,
                "amount": amount,
                "currency": currency,
            }
        )
    
    def log_authentication(self, user_id: str, username: str, success: bool):
        """Log authentication attempt"""
        event = "authentication_success" if success else "authentication_failure"
        message = f"Authentication {'successful' if success else 'failed'} for {username}"
        
        self.logger.info(
            message,
            extra={
                "event": event,
                "user_id": user_id if success else None,
                "username": username,
                "success": success,
            }
        )


def setup_logging(debug: bool = False):
    """
    Setup application logging configuration
    """
    # Set log level based on debug mode
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Create JSON formatter
    json_formatter = JSONFormatter()
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(json_formatter)
    console_handler.setLevel(log_level)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Setup application loggers
    app_loggers = [
        "preklo",
        "preklo.requests",
        "preklo.business",
        "preklo.security",
        "preklo.blockchain",
        "preklo.circle",
    ]
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        logger.propagate = True
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Create logger instances
    request_logger = RequestLogger()
    business_logger = BusinessLogger()
    
    return request_logger, business_logger


# Global logger instances
request_logger = RequestLogger()
business_logger = BusinessLogger()
