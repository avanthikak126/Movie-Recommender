import streamlit as st
from auth import get_watchlist, remove_from_watchlist

st.title("⭐ My Watchlist")

if "username" not in st.session_state:
    st.warning("Please login first.")
    st.stop()

movies = get_watchlist(st.session_state["username"])

if not movies:
    st.info("Your watchlist is empty.")
else:
    for movie in movies:
        col1, col2 = st.columns([4, 1])

        with col1:
            st.write(f"🎬 {movie.movie_title}")

        with col2:
            if st.button(
                "❌ Remove",
                key=f"remove_{movie.id}"
            ):
                remove_from_watchlist(movie.id)
                st.rerun()