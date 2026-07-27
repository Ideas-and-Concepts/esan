import streamlit as st


def apply_theme(mode):

    if mode == "Dark":

        st.markdown(
        """
        <style>

        .stApp {
            background:#121212;
            color:white;
        }

        div[data-testid="metric-container"] {

            background:#1E1E1E;
            border-radius:15px;
            padding:20px;

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

        div[data-testid="metric-container"] {

            background:white;
            border-radius:15px;
            padding:20px;

        }

        </style>

        """,
        unsafe_allow_html=True
        )