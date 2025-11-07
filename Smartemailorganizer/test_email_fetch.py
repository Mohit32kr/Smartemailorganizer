#!/usr/bin/env python3
"""
Standalone test script to verify email fetching works.
Tests IMAP connection and email retrieval.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.imap_handler import IMAPHandler
from backend.classifier import EmailClassifier
from backend.config import config


def test_email_fetch():
    """Test email fetching with user credentials."""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    print("=" * 70)
    print("Email Fetch Test")
    print("=" * 70)
    print()
    
    # Get credentials from environment or user input
    email = os.getenv("MAIL_ID")
    password = os.getenv("APP_PASSWORD")
    
    if not email or not password:
        print("Environment variables not found. Please enter credentials:")
        email = input("Enter your Gmail address: ").strip()
        password = input("Enter your Gmail App Password (16 chars, no spaces): ").strip()
    else:
        print(f"Using credentials from environment variables")
        print(f"Email: {email}")
        print(f"Password: {'*' * len(password)}")
    
    if not email or not password:
        print("✗ Email and password are required")
        return False
    
    print()
    print("-" * 70)
    print("Testing IMAP Connection...")
    print("-" * 70)
    
    try:
        # Initialize IMAP handler
        imap_handler = IMAPHandler(email, password)
        print(f"✓ IMAP handler initialized")
        print(f"  Server: {config.IMAP_SERVER}:{config.IMAP_PORT}")
        
        # Connect to IMAP
        if not imap_handler.connect():
            print("✗ Failed to connect to IMAP server")
            print("  Check your credentials and internet connection")
            return False
        
        print("✓ Connected to IMAP server")
        
        # Fetch emails
        print()
        print("Fetching emails (this may take a moment)...")
        emails = imap_handler.fetch_latest_emails(count=10)
        
        # Disconnect
        imap_handler.disconnect()
        
        if not emails:
            print("✗ No emails fetched")
            print("  This could mean:")
            print("  - Your inbox is empty")
            print("  - Authentication failed")
            print("  - IMAP access is not enabled")
            return False
        
        print(f"✓ Successfully fetched {len(emails)} emails!")
        print()
        print("-" * 70)
        print("Email Details:")
        print("-" * 70)
        
        for i, email_data in enumerate(emails[:5], 1):  # Show first 5
            print(f"\n{i}. From: {email_data.sender}")
            print(f"   Subject: {email_data.subject}")
            print(f"   Date: {email_data.date}")
            print(f"   Body preview: {email_data.body[:100]}...")
        
        if len(emails) > 5:
            print(f"\n... and {len(emails) - 5} more emails")
        
        # Test classification
        print()
        print("-" * 70)
        print("Testing Email Classification...")
        print("-" * 70)
        
        try:
            classifier = EmailClassifier(config.MODEL_PATH)
            
            if not classifier.is_trained:
                print("  Classifier not trained yet, training now...")
                from backend.training_data import get_training_data
                training_data = get_training_data()
                classifier.train(training_data)
                classifier.save_model()
                print("  ✓ Classifier trained")
            else:
                classifier.load_model()
                print("  ✓ Classifier loaded")
            
            # Classify first email
            if emails:
                first_email = emails[0]
                category = classifier.classify(first_email.subject, first_email.body)
                print(f"\n  Example classification:")
                print(f"  Subject: {first_email.subject}")
                print(f"  Category: {category}")
        
        except Exception as e:
            print(f"  ⚠ Classification test failed: {e}")
            print("  (This is okay, classification is optional)")
        
        print()
        print("=" * 70)
        print("✓ Email Fetch Test PASSED!")
        print("=" * 70)
        print()
        print("Your Gmail credentials are working correctly.")
        print("You can now use these credentials in the application.")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print("✗ Email Fetch Test FAILED")
        print("=" * 70)
        print(f"\nError: {str(e)}")
        print()
        print("Common issues:")
        print("1. Wrong app password - make sure you removed all spaces")
        print("2. App password not created - create one in Google Account settings")
        print("3. IMAP not enabled - check Gmail settings")
        print("4. 2-Step Verification not enabled - required for app passwords")
        print()
        
        # Print detailed error for debugging
        import traceback
        print("Detailed error:")
        print("-" * 70)
        traceback.print_exc()
        print("-" * 70)
        
        return False


if __name__ == "__main__":
    try:
        success = test_email_fetch()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
