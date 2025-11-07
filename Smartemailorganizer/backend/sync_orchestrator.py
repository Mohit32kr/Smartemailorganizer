"""
Sync Orchestrator for concurrent email synchronization operations.
"""
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from typing import List, Optional
import logging

from database import DatabaseManager, User
from imap_handler import IMAPHandler, EmailData
from classifier import EmailClassifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a sync operation for a user."""
    user_email: str
    success: bool
    fetched_count: int = 0
    classified_count: int = 0
    saved_count: int = 0
    errors: List[str] = field(default_factory=list)
    
    def __repr__(self):
        return (f"SyncResult(user={self.user_email}, success={self.success}, "
                f"fetched={self.fetched_count}, saved={self.saved_count}, "
                f"errors={len(self.errors)})")


class SyncOrchestrator:
    """Orchestrates concurrent email synchronization for multiple users."""
    
    def __init__(self, db_manager: DatabaseManager, classifier: EmailClassifier, 
                 max_workers: int = 5):
        """
        Initialize the SyncOrchestrator.
        
        Args:
            db_manager: DatabaseManager instance for database operations
            classifier: EmailClassifier instance for email categorization
            max_workers: Maximum number of concurrent sync threads (default: 5)
        """
        self.db_manager = db_manager
        self.classifier = classifier
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        logger.info(f"SyncOrchestrator initialized with max_workers={max_workers}")

    def sync_user_emails(self, user: User, email_password: str, count: int = 50) -> SyncResult:
        """
        Sync emails for a single user.
        
        This method:
        1. Creates an IMAP handler with user credentials
        2. Fetches emails from the mail server
        3. Classifies each email using the NLP classifier
        4. Saves classified emails to the database
        5. Handles errors for individual emails without stopping the sync
        
        Args:
            user: User object containing user information
            email_password: User's email password (app-specific password)
            count: Number of emails to fetch (default: 50)
            
        Returns:
            SyncResult: Result of the sync operation with counts and errors
        """
        result = SyncResult(user_email=user.email, success=False)
        
        try:
            logger.info(f"Starting sync for user: {user.email}")
            
            # Create IMAP handler instance with user credentials
            imap_handler = IMAPHandler(user.email, email_password)
            
            # Connect to IMAP server
            if not imap_handler.connect():
                error_msg = "Failed to connect to IMAP server"
                logger.error(f"{error_msg} for user {user.email}")
                result.errors.append(error_msg)
                return result
            
            try:
                # Fetch emails using IMAP handler
                emails = imap_handler.fetch_latest_emails(count)
                result.fetched_count = len(emails)
                logger.info(f"Fetched {result.fetched_count} emails for {user.email}")
                
                # Process each email
                for email_data in emails:
                    try:
                        # Classify email using NLP classifier
                        category = self.classifier.classify(email_data.subject, email_data.body)
                        result.classified_count += 1
                        
                        # Save classified email to database
                        saved_email = self.db_manager.save_email(
                            user_id=user.id,
                            message_id=email_data.message_id,
                            sender=email_data.sender,
                            subject=email_data.subject,
                            body=email_data.body,
                            category=category,
                            date=email_data.date
                        )
                        
                        if saved_email:
                            result.saved_count += 1
                        # If saved_email is None, it's a duplicate - not an error
                        
                    except Exception as e:
                        # Handle errors for individual emails without stopping sync
                        error_msg = f"Error processing email '{email_data.subject}': {str(e)}"
                        logger.error(error_msg)
                        result.errors.append(error_msg)
                        continue
                
                # Mark as successful if we processed emails
                result.success = True
                logger.info(f"Sync completed for {user.email}: "
                          f"fetched={result.fetched_count}, "
                          f"classified={result.classified_count}, "
                          f"saved={result.saved_count}, "
                          f"errors={len(result.errors)}")
                
            finally:
                # Ensure IMAP connection is closed
                imap_handler.disconnect()
                
        except Exception as e:
            error_msg = f"Sync failed for user {user.email}: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.success = False
        
        return result

    def sync_multiple_users(self, user_credentials: List[tuple[User, str]], 
                           count: int = 50) -> List[SyncResult]:
        """
        Sync emails for multiple users concurrently.
        
        This method:
        1. Submits sync tasks to the thread pool executor
        2. Collects results from all futures
        3. Returns a list of SyncResults
        
        Args:
            user_credentials: List of tuples (User, email_password)
            count: Number of emails to fetch per user (default: 50)
            
        Returns:
            List[SyncResult]: List of sync results for all users
        """
        logger.info(f"Starting concurrent sync for {len(user_credentials)} users")
        
        # Submit sync tasks to thread pool executor
        futures: List[Future] = []
        for user, password in user_credentials:
            future = self.executor.submit(self.sync_user_emails, user, password, count)
            futures.append(future)
        
        # Collect results from all futures
        results: List[SyncResult] = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
                logger.info(f"Completed sync for user: {result.user_email}")
            except Exception as e:
                logger.error(f"Error in concurrent sync task: {e}")
                # Create error result for failed task
                error_result = SyncResult(
                    user_email="unknown",
                    success=False,
                    errors=[f"Task execution failed: {str(e)}"]
                )
                results.append(error_result)
        
        logger.info(f"Concurrent sync completed for {len(results)} users")
        return results
    
    def shutdown(self, wait: bool = True):
        """
        Shutdown the thread pool executor.
        
        Args:
            wait: If True, wait for all pending tasks to complete
        """
        logger.info("Shutting down SyncOrchestrator")
        self.executor.shutdown(wait=wait)


# Example usage
if __name__ == "__main__":
    """Example usage of SyncOrchestrator."""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python sync_orchestrator.py <email> <password>")
        sys.exit(1)
    
    email_address = sys.argv[1]
    password = sys.argv[2]
    
    # Initialize components
    db_manager = DatabaseManager()
    classifier = EmailClassifier()
    
    # Ensure classifier is trained
    if not classifier.is_trained:
        print("Classifier not trained. Please train it first.")
        sys.exit(1)
    
    # Create or get user
    user = db_manager.get_user_by_email(email_address)
    if not user:
        print(f"User {email_address} not found in database")
        sys.exit(1)
    
    # Create orchestrator
    orchestrator = SyncOrchestrator(db_manager, classifier)
    
    try:
        # Sync single user
        print(f"Syncing emails for {email_address}...")
        result = orchestrator.sync_user_emails(user, password)
        
        print(f"\nSync Result:")
        print(f"  Success: {result.success}")
        print(f"  Fetched: {result.fetched_count}")
        print(f"  Classified: {result.classified_count}")
        print(f"  Saved: {result.saved_count}")
        print(f"  Errors: {len(result.errors)}")
        
        if result.errors:
            print("\nErrors:")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
    
    finally:
        orchestrator.shutdown()
