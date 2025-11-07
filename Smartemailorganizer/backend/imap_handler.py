"""
IMAP Handler for fetching emails from Gmail
"""
import imaplib
import email
from email.header import decode_header
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EmailData:
    """Structure for parsed email data"""
    sender: str
    subject: str
    body: str
    date: datetime
    message_id: str


class IMAPHandler:
    """Handles IMAP connection and email fetching from Gmail"""
    
    def __init__(self, email: str, password: str):
        """
        Initialize IMAP handler with user credentials
        
        Args:
            email: User's email address
            password: User's app-specific password
        """
        self.email = email
        self.password = password
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.imap_server = "imap.gmail.com"
        self.imap_port = 993
        self.timeout = 30
    
    def connect(self) -> bool:
        """
        Establish SSL connection to Gmail IMAP server
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to {self.imap_server}:{self.imap_port}")
            self.connection = imaplib.IMAP4_SSL(
                self.imap_server,
                self.imap_port,
                timeout=self.timeout
            )
            
            # Login with credentials
            self.connection.login(self.email, self.password)
            logger.info(f"Successfully connected as {self.email}")
            return True
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close IMAP connection"""
        if self.connection:
            try:
                self.connection.logout()
                logger.info("IMAP connection closed")
            except Exception as e:
                logger.error(f"Error closing IMAP connection: {e}")
            finally:
                self.connection = None

    def fetch_latest_emails(self, count: int = 50) -> List[EmailData]:
        """
        Fetch latest N emails from inbox
        
        Args:
            count: Number of emails to fetch (default: 50)
            
        Returns:
            List[EmailData]: List of parsed email data
        """
        emails = []
        
        try:
            # Check if connection exists
            if not self.connection:
                logger.error("No active IMAP connection")
                return emails
            
            # Select INBOX folder
            status, messages = self.connection.select("INBOX")
            if status != "OK":
                logger.error("Failed to select INBOX")
                return emails
            
            # Search for all messages
            status, message_ids = self.connection.search(None, "ALL")
            if status != "OK":
                logger.error("Failed to search messages")
                return emails
            
            # Get list of message IDs
            id_list = message_ids[0].split()
            
            # Get latest N UIDs (from the end of the list)
            latest_ids = id_list[-count:] if len(id_list) > count else id_list
            
            logger.info(f"Fetching {len(latest_ids)} emails")
            
            # Fetch email data for each UID
            for msg_id in latest_ids:
                try:
                    status, msg_data = self.connection.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        logger.warning(f"Failed to fetch message {msg_id}")
                        continue
                    
                    # Parse the raw email
                    raw_email = msg_data[0][1]
                    email_data = self._parse_email(raw_email)
                    
                    if email_data:
                        emails.append(email_data)
                        
                except Exception as e:
                    logger.error(f"Error fetching message {msg_id}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(emails)} emails")
            return emails
            
        except Exception as e:
            logger.error(f"Error in fetch_latest_emails: {e}")
            return emails

    def _parse_email(self, raw_email: bytes) -> Optional[EmailData]:
        """
        Parse raw email into structured data
        
        Args:
            raw_email: Raw email bytes from IMAP
            
        Returns:
            EmailData: Parsed email data or None if parsing fails
        """
        try:
            # Parse email message
            msg = email.message_from_bytes(raw_email)
            
            # Extract and decode subject
            subject = self._decode_header(msg.get("Subject", ""))
            
            # Extract sender
            sender = self._decode_header(msg.get("From", ""))
            
            # Extract message ID
            message_id = msg.get("Message-ID", "")
            
            # Extract date
            date_str = msg.get("Date", "")
            date = self._parse_date(date_str)
            
            # Extract body
            body = self._extract_body(msg)
            
            return EmailData(
                sender=sender,
                subject=subject,
                body=body,
                date=date,
                message_id=message_id
            )
            
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """
        Decode email header properly
        
        Args:
            header: Raw header string
            
        Returns:
            str: Decoded header string
        """
        if not header:
            return ""
        
        try:
            decoded_parts = decode_header(header)
            decoded_string = ""
            
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    # Decode bytes to string
                    if encoding:
                        decoded_string += part.decode(encoding, errors='ignore')
                    else:
                        decoded_string += part.decode('utf-8', errors='ignore')
                else:
                    decoded_string += str(part)
            
            return decoded_string
            
        except Exception as e:
            logger.error(f"Error decoding header: {e}")
            return str(header)
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse email date string to datetime
        
        Args:
            date_str: Date string from email header
            
        Returns:
            datetime: Parsed datetime or current time if parsing fails
        """
        try:
            # Parse email date format
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {e}")
            return datetime.utcnow()
    
    def _extract_body(self, msg) -> str:
        """
        Extract plain text body from email message
        Handle multipart emails to extract plain text body
        
        Args:
            msg: Email message object
            
        Returns:
            str: Plain text body
        """
        body = ""
        
        try:
            if msg.is_multipart():
                # Handle multipart emails
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    
                    # Look for plain text parts that are not attachments
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                charset = part.get_content_charset() or 'utf-8'
                                body = payload.decode(charset, errors='ignore')
                                break
                        except Exception as e:
                            logger.error(f"Error decoding multipart body: {e}")
                            continue
            else:
                # Handle simple emails
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='ignore')
            
            return body.strip()
            
        except Exception as e:
            logger.error(f"Error extracting body: {e}")
            return ""

    def __enter__(self):
        """Context manager entry - establish connection"""
        if not self.connect():
            raise ConnectionError("Failed to establish IMAP connection")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed"""
        self.disconnect()
        return False
    
    def fetch_emails_safe(self, count: int = 50) -> tuple[List[EmailData], bool]:
        """
        Safely fetch emails with automatic connection management
        
        Args:
            count: Number of emails to fetch (default: 50)
            
        Returns:
            tuple: (List of EmailData, success status)
        """
        try:
            # Connect
            if not self.connect():
                logger.error("Failed to connect to IMAP server")
                return [], False
            
            # Fetch emails
            emails = self.fetch_latest_emails(count)
            
            # Disconnect
            self.disconnect()
            
            return emails, True
            
        except Exception as e:
            logger.error(f"Error in fetch_emails_safe: {e}")
            # Ensure connection is closed even on error
            self.disconnect()
            return [], False


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python imap_handler.py <email> <password>")
        sys.exit(1)
    
    email_address = sys.argv[1]
    password = sys.argv[2]
    
    # Using context manager
    try:
        with IMAPHandler(email_address, password) as handler:
            emails = handler.fetch_latest_emails(10)
            print(f"Fetched {len(emails)} emails")
            for email_data in emails[:3]:  # Print first 3
                print(f"\nFrom: {email_data.sender}")
                print(f"Subject: {email_data.subject}")
                print(f"Date: {email_data.date}")
                print(f"Body preview: {email_data.body[:100]}...")
    except Exception as e:
        print(f"Error: {e}")
