"""
Esan ERP Configuration
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


SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "esan-development-key"
)


DEFAULT_CURRENCY = "UGX"


ROLES = [
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