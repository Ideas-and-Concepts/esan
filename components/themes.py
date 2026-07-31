"""
Theme Component
Esan ERP - Light/Dark toggle
"""

import streamlit as st

def esan_theme(theme):
    if theme == "Dark":
        st.markdown("""
        <style>
        /* Dark theme overrides */
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        .stSidebar {
            background-color: #262730;
        }
        .st-bq {
            background-color: #262730;
        }
        .stMetric {
            background-color: #1a1c23;
            border-radius: 8px;
            padding: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Light theme (default)
        st.markdown("""
        <style>
        .stApp {
            background-color: #ffffff;
            color: #31333f;
        }
        .stMetric {
            background-color: #f0f2f6;
            border-radius: 8px;
            padding: 10px;
        }
        </style>
        """, unsafe_allow_html=True)