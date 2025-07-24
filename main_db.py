import streamlit as st
from pyvis.network import Network
import networkx as nx
import tempfile
import os
import json
from cypher_engine import execute_query, create_index
import time

def main_db_page():
    # Get the current database name from session state
    db_name = st.session_state.get("current_db")
    if not db_name:
        st.error("No database selected.")
        st.stop()

# Construct the full path to that database's folder
    db_path = os.path.join("databases", db_name)
    db = st.session_state.get("selected_db", "")
    lilac = "#C8A2C8"
    st.balloons()

    st.markdown(f"<h3 style='color:{lilac}'>🧠 Working in: <code>{db}</code></h3>", unsafe_allow_html=True)

    st.subheader("🔎 Run Cypher Query")
    query = st.text_area("Enter Cypher Query", height=150)
    use_index = st.checkbox("Use Index", value=True)

    if st.button("Run Query"):
        if use_index:
            start_time = time.time()
            result = execute_query(query, db_path, use_index=True)
            exec_time = time.time() - start_time
            st.markdown("### With Index")
        else:
            start_time = time.time()
            result = execute_query(query, db_path, use_index=False)
            exec_time = time.time() - start_time
            st.markdown("### Without Index")

        if "error" in result:
            st.error(result["error"])
        else:
            show_graph_and_list(result)
            st.markdown(f"⏱️ Query executed in **{exec_time:.3f} seconds**")

    st.divider()

    st.subheader("🧩 Add Index")
    with st.form("add_index_form"):
        label = st.text_input("Entity Label (e.g., Person)")
        prop = st.text_input("Property to Index (e.g., name)")
        if st.form_submit_button("Add Index"):
            index_path = f"databases/{db}/indexes.json"
            if os.path.exists(index_path):
                with open(index_path) as f:
                    indexes = json.load(f)
            else:
                indexes = {}

            create_index(os.path.join("databases", db), label, prop)
            st.success(f"Index created for `{label}.{prop}`")

    st.divider()

    if st.button("🚦 Begin Transaction"):
        st.session_state.page = "transaction"

def show_graph_and_list(data):
    # Graph View
    net = Network(height="400px", bgcolor="black", font_color="#C8A2C8")
    for node in data["nodes"]:
        label = node["labels"][0] if node["labels"] else "Node"
        name = node["properties"].get("name", "")
        # Convert properties dict to a string for tooltip
        tooltip = ", ".join([f"{k}: {v}" for k, v in node["properties"].items()])
        net.add_node(
            node["id"],
            label=f"{label}: {name}",
            title=tooltip
        )

    for edge in data["relationships"]:
        net.add_edge(edge["start_node"], edge["end_node"], label=edge["type"])

    temp_dir = tempfile.mkdtemp()
    html_path = os.path.join(temp_dir, "graph.html")
    net.write_html(html_path)  # ✅ use write_html instead of show()

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    st.components.v1.html(html_content, height=420)

    # List View
    st.subheader("📋 Output List")
    st.json(data)
