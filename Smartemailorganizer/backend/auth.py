"""
Authentication module for JWT token management and password hashing.
"""
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


class AuthManager:
    """Manages user authentication, password hashing, and JWT token operations."""
    
    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        """
        Initialize AuthManager with JWT configuration.
        
        Args:
            secret_key: Secret key for JWT signing. If None, loads from JWT_SECRET env var.
            algorithm: JWT signing algorithm (default: HS256)
        
        Raises:
            ValueError: If secret_key is not provided and JWT_SECRET env var is not set
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET")
        if not self.secret_key:
            raise ValueError("JWT_SECRET must be provided or set as environment variable")
        
        self.algorithm = algorithm
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt with automatic salt generation.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password as a string
        """
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    def create_access_token(self, user_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Generate a JWT access token for an authenticated user.
        
        Args:
            user_id: User's database ID
            email: User's email address
            expires_delta: Token expiration time. Defaults to 24 hours if not provided.
            
        Returns:
            Encoded JWT token as a string
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=24)
        
        # Calculate expiration timestamp
        expire = datetime.utcnow() + expires_delta
        
        # Create JWT payload
        payload = {
            "sub": email,  # Subject (user identifier)
            "user_id": user_id,
            "exp": expire,  # Expiration timestamp
            "iat": datetime.utcnow()  # Issued at timestamp
        }
        
        # Encode and return token
        encoded_jwt = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> dict:
        """
        Validate a JWT token and extract its payload.
        
        Args:
            token: JWT token string to validate
            
        Returns:
            Decoded token payload as a dictionary
            
        Raises:
            HTTPException: If token is invalid, expired, or malformed
        """
        try:
            # Decode and validate token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )


# HTTP Bearer security scheme for FastAPI
security = HTTPBearer()

# Global auth manager instance for dependency injection
_auth_manager_instance: Optional[AuthManager] = None


def set_auth_manager(auth_manager: AuthManager):
    """
    Set the global AuthManager instance for use in dependency injection.
    
    This should be called during application startup to configure the
    AuthManager with the correct secret key.
    
    Args:
        auth_manager: Configured AuthManager instance
    """
    global _auth_manager_instance
    _auth_manager_instance = auth_manager


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    FastAPI dependency function to extract and validate JWT from Authorization header.
    
    This function can be used as a dependency in FastAPI route handlers to ensure
    the request is authenticated and to extract user information from the JWT token.
    
    Args:
        credentials: HTTP authorization credentials extracted by FastAPI
        
    Returns:
        Dictionary containing user information from the validated token
        
    Raises:
        HTTPException: If token is missing, invalid, or expired
        
    Example:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["user_id"], "email": user["sub"]}
    """
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token from credentials
    token = credentials.credentials
    
    # Use global auth manager instance
    if _auth_manager_instance is None:
        raise HTTPException(
            status_code=500,
            detail="Authentication system not initialized"
        )
    
    # Verify token and return user information
    return _auth_manager_instance.verify_token(token)
