# Implementation Plan

- [x] 1. Set up project structure and dependencies





  - Create backend directory with Python package structure
  - Create frontend directory for static files
  - Create data and models directories for storage
  - Write requirements.txt with all Python dependencies (fastapi, uvicorn, sqlalchemy, scikit-learn, pyjwt, bcrypt, email-validator)
  - Create .env.example file for environment variable template
  - _Requirements: 9.4, 9.5_

- [x] 2. Implement database layer with SQLAlchemy models












  - [x] 2.1 Create database.py with SQLAlchemy setup

    - Define Base declarative class
    - Configure SQLite engine with connection pooling for thread safety
    - Create session factory with scoped sessions
    - _Requirements: 4.1, 4.3, 8.5_


  - [x] 2.2 Implement User and Email SQLAlchemy models



    - Write User model with id, email, password_hash, created_at fields
    - Write Email model with id, user_id, message_id, sender, subject, body, category, date, created_at fields
    - Add relationship definitions between User and Email
    - Add UNIQUE constraint on (user_id, message_id)
    - _Requirements: 4.1, 4.2_


  - [x] 2.3 Create database indexes for query optimization

    - Add index on (user_id, category)
    - Add index on (user_id, date DESC)
    - Add index on (user_id, sender)

    - _Requirements: 4.3, 4.5_

  - [x] 2.4 Implement DatabaseManager class with CRUD operations

    - Write create_user method with duplicate email handling
    - Write get_user_by_email method
    - Write save_email method with duplicate message_id handling
    - Write get_emails method with pagination and category filtering
    - Write search_emails method with case-insensitive matching

    - Write get_email_stats method for category counts

  - [x] 2.5 Add database initialization script
    - Create init_db function to create all tables
    - Add command-line interface for database initialization
    - _Requirements: 4.1_

- [x] 3. Implement authentication module with JWT






  - [x] 3.1 Create auth.py with AuthManager class

    - Implement hash_password method using bcrypt
    - Implement verify_password method
    - Implement create_access_token method with 24-hour expiration
    - Implement verify_token method with signature and expiration validation
    - Load JWT secret from environment variable
    - _Requirements: 1.1, 1.2, 1.5_

  - [x] 3.2 Create JWT middleware for FastAPI

    - Write dependency function to extract and validate JWT from Authorization header
    - Return user information from validated token
    - Raise HTTPException for missing or invalid tokens
    - _Requirements: 1.4, 1.5_

- [x] 4. Implement IMAP handler for email fetching






  - [x] 4.1 Create imap_handler.py with IMAPHandler class

    - Implement __init__ to store credentials
    - Implement connect method to establish SSL connection to imap.gmail.com:993
    - Implement disconnect method to close connection
    - Add connection timeout of 30 seconds
    - _Requirements: 2.1, 2.5_

  - [x] 4.2 Implement email fetching logic

    - Write fetch_latest_emails method to retrieve latest 50 emails
    - Select INBOX folder
    - Search for all messages and get latest 50 UIDs
    - Fetch email data for each UID
    - _Requirements: 2.2_
  - [x] 4.3 Implement email parsing functionality


    - Write _parse_email method to extract sender, subject, date, body, message_id
    - Handle multipart emails to extract plain text body
    - Decode email headers properly
    - Handle parsing errors gracefully
    - _Requirements: 2.3_

  - [x] 4.4 Add error handling and logging

    - Wrap IMAP operations in try-except blocks
    - Log connection failures and return failure status
    - Ensure connection is closed even on errors
    - _Requirements: 2.4, 2.5_

- [x] 5. Implement SMTP handler for email sending






  - [x] 5.1 Create smtp_handler.py with SMTPHandler class

    - Implement __init__ to store credentials
    - Implement _create_message method to build MIMEText message
    - Set From, To, Subject headers properly
    - _Requirements: 7.3, 7.4_

  - [x] 5.2 Implement email sending with retry logic


    - Write send_email method to connect to smtp.gmail.com:587
    - Use STARTTLS for secure connection
    - Implement retry logic with max 3 attempts
    - Log all send attempts
    - Return success/failure status
    - _Requirements: 7.4, 7.5_

- [x] 6. Implement NLP classifier for email categorization






  - [x] 6.1 Create classifier.py with EmailClassifier class

    - Define CATEGORIES constant: ["Work", "Personal", "Spam", "Promotions"]
    - Implement __init__ to set model path
    - Create TfidfVectorizer with max_features=1000, stop_words='english', ngram_range=(1,2)
    - Create MultinomialNB classifier with alpha=0.1
    - Build sklearn Pipeline combining vectorizer and classifier
    - _Requirements: 3.2, 3.3, 3.4_

  - [x] 6.2 Create training dataset with labeled examples

    - Create training_data.py with 100+ labeled email examples
    - Include 25+ examples per category (Work, Personal, Spam, Promotions)
    - Format as list of tuples: (text, category)
    - _Requirements: 3.5_

  - [x] 6.3 Implement model training and persistence

    - Write train method to fit pipeline on training data
    - Write save_model method to pickle trained model
    - Write load_model method to unpickle model
    - Handle missing model file by training new model
    - _Requirements: 3.3, 3.5_

  - [x] 6.4 Implement classification method

    - Write classify method that combines subject and body
    - Use trained pipeline to predict category
    - Return one of the four categories
    - Handle classification errors gracefully
    - _Requirements: 3.1, 3.2, 3.4_
-

- [x] 7. Implement sync orchestrator for concurrent operations



  - [x] 7.1 Create sync_orchestrator.py with SyncOrchestrator class


    - Initialize ThreadPoolExecutor with max_workers=5
    - Define SyncResult dataclass for return values
    - _Requirements: 8.2, 8.3_
  - [x] 7.2 Implement single user sync workflow


    - Write sync_user_emails method
    - Create IMAPHandler instance with user credentials
    - Fetch emails using IMAP handler
    - Classify each email using NLP classifier
    - Save classified emails to database
    - Handle errors for individual emails without stopping sync
    - Return SyncResult with counts and errors
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 4.2, 8.4_
  - [x] 7.3 Implement concurrent multi-user sync


    - Write sync_multiple_users method
    - Submit sync tasks to thread pool executor
    - Collect results from all futures
    - Return list of SyncResults
    - _Requirements: 8.1, 8.2_

- [x] 8. Implement FastAPI backend with REST endpoints







  - [x] 8.1 Create main.py with FastAPI application setup

    - Initialize FastAPI app
    - Configure CORS for localhost origin
    - Add static file mounting for frontend
    - Initialize database manager, auth manager, classifier, sync orchestrator
    - Load environment variables

    - _Requirements: 9.5_

  - [x] 8.2 Implement authentication endpoints

    - Write POST /api/auth/register endpoint
    - Validate email format and password strength
    - Hash password and create user in database
    - Write POST /api/auth/login endpoint
    - Verify credentials against database
    - Generate and return JWT token
    - _Requirements: 1.1, 1.2_



  - [x] 8.3 Implement email listing and detail endpoints

    - Write GET /api/emails endpoint with JWT authentication
    - Support pagination with page and page_size query parameters
    - Support category filtering with category query parameter
    - Return email list with preview (first 100 chars of body)
    - Write GET /api/emails/{id} endpoint to return full email details
    - Verify email belongs to authenticated user

    - _Requirements: 5.1, 5.4, 5.5_



  - [x] 8.4 Implement email search endpoint

    - Write GET /api/emails/search endpoint with JWT authentication
    - Accept query parameter for search text
    - Call database search_emails method
    - Return matching emails filtered by user




    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [x] 8.5 Implement email sending endpoint

    - Write POST /api/emails/send endpoint with JWT authentication
    - Validate request body (to, subject, body fields)
    - Get user credentials from database
    - Create SMTP handler and send email


    - Return success or error response


    - _Requirements: 7.1, 7.2, 7.5_
  - [x] 8.6 Implement email sync endpoint

    - Write POST /api/emails/sync endpoint with JWT authentication
    - Get user credentials from database

    - Call sync orchestrator for current user

    - Return sync result with counts
    - _Requirements: 2.1, 2.2, 8.1, 8.4_
  - [x] 8.7 Implement statistics endpoint


    - Write GET /api/stats endpoint with JWT authentication


    - Call database get_email_stats method
    - Return category counts for user
    - _Requirements: 4.5_
  - [x] 8.8 Add global exception handlers

    - Create exception handler for authentication errors (401)
    - Create exception handler for validation errors (400)
    - Create exception handler for server errors (500)
    - Return consistent error JSON format
    - _Requirements: 1.4_

- [x] 9. Create frontend login page




  - [x] 9.1 Create login.html with Bootstrap layout


    - Add HTML structure with Bootstrap 5 CDN
    - Create login form with email and password fields
    - Add login button and error message container
    - Include link to register (future enhancement)
    - _Requirements: 1.1, 1.2_


  - [x] 9.2 Create login.js for authentication logic









    - Write login function to call POST /api/auth/login
    - Store JWT token in localStorage on success
    - Redirect to inbox.html on successful login
    - Display error message on failure
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 10. Create frontend inbox page





  - [x] 10.1 Create inbox.html with main UI structure

    - Add navigation bar with sync button and logout button
    - Create category filter buttons (All, Work, Personal, Spam, Promotions)
    - Add search input field
    - Create email list table with columns: sender, subject, category, date
    - Add pagination controls
    - Create email detail modal
    - Create compose email modal with recipient, subject, body fields
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 7.1_

  - [x] 10.2 Create api.js with APIClient class

    - Implement constructor to load token from localStorage
    - Write login method
    - Write getEmails method with pagination and category parameters
    - Write searchEmails method
    - Write sendEmail method
    - Write syncEmails method
    - Add Authorization header with Bearer token to all requests
    - Handle 401 errors by redirecting to login
    - _Requirements: 5.5_

  - [x] 10.3 Create inbox.js with InboxManager class

    - Implement loadEmails method to fetch and render email list
    - Implement handleCategoryFilter to filter by category
    - Implement handleSearch to search emails
    - Implement handleSync to trigger sync and show progress
    - Implement handleCompose to send email via modal
    - Implement renderEmailList to populate table
    - Implement renderEmailDetail to show email in modal
    - Add event listeners for all UI interactions
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 6.1, 6.5, 7.1_

  - [x] 10.4 Create styles.css for custom styling

    - Style category filter buttons with color coding
    - Style email list table for readability
    - Add loading spinner styles
    - Style modals for email detail and compose
    - Add responsive design for mobile devices
    - _Requirements: 5.1_

  - [x] 10.5 Implement toast notifications for user feedback

    - Create toast.js utility for showing notifications
    - Show success toast on email sent
    - Show success toast on sync completed
    - Show error toast on API failures
    - _Requirements: 7.5_

- [x] 11. Create application startup and configuration






  - [x] 11.1 Create config.py for centralized configuration

    - Define configuration class with environment variables
    - Set JWT_SECRET, DATABASE_PATH, MODEL_PATH
    - Set IMAP/SMTP server settings
    - Set thread pool size
    - _Requirements: 9.5_

  - [x] 11.2 Create startup script

    - Write run.py or run.sh to start application
    - Check for required environment variables
    - Initialize database if not exists
    - Train classifier if model not exists
    - Start uvicorn server on localhost:8000
    - _Requirements: 9.5_

  - [x] 11.3 Create README.md with setup instructions

    - Document prerequisites (Python 3.9+, Gmail app password)
    - Provide installation steps
    - Explain environment variable configuration
    - Include usage instructions
    - Add troubleshooting section
    - _Requirements: 9.1, 9.2_
