# Local Email Manager

A privacy-first, offline-capable email management system that fetches emails via IMAP, classifies them using local NLP models, and provides a web interface for email interaction. All data stays on your machine.

## Features

- 🔒 **Privacy-First**: All data stored locally, no cloud services required
- 🤖 **Smart Classification**: Automatic email categorization (Work, Personal, Spam, Promotions)
- 🔍 **Fast Search**: Search emails by subject or sender
- 📧 **Send Emails**: Compose and send emails directly from the interface
- 🔄 **Auto-Sync**: Fetch latest emails from your Gmail account
- 👥 **Multi-User**: Support for multiple users with concurrent sync
- 🌐 **Web Interface**: Clean, responsive web UI

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9 or higher**
- **pip** (Python package manager)
- **Gmail Account** with App Password enabled

### Setting Up Gmail App Password

Since this application uses IMAP/SMTP to access Gmail, you need to create an App Password:

1. Go to your [Google Account Security Settings](https://myaccount.google.com/security)
2. Enable **2-Step Verification** (if not already enabled)
3. Go to **App Passwords** section
4. Select **Mail** and **Other (Custom name)**
5. Enter "Local Email Manager" as the name
6. Click **Generate**
7. Copy the 16-character password (you'll need this during setup)

**Note**: Never use your regular Gmail password with this application.

## Installation

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd local-email-manager
```

### 2. Create Virtual Environment (Recommended)

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (or set environment variables):

```bash
# Required: JWT Secret Key (generate a secure random string)
JWT_SECRET=your-secure-secret-key-at-least-32-characters-long

# Optional: Custom paths
DATABASE_PATH=./data/emails.db
MODEL_PATH=./models/classifier.pkl

# Optional: Server settings
SERVER_HOST=127.0.0.1
SERVER_PORT=8000

# Optional: IMAP/SMTP settings (defaults to Gmail)
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Optional: Performance settings
THREAD_POOL_SIZE=5
DEFAULT_FETCH_COUNT=50
```

### Generating a Secure JWT Secret

**On Windows (PowerShell):**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**On macOS/Linux:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and set it as your `JWT_SECRET`.

## Running the Application

### Quick Start (Development Mode)

The application comes with a default development configuration. To start immediately:

1. **Install dependencies** (if not already done):
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:

**On Windows:**
```bash
python run.py
```
or
```bash
run.bat
```

**On macOS/Linux:**
```bash
python3 run.py
```

The script will automatically:
- ✓ Validate configuration
- ✓ Create required directories
- ✓ Initialize the database
- ✓ Train the email classifier
- ✓ Start the web server

### Access the Application

Once the server starts, open your browser and navigate to:

```
http://localhost:8000
```

## Usage

### First Time Setup

1. **Register an Account**
   - Open the application in your browser
   - Click "Register" (or modify login.html to add registration)
   - Enter your Gmail address and App Password

2. **Login**
   - Enter your Gmail address
   - Enter your Gmail App Password
   - Click "Login"

3. **Sync Emails**
   - Click the "Sync" button in the navigation bar
   - Wait for emails to be fetched and classified
   - Your emails will appear in the inbox

### Managing Emails

- **View Emails**: Click on any email in the list to view full content
- **Filter by Category**: Use category buttons (Work, Personal, Spam, Promotions)
- **Search**: Type in the search box to find emails by subject or sender
- **Compose Email**: Click "Compose" to send a new email
- **Sync**: Click "Sync" to fetch latest emails from server

### Logging Out

Click the "Logout" button in the navigation bar to clear your session.

## Project Structure

```
local-email-manager/
├── backend/
│   ├── auth.py              # Authentication & JWT handling
│   ├── classifier.py        # NLP email classifier
│   ├── config.py            # Configuration management
│   ├── database.py          # Database models & operations
│   ├── imap_handler.py      # Email fetching via IMAP
│   ├── main.py              # FastAPI application
│   ├── smtp_handler.py      # Email sending via SMTP
│   ├── sync_orchestrator.py # Concurrent sync operations
│   └── training_data.py     # Classifier training data
├── frontend/
│   ├── api.js               # API client
│   ├── inbox.html           # Main inbox interface
│   ├── inbox.js             # Inbox logic
│   ├── login.html           # Login page
│   ├── login.js             # Login logic
│   ├── styles.css           # Custom styles
│   └── toast.js             # Toast notifications
├── data/
│   └── emails.db            # SQLite database (created on first run)
├── models/
│   └── classifier.pkl       # Trained ML model (created on first run)
├── run.py                   # Startup script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Troubleshooting

### Issue: "Authentication failed" when syncing

**Solution:**
- Verify you're using a Gmail App Password, not your regular password
- Ensure 2-Step Verification is enabled on your Google Account
- Check that the App Password was copied correctly (no spaces)

### Issue: "Database locked" error

**Solution:**
- Close any other instances of the application
- Delete `data/emails.db` and restart (this will clear all data)
- Reduce `THREAD_POOL_SIZE` in configuration

### Issue: "Module not found" errors

**Solution:**
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (must be 3.9+)

### Issue: Server won't start on port 8000

**Solution:**
- Check if another application is using port 8000
- Change the port: `set SERVER_PORT=8080` (Windows) or `export SERVER_PORT=8080` (macOS/Linux)
- Kill existing process: `netstat -ano | findstr :8000` (Windows) or `lsof -i :8000` (macOS/Linux)

### Issue: Emails not being classified correctly

**Solution:**
- Delete `models/classifier.pkl` and restart to retrain
- Add more training examples in `backend/training_data.py`
- Check that email content is being fetched properly

### Issue: "JWT_SECRET too short" error

**Solution:**
- Generate a new secret key (see Configuration section)
- Ensure the secret is at least 32 characters long
- Set it in your `.env` file or environment variables

## Security Considerations

- **Never commit** your `.env` file or JWT secret to version control
- **Use App Passwords** instead of your main Gmail password
- **Run locally only** - this application is designed for single-machine use
- **HTTPS**: For production, run behind a reverse proxy with SSL
- **Firewall**: Ensure the application is not exposed to the internet

## Performance Tips

- **Reduce fetch count**: Set `DEFAULT_FETCH_COUNT=20` for faster syncs
- **Adjust thread pool**: Increase `THREAD_POOL_SIZE` for faster multi-user sync
- **Database optimization**: The database is automatically indexed for performance
- **Regular cleanup**: Periodically delete old emails to keep database size manageable

## Development

### Running Tests

```bash
pytest test_auth.py test_database.py -v
```

### Adding Training Data

Edit `backend/training_data.py` to add more labeled examples for better classification:

```python
training_data.append(("Your email text here", "Work"))
```

Then delete `models/classifier.pkl` and restart to retrain.

## License

This project is provided as-is for personal use.

## Support

For issues, questions, or contributions, please refer to the project repository.

---

**Built with**: Python, FastAPI, SQLite, scikit-learn, Bootstrap
