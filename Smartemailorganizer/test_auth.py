"""
Tests for authentication module.
"""
import os
import time
from datetime import timedelta

import pytest
from fastapi import HTTPException

from backend.auth import AuthManager, get_current_user
from fastapi.security import HTTPAuthorizationCredentials


# Set test JWT secret
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"


def test_hash_password():
    """Test password hashing."""
    auth = AuthManager()
    password = "my_secure_password"
    
    hashed = auth.hash_password(password)
    
    # Verify hash is different from original
    assert hashed != password
    # Verify hash is a string
    assert isinstance(hashed, str)
    # Verify hash starts with bcrypt prefix
    assert hashed.startswith("$2b$")


def test_verify_password():
    """Test password verification."""
    auth = AuthManager()
    password = "my_secure_password"
    
    hashed = auth.hash_password(password)
    
    # Correct password should verify
    assert auth.verify_password(password, hashed) is True
    
    # Wrong password should not verify
    assert auth.verify_password("wrong_password", hashed) is False


def test_create_access_token():
    """Test JWT token creation."""
    auth = AuthManager()
    user_id = 1
    email = "test@example.com"
    
    token = auth.create_access_token(user_id, email)
    
    # Verify token is a string
    assert isinstance(token, str)
    # Verify token has JWT structure (3 parts separated by dots)
    assert len(token.split('.')) == 3


def test_verify_token():
    """Test JWT token verification."""
    auth = AuthManager()
    user_id = 1
    email = "test@example.com"
    
    # Create token
    token = auth.create_access_token(user_id, email)
    
    # Verify token
    payload = auth.verify_token(token)
    
    # Check payload contents
    assert payload["user_id"] == user_id
    assert payload["sub"] == email
    assert "exp" in payload
    assert "iat" in payload


def test_verify_expired_token():
    """Test that expired tokens are rejected."""
    auth = AuthManager()
    user_id = 1
    email = "test@example.com"
    
    # Create token that expires immediately
    token = auth.create_access_token(user_id, email, expires_delta=timedelta(seconds=-1))
    
    # Verify token raises exception
    with pytest.raises(HTTPException) as exc_info:
        auth.verify_token(token)
    
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_verify_invalid_token():
    """Test that invalid tokens are rejected."""
    auth = AuthManager()
    
    # Try to verify an invalid token
    with pytest.raises(HTTPException) as exc_info:
        auth.verify_token("invalid.token.here")
    
    assert exc_info.value.status_code == 401


def test_auth_manager_without_secret():
    """Test that AuthManager raises error without JWT secret."""
    # Temporarily remove JWT_SECRET
    original_secret = os.environ.get("JWT_SECRET")
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]
    
    try:
        with pytest.raises(ValueError) as exc_info:
            AuthManager()
        
        assert "JWT_SECRET" in str(exc_info.value)
    finally:
        # Restore original secret
        if original_secret:
            os.environ["JWT_SECRET"] = original_secret


def test_get_current_user():
    """Test the FastAPI dependency function."""
    auth = AuthManager()
    user_id = 1
    email = "test@example.com"
    
    # Create token
    token = auth.create_access_token(user_id, email)
    
    # Create mock credentials
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    # Get current user
    user = get_current_user(credentials, auth)
    
    # Verify user information
    assert user["user_id"] == user_id
    assert user["sub"] == email


def test_get_current_user_invalid_token():
    """Test that get_current_user rejects invalid tokens."""
    auth = AuthManager()
    
    # Create mock credentials with invalid token
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token")
    
    # Should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials, auth)
    
    assert exc_info.value.status_code == 401


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
