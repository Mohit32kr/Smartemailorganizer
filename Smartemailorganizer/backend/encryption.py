"""
Simple encryption utility for storing email passwords.
Uses Fernet symmetric encryption from cryptography library.
"""
from cryptography.fernet import Fernet
from backend.config import config
import base64
import hashlib


class EncryptionManager:
    """Manages encryption and decryption of sensitive data."""
    
    def __init__(self, secret_key: str = None):
        """
        Initialize encryption manager with a secret key.
        
        Args:
            secret_key: Secret key for encryption. Uses JWT_SECRET if not provided.
        """
        # Use JWT_SECRET to derive encryption key
        key_material = secret_key or config.JWT_SECRET
        
        # Derive a valid Fernet key from the secret
        key_bytes = hashlib.sha256(key_material.encode()).digest()
        self.key = base64.urlsafe_b64encode(key_bytes)
        self.cipher = Fernet(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            return None
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            encrypted: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted:
            return None
        
        decrypted_bytes = self.cipher.decrypt(encrypted.encode())
        return decrypted_bytes.decode()


# Global encryption manager instance
encryption_manager = EncryptionManager()
