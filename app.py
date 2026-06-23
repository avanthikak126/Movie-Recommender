import streamlit as st
import utils

# Initialize Configuration and CSS
utils.set_page_config()
utils.inject_custom_css()

# Session State Persistence
if 'recent_searches' not in st.session_state:
    st.session_state.recent_searches = []
if 'selected_movie' not in st.session_state:
    st.session_state.selected_movie = None
if 'show_performance_benchmark' not in st.session_state:
    st.session_state.show_performance_benchmark = False
if 'benchmark_movie_id' not in st.session_state:
    st.session_state.benchmark_movie_id = None
if 'benchmark_results' not in st.session_state:
    st.session_state.benchmark_results = None

landing_page = st.Page("views/landing.py", title="Welcome", default=True)
login_page = st.Page("views/login.py", title="Login")
signup_page = st.Page("views/Signup.py", title="Sign Up")

home_page = st.Page("views/home.py", title="Home", default=True, icon="🏠")
watchlist_page = st.Page("views/watchlist.py", title="Watchlist", icon="⭐")

if "username" not in st.session_state:
    pg = st.navigation([landing_page, login_page, signup_page], position="hidden")
else:
    pg = st.navigation([home_page, watchlist_page], position="hidden")

pg.run()

if "username" in st.session_state:
    utils.render_sidebar()
