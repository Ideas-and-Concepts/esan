"""
Esan ERP Configuration
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System
Version 1.2.0 Alpha

Reads configuration from environment variables (or Streamlit secrets)
with sensible defaults for local development.
"""

import os

# -----------------------------
#  COMPANY DETAILS
# -----------------------------
COMPANY_NAME = os.getenv("COMPANY_NAME", "Nile Harvest Foods Ltd.")
COMPANY_SHORT = os.getenv("COMPANY_SHORT", "Nile Harvest")
COMPANY_ADDRESS = os.getenv("COMPANY_ADDRESS", "Kampala, Uganda")
COMPANY_PHONE = os.getenv("COMPANY_PHONE", "+256 700 000 000")
COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "info@nileharvest.com")
COMPANY_WEBSITE = os.getenv("COMPANY_WEBSITE", "https://nileharvest.com")

# -----------------------------
#  APP VERSION
# -----------------------------
VERSION = os.getenv("APP_VERSION", "1.2.0 Alpha")
APP_NAME = os.getenv("APP_NAME", "Esan ERP")
APP_ICON = os.getenv("APP_ICON", "🌾")

# -----------------------------
#  SECURITY
# -----------------------------
# Secret key for session encryption (change in production)
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")

# -----------------------------
#  DATABASE (informational – actual URL loaded from st.secrets)
# -----------------------------
# This is only a fallback placeholder. In production, DATABASE_URL should
# be set via Streamlit secrets or environment variable.
FALLBACK_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///esan_erp.db")

# -----------------------------
#  ERP DEFAULTS
# -----------------------------
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "UGX")
DEFAULT_UNIT = os.getenv("DEFAULT_UNIT", "Kg")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Africa/Kampala")
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
LOW_STOCK_THRESHOLD = float(os.getenv("LOW_STOCK_THRESHOLD", "100.0"))

# -----------------------------
#  DATE & TIME FORMATS
# -----------------------------
DATE_FORMAT = os.getenv("DATE_FORMAT", "%Y-%m-%d")
DATETIME_FORMAT = os.getenv("DATETIME_FORMAT", "%Y-%m-%d %H:%M:%S")
TIMEZONE = os.getenv("TIMEZONE", "Africa/Kampala")

# -----------------------------
#  FEATURE FLAGS
# -----------------------------
ENABLE_AI_ASSISTANT = os.getenv("ENABLE_AI_ASSISTANT", "true").lower() in ("true", "1", "yes")
ENABLE_NOTIFICATIONS = os.getenv("ENABLE_NOTIFICATIONS", "false").lower() in ("true", "1", "yes")
ENABLE_API = os.getenv("ENABLE_API", "false").lower() in ("true", "1", "yes")

# -----------------------------
#  EMAIL SETTINGS (for future use)
# -----------------------------
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@nileharvest.com")