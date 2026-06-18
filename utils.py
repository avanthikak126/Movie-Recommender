import streamlit as st

def set_page_config():
    st.set_page_config(
        page_title="RECFLIX",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

def inject_custom_css():
    with open("assets/style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def show_loading_animation():
    with st.spinner("🔎 Searching Ball Tree..."):
        pass
    with st.spinner("🎬 Finding Similar Movies..."):
        pass
    with st.spinner("🍿 Preparing Recommendations..."):
        pass
