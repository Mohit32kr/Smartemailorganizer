"""
SMTP Handler for sending emails via Gmail SMTP server.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SMTPHandler:
    """Handles email sending via SMTP protocol."""
    
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    MAX_RETRIES = 3
    
    def __init__(self, email: str, password: str):
        """
        Initialize SMTP handler with user credentials.
        
        Args:
            email: User's email address
            password: User's app-specific password
        """
        self.email = email
        self.password = password
    
    def _create_message(self, to: str, subject: str, body: str) -> MIMEText:
        """
        Create a MIME message for email sending.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            body: Email body content
            
        Returns:
            MIMEText message object
        """
        message = MIMEText(body, 'plain')
        message['From'] = self.email
        message['To'] = to
        message['Subject'] = subject
        
        return message
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """
        Send email via SMTP with retry logic.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            body: Email body content
            
        Returns:
            True if email sent successfully, False otherwise
        """
        message = self._create_message(to, subject, body)
        
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.info(f"Attempt {attempt}/{self.MAX_RETRIES}: Sending email to {to}")
                
                # Connect to SMTP server
                with smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT, timeout=30) as server:
                    # Start TLS encryption
                    server.starttls()
                    
                    # Login with credentials
                    server.login(self.email, self.password)
                    
                    # Send email
                    server.send_message(message)
                    
                logger.info(f"Successfully sent email to {to}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"Authentication failed on attempt {attempt}: {e}")
                # Don't retry authentication errors
                return False
                
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error on attempt {attempt}: {e}")
                if attempt == self.MAX_RETRIES:
                    logger.error(f"Failed to send email after {self.MAX_RETRIES} attempts")
                    return False
                    
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                if attempt == self.MAX_RETRIES:
                    logger.error(f"Failed to send email after {self.MAX_RETRIES} attempts")
                    return False
        
        return False
