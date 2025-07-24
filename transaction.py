import os
import json
import streamlit as st
from cypher_engine import execute_query

def transaction_page():
    db_name = st.session_state.get("current_db")
    if not db_name:
        st.error("No database selected.")
        return

    db_path = os.path.join("databases", db_name)
    temp_path = os.path.join(db_path, "transaction_temp")
    lilac = "#C8A2C8"

    st.markdown(f"<h2 style='color:{lilac}'>⚙️ Transaction Manager</h2>", unsafe_allow_html=True)

    # Initialize transaction state
    if "transaction_active" not in st.session_state:
        st.session_state.transaction_active = False

    # 🔙 Back Button - Always visible
    if st.button("🔙 Back to Main DB"):
        if st.session_state.transaction_active:
            st.session_state.transaction_active = False
            cleanup_transaction(temp_path)
            st.warning("Transaction rolled back before returning to Main DB.")
        st.switch_page("main_db.py")

    if not st.session_state.transaction_active:
        if st.button("🔄 BEGIN TRANSACTION"):
            os.makedirs(temp_path, exist_ok=True)
            for f in ["nodes.json", "relationships.json"]:
                src = os.path.join(db_path, f)
                dst = os.path.join(temp_path, f)
                if os.path.exists(src):
                    with open(src, 'r') as fr, open(dst, 'w') as fw:
                        json.dump(json.load(fr), fw, indent=2)
            st.session_state.transaction_active = True
            st.success("Transaction started.")
    else:
        st.info("Transaction in progress...")

        query = st.text_area("Run Cypher Query (in transaction)", height=150)

        if st.button("Execute Query"):
            result = execute_query(query, temp_path, use_index=True)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success("Query executed on transaction data.")
                st.json(result)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ COMMIT"):
                for f in ["nodes.json", "relationships.json"]:
                    src = os.path.join(temp_path, f)
                    dst = os.path.join(db_path, f)
                    if os.path.exists(src):
                        with open(src, 'r') as fr, open(dst, 'w') as fw:
                            json.dump(json.load(fr), fw, indent=2)
                st.session_state.transaction_active = False
                st.success("Changes committed to database.")
                cleanup_transaction(temp_path)

        with col2:
            if st.button("❌ ROLLBACK"):
                st.session_state.transaction_active = False
                cleanup_transaction(temp_path)
                st.warning("Transaction rolled back.")

def cleanup_transaction(temp_path):
    if os.path.exists(temp_path):
        for file in os.listdir(temp_path):
            os.remove(os.path.join(temp_path, file))
        os.rmdir(temp_path)
