import streamlit as st

def landing_page():
    lilac = "#C8A2C8"
    st.markdown(f"<h1 style='color:{lilac}; text-align:center;'>Welcome to GraphDB 🌿</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>Unlock the true potential of connected data. Our custom graph database delivers speed, flexibility, and insights—so you see what others miss.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 0.5, 2])
    with col2:
        if st.button("Go to Dashboard"):
            st.session_state.page = "dashboard"
