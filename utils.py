"""
Esan ERP Utilities
"""


def format_currency(amount):

    return f"UGX {amount:,.0f}"



def success_message(message):

    return f"✅ {message}"



def error_message(message):

    return f"❌ {message}"