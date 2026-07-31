"""
User Management (Admin only)
"""

import streamlit as st
import pandas as pd
from services.user_service import get_all_users, create_user, reset_password

def user_management_page():
    if st.session_state.get("role") != "Administrator":
        st.error("Access denied. Administrator role required.")
        return

    st.title("🔐 User Management")
    tab1, tab2, tab3 = st.tabs(["All Users", "Add User", "Reset Password"])

    with tab1:
        users = get_all_users()
        if users:
            data = []
            for u in users:
                data.append({
                    "Username": u.username,
                    "Full Name": u.full_name,
                    "Email": u.email,
                    "Role": u.role,
                    "Active": u.active,
                    "Created": u.created_at.strftime("%Y-%m-%d") if u.created_at else ""
                })
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.info("No users found.")

    with tab2:
        with st.form("create_user_form"):
            username = st.text_input("Username *")
            full_name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["user", "Administrator"])
            if st.form_submit_button("Create User"):
                if not username or not password:
                    st.error("Username and password are required.")
                    return
                result = create_user(username, password, full_name, email, role)
                if result is None:
                    st.error("Username already exists.")
                else:
                    st.success(f"User '{username}' created.")
                    st.rerun()

    with tab3:
        users = get_all_users()
        user_opts = [u.username for u in users]
        selected = st.selectbox("Select user", user_opts)
        new_pass = st.text_input("New password", type="password")
        if st.button("Reset Password"):
            if reset_password(selected, new_pass):
                st.success(f"Password for '{selected}' reset.")
            else:
                st.error("Failed to reset password.")