"""
Esan ERP
Dashboard Services Tests

Tests modules/dashboard/services.py without Streamlit rendering.
"""

from modules.dashboard.services import get_dashboard_summary


# ============================================================
# REQUIRED TOP-LEVEL SECTIONS
# ============================================================

REQUIRED_SECTIONS = {
    "sales",
    "procurement",
    "inventory",
    "production",
    "receivables",
    "alerts",
    "recent_activity",
}


# ============================================================
# REQUIRED SECTION KEYS
# ============================================================

SALES_KEYS = {
    "total_sales",
    "sales_orders",
    "pending_orders",
    "completed_orders",
}

PROCUREMENT_KEYS = {
    "total_procurement",
    "purchase_orders",
    "pending_orders",
    "completed_orders",
}

INVENTORY_KEYS = {
    "total_products",
    "total_quantity",
    "low_stock_items",
    "out_of_stock_items",
}

PRODUCTION_KEYS = {
    "milling_batches",
    "packaging_batches",
    "completed_batches",
    "active_batches",
}

RECEIVABLES_KEYS = {
    "total_invoiced",
    "total_paid",
    "total_outstanding",
    "overdue_amount",
}


# ============================================================
# BASIC VALUE-TYPE CHECK
# ============================================================

def assert_numeric(value, name):
    assert isinstance(
        value,
        (int, float),
    ), f"{name} must be numeric, got {type(value).__name__}"


# ============================================================
# TEST: COMPLETE DASHBOARD STRUCTURE
# ============================================================

def test_dashboard_summary_has_expected_sections():

    summary = get_dashboard_summary()

    assert isinstance(summary, dict)

    assert REQUIRED_SECTIONS.issubset(
        summary.keys()
    )


# ============================================================
# TEST: SALES
# ============================================================

def test_sales_section():

    summary = get_dashboard_summary()

    sales = summary["sales"]

    assert isinstance(sales, dict)

    assert SALES_KEYS.issubset(
        sales.keys()
    )

    for key in SALES_KEYS:
        assert_numeric(
            sales[key],
            f"sales['{key}']",
        )


# ============================================================
# TEST: PROCUREMENT
# ============================================================

def test_procurement_section():

    summary = get_dashboard_summary()

    procurement = summary["procurement"]

    assert isinstance(procurement, dict)

    assert PROCUREMENT_KEYS.issubset(
        procurement.keys()
    )

    for key in PROCUREMENT_KEYS:
        assert_numeric(
            procurement[key],
            f"procurement['{key}']",
        )


# ============================================================
# TEST: INVENTORY
# ============================================================

def test_inventory_section():

    summary = get_dashboard_summary()

    inventory = summary["inventory"]

    assert isinstance(inventory, dict)

    assert INVENTORY_KEYS.issubset(
        inventory.keys()
    )

    for key in INVENTORY_KEYS:
        assert_numeric(
            inventory[key],
            f"inventory['{key}']",
        )


# ============================================================
# TEST: PRODUCTION
# ============================================================

def test_production_section():

    summary = get_dashboard_summary()

    production = summary["production"]

    assert isinstance(production, dict)

    assert PRODUCTION_KEYS.issubset(
        production.keys()
    )

    for key in PRODUCTION_KEYS:
        assert_numeric(
            production[key],
            f"production['{key}']",
        )


# ============================================================
# TEST: RECEIVABLES
# ============================================================

def test_receivables_section():

    summary = get_dashboard_summary()

    receivables = summary["receivables"]

    assert isinstance(receivables, dict)

    assert RECEIVABLES_KEYS.issubset(
        receivables.keys()
    )

    for key in RECEIVABLES_KEYS:
        assert_numeric(
            receivables[key],
            f"receivables['{key}']",
        )


# ============================================================
# TEST: ALERTS
# ============================================================

def test_alerts_section():

    summary = get_dashboard_summary()

    alerts = summary["alerts"]

    assert isinstance(alerts, list)

    for alert in alerts:

        assert isinstance(
            alert,
            dict,
        )

        assert "type" in alert
        assert "message" in alert

        assert isinstance(
            alert["type"],
            str,
        )

        assert isinstance(
            alert["message"],
            str,
        )


# ============================================================
# TEST: RECENT ACTIVITY
# ============================================================

def test_recent_activity_section():

    summary = get_dashboard_summary()

    activity = summary["recent_activity"]

    assert isinstance(
        activity,
        list,
    )

    for item in activity:

        assert isinstance(
            item,
            dict,
        )

        assert "type" in item
        assert "description" in item

        assert isinstance(
            item["type"],
            str,
        )

        assert isinstance(
            item["description"],
            str,
        )


# ============================================================
# TEST: SAFE FALLBACKS
# ============================================================

def test_dashboard_summary_is_safe_for_empty_database():

    summary = get_dashboard_summary()

    assert isinstance(
        summary,
        dict,
    )

    # Numeric sections must always remain usable.
    for section_name in (
        "sales",
        "procurement",
        "inventory",
        "production",
        "receivables",
    ):

        section = summary[section_name]

        assert isinstance(
            section,
            dict,
        )

        for value in section.values():

            assert isinstance(
                value,
                (int, float),
            )

    # These should never be None.
    assert isinstance(
        summary["alerts"],
        list,
    )

    assert isinstance(
        summary["recent_activity"],
        list,
    )


from unittest.mock import MagicMock, patch

from modules.dashboard.services import get_dashboard_summary


# ============================================================
# FIXED TEST DATA
# ============================================================

FIXED_SALES = {
    "total_sales": 12500000.0,
    "sales_orders": 25,
    "pending_orders": 7,
    "completed_orders": 18,
}

FIXED_PROCUREMENT = {
    "total_procurement": 6800000.0,
    "purchase_orders": 14,
    "pending_orders": 4,
    "completed_orders": 10,
}

FIXED_INVENTORY = {
    "total_products": 42,
    "total_quantity": 18500.0,
    "low_stock_items": 5,
    "out_of_stock_items": 2,
}

FIXED_RECEIVABLES = {
    "total_invoiced": 15000000.0,
    "total_paid": 9500000.0,
    "total_outstanding": 5500000.0,
    "overdue_amount": 1200000.0,
}


# ============================================================
# MOCK DATABASE SESSION
# ============================================================

def make_mock_session():

    session = MagicMock()

    # Prevent the service from actually committing anything.
    session.commit.return_value = None

    # Prevent accidental database cleanup errors.
    session.close.return_value = None

    return session


# ============================================================
# DETERMINISTIC DASHBOARD TEST
# ============================================================

@patch(
    "modules.dashboard.services.SessionLocal"
)
def test_dashboard_summary_with_fixed_database(
    mock_session_local,
):

    mock_db = make_mock_session()

    mock_session_local.return_value = mock_db

    # --------------------------------------------------------
    # Replace individual service functions with fixed values.
    #
    # This tests the dashboard contract independently of the
    # database implementation.
    # --------------------------------------------------------

    with patch(
        "modules.dashboard.services.get_sales_summary",
        return_value=FIXED_SALES,
    ), patch(
        "modules.dashboard.services.get_procurement_summary",
        return_value=FIXED_PROCUREMENT,
    ), patch(
        "modules.dashboard.services.get_inventory_summary",
        return_value=FIXED_INVENTORY,
    ), patch(
        "modules.dashboard.services.get_production_summary",
        return_value={
            "milling_batches": 8,
            "packaging_batches": 12,
            "completed_batches": 15,
            "active_batches": 5,
        },
    ), patch(
        "modules.dashboard.services.get_receivables_summary",
        return_value=FIXED_RECEIVABLES,
    ), patch(
        "modules.dashboard.services.get_dashboard_alerts",
        return_value=[],
    ), patch(
        "modules.dashboard.services.get_recent_activity",
        return_value=[],
    ):

        summary = get_dashboard_summary()

    # ========================================================
    # VERIFY SALES
    # ========================================================

    assert summary["sales"] == FIXED_SALES

    assert summary["sales"]["total_sales"] == 12500000.0
    assert summary["sales"]["sales_orders"] == 25
    assert summary["sales"]["pending_orders"] == 7
    assert summary["sales"]["completed_orders"] == 18

    # ========================================================
    # VERIFY PROCUREMENT
    # ========================================================

    assert summary["procurement"] == FIXED_PROCUREMENT

    assert (
        summary["procurement"]["total_procurement"]
        == 6800000.0
    )

    assert (
        summary["procurement"]["purchase_orders"]
        == 14
    )

    # ========================================================
    # VERIFY INVENTORY
    # ========================================================

    assert summary["inventory"] == FIXED_INVENTORY

    assert (
        summary["inventory"]["total_products"]
        == 42
    )

    assert (
        summary["inventory"]["total_quantity"]
        == 18500.0
    )

    assert (
        summary["inventory"]["low_stock_items"]
        == 5
    )

    assert (
        summary["inventory"]["out_of_stock_items"]
        == 2
    )

    # ========================================================
    # VERIFY RECEIVABLES
    # ========================================================

    assert summary["receivables"] == FIXED_RECEIVABLES

    assert (
        summary["receivables"]["total_invoiced"]
        == 15000000.0
    )

    assert (
        summary["receivables"]["total_paid"]
        == 9500000.0
    )

    assert (
        summary["receivables"]["total_outstanding"]
        == 5500000.0
    )

    assert (
        summary["receivables"]["overdue_amount"]
        == 1200000.0
    )

    # ========================================================
    # VERIFY LIST SECTIONS
    # ========================================================

    assert summary["alerts"] == []

    assert summary["recent_activity"] == []