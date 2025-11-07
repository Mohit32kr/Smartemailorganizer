#!/usr/bin/env python3
"""
Database migration script to add email_password column to users table.
"""
import sys
import os
import sqlite3
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.config import config


def migrate_database():
    """Add email_password column to users table if it doesn't exist."""
    db_path = config.DATABASE_PATH
    
    if not os.path.exists(db_path):
        print(f"✓ Database doesn't exist yet at {db_path}")
        print("  It will be created with the new schema on first run")
        return True
    
    print(f"Migrating database at {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if email_password column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'email_password' in columns:
            print("✓ Database already has email_password column")
            conn.close()
            return True
        
        # Add email_password column
        print("  Adding email_password column...")
        cursor.execute("ALTER TABLE users ADD COLUMN email_password TEXT")
        conn.commit()
        
        print("✓ Migration completed successfully")
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration")
    print("=" * 60)
    print()
    
    success = migrate_database()
    
    if success:
        print("\n✓ Database is ready")
        print("  You can now start the server with: python run.py")
    else:
        print("\n✗ Migration failed")
        print("  You may need to delete the database and start fresh")
        print(f"  Database location: {config.DATABASE_PATH}")
    
    sys.exit(0 if success else 1)
