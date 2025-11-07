"""
Configuration module for Email Management System.
Centralizes all environment variables and application settings.
"""
import os
from pathlib import Path


class Config:
    """Centralized configuration class for the Email Management System."""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = BASE_DIR / "models"
    
    # Security settings
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    # Database settings
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "emails.db"))
    
    # ML Model settings
    MODEL_PATH = os.getenv("MODEL_PATH", str(MODELS_DIR / "classifier.pkl"))
    
    # IMAP settings
    IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
    IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
    IMAP_TIMEOUT = int(os.getenv("IMAP_TIMEOUT", "30"))
    
    # SMTP settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", "30"))
    
    # Sync settings
    THREAD_POOL_SIZE = int(os.getenv("THREAD_POOL_SIZE", "5"))
    SYNC_TIMEOUT_MINUTES = int(os.getenv("SYNC_TIMEOUT_MINUTES", "5"))
    DEFAULT_FETCH_COUNT = int(os.getenv("DEFAULT_FETCH_COUNT", "50"))
    
    # Server settings
    SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
    
    # CORS settings
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist."""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
        cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate critical configuration values."""
        errors = []
        
        if cls.JWT_SECRET == "dev-secret-key-change-in-production":
            errors.append("WARNING: Using default JWT_SECRET. Set JWT_SECRET environment variable for production.")
        
        if len(cls.JWT_SECRET) < 32:
            errors.append("ERROR: JWT_SECRET must be at least 32 characters long.")
        
        return errors
    
    @classmethod
    def display(cls):
        """Display current configuration (excluding sensitive data)."""
        print("=" * 60)
        print("Email Management System Configuration")
        print("=" * 60)
        print(f"Database Path: {cls.DATABASE_PATH}")
        print(f"Model Path: {cls.MODEL_PATH}")
        print(f"IMAP Server: {cls.IMAP_SERVER}:{cls.IMAP_PORT}")
        print(f"SMTP Server: {cls.SMTP_SERVER}:{cls.SMTP_PORT}")
        print(f"Thread Pool Size: {cls.THREAD_POOL_SIZE}")
        print(f"Server: {cls.SERVER_HOST}:{cls.SERVER_PORT}")
        print(f"JWT Algorithm: {cls.JWT_ALGORITHM}")
        print(f"JWT Expiration: {cls.JWT_EXPIRATION_HOURS} hours")
        print("=" * 60)


# Create a singleton instance
config = Config()
