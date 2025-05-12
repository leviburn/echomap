#!/usr/bin/env python3
"""
Production server launcher for EchoMap

This script initializes and runs the EchoMap application in a production environment
using Gunicorn WSGI server.

Usage:
    python run.py
"""

import os
import sys
import logging
from dotenv import load_dotenv
import gunicorn.app.base

# Ensure the application directory is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("echomap")

# Import the Flask application
try:
    from app import app as flask_app
except ImportError as e:
    logger.critical(f"Failed to import Flask application: {e}")
    sys.exit(1)

# Check for essential environment variables
required_vars = ["OPENAI_API_KEY", "SECRET_KEY"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.critical(f"Missing required environment variables: {', '.join(missing_vars)}")
    logger.info("Run generate_secrets.py to create a secure SECRET_KEY")
    sys.exit(1)

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    """Standalone Gunicorn application for serving the Flask app."""
    
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

if __name__ == "__main__":
    # Get configuration from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "2"))
    threads = int(os.getenv("THREADS", "4"))
    
    # Log startup information
    logger.info(f"Starting EchoMap production server on {host}:{port}")
    
    # Configuration for Gunicorn
    options = {
        "bind": f"{host}:{port}",
        "workers": workers,
        "threads": threads,
        "worker_class": "sync",
        "timeout": 120,
        "accesslog": "-",
        "errorlog": "-",
        "loglevel": log_level.lower(),
        "preload_app": True,
    }
    
    # Run the application with Gunicorn
    StandaloneApplication(flask_app, options).run()