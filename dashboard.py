import streamlit as st
import os
from utils import hash_password, create_database

def dashboard_page():
    green = "#228B22"
    lilac = "#C8A2C8"
    st.markdown(f"<h2 style='color:{green}'>📊 Your Databases</h2>", unsafe_allow_html=True)

    if st.button("➕ Create New Database"):
        st.session_state.show_create_db = True

    if st.session_state.get("show_create_db"):
        with st.form("create_db_form"):
            db_name = st.text_input("Database Name")
            db_pass = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Create")
            if submitted:
                if not db_name or not db_pass:
                    st.warning("Name and password required.")
                else:
                    if os.path.exists(f"databases/{db_name}"):
                        st.error("Database already exists!")
                    else:
                        create_database(db_name, hash_password(db_pass))
                        st.success(f"Database '{db_name}' created!")
                        st.session_state.show_create_db = False

    # List database cards
    db_names = os.listdir("databases")
    cols = st.columns(3)
    for i, db in enumerate(db_names):
        with cols[i % 3]:
            st.markdown(f"### 🗃️ {db}")
            if st.button(f"Access {db}", key=f"btn_{db}"):
                st.session_state.selected_db = db
                st.session_state.page = "auth"
