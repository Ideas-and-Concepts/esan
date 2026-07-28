"""
Notification Service
Simple logger for system events (could be extended to email/SMS)
"""

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EsanERP")

def notify_event(event_type, message):
    """
    Log a notification event. In future, this could send emails or push notifications.
    """
    logger.info(f"[{event_type}] {message}")

def low_stock_alert(product_name, current_qty, threshold=100):
    msg = f"Low stock alert: {product_name} has only {current_qty} units (threshold: {threshold})."
    notify_event("LOW_STOCK", msg)

def payment_received(invoice_number, amount):
    msg = f"Payment of ${amount:,.2f} received for invoice {invoice_number}."
    notify_event("PAYMENT", msg)

def order_dispatched(order_number):
    msg = f"Order {order_number} has been dispatched."
    notify_event("DISPATCH", msg)

def batch_completed(batch_type, batch_number):
    msg = f"{batch_type} batch {batch_number} completed."
    notify_event("PRODUCTION", msg)