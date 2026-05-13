"""Configuration for the HR system.

All settings can be overridden via environment variables.
Copy .env.example to .env and edit it for local development.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Secret key for Flask sessions and CSRF
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# Database
DATABASE_PATH = os.path.join(BASE_DIR, "data", "hr.db")

# Upload settings
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "cvs")
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_CV_EXTENSIONS = {"pdf", "doc", "docx"}
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "doc", "docx"}

# Admin credentials - use password hash, not plain text
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get(
    "ADMIN_PASSWORD_HASH",
    "scrypt:32768:8:1$Wm4rfla1kNuNb64D$2b8c31144ea7891af9948c9d12404298e60e7da9cb8de7dda62f392e913e1941c22cdc0a37a4aa63d7a9074e2aec8875857731e17e52e2ecf073761576d1047f"
)

# Session settings
PERMANENT_SESSION_LIFETIME = int(os.environ.get("PERMANENT_SESSION_LIFETIME", 3600))  # 1 hour
SESSION_TIMEOUT = int(os.environ.get("SESSION_TIMEOUT", 1800))  # 30 minutes

# Mail settings (optional)
MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")

# Webhook settings
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "your-webhook-secret-key-change-in-production")
WEBHOOK_ENABLED = os.environ.get("WEBHOOK_ENABLED", "False").lower() in ("true", "1", "yes")
