#!/usr/bin/env python3
"""
Startup script for Email Management System.
Handles initialization and starts the FastAPI server.
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.config import config
from backend.database import DatabaseManager, init_db
from backend.classifier import EmailClassifier
from backend.training_data import get_training_data


def check_environment():
    """Check for required environment variables and configuration."""
    print("Checking environment configuration...")
    
    errors = config.validate()
    
    for error in errors:
        if error.startswith("ERROR"):
            print(f"❌ {error}")
            return False
        else:
            print(f"⚠️  {error}")
    
    print("✓ Environment configuration valid")
    return True


def initialize_directories():
    """Create required directories if they don't exist."""
    print("Initializing directories...")
    config.ensure_directories()
    print(f"✓ Data directory: {config.DATA_DIR}")
    print(f"✓ Models directory: {config.MODELS_DIR}")


def initialize_database():
    """Initialize database if it doesn't exist."""
    db_path = Path(config.DATABASE_PATH)
    
    if db_path.exists():
        print(f"✓ Database already exists at {config.DATABASE_PATH}")
        return True
    
    print(f"Creating database at {config.DATABASE_PATH}...")
    try:
        init_db()
        print("✓ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False


def initialize_classifier():
    """Train classifier if model doesn't exist."""
    model_path = Path(config.MODEL_PATH)
    
    if model_path.exists():
        print(f"✓ Classifier model already exists at {config.MODEL_PATH}")
        return True
    
    print(f"Training classifier model...")
    try:
        classifier = EmailClassifier(config.MODEL_PATH)
        training_data = get_training_data()
        
        print(f"  Training with {len(training_data)} examples...")
        classifier.train(training_data)
        classifier.save_model()
        
        print(f"✓ Classifier trained and saved to {config.MODEL_PATH}")
        return True
    except Exception as e:
        print(f"❌ Failed to train classifier: {e}")
        return False


def start_server():
    """Start the FastAPI server using uvicorn."""
    print("\n" + "=" * 60)
    print("Starting Email Management System Server")
    print("=" * 60)
    config.display()
    print("\n🚀 Server starting...")
    print(f"   Access the application at: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    print("   Press CTRL+C to stop the server\n")
    
    try:
        import uvicorn
        uvicorn.run(
            "backend.main:app",
            host=config.SERVER_HOST,
            port=config.SERVER_PORT,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return False
    
    return True


def main():
    """Main startup routine."""
    print("\n" + "=" * 60)
    print("Email Management System - Startup")
    print("=" * 60 + "\n")
    
    # Step 1: Check environment
    if not check_environment():
        print("\n❌ Startup failed: Environment configuration errors")
        sys.exit(1)
    
    # Step 2: Initialize directories
    initialize_directories()
    
    # Step 3: Initialize database
    if not initialize_database():
        print("\n❌ Startup failed: Database initialization error")
        sys.exit(1)
    
    # Step 4: Initialize classifier
    if not initialize_classifier():
        print("\n❌ Startup failed: Classifier initialization error")
        sys.exit(1)
    
    print("\n✓ All initialization complete")
    
    # Step 5: Start server
    start_server()


if __name__ == "__main__":
    main()
