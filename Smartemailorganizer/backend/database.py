"""
Database layer with SQLAlchemy models and CRUD operations.
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import Optional, List
import os

# Create declarative base
Base = declarative_base()


class User(Base):
    """User model for storing user credentials."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    email_password = Column(String, nullable=True)  # Encrypted email password for IMAP/SMTP
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to emails
    emails = relationship("Email", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


class Email(Base):
    """Email model for storing email metadata."""
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship to user
    user = relationship("User", back_populates="emails")
    
    # Unique constraint on (user_id, message_id) to prevent duplicates
    __table_args__ = (
        UniqueConstraint('user_id', 'message_id', name='uix_user_message'),
        # Indexes for query optimization
        Index('idx_user_category', 'user_id', 'category'),
        Index('idx_user_date', 'user_id', 'date'),
        Index('idx_user_sender', 'user_id', 'sender'),
    )
    
    def __repr__(self):
        return f"<Email(id={self.id}, subject={self.subject}, category={self.category})>"


class DatabaseManager:
    """Manager class for database operations."""
    
    def __init__(self, db_path: str = "./data/emails.db"):
        """
        Initialize database connection with thread-safe configuration.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create engine with connection pooling for thread safety
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},  # Allow multi-threading
            pool_pre_ping=True,  # Verify connections before using
            pool_size=10,  # Connection pool size
            max_overflow=20  # Additional connections if pool is full
        )
        
        # Create scoped session factory for thread-local sessions
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)
    
    def create_user(self, email: str, password_hash: str, email_password: str = None) -> Optional[User]:
        """
        Create a new user.
        
        Args:
            email: User email address
            password_hash: Hashed password for authentication
            email_password: Encrypted email password for IMAP/SMTP (optional)
            
        Returns:
            User object if created successfully, None if email already exists
        """
        session = self.Session()
        try:
            user = User(email=email, password_hash=password_hash, email_password=email_password)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except IntegrityError:
            session.rollback()
            return None
        finally:
            session.close()
    
    def update_user_email_password(self, user_id: int, encrypted_password: str) -> bool:
        """
        Update user's encrypted email password.
        
        Args:
            user_id: User ID
            encrypted_password: Encrypted email password
            
        Returns:
            True if updated successfully, False otherwise
        """
        session = self.Session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.email_password = encrypted_password
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email address.
        
        Args:
            email: User email address
            
        Returns:
            User object if found, None otherwise
        """
        session = self.Session()
        try:
            user = session.query(User).filter(User.email == email).first()
            return user
        finally:
            session.close()

    def save_email(self, user_id: int, message_id: str, sender: str, 
                   subject: str, body: str, category: str, date: datetime) -> Optional[Email]:
        """
        Save email to database with duplicate message_id handling.
        
        Args:
            user_id: User ID
            message_id: Unique message identifier
            sender: Email sender address
            subject: Email subject
            body: Email body text
            category: Email category (Work, Personal, Spam, Promotions)
            date: Email date
            
        Returns:
            Email object if saved successfully, None if duplicate
        """
        session = self.Session()
        try:
            email = Email(
                user_id=user_id,
                message_id=message_id,
                sender=sender,
                subject=subject,
                body=body,
                category=category,
                date=date
            )
            session.add(email)
            session.commit()
            session.refresh(email)
            return email
        except IntegrityError:
            # Duplicate message_id for this user
            session.rollback()
            return None
        finally:
            session.close()
    
    def get_emails(self, user_id: int, category: Optional[str] = None, 
                   page: int = 1, page_size: int = 20) -> tuple[List[Email], int]:
        """
        Get paginated emails for a user with optional category filtering.
        
        Args:
            user_id: User ID
            category: Optional category filter
            page: Page number (1-indexed)
            page_size: Number of emails per page
            
        Returns:
            Tuple of (list of Email objects, total count)
        """
        session = self.Session()
        try:
            query = session.query(Email).filter(Email.user_id == user_id)
            
            # Apply category filter if provided
            if category:
                query = query.filter(Email.category == category)
            
            # Get total count
            total = query.count()
            
            # Apply pagination and ordering
            emails = query.order_by(Email.date.desc()).offset((page - 1) * page_size).limit(page_size).all()
            
            return emails, total
        finally:
            session.close()
    
    def search_emails(self, user_id: int, query: str) -> List[Email]:
        """
        Search emails by subject or sender with case-insensitive matching.
        
        Args:
            user_id: User ID
            query: Search query text
            
        Returns:
            List of matching Email objects
        """
        session = self.Session()
        try:
            # Case-insensitive search in subject and sender
            search_pattern = f"%{query}%"
            emails = session.query(Email).filter(
                Email.user_id == user_id,
                (Email.subject.ilike(search_pattern) | Email.sender.ilike(search_pattern))
            ).order_by(Email.date.desc()).all()
            
            return emails
        finally:
            session.close()
    
    def get_email_stats(self, user_id: int) -> dict:
        """
        Get email statistics by category for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with category counts
        """
        session = self.Session()
        try:
            from sqlalchemy import func
            
            # Query category counts
            results = session.query(
                Email.category,
                func.count(Email.id).label('count')
            ).filter(
                Email.user_id == user_id
            ).group_by(Email.category).all()
            
            # Convert to dictionary
            stats = {category: count for category, count in results}
            
            # Ensure all categories are present
            for category in ["Work", "Personal", "Spam", "Promotions"]:
                if category not in stats:
                    stats[category] = 0
            
            return stats
        finally:
            session.close()


def init_db(db_path: str = "./data/emails.db"):
    """
    Initialize database by creating all tables.
    
    Args:
        db_path: Path to SQLite database file
    """
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create engine
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    print(f"Database initialized at {db_path}")


if __name__ == "__main__":
    import sys
    
    # Command-line interface for database initialization
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        db_path = sys.argv[2] if len(sys.argv) > 2 else "./data/emails.db"
        init_db(db_path)
    else:
        print("Usage: python database.py --init [db_path]")
        print("Example: python database.py --init ./data/emails.db")
