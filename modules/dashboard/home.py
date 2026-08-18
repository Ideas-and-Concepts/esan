"""
Esan ERP
Overview Dashboard

Nile Harvest Foods Ltd.
"""

import streamlit as st

from modules.dashboard.services import get_dashboard_summary


def dashboard_home():
    """
    Render the Esan ERP Overview Dashboard.

    Dashboard data is provided by:
        modules.dashboard.services.get_dashboard_summary()

    The dashboard is intentionally defensive so that a missing
    database table or unavailable service does not crash Streamlit.
    """

    st.title("🏠 Esan ERP Overview")

    st.caption(
        "Nile Harvest Foods Ltd. | Enterprise Resource Planning Dashboard"
    )

    # ========================================================
    # LOAD DASHBOARD DATA
    # ========================================================

    try:
        summary = get_dashboard_summary()

    except Exception as exc:
        st.error("Unable to load the Overview Dashboard.")
        st.caption(
            "The dashboard service encountered an error. "
            "Check esan_erp.log for details."
        )

        # Keep Streamlit running instead of crashing.
        summary = {}

    if not isinstance(summary, dict):
        summary = {}

    # ========================================================
    # SAFE SECTION HELPER
    # ========================================================

    def section(name):
        value = summary.get(name, {})

        if isinstance(value, dict):
            return value

        return {}

    # ========================================================
    # DASHBOARD SECTIONS
    # ========================================================

    sales = section("sales")
    procurement = section("procurement")
    inventory = section("inventory")
    production = section("production")
    receivables = section("receivables")

    alerts = summary.get("alerts", [])
    recent_activity = summary.get(
        "recent_activity",
        [],
    )

    if not isinstance(alerts, list):
        alerts = []

    if not isinstance(recent_activity, list):
        recent_activity = []

    # ========================================================
    # KPI CARDS
    # ========================================================

    st.subheader("📊 Business Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    # --------------------------------------------------------
    # SALES
    # --------------------------------------------------------

    with col1:

        st.metric(
            "Sales",
            sales.get(
                "total",
                sales.get(
                    "total_sales",
                    0,
                ),
            ),
        )

    # --------------------------------------------------------
    # PROCUREMENT
    # --------------------------------------------------------

    with col2:

        st.metric(
            "Procurement",
            procurement.get(
                "total",
                procurement.get(
                    "total_procurement",
                    0,
                ),
            ),
        )

    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------

    with col3:

        st.metric(
            "Inventory",
            inventory.get(
                "total",
                inventory.get(
                    "total_inventory",
                    0,
                ),
            ),
        )

    # --------------------------------------------------------
    # PRODUCTION
    # --------------------------------------------------------

    with col4:

        st.metric(
            "Production",
            production.get(
                "total",
                production.get(
                    "total_production",
                    0,
                ),
            ),
        )

    # --------------------------------------------------------
    # RECEIVABLES
    # --------------------------------------------------------

    with col5:

        st.metric(
            "Receivables",
            receivables.get(
                "total",
                receivables.get(
                    "total_receivables",
                    0,
                ),
            ),
        )

    # ========================================================
    # SALES / PROCUREMENT
    # ========================================================

    st.divider()

    col1, col2 = st.columns(2)

    # --------------------------------------------------------
    # SALES
    # --------------------------------------------------------

    with col1:

        st.subheader("🚚 Sales")

        st.write(
            f"Orders: **{sales.get('orders', 0)}**"
        )

        st.write(
            f"Customers: **{sales.get('customers', 0)}**"
        )

        st.write(
            f"Invoices: **{sales.get('invoices', 0)}**"
        )

        st.write(
            f"Payments: **{sales.get('payments', 0)}**"
        )

    # --------------------------------------------------------
    # PROCUREMENT
    # --------------------------------------------------------

    with col2:

        st.subheader("🌾 Procurement")

        st.write(
            f"Suppliers: **{procurement.get('suppliers', 0)}**"
        )

        st.write(
            f"Purchase Orders: "
            f"**{procurement.get('purchase_orders', 0)}**"
        )

        st.write(
            f"Purchases: "
            f"**{procurement.get('purchases', 0)}**"
        )

    # ========================================================
    # INVENTORY / PRODUCTION
    # ========================================================

    st.divider()

    col1, col2 = st.columns(2)

    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------

    with col1:

        st.subheader("📦 Inventory")

        st.write(
            f"Products: **{inventory.get('products', 0)}**"
        )

        st.write(
            f"Stock Quantity: "
            f"**{inventory.get('quantity', 0)}**"
        )

        st.write(
            f"Low Stock Items: "
            f"**{inventory.get('low_stock', 0)}**"
        )

    # --------------------------------------------------------
    # PRODUCTION
    # --------------------------------------------------------

    with col2:

        st.subheader("🏭 Production")

        st.write(
            f"Milling Batches: "
            f"**{production.get('milling_batches', 0)}**"
        )

        st.write(
            f"Packaging Batches: "
            f"**{production.get('packaging_batches', 0)}**"
        )

        st.write(
            f"Production Quantity: "
            f"**{production.get('quantity', 0)}**"
        )

    # ========================================================
    # RECEIVABLES
    # ========================================================

    st.divider()

    st.subheader("💰 Receivables")

    receivable_col1, receivable_col2, receivable_col3 = (
        st.columns(3)
    )

    with receivable_col1:

        st.metric(
            "Outstanding",
            receivables.get(
                "outstanding",
                receivables.get(
                    "total",
                    0,
                ),
            ),
        )

    with receivable_col2:

        st.metric(
            "Invoices",
            receivables.get(
                "invoices",
                0,
            ),
        )

    with receivable_col3:

        st.metric(
            "Overdue",
            receivables.get(
                "overdue",
                0,
            ),
        )

    # ========================================================
    # ALERTS
    # ========================================================

    st.divider()

    st.subheader("⚠️ Alerts")

    if alerts:

        for alert in alerts:

            if isinstance(alert, dict):

                message = alert.get(
                    "message",
                    alert.get(
                        "title",
                        "Dashboard alert",
                    ),
                )

                level = alert.get(
                    "level",
                    "info",
                )

                if level == "error":

                    st.error(message)

                elif level == "warning":

                    st.warning(message)

                elif level == "success":

                    st.success(message)

                else:

                    st.info(message)

            else:

                st.info(str(alert))

    else:

        st.success(
            "No critical alerts at the moment."
        )

    # ========================================================
    # RECENT ACTIVITY
    # ========================================================

    st.divider()

    st.subheader("🕒 Recent Activity")

    if recent_activity:

        for activity in recent_activity:

            if isinstance(activity, dict):

                activity_type = activity.get(
                    "type",
                    "Activity",
                )

                description = activity.get(
                    "description",
                    activity.get(
                        "message",
                        "",
                    ),
                )

                timestamp = activity.get(
                    "timestamp",
                    "",
                )

                st.markdown(
                    f"**{activity_type}**  \n"
                    f"{description}"
                )

                if timestamp:

                    st.caption(
                        str(timestamp)
                    )

                st.divider()

            else:

                st.write(
                    str(activity)
                )

    else:

        st.info(
            "No recent activity available."
        )


# ============================================================
# DIRECT EXECUTION SUPPORT
# ============================================================

if __name__ == "__main__":
    dashboard_home()