import streamlit as st
import os
from utils import hash_password

def auth_page():
    lilac = "#C8A2C8"
    db = st.session_state.get("selected_db")

    if not db:
        st.warning("No database selected.")
        return

    st.markdown(f"<h3 style='color:{lilac}'>🔒 Authenticate for <code>{db}</code></h3>", unsafe_allow_html=True)
    pwd_input = st.text_input("Enter password", type="password")

    if st.button("Login"):
        pwd_path = f"databases/{db}/password.txt"
        if os.path.exists(pwd_path):
            with open(pwd_path) as f:
                stored_hash = f.read().strip()
            if hash_password(pwd_input) == stored_hash:
                st.success("✅ Access granted!")
                st.session_state["current_db"] = db
                st.session_state.page = "main_db"
            else:
                st.error("❌ Incorrect password")
        else:
            st.error("Password file not found.")
