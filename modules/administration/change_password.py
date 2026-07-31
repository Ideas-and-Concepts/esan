"""
Change Password (for all logged-in users)
"""

import streamlit as st
from services.user_service import change_password

def change_password_page():
    st.title("🔑 Change Password")
    with st.form("change_password_form"):
        old = st.text_input("Current Password", type="password")
        new = st.text_input("New Password", type="password")
        confirm = st.text_input("Confirm New Password", type="password")
        if st.form_submit_button("Update Password"):
            if new != confirm:
                st.error("Passwords do not match.")
                return
            if len(new) < 4:
                st.error("Password must be at least 4 characters.")
                return
            username = st.session_state.username
            if change_password(username, old, new):
                st.success("Password updated. Please log out and log back in.")
            else:
                st.error("Incorrect current password.")