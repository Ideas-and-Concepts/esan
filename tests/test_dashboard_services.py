"""
Esan ERP
Dashboard Services Tests

Strict contract tests for:

- Sales
- Procurement
- Inventory
- Production
- Receivables
- Alerts
- Recent Activity

These tests verify that the dashboard service always returns
the structure expected by modules/dashboard/home.py.

The tests are intentionally tolerant of missing database
tables because services.py is expected to provide graceful
fallbacks.
"""

import importlib


# ============================================================
# IMPORT SERVICE
# ============================================================

services = importlib.import_module(
    "modules.dashboard.services"
)


# ============================================================
# EXPECTED TOP-LEVEL STRUCTURE
# ============================================================

EXPECTED_TOP_LEVEL_KEYS = {
    "sales",
    "procurement",
    "inventory",
    "production",
    "receivables",
    "alerts",
    "recent_activity",
}


# ============================================================
# EXPECTED SECTION KEYS
# ============================================================

SALES_KEYS = {
    "today",
    "month",
    "orders",
    "revenue",
}

PROCUREMENT_KEYS = {
    "today",
    "month",
    "orders",
    "spend",
}

INVENTORY_KEYS = {
    "total_items",
    "total_quantity",
    "low_stock_items",
    "stock_value",
}

PRODUCTION_KEYS = {
    "today",
    "month",
    "batches",
    "quantity",
}

RECEIVABLES_KEYS = {
    "outstanding",
    "overdue",
    "customers",
    "invoices",
}

ALERT_KEYS = {
    "type",
    "severity",
    "message",
}

ACTIVITY_KEYS = {
    "type",
    "description",
    "timestamp",
}


# ============================================================
# HELPERS
# ============================================================

def assert_numeric(value):
    """
    Verify a dashboard numeric value.

    bool is explicitly excluded because bool is technically
    an int subclass in Python.
    """

    assert isinstance(
        value,
        (int, float),
    )

    assert not isinstance(
        value,
        bool,
    )


def assert_exact_dict_keys(
    data,
    expected_keys,
):
    assert isinstance(
        data,
        dict,
    )

    assert set(data.keys()) == expected_keys


# ============================================================
# MAIN SUMMARY
# ============================================================

def test_dashboard_summary_exact_structure():

    summary = services.get_dashboard_summary()

    assert isinstance(
        summary,
        dict,
    )

    assert set(summary.keys()) == (
        EXPECTED_TOP_LEVEL_KEYS
    )


# ============================================================
# SALES
# ============================================================

def test_sales_exact_structure():

    summary = services.get_dashboard_summary()

    sales = summary["sales"]

    assert_exact_dict_keys(
        sales,
        SALES_KEYS,
    )


def test_sales_value_types():

    summary = services.get_dashboard_summary()

    sales = summary["sales"]

    assert_numeric(
        sales["today"]
    )

    assert_numeric(
        sales["month"]
    )

    assert isinstance(
        sales["orders"],
        int,
    )

    assert not isinstance(
        sales["orders"],
        bool,
    )

    assert_numeric(
        sales["revenue"]
    )


# ============================================================
# PROCUREMENT
# ============================================================

def test_procurement_exact_structure():

    summary = services.get_dashboard_summary()

    procurement = summary["procurement"]

    assert_exact_dict_keys(
        procurement,
        PROCUREMENT_KEYS,
    )


def test_procurement_value_types():

    summary = services.get_dashboard_summary()

    procurement = summary["procurement"]

    assert_numeric(
        procurement["today"]
    )

    assert_numeric(
        procurement["month"]
    )

    assert isinstance(
        procurement["orders"],
        int,
    )

    assert not isinstance(
        procurement["orders"],
        bool,
    )

    assert_numeric(
        procurement["spend"]
    )


# ============================================================
# INVENTORY
# ============================================================

def test_inventory_exact_structure():

    summary = services.get_dashboard_summary()

    inventory = summary["inventory"]

    assert_exact_dict_keys(
        inventory,
        INVENTORY_KEYS,
    )


def test_inventory_value_types():

    summary = services.get_dashboard_summary()

    inventory = summary["inventory"]

    assert isinstance(
        inventory["total_items"],
        int,
    )

    assert not isinstance(
        inventory["total_items"],
        bool,
    )

    assert_numeric(
        inventory["total_quantity"]
    )

    assert isinstance(
        inventory["low_stock_items"],
        int,
    )

    assert not isinstance(
        inventory["low_stock_items"],
        bool,
    )

    assert_numeric(
        inventory["stock_value"]
    )


# ============================================================
# PRODUCTION
# ============================================================

def test_production_exact_structure():

    summary = services.get_dashboard_summary()

    production = summary["production"]

    assert_exact_dict_keys(
        production,
        PRODUCTION_KEYS,
    )


def test_production_value_types():

    summary = services.get_dashboard_summary()

    production = summary["production"]

    assert_numeric(
        production["today"]
    )

    assert_numeric(
        production["month"]
    )

    assert isinstance(
        production["batches"],
        int,
    )

    assert not isinstance(
        production["batches"],
        bool,
    )

    assert_numeric(
        production["quantity"]
    )


# ============================================================
# RECEIVABLES
# ============================================================

def test_receivables_exact_structure():

    summary = services.get_dashboard_summary()

    receivables = summary["receivables"]

    assert_exact_dict_keys(
        receivables,
        RECEIVABLES_KEYS,
    )


def test_receivables_value_types():

    summary = services.get_dashboard_summary()

    receivables = summary["receivables"]

    assert_numeric(
        receivables["outstanding"]
    )

    assert_numeric(
        receivables["overdue"]
    )

    assert isinstance(
        receivables["customers"],
        int,
    )

    assert not isinstance(
        receivables["customers"],
        bool,
    )

    assert isinstance(
        receivables["invoices"],
        int,
    )

    assert not isinstance(
        receivables["invoices"],
        bool,
    )


# ============================================================
# ALERTS
# ============================================================

def test_alerts_is_list():

    summary = services.get_dashboard_summary()

    alerts = summary["alerts"]

    assert isinstance(
        alerts,
        list,
    )


def test_alert_items_have_exact_structure():

    summary = services.get_dashboard_summary()

    alerts = summary["alerts"]

    for alert in alerts:

        assert isinstance(
            alert,
            dict,
        )

        assert set(alert.keys()) == (
            ALERT_KEYS
        )


def test_alert_item_value_types():

    summary = services.get_dashboard_summary()

    alerts = summary["alerts"]

    for alert in alerts:

        assert isinstance(
            alert["type"],
            str,
        )

        assert isinstance(
            alert["severity"],
            str,
        )

        assert isinstance(
            alert["message"],
            str,
        )


# ============================================================
# RECENT ACTIVITY
# ============================================================

def test_recent_activity_is_list():

    summary = services.get_dashboard_summary()

    recent_activity = summary[
        "recent_activity"
    ]

    assert isinstance(
        recent_activity,
        list,
    )


def test_recent_activity_items_have_exact_structure():

    summary = services.get_dashboard_summary()

    recent_activity = summary[
        "recent_activity"
    ]

    for activity in recent_activity:

        assert isinstance(
            activity,
            dict,
        )

        assert set(activity.keys()) == (
            ACTIVITY_KEYS
        )


def test_recent_activity_item_value_types():

    summary = services.get_dashboard_summary()

    recent_activity = summary[
        "recent_activity"
    ]

    for activity in recent_activity:

        assert isinstance(
            activity["type"],
            str,
        )

        assert isinstance(
            activity["description"],
            str,
        )

        assert isinstance(
            activity["timestamp"],
            str,
        )


# ============================================================
# GRACEFUL FALLBACK CONTRACT
# ============================================================

def test_missing_tables_still_return_valid_contract():

    """
    services.py should return the same contract even when
    one or more ERP database tables do not exist yet.
    """

    summary = services.get_dashboard_summary()

    assert isinstance(
        summary,
        dict,
    )

    assert set(summary.keys()) == (
        EXPECTED_TOP_LEVEL_KEYS
    )

    assert_exact_dict_keys(
        summary["sales"],
        SALES_KEYS,
    )

    assert_exact_dict_keys(
        summary["procurement"],
        PROCUREMENT_KEYS,
    )

    assert_exact_dict_keys(
        summary["inventory"],
        INVENTORY_KEYS,
    )

    assert_exact_dict_keys(
        summary["production"],
        PRODUCTION_KEYS,
    )

    assert_exact_dict_keys(
        summary["receivables"],
        RECEIVABLES_KEYS,
    )

    assert isinstance(
        summary["alerts"],
        list,
    )

    assert isinstance(
        summary["recent_activity"],
        list,
    )


# ============================================================
# REPEATED CALL SAFETY
# ============================================================

def test_dashboard_summary_multiple_calls():

    first = services.get_dashboard_summary()

    second = services.get_dashboard_summary()

    assert set(first.keys()) == (
        EXPECTED_TOP_LEVEL_KEYS
    )

    assert set(second.keys()) == (
        EXPECTED_TOP_LEVEL_KEYS
    )