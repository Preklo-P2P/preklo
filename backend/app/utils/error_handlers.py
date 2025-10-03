"""
Global Error Handlers
Provides consistent error handling and user-friendly error messages
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import logging
from typing import Union
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrekloException(Exception):
    """Base exception for Preklo application"""
    def __init__(self, message: str, error_code: str = "PREKLO_ERROR", details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class BlockchainException(PrekloException):
    """Exception for blockchain-related errors"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "BLOCKCHAIN_ERROR", details)


class CircleException(PrekloException):
    """Exception for Circle API-related errors"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "CIRCLE_ERROR", details)


class AuthenticationException(PrekloException):
    """Exception for authentication-related errors"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "AUTH_ERROR", details)


class ValidationException(PrekloException):
    """Exception for validation-related errors"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)


def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: dict = None,
    request_id: str = None
) -> JSONResponse:
    """
    Create a standardized error response
    """
    error_data = {
        "status": "error",
        "error": {
            "code": error_code,
            "message": message,
            "details": details or {},
        }
    }
    
    if request_id:
        error_data["error"]["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=error_data
    )


async def preklo_exception_handler(request: Request, exc: PrekloException):
    """
    Handle custom Preklo exceptions
    """
    logger.error(f"Preklo Exception: {exc.error_code} - {exc.message}")
    
    # Map error codes to HTTP status codes
    status_code_map = {
        "BLOCKCHAIN_ERROR": 502,  # Bad Gateway
        "CIRCLE_ERROR": 502,      # Bad Gateway
        "AUTH_ERROR": 401,        # Unauthorized
        "VALIDATION_ERROR": 400,  # Bad Request
        "PREKLO_ERROR": 500    # Internal Server Error
    }
    
    status_code = status_code_map.get(exc.error_code, 500)
    
    return create_error_response(
        status_code=status_code,
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        request_id=getattr(request.state, "request_id", None)
    )


async def http_exception_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]):
    """
    Handle FastAPI HTTP exceptions
    """
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    
    # Map common HTTP status codes to user-friendly messages
    user_friendly_messages = {
        400: "Invalid request. Please check your input and try again.",
        401: "Authentication required. Please log in and try again.",
        403: "Access denied. You don't have permission to perform this action.",
        404: "The requested resource was not found.",
        409: "Conflict. The resource already exists or there's a conflict with the current state.",
        422: "Invalid input data. Please check your request and try again.",
        429: "Too many requests. Please slow down and try again later.",
        500: "Internal server error. Please try again later.",
        502: "Service temporarily unavailable. Please try again later.",
        503: "Service temporarily unavailable. Please try again later."
    }
    
    message = user_friendly_messages.get(exc.status_code, str(exc.detail))
    
    return create_error_response(
        status_code=exc.status_code,
        error_code=f"HTTP_{exc.status_code}",
        message=message,
        details={"original_detail": str(exc.detail)} if str(exc.detail) != message else {},
        request_id=getattr(request.state, "request_id", None)
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors
    """
    logger.warning(f"Validation Error: {exc.errors()}")
    
    # Format validation errors for user-friendly display
    formatted_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    return create_error_response(
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Invalid input data. Please check the highlighted fields.",
        details={"validation_errors": formatted_errors},
        request_id=getattr(request.state, "request_id", None)
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle SQLAlchemy database errors
    """
    logger.error(f"Database Error: {str(exc)}")
    
    # Handle specific database errors
    if isinstance(exc, IntegrityError):
        # Extract constraint violation details
        error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        
        if "unique constraint" in error_msg.lower():
            return create_error_response(
                status_code=409,
                error_code="DUPLICATE_RESOURCE",
                message="A resource with the provided information already exists.",
                details={"constraint_violation": True},
                request_id=getattr(request.state, "request_id", None)
            )
        elif "foreign key constraint" in error_msg.lower():
            return create_error_response(
                status_code=400,
                error_code="INVALID_REFERENCE",
                message="Referenced resource does not exist.",
                details={"foreign_key_violation": True},
                request_id=getattr(request.state, "request_id", None)
            )
    
    # Generic database error
    return create_error_response(
        status_code=500,
        error_code="DATABASE_ERROR",
        message="A database error occurred. Please try again later.",
        details={},
        request_id=getattr(request.state, "request_id", None)
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions
    """
    logger.error(f"Unexpected Error: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return create_error_response(
        status_code=500,
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again later.",
        details={"error_type": type(exc).__name__} if logger.level <= logging.DEBUG else {},
        request_id=getattr(request.state, "request_id", None)
    )


def setup_error_handlers(app):
    """
    Setup all error handlers for the FastAPI app
    """
    app.add_exception_handler(PrekloException, preklo_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


# Utility functions for raising common errors
def raise_not_found(resource: str, identifier: str = None):
    """Raise a standardized not found error"""
    message = f"{resource} not found"
    if identifier:
        message += f" with identifier: {identifier}"
    
    raise HTTPException(
        status_code=404,
        detail=message
    )


def raise_unauthorized(message: str = "Authentication required"):
    """Raise a standardized unauthorized error"""
    raise HTTPException(
        status_code=401,
        detail=message
    )


def raise_forbidden(message: str = "Access denied"):
    """Raise a standardized forbidden error"""
    raise HTTPException(
        status_code=403,
        detail=message
    )


def raise_bad_request(message: str, details: dict = None):
    """Raise a standardized bad request error"""
    raise ValidationException(message, details)


def raise_blockchain_error(message: str, details: dict = None):
    """Raise a blockchain-related error"""
    raise BlockchainException(message, details)


def raise_circle_error(message: str, details: dict = None):
    """Raise a Circle API-related error"""
    raise CircleException(message, details)
