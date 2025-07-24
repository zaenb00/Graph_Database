import streamlit as st
from landing import landing_page
from dashboard import dashboard_page
from auth import auth_page
from main_db import main_db_page
from transaction import transaction_page

st.set_page_config(page_title="GraphDB", layout="wide")
custom_css = """
    <style>
        body {
            background-color: black;
        }
        h1, h2, h3, h4, h5, h6, p, div, span, label {
            color: #C8A2C8 !important;
        }
        .stButton > button {
            background-color: black !important;
            color: #C8A2C8 !important;
            border: 1px solid #C8A2C8;
            font-size: 14px !important;
            padding: 6px 12px !important;
            border-radius: 8px;
        }
        .stButton > button:hover {
            background-color: #C8A2C8 !important;
            color: black !important;
        }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


if "page" not in st.session_state:
    st.session_state.page = "landing"

page = st.session_state.page

if page == "landing":
    landing_page()
elif page == "dashboard":
    dashboard_page()
elif page == "auth":
    auth_page()
elif page == "main_db":
    main_db_page()
elif page == "transaction":
    transaction_page()
