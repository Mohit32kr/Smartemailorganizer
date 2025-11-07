#!/usr/bin/env python3
"""
Quick script to register a test user.
"""
import requests
import sys

API_URL = "http://localhost:8000/api"

def register_user(email, password):
    """Register a new user."""
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={
                "email": email,
                "password": password
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✓ User registered successfully!")
            print(f"  Email: {email}")
            print(f"  Token: {data['access_token'][:20]}...")
            print(f"\nYou can now login at http://localhost:8000")
            return True
        else:
            error = response.json()
            print(f"✗ Registration failed: {error.get('detail', 'Unknown error')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to server. Is it running?")
        print("  Start the server with: python run.py")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Email Manager - User Registration")
    print("=" * 60)
    
    if len(sys.argv) == 3:
        email = sys.argv[1]
        password = sys.argv[2]
    else:
        print("\nUsage: python register_user.py <email> <password>")
        print("\nExample:")
        print("  python register_user.py test@example.com mypassword123")
        print("\nOr enter details now:")
        print()
        
        email = input("Email: ").strip()
        password = input("Password (min 8 chars, must have letter and digit): ").strip()
    
    if not email or not password:
        print("✗ Email and password are required")
        sys.exit(1)
    
    print(f"\nRegistering user: {email}")
    success = register_user(email, password)
    
    sys.exit(0 if success else 1)
