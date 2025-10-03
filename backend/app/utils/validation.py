"""
Environment and Input Validation
Validates environment variables and provides additional input sanitization
"""

import os
import re
from typing import List, Optional
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger("preklo.validation")


class EnvironmentValidator:
    """
    Validates that required environment variables are set
    """
    
    REQUIRED_VARS = [
        "DATABASE_URL",
        "JWT_SECRET_KEY",
        "APTOS_NODE_URL",
    ]
    
    RECOMMENDED_VARS = [
        "APTOS_PRIVATE_KEY",
        "APTOS_CONTRACT_ADDRESS", 
        "CIRCLE_API_KEY",
        "NODIT_API_KEY",
    ]
    
    @classmethod
    def validate_environment(cls) -> bool:
        """
        Validate that all required environment variables are set
        """
        missing_required = []
        missing_recommended = []
        
        # Check required variables (allow defaults for development)
        for var in cls.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                missing_required.append(var)
            elif var == "JWT_SECRET_KEY" and value == "your_super_secret_jwt_key_here":
                # Allow default JWT key in development but warn
                logger.warning(f"{var} is using default value - change for production")
            elif value in ["", "your_secret_here", "your_key_here"]:
                missing_required.append(var)
        
        # Check recommended variables
        for var in cls.RECOMMENDED_VARS:
            if not os.getenv(var) or os.getenv(var) in ["", "your_secret_here", "your_key_here", "0x1"]:
                missing_recommended.append(var)
        
        # Log results
        if missing_required:
            logger.error(f"Missing required environment variables: {missing_required}")
            return False
        
        if missing_recommended:
            logger.warning(f"Missing recommended environment variables: {missing_recommended}")
            logger.warning("Some features may not work properly in production")
        
        logger.info("Environment validation passed")
        return True
    
    @classmethod
    def validate_jwt_secret(cls) -> bool:
        """
        Validate JWT secret key strength
        """
        jwt_secret = os.getenv("JWT_SECRET_KEY", "")
        
        if len(jwt_secret) < 20:  # Reduced for development
            logger.error("JWT_SECRET_KEY must be at least 20 characters long")
            return False
        
        if jwt_secret == "your_super_secret_jwt_key_here":
            logger.warning("JWT_SECRET_KEY is using default value - change it for production")
            # Allow default in development
            return True
        
        return True


class InputValidator:
    """
    Additional input validation and sanitization
    """
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Validate username format
        """
        if not username or len(username) < 3 or len(username) > 32:
            return False
        
        # Allow alphanumeric, underscores, and hyphens
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_wallet_address(address: str) -> bool:
        """
        Validate Aptos wallet address format
        """
        if not address:
            return False
        
        # Aptos addresses are hex strings, can be various lengths
        pattern = r'^0x[a-fA-F0-9]+$'
        return bool(re.match(pattern, address)) and len(address) >= 3
    
    @staticmethod
    def validate_amount(amount_str: str, currency: str) -> Optional[Decimal]:
        """
        Validate and parse monetary amount
        """
        try:
            amount = Decimal(amount_str)
            
            # Check for negative amounts
            if amount <= 0:
                return None
            
            # Check decimal places based on currency
            if currency in ["USDC", "USDT"]:
                # Max 6 decimal places for stablecoins
                if amount.as_tuple().exponent < -6:
                    return None
            elif currency == "APT":
                # Max 8 decimal places for APT
                if amount.as_tuple().exponent < -8:
                    return None
            
            # Check maximum amounts (prevent overflow)
            max_amount = Decimal("1000000")  # 1 million max
            if amount > max_amount:
                return None
            
            return amount
            
        except (InvalidOperation, ValueError):
            return None
    
    @staticmethod
    def sanitize_description(description: str) -> str:
        """
        Sanitize payment description
        """
        if not description:
            return ""
        
        # Remove potential XSS characters
        description = re.sub(r'[<>"\']', '', description)
        
        # Limit length
        return description[:500]
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Basic email validation
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_currency_type(currency: str) -> bool:
        """
        Validate supported currency types
        """
        supported_currencies = ["APT", "USDC", "USDT"]
        return currency in supported_currencies
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password strength
        Returns (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if len(password) > 128:
            return False, "Password must be no more than 128 characters long"
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        # Check for at least one digit
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        # Check for common weak passwords
        weak_passwords = [
            "password", "123456", "password123", "admin", "qwerty",
            "letmein", "welcome", "monkey", "1234567890", "abc123"
        ]
        
        if password.lower() in weak_passwords:
            return False, "Password is too common, please choose a stronger password"
        
        return True, ""


def validate_startup_environment() -> bool:
    """
    Validate environment on application startup
    """
    logger.info("Validating startup environment...")
    
    env_valid = EnvironmentValidator.validate_environment()
    jwt_valid = EnvironmentValidator.validate_jwt_secret()
    
    if not env_valid:
        logger.error("Environment validation failed - application may not work correctly")
        return False
    
    if not jwt_valid:
        logger.error("JWT configuration invalid - authentication will not work")
        return False
    
    logger.info("Startup environment validation completed successfully")
    return True
