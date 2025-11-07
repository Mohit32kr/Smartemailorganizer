"""
Test script to verify database functionality.
"""
from backend.database import DatabaseManager
from datetime import datetime

def test_database():
    """Test all database operations."""
    print("Testing Database Layer...")
    
    # Initialize database manager
    db = DatabaseManager("./data/test_emails.db")
    
    # Test 1: Create user
    print("\n1. Testing create_user...")
    user = db.create_user("test@example.com", "hashed_password_123")
    if user:
        print(f"✓ User created: {user}")
    else:
        print("✗ Failed to create user")
        return
    
    # Test 2: Try to create duplicate user
    print("\n2. Testing duplicate user handling...")
    duplicate = db.create_user("test@example.com", "another_hash")
    if duplicate is None:
        print("✓ Duplicate user correctly rejected")
    else:
        print("✗ Duplicate user was created (should not happen)")
    
    # Test 3: Get user by email
    print("\n3. Testing get_user_by_email...")
    retrieved_user = db.get_user_by_email("test@example.com")
    if retrieved_user and retrieved_user.email == "test@example.com":
        print(f"✓ User retrieved: {retrieved_user}")
    else:
        print("✗ Failed to retrieve user")
        return
    
    # Test 4: Save emails
    print("\n4. Testing save_email...")
    email1 = db.save_email(
        user_id=user.id,
        message_id="msg001",
        sender="sender1@example.com",
        subject="Test Email 1",
        body="This is the body of test email 1",
        category="Work",
        date=datetime(2025, 11, 7, 10, 0, 0)
    )
    if email1:
        print(f"✓ Email 1 saved: {email1}")
    else:
        print("✗ Failed to save email 1")
        return
    
    email2 = db.save_email(
        user_id=user.id,
        message_id="msg002",
        sender="sender2@example.com",
        subject="Test Email 2",
        body="This is the body of test email 2",
        category="Personal",
        date=datetime(2025, 11, 7, 11, 0, 0)
    )
    if email2:
        print(f"✓ Email 2 saved: {email2}")
    
    # Test 5: Try to save duplicate email
    print("\n5. Testing duplicate email handling...")
    duplicate_email = db.save_email(
        user_id=user.id,
        message_id="msg001",
        sender="sender1@example.com",
        subject="Duplicate",
        body="Should not be saved",
        category="Spam",
        date=datetime(2025, 11, 7, 12, 0, 0)
    )
    if duplicate_email is None:
        print("✓ Duplicate email correctly rejected")
    else:
        print("✗ Duplicate email was saved (should not happen)")
    
    # Test 6: Get all emails
    print("\n6. Testing get_emails (all)...")
    emails, total = db.get_emails(user.id, page=1, page_size=20)
    print(f"✓ Retrieved {len(emails)} emails (total: {total})")
    for email in emails:
        print(f"  - {email.subject} ({email.category})")
    
    # Test 7: Get emails by category
    print("\n7. Testing get_emails (filtered by category)...")
    work_emails, work_total = db.get_emails(user.id, category="Work", page=1, page_size=20)
    print(f"✓ Retrieved {len(work_emails)} Work emails (total: {work_total})")
    for email in work_emails:
        print(f"  - {email.subject} ({email.category})")
    
    # Test 8: Search emails
    print("\n8. Testing search_emails...")
    search_results = db.search_emails(user.id, "Test")
    print(f"✓ Search for 'Test' returned {len(search_results)} results")
    for email in search_results:
        print(f"  - {email.subject}")
    
    # Test 9: Get email stats
    print("\n9. Testing get_email_stats...")
    stats = db.get_email_stats(user.id)
    print(f"✓ Email statistics: {stats}")
    
    # Test 10: Pagination
    print("\n10. Testing pagination...")
    # Add more emails for pagination test
    for i in range(3, 8):
        db.save_email(
            user_id=user.id,
            message_id=f"msg{i:03d}",
            sender=f"sender{i}@example.com",
            subject=f"Test Email {i}",
            body=f"Body of email {i}",
            category="Promotions",
            date=datetime(2025, 11, 7, 12 + i, 0, 0)
        )
    
    page1_emails, total = db.get_emails(user.id, page=1, page_size=3)
    page2_emails, _ = db.get_emails(user.id, page=2, page_size=3)
    print(f"✓ Page 1: {len(page1_emails)} emails, Page 2: {len(page2_emails)} emails (Total: {total})")
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)

if __name__ == "__main__":
    test_database()
