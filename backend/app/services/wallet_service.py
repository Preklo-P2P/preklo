"""
Wallet Service
Handles custodial wallet generation, encryption, and management
"""

import os
import secrets
import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import json

logger = logging.getLogger("preklo.wallet_service")

try:
    from aptos_sdk.account import Account
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    Account = None
    print("WARNING: Aptos SDK not available, using mock wallet service")


class WalletService:
    def __init__(self):
        # Get encryption key from environment or use fixed key for testing
        self.master_key = os.getenv("WALLET_ENCRYPTION_KEY")
        if not self.master_key:
            # Use a fixed key for testing - in production, this should be set as an environment variable
            self.master_key = "dGVzdGluZ19maXhlZF9lbmNyeXB0aW9uX2tleV9mb3JfaGFja2F0aG9u"  # Fixed base64 key for testing
            logger.warning("Using fixed testing encryption key. Set WALLET_ENCRYPTION_KEY in production!")
        
        # Security monitoring
        self._failed_attempts = {}
        self._max_failed_attempts = 5
        self._lockout_duration = timedelta(minutes=15)
        
        # Backup tracking
        self._backup_requests = {}
        self._backup_cooldown = timedelta(hours=24)
    
    def _format_aptos_address(self, address: str) -> str:
        """
        Format an Aptos address to ensure it's 64 hex characters (32 bytes)
        """
        # Remove 0x prefix if present
        clean_address = address.replace('0x', '')
        
        # Pad with zeros to make it 64 characters (32 bytes)
        formatted_address = clean_address.zfill(64)
        
        # Add 0x prefix back
        return f"0x{formatted_address}"
    
    def generate_wallet(self) -> Tuple[str, str]:
        """
        Generate a new Aptos wallet with enhanced security
        Returns: (wallet_address, private_key_hex)
        """
        if not SDK_AVAILABLE or Account is None:
            # Mock wallet generation for testing
            mock_address = f"0x{secrets.token_hex(32)}"
            mock_private_key = secrets.token_hex(32)
            logger.info("Generated mock wallet for testing")
            return mock_address, mock_private_key
        
        try:
            # Generate new Aptos account
            account = Account.generate()
            wallet_address = str(account.address())
            private_key_hex = account.private_key.hex()
            
            # Ensure address is properly formatted (64 hex chars)
            wallet_address = self._format_aptos_address(wallet_address)
            
            logger.info(f"Generated new Aptos wallet: {wallet_address}")
            return wallet_address, private_key_hex
            
        except Exception as e:
            logger.error(f"Error generating wallet: {e}")
            # Fallback to mock generation
            mock_address = f"0x{secrets.token_hex(32)}"
            mock_private_key = secrets.token_hex(32)
            logger.warning("Falling back to mock wallet generation")
            return mock_address, mock_private_key
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from user password and salt
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
    
    def encrypt_private_key(self, private_key: str, user_password: str) -> str:
        """
        Encrypt private key using user password + master key
        Returns: base64 encoded encrypted data with salt
        """
        try:
            # Generate random salt
            salt = os.urandom(16)
            
            # Derive key from user password
            user_key = self._derive_key(user_password, salt)
            
            # Combine with master key for double encryption
            combined_key = base64.urlsafe_b64encode(
                bytes(a ^ b for a, b in zip(
                    base64.urlsafe_b64decode(user_key),
                    base64.urlsafe_b64decode(self.master_key.encode())
                ))
            )
            
            # Encrypt private key
            fernet = Fernet(combined_key)
            encrypted_key = fernet.encrypt(private_key.encode())
            
            # Combine salt + encrypted data
            encrypted_data = base64.urlsafe_b64encode(salt + encrypted_key).decode()
            
            return encrypted_data
            
        except Exception as e:
            print(f"Error encrypting private key: {e}")
            raise
    
    def decrypt_private_key(self, encrypted_data: str, user_password: str, user_id: str = None) -> Optional[str]:
        """
        Decrypt private key using user password + master key with security monitoring
        Returns: decrypted private key or None if failed
        """
        # Check for security lockout
        if user_id and self._is_user_locked_out(user_id):
            logger.warning(f"User {user_id} is locked out due to too many failed attempts")
            return None
        
        try:
            # Decode encrypted data
            data = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Extract salt and encrypted key
            salt = data[:16]
            encrypted_key = data[16:]
            
            # Derive key from user password
            user_key = self._derive_key(user_password, salt)
            
            # Combine with master key
            combined_key = base64.urlsafe_b64encode(
                bytes(a ^ b for a, b in zip(
                    base64.urlsafe_b64decode(user_key),
                    base64.urlsafe_b64decode(self.master_key.encode())
                ))
            )
            
            # Decrypt private key
            fernet = Fernet(combined_key)
            decrypted_key = fernet.decrypt(encrypted_key).decode()
            
            # Reset failed attempts on success
            if user_id and user_id in self._failed_attempts:
                del self._failed_attempts[user_id]
                logger.info(f"Successfully decrypted private key for user {user_id}")
            
            return decrypted_key
            
        except Exception as e:
            logger.error(f"Error decrypting private key: {e}")
            
            # Track failed attempts
            if user_id:
                self._track_failed_attempt(user_id)
            
            return None
    
    def _is_user_locked_out(self, user_id: str) -> bool:
        """Check if user is locked out due to too many failed attempts"""
        if user_id not in self._failed_attempts:
            return False
        
        attempts_data = self._failed_attempts[user_id]
        if attempts_data['count'] < self._max_failed_attempts:
            return False
        
        # Check if lockout period has expired
        if datetime.now() - attempts_data['last_attempt'] > self._lockout_duration:
            del self._failed_attempts[user_id]
            return False
        
        return True
    
    def _track_failed_attempt(self, user_id: str):
        """Track failed decryption attempts"""
        now = datetime.now()
        
        if user_id not in self._failed_attempts:
            self._failed_attempts[user_id] = {'count': 0, 'last_attempt': now}
        
        self._failed_attempts[user_id]['count'] += 1
        self._failed_attempts[user_id]['last_attempt'] = now
        
        count = self._failed_attempts[user_id]['count']
        logger.warning(f"Failed decryption attempt {count} for user {user_id}")
        
        if count >= self._max_failed_attempts:
            logger.error(f"User {user_id} locked out due to {count} failed attempts")
    
    def create_custodial_wallet(self, user_password: str) -> Tuple[str, str]:
        """
        Create a new custodial wallet with encrypted private key
        Returns: (wallet_address, encrypted_private_key)
        """
        # Generate new wallet
        wallet_address, private_key = self.generate_wallet()
        
        # Encrypt private key
        encrypted_private_key = self.encrypt_private_key(private_key, user_password)
        
        return wallet_address, encrypted_private_key
    
    def get_account_for_transaction(self, encrypted_private_key: str, user_password: str, user_id: str = None) -> Optional['Account']:
        """
        Get Aptos Account object for signing transactions with enhanced security
        Returns: Account object or None if failed
        """
        if not SDK_AVAILABLE or Account is None:
            logger.warning("Aptos SDK not available, cannot create account")
            return None
        
        try:
            # Decrypt private key with security monitoring
            private_key = self.decrypt_private_key(encrypted_private_key, user_password, user_id)
            if not private_key:
                logger.error("Failed to decrypt private key for transaction")
                return None
            
            # Create Account object
            account = Account.load_key(private_key)
            logger.info(f"Successfully created account for transaction (user: {user_id})")
            return account
            
        except Exception as e:
            logger.error(f"Error creating account for transaction: {e}")
            return None
    
    def export_wallet_data(self, encrypted_private_key: str, user_password: str, user_id: str = None) -> Optional[dict]:
        """
        Export wallet data for user to migrate to self-custody with backup tracking
        Returns: dict with address and private key or None if failed
        """
        # Check backup cooldown
        if user_id and self._is_backup_cooldown_active(user_id):
            logger.warning(f"User {user_id} attempted backup export during cooldown period")
            return None
        
        try:
            # Decrypt private key with security monitoring
            private_key = self.decrypt_private_key(encrypted_private_key, user_password, user_id)
            if not private_key:
                logger.error("Failed to decrypt private key for export")
                return None
            
            if SDK_AVAILABLE and Account is not None:
                # Get wallet address from private key
                account = Account.load_key(private_key)
                wallet_address = str(account.address())
            else:
                # For mock, we can't derive address from private key
                wallet_address = "Mock wallet - use real SDK"
            
            # Track backup request
            if user_id:
                self._track_backup_request(user_id)
                logger.info(f"Wallet export completed for user {user_id}")
            
            return {
                "wallet_address": wallet_address,
                "private_key": private_key,
                "mnemonic": None,  # Could add mnemonic generation later
                "export_warning": "Keep this private key secure. Anyone with access can control your wallet.",
                "export_timestamp": datetime.now().isoformat(),
                "backup_id": f"backup_{user_id}_{int(datetime.now().timestamp())}" if user_id else None
            }
            
        except Exception as e:
            logger.error(f"Error exporting wallet data: {e}")
            return None
    
    def _is_backup_cooldown_active(self, user_id: str) -> bool:
        """Check if user is in backup cooldown period"""
        if user_id not in self._backup_requests:
            return False
        
        last_backup = self._backup_requests[user_id]
        return datetime.now() - last_backup < self._backup_cooldown
    
    def _track_backup_request(self, user_id: str):
        """Track backup request for cooldown management"""
        self._backup_requests[user_id] = datetime.now()
    
    def get_backup_status(self, user_id: str) -> Dict[str, Any]:
        """Get backup status and cooldown information"""
        if user_id not in self._backup_requests:
            return {
                "can_backup": True,
                "last_backup": None,
                "cooldown_remaining": None
            }
        
        last_backup = self._backup_requests[user_id]
        time_since_backup = datetime.now() - last_backup
        
        if time_since_backup < self._backup_cooldown:
            cooldown_remaining = self._backup_cooldown - time_since_backup
            return {
                "can_backup": False,
                "last_backup": last_backup.isoformat(),
                "cooldown_remaining": str(cooldown_remaining)
            }
        else:
            return {
                "can_backup": True,
                "last_backup": last_backup.isoformat(),
                "cooldown_remaining": None
            }
    
    def get_security_status(self, user_id: str) -> Dict[str, Any]:
        """Get security status including failed attempts and lockout information"""
        if user_id not in self._failed_attempts:
            return {
                "is_locked_out": False,
                "failed_attempts": 0,
                "lockout_remaining": None
            }
        
        attempts_data = self._failed_attempts[user_id]
        is_locked_out = self._is_user_locked_out(user_id)
        
        if is_locked_out:
            lockout_remaining = self._lockout_duration - (datetime.now() - attempts_data['last_attempt'])
            return {
                "is_locked_out": True,
                "failed_attempts": attempts_data['count'],
                "lockout_remaining": str(lockout_remaining)
            }
        else:
            return {
                "is_locked_out": False,
                "failed_attempts": attempts_data['count'],
                "lockout_remaining": None
            }
    
    def validate_wallet_address(self, address: str) -> bool:
        """Validate Aptos wallet address format"""
        try:
            if not address.startswith("0x"):
                return False
            
            # Remove 0x prefix and check if it's valid hex
            hex_part = address[2:]
            if len(hex_part) != 64:  # Aptos addresses are 32 bytes = 64 hex chars
                return False
            
            # Check if it's valid hexadecimal
            int(hex_part, 16)
            return True
            
        except (ValueError, AttributeError):
            return False
    
    def generate_wallet_backup_phrase(self, private_key: str) -> Optional[str]:
        """Generate a backup phrase for wallet recovery (placeholder for future implementation)"""
        # This is a placeholder for future mnemonic phrase generation
        # In a real implementation, you would use a BIP39-compatible library
        logger.info("Wallet backup phrase generation requested (not yet implemented)")
        return None


# Global wallet service instance
wallet_service = WalletService()
