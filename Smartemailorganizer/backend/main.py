"""
FastAPI backend for Local Email Manager.
Provides REST API endpoints for email management with JWT authentication.
"""
import os
from typing import Optional, List
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, validator
from dotenv import load_dotenv

from database import DatabaseManager, User, Email
from auth import AuthManager, get_current_user, set_auth_manager
from classifier import EmailClassifier
from sync_orchestrator import SyncOrchestrator
from smtp_handler import SMTPHandler
from config import config

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Local Email Manager",
    description="Privacy-first email management system with local NLP classification",
    version="1.0.0"
)

# Configure CORS using config
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components using config
db_manager = DatabaseManager(config.DATABASE_PATH)
auth_manager = AuthManager(secret_key=config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
classifier = EmailClassifier(config.MODEL_PATH)
sync_orchestrator = SyncOrchestrator(db_manager, classifier, max_workers=config.THREAD_POOL_SIZE)

# Set global auth manager for dependency injection
set_auth_manager(auth_manager)

# Ensure classifier is trained
if not classifier.is_trained:
    try:
        classifier.load_model()
    except Exception as e:
        print(f"Warning: Classifier not trained. Please train it first: {e}")


# ============================================================================
# Request/Response Models
# ============================================================================

class RegisterRequest(BaseModel):
    """Request model for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Validate password (accepts Gmail app passwords)."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        # Removed digit requirement to support Gmail app passwords (16 lowercase letters)
        return v


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Response model for successful login."""
    access_token: str
    token_type: str = "bearer"


class EmailPreview(BaseModel):
    """Email preview model for list view."""
    id: int
    sender: str
    subject: str
    category: str
    date: str
    preview: str


class EmailDetail(BaseModel):
    """Full email detail model."""
    id: int
    sender: str
    subject: str
    body: str
    category: str
    date: str


class EmailListResponse(BaseModel):
    """Response model for email list."""
    emails: List[EmailPreview]
    total: int
    page: int
    page_size: int


class SendEmailRequest(BaseModel):
    """Request model for sending email."""
    to: EmailStr
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class SyncResponse(BaseModel):
    """Response model for sync operation."""
    status: str
    fetched: int
    classified: int
    saved: int
    errors: List[str]


class StatsResponse(BaseModel):
    """Response model for email statistics."""
    Work: int
    Personal: int
    Spam: int
    Promotions: int


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    message: str
    details: Optional[dict] = None


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with consistent error format."""
    error_code = "authentication_error" if exc.status_code == 401 else \
                 "validation_error" if exc.status_code == 400 else \
                 "server_error"
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error_code,
            "message": exc.detail,
            "details": {}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions with consistent error format."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "server_error",
            "message": "An unexpected error occurred",
            "details": {"exception": str(exc)}
        }
    )


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user.
    
    Validates email format and password strength, hashes password,
    and creates user in database. Also stores encrypted email password for IMAP/SMTP.
    """
    from encryption import encryption_manager
    
    # Check if user already exists
    existing_user = db_manager.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )
    
    # Hash password for authentication
    password_hash = auth_manager.hash_password(request.password)
    
    # Encrypt email password for IMAP/SMTP access
    encrypted_email_password = encryption_manager.encrypt(request.password)
    
    # Create user in database with both passwords
    user = db_manager.create_user(request.email, password_hash, encrypted_email_password)
    if not user:
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )
    
    # Generate JWT token
    access_token = auth_manager.create_access_token(
        user_id=user.id,
        email=user.email,
        expires_delta=timedelta(hours=24)
    )
    
    return LoginResponse(access_token=access_token)


@app.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    Verifies credentials against database and generates JWT token.
    """
    # Get user by email
    user = db_manager.get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not auth_manager.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    # Generate JWT token
    access_token = auth_manager.create_access_token(
        user_id=user.id,
        email=user.email,
        expires_delta=timedelta(hours=24)
    )
    
    return LoginResponse(access_token=access_token)


# ============================================================================
# Email Endpoints
# ============================================================================

@app.get("/api/emails", response_model=EmailListResponse)
async def get_emails(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated list of emails with optional category filtering.
    
    Requires JWT authentication. Returns email list with preview.
    """
    user_id = current_user["user_id"]
    
    # Validate category if provided
    if category and category not in classifier.CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(classifier.CATEGORIES)}"
        )
    
    # Get emails from database
    emails, total = db_manager.get_emails(user_id, category, page, page_size)
    
    # Convert to response model
    email_previews = [
        EmailPreview(
            id=email.id,
            sender=email.sender,
            subject=email.subject,
            category=email.category,
            date=email.date.isoformat(),
            preview=email.body[:100] + "..." if len(email.body) > 100 else email.body
        )
        for email in emails
    ]
    
    return EmailListResponse(
        emails=email_previews,
        total=total,
        page=page,
        page_size=page_size
    )


@app.get("/api/emails/{email_id}", response_model=EmailDetail)
async def get_email_detail(
    email_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get full details of a specific email.
    
    Requires JWT authentication. Verifies email belongs to authenticated user.
    """
    user_id = current_user["user_id"]
    
    # Get email from database
    session = db_manager.Session()
    try:
        email = session.query(Email).filter(
            Email.id == email_id,
            Email.user_id == user_id
        ).first()
        
        if not email:
            raise HTTPException(
                status_code=404,
                detail="Email not found"
            )
        
        return EmailDetail(
            id=email.id,
            sender=email.sender,
            subject=email.subject,
            body=email.body,
            category=email.category,
            date=email.date.isoformat()
        )
    finally:
        session.close()


@app.get("/api/emails/search", response_model=List[EmailPreview])
async def search_emails(
    query: str = Query(..., min_length=1),
    current_user: dict = Depends(get_current_user)
):
    """
    Search emails by subject or sender.
    
    Requires JWT authentication. Performs case-insensitive search.
    """
    user_id = current_user["user_id"]
    
    # Search emails in database
    emails = db_manager.search_emails(user_id, query)
    
    # Convert to response model
    email_previews = [
        EmailPreview(
            id=email.id,
            sender=email.sender,
            subject=email.subject,
            category=email.category,
            date=email.date.isoformat(),
            preview=email.body[:100] + "..." if len(email.body) > 100 else email.body
        )
        for email in emails
    ]
    
    return email_previews


@app.post("/api/emails/send")
async def send_email(
    request: SendEmailRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send an email via SMTP.
    
    Requires JWT authentication. Uses user's credentials to send email.
    """
    from encryption import encryption_manager
    
    user_id = current_user["user_id"]
    user_email = current_user["sub"]
    
    # Get user from database
    user = db_manager.get_user_by_email(user_email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Check if user has email password stored
    if not user.email_password:
        raise HTTPException(
            status_code=400,
            detail="Email password not configured. Please update your account settings."
        )
    
    # Decrypt email password
    try:
        email_password = encryption_manager.decrypt(user.email_password)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to decrypt email password: {str(e)}"
        )
    
    # Send email via SMTP
    try:
        smtp_handler = SMTPHandler(user_email, email_password)
        success = smtp_handler.send_email(request.to, request.subject, request.body)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to send email"
            )
        
        return {"status": "success", "message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )


@app.post("/api/emails/sync", response_model=SyncResponse)
async def sync_emails(
    current_user: dict = Depends(get_current_user)
):
    """
    Trigger email synchronization for the authenticated user.
    
    Requires JWT authentication. Fetches latest emails from IMAP server,
    classifies them, and saves to database.
    """
    from encryption import encryption_manager
    
    user_id = current_user["user_id"]
    user_email = current_user["sub"]
    
    # Get user from database
    user = db_manager.get_user_by_email(user_email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Check if user has email password stored
    if not user.email_password:
        raise HTTPException(
            status_code=400,
            detail="Email password not configured. Please update your account settings."
        )
    
    # Decrypt email password
    try:
        email_password = encryption_manager.decrypt(user.email_password)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to decrypt email password: {str(e)}"
        )
    
    # Sync emails
    try:
        result = sync_orchestrator.sync_user_emails(user, email_password)
        
        return SyncResponse(
            status="success" if result.success else "failed",
            fetched=result.fetched_count,
            classified=result.classified_count,
            saved=result.saved_count,
            errors=result.errors
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get email statistics by category for the authenticated user.
    
    Requires JWT authentication. Returns count of emails in each category.
    """
    user_id = current_user["user_id"]
    
    # Get statistics from database
    stats = db_manager.get_email_stats(user_id)
    
    return StatsResponse(**stats)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "classifier_trained": classifier.is_trained
    }


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("Starting Local Email Manager API...")
    print(f"Database: {config.DATABASE_PATH}")
    print(f"Model: {config.MODEL_PATH}")
    print(f"Classifier trained: {classifier.is_trained}")
    print(f"Server: {config.SERVER_HOST}:{config.SERVER_PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    print("Shutting down Local Email Manager API...")
    sync_orchestrator.shutdown()


# ============================================================================
# Static Files - Mount AFTER all API routes
# ============================================================================

# Mount static files for frontend (if frontend directory exists)
# This must be done AFTER all API routes are defined
# Note: API routes are at /api/* so they won't conflict with static files at root
from fastapi.responses import FileResponse

@app.get("/")
async def serve_root():
    """Serve the index.html file."""
    return FileResponse("frontend/index.html")

# Mount static files for other frontend assets
if os.path.exists("./frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
    
    # Serve HTML files directly
    @app.get("/{file_path:path}")
    async def serve_frontend(file_path: str):
        """Serve frontend files, defaulting to index.html for unknown routes."""
        # Don't serve API routes
        if file_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        
        # Try to serve the requested file
        file_location = f"frontend/{file_path}"
        if os.path.exists(file_location) and os.path.isfile(file_location):
            return FileResponse(file_location)
        
        # Default to index.html for SPA routing
        return FileResponse("frontend/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
