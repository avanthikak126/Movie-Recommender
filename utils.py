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
        css = f.read()

    # Hide default sidebar navigation globally
    css += "\n[data-testid='stSidebarNav'] { display: none !important; }\n"

    # Completely hide sidebar if not logged in
    if "username" not in st.session_state:
        css += "\n[data-testid='collapsedControl'] { display: none !important; }\n"
        css += "\n[data-testid='stSidebar'] { display: none !important; }\n"

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def render_sidebar():
    if "username" in st.session_state:
        with st.sidebar:
            st.markdown("### Account")
            st.caption(f"Signed in as **{st.session_state['username']}**")
            st.page_link("app.py", label="Home", icon="🏠")
            st.page_link("pages/watchlist.py", label="Watchlist", icon="⭐")
            if st.button("Logout", use_container_width=True):
                st.session_state.clear()
                st.switch_page("app.py")

def show_loading_animation():
    with st.spinner("🔎 Searching Ball Tree..."):
        pass
    with st.spinner("🎬 Finding Similar Movies..."):
        pass
    with st.spinner("🍿 Preparing Recommendations..."):
        pass
