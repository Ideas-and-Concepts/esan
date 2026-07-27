"""
Esan ERP Theme Manager
"""

import streamlit as st


def esan_theme(mode):


    if mode == "Dark":

        st.markdown(
            """
            <style>

            .stApp {

                background-color:#111827;

                color:white;

            }


            div[data-testid="stMetric"] {

                background:#1F2937;

                padding:20px;

                border-radius:15px;

            }


            </style>
            """,
            unsafe_allow_html=True
        )


    else:


        st.markdown(

            """
            <style>

            .stApp {

                background:#F5F7FA;

            }


            div[data-testid="stMetric"] {

                background:white;

                padding:20px;

                border-radius:15px;

                box-shadow:0 2px 8px #ddd;

            }


            </style>
            """,

            unsafe_allow_html=True

        )