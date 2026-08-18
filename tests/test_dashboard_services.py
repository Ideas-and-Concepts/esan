"""
Esan ERP
Dashboard Services Tests

Tests the fallback structure returned by:
modules.dashboard.services.get_dashboard_summary()

The tests intentionally work even when optional ERP models/tables
are missing.
"""

import importlib


# ============================================================
# IMPORT DASHBOARD SERVICES
# ============================================================

services = importlib.import_module(
    "modules.dashboard.services"
)


# ============================================================
# EXPECTED DASHBOARD STRUCTURE
# ============================================================

EXPECTED_KEYS = {
    "sales",
    "procurement",
    "inventory",
    "production",
    "receivables",
    "alerts",
    "recent_activity",
}


# ============================================================
# TEST: SUMMARY STRUCTURE
# ============================================================

def test_dashboard_summary_structure():

    summary = services.get_dashboard_summary()

    assert isinstance(
        summary,
        dict,
    )

    assert set(summary.keys()) == EXPECTED_KEYS


# ============================================================
# TEST: SALES
# ============================================================

def test_sales_structure():

    summary = services.get_dashboard_summary()

    sales = summary["sales"]

    assert isinstance(
        sales,
        dict,
    )


# ============================================================
# TEST: PROCUREMENT
# ============================================================

def test_procurement_structure():

    summary = services.get_dashboard_summary()

    procurement = summary["procurement"]

    assert isinstance(
        procurement,
        dict,
    )


# ============================================================
# TEST: INVENTORY
# ============================================================

def test_inventory_structure():

    summary = services.get_dashboard_summary()

    inventory = summary["inventory"]

    assert isinstance(
        inventory,
        dict,
    )


# ============================================================
# TEST: PRODUCTION
# ============================================================

def test_production_structure():

    summary = services.get_dashboard_summary()

    production = summary["production"]

    assert isinstance(
        production,
        dict,
    )


# ============================================================
# TEST: RECEIVABLES
# ============================================================

def test_receivables_structure():

    summary = services.get_dashboard_summary()

    receivables = summary["receivables"]

    assert isinstance(
        receivables,
        dict,
    )


# ============================================================
# TEST: ALERTS
# ============================================================

def test_alerts_structure():

    summary = services.get_dashboard_summary()

    alerts = summary["alerts"]

    assert isinstance(
        alerts,
        list,
    )


# ============================================================
# TEST: RECENT ACTIVITY
# ============================================================

def test_recent_activity_structure():

    summary = services.get_dashboard_summary()

    recent_activity = summary[
        "recent_activity"
    ]

    assert isinstance(
        recent_activity,
        list,
    )


# ============================================================
# TEST: ALL SECTIONS ARE SAFE
# ============================================================

def test_dashboard_summary_is_safe():

    """
    The dashboard must return a usable structure even if
    database models or tables are unavailable.
    """

    summary = services.get_dashboard_summary()

    assert summary is not None

    assert isinstance(
        summary,
        dict,
    )

    for key in EXPECTED_KEYS:

        assert key in summary


# ============================================================
# TEST: REPEATED CALLS
# ============================================================

def test_dashboard_summary_can_be_called_repeatedly():

    first = services.get_dashboard_summary()

    second = services.get_dashboard_summary()

    assert isinstance(first, dict)

    assert isinstance(second, dict)

    assert set(first.keys()) == EXPECTED_KEYS

    assert set(second.keys()) == EXPECTED_KEYS