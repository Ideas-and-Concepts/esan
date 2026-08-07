"""
Esan ERP Controller
Nile Harvest Foods Ltd.
Enterprise Milling & Packaging Management System

Version 1.3.0 Alpha
"""

import streamlit as st
import os
import logging
from datetime import datetime
from sqlalchemy import inspect

from config import COMPANY_NAME, VERSION
from database import Base, engine, SessionLocal, DATABASE_URL
from models import User
from auth import verify_password


# ==================================================
# LOGGING
# ==================================================

logging.basicConfig(
    filename="esan_erp.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Esan ERP",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# CLEAN UI
# ==================================================

st.markdown(
    """
    <style>

    #MainMenu {
        display:none;
    }

    footer {
        display:none;
    }

    header {
        display:none;
    }

    .block-container {
        padding-top:2rem;
        padding-bottom:1rem;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ==================================================
# SAFE MODULE IMPORT SYSTEM
# ==================================================

module_errors = []


def safe_import(module_path, function_name):

    try:

        module = __import__(
            module_path,
            fromlist=[function_name]
        )

        if hasattr(module, function_name):

            return getattr(
                module,
                function_name
            )

        module_errors.append(
            f"{module_path}: Missing {function_name}"
        )

        return None


    except Exception as e:

        module_errors.append(
            f"{module_path}: {str(e)}"
        )

        logging.error(
            f"{module_path} failed: {e}"
        )

        return None



# ==================================================
# ADMIN CREATION
# ==================================================

try:

    from services.user_service import create_admin


except ImportError:


    def create_admin(db):

        admin = (
            db.query(User)
            .filter(
                User.username=="admin"
            )
            .first()
        )


        if not admin:

            from auth import hash_password


            admin = User(

                username="admin",

                password_hash=
                hash_password(
                    "admin123"
                ),

                role="Administrator",

                full_name=
                "System Administrator",

                email=
                "admin@nileharvest.com"

            )


            db.add(admin)

            db.commit()



# ==================================================
# SEED DATA
# ==================================================

try:

    from seed.seed_data import load_seed_data


except ImportError:

    load_seed_data = None



# ==================================================
# MODULE REGISTRY
# ==================================================

dashboard_home = safe_import(
    "modules.dashboard.home",
    "dashboard_home"
)


procurement_dashboard = safe_import(
    "modules.procurement.dashboard",
    "procurement_dashboard"
)


warehouse_dashboard = safe_import(
    "modules.warehouse.dashboard",
    "warehouse_dashboard"
)


milling_dashboard = safe_import(
    "modules.milling.dashboard",
    "milling_dashboard"
)


packaging_dashboard = safe_import(
    "modules.packaging.dashboard",
    "packaging_dashboard"
)


sales_dashboard = safe_import(
    "modules.sales.dashboard",
    "sales_dashboard"
)


customers_page = safe_import(
    "modules.sales.customers",
    "customers_page"
)


quotations_page = safe_import(
    "modules.sales.quotations",
    "quotations_page"
)


sales_orders_page = safe_import(
    "modules.sales.orders",
    "sales_orders_page"
)


delivery_page = safe_import(
    "modules.sales.delivery",
    "delivery_page"
)


dispatch_page = safe_import(
    "modules.sales.dispatch",
    "dispatch_page"
)


finance_dashboard = safe_import(
    "modules.finance.dashboard",
    "finance_dashboard"
)


invoices_page = safe_import(
    "modules.finance.invoices",
    "invoices_page"
)


payments_page = safe_import(
    "modules.finance.payments",
    "payments_page"
)


reports_dashboard = safe_import(
    "modules.reports.dashboard",
    "reports_dashboard"
)


logistics_dashboard = safe_import(
    "modules.logistics.dashboard",
    "logistics_dashboard"
)


hr_dashboard = safe_import(
    "modules.hr.dashboard",
    "hr_dashboard"
)


maintenance_dashboard = safe_import(
    "modules.maintenance.dashboard",
    "maintenance_dashboard"
)


ai_assistant_page = safe_import(
    "modules.ai_assistant.ai_page",
    "ai_assistant_page"
)


user_management_page = safe_import(
    "modules.administration.user_management",
    "user_management_page"
)


change_password_page = safe_import(
    "modules.administration.change_password",
    "change_password_page"
)

