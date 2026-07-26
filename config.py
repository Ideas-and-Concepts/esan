"""
Esan ERP Configuration
Nile Harvest Foods Ltd.
"""

import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Esan ERP"
COMPANY_NAME = "Nile Harvest Foods Ltd."
VERSION = "1.0.0 Alpha"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///esan.db"
)
)

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key"
)

DEFAULT_CURRENCY = "UGX"

SUPPORTED_CURRENCIES = [
    "UGX",
    "USD",
    "SSP"
]

ROLE_LIST = [
    "Administrator",
    "Managing Director",
    "Plant Manager",
    "Procurement Officer",
    "Warehouse Officer",
    "Finance Officer",
    "Sales Officer",
    "Quality Officer",
    "Investor"
]
