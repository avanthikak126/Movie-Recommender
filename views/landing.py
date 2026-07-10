import streamlit as st

def render_auth_landing_page():
    st.markdown("""
<div class="hero-section">
    <div class="hero-spotlight"></div>
    <div class="hero-particles">
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
    </div>
    <div class="hero-content">
        <div class="hero-badge">🎬 Movie Recommendations Engine</div>
        <h1 class="hero-title">RECFLIX</h1>
        <p class="hero-subtitle">Discover Your Next Favorite Movie</p>
        <p class="hero-description">
            Sign in to unlock personalized recommendations,<br>
            analytics, watchlists, and TMDB comparisons.
        </p>
    </div>
    <div class="hero-glow"></div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
    <div style="max-width: 820px; margin: 0 auto 1.25rem auto; text-align: center;">
        <p style="font-size: 1.05rem; line-height: 1.7; color: rgba(255,255,255,0.82);">
            Welcome to RECFLIX, a cinematic recommendation experience powered by
            collaborative filtering, content signals, and real-time TMDB data.
            Log in or create an account to start exploring.
        </p>
    </div>
    """, unsafe_allow_html=True)

    login_col, signup_col = st.columns(2)
    with login_col:
        if st.button("Login", width="stretch"):
            st.switch_page("views/login.py")
    with signup_col:
        if st.button("Sign Up", width="stretch"):
            st.switch_page("views/Signup.py")

render_auth_landing_page()
