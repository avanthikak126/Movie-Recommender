import streamlit as st
import pandas as pd
from recommender import get_cached_recommender
from tmdb import tmdb_client
from evaluation import Evaluator
import utils
import analytics
import requests

# Initialize Configuration and CSS
utils.set_page_config()
utils.inject_custom_css()

# Session State Persistence
if 'recent_searches' not in st.session_state:
    st.session_state.recent_searches = []
if 'selected_movie' not in st.session_state:
    st.session_state.selected_movie = None

# Load Data and Build Model once via Streamlit cache
recommender = get_cached_recommender()

if 'evaluator' not in st.session_state:
    st.session_state.evaluator = Evaluator(recommender)

# --- HELPER: VALIDATED POSTER RENDERING ---
@st.cache_data(show_spinner=False)
def validate_poster_url(url):
    """Cache the URL validation so we don't delay Streamlit reruns."""
    if not url or "via.placeholder.com" in url:
        return True # Placeholder is assumed valid
    try:
        resp = requests.head(url, timeout=2)
        return resp.status_code == 200
    except:
        return False

def render_poster(title, poster_url):
    print(f"Movie: {title}")
    print(f"Poster URL: {poster_url}")
    print(f"Render Attempt: Yes")
    
    is_valid = validate_poster_url(poster_url)
    
    if is_valid:
        print(f"Render Success: Yes\n")
        st.image(poster_url, use_container_width=True)
    else:
        print(f"Render Success: No (URL invalid or 404. Falling back to placeholder)\n")
        fallback_url = "https://via.placeholder.com/500x750/1d1e26/e50914?text=No+Poster+Found"
        st.image(fallback_url, use_container_width=True)

# --- CINEMATIC HERO BANNER ---
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
            Powered by Ball Tree Collaborative Filtering<br>
            and MovieLens 1M Ratings
        </p>
    </div>
    <div class="hero-glow"></div>
</div>
""", unsafe_allow_html=True)

# --- STATS ROW ---
hero_stats = recommender.stats
st.markdown(f"""
<div class="stats-row">
    <div class="stat-card">
        <div class="stat-icon">🎬</div>
        <div class="stat-value">{hero_stats['movies']:,}</div>
        <div class="stat-label">Movies Indexed</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-value">{hero_stats['users']:,}</div>
        <div class="stat-label">Active Users</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">⭐</div>
        <div class="stat-value">{hero_stats['ratings']:,}</div>
        <div class="stat-label">Total Ratings</div>
    </div>
    <div class="stat-card">
        <div class="stat-icon">🌳</div>
        <div class="stat-value">{hero_stats['nodes']:,}</div>
        <div class="stat-label">Ball Tree Nodes</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    " Discover Movies", 
    " Analytics Dashboard", 
    " Ball Tree Explorer", 
    " Formal Validation"
])

with tab1:
    # --- SEARCH BAR ---
    all_movies = recommender.movies_df['Title'].tolist()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_title = st.selectbox(
            "Search for a movie...",
            options=[""] + all_movies,
            index=0,
            help="Type to search through all available movies."
        )
    with col2:
        st.write("")
        st.write("")
        search_btn = st.button("Get Recommendations", use_container_width=True)

    if search_btn and selected_title:
        with st.spinner("Finding Similar Movies..."):
            selected_movie = recommender.movies_df[recommender.movies_df['Title'] == selected_title].iloc[0].to_dict()
            st.session_state.selected_movie = selected_movie
            if selected_movie not in st.session_state.recent_searches:
                st.session_state.recent_searches.insert(0, selected_movie)
                if len(st.session_state.recent_searches) > 5:
                    st.session_state.recent_searches.pop()
            
            recs, _ = recommender.get_recommendations(selected_movie['MovieID'])
            for r in recs[:5]:
                tmdb_client.get_movie_details(r['Title'])

    if st.session_state.selected_movie:
        selected_m = st.session_state.selected_movie
        st.markdown("---")
        
        # Details & Poster
        col_img, col_info = st.columns([1, 2])
        tmdb_data = tmdb_client.get_movie_details(selected_m['Title'])
        
        with col_img:
            render_poster(selected_m['Title'], tmdb_data['poster_url'])
            
        with col_info:
            st.markdown(f"<h2>{selected_m['Title']}</h2>", unsafe_allow_html=True)
            st.markdown(f"**Genres:** {selected_m['Genres']}")
            st.markdown(f"**Year:** {selected_m['Title'].split('(')[-1].strip(')') if '(' in selected_m['Title'] else 'Unknown'}")
            st.markdown(f"**Average Rating:** ⭐ {selected_m['AvgRating']:.2f}/5")
            if tmdb_data.get('overview'):
                st.markdown(f"**Overview:** {tmdb_data['overview']}")
                
        # RECOMMENDATIONS
        st.markdown("### 🎬 Recommended for You")
        
        recs, _ = recommender.get_recommendations(selected_m['MovieID'])
        
        if recs:
            cols = st.columns(5)
            
            rec_tmdbs = [tmdb_client.get_movie_details(r['Title']) for r in recs[:5]]
            
            for i, rec in enumerate(recs[:5]):
                rec_tmdb = rec_tmdbs[i]
                with cols[i]:
                    render_poster(rec['Title'], rec_tmdb['poster_url'])
                    st.markdown(f"**{rec['Title']}**")
                    st.markdown(f"**Genres:** {rec['Genres']}")
                    st.markdown(f"⭐ {rec['AvgRating']:.1f}/5")
                    st.markdown(f"**Score:** {rec['similarity']}%")
                    
            # TMDB COMPARISON
            st.markdown("### ⚖️ Comparison with TMDB Similar Movies")
            tmdb_similar = tmdb_client.get_similar_movies(tmdb_data.get('id'))
            
            if tmdb_similar:
                t_cols = st.columns(5)
                for i, tmdb_rec in enumerate(tmdb_similar[:5]):
                    with t_cols[i]:
                        render_poster(tmdb_rec.get('title', 'Unknown'), tmdb_rec.get('poster_url', ''))
                        st.markdown(f"**{tmdb_rec.get('title', tmdb_rec.get('name', 'Unknown'))}**")
                        st.markdown(f"⭐ {tmdb_rec.get('vote_average', 0) / 2:.1f}/5")

    # TRENDING SECTION
    st.markdown("---")
    st.markdown("### 🔥 Trending Movies")
    trending = recommender.get_trending(5)
    cols = st.columns(5)
    
    trending_tmdbs = [tmdb_client.get_movie_details(t['Title']) for t in trending]
    
    for i, t_movie in enumerate(trending):
        t_tmdb = trending_tmdbs[i]
        with cols[i]:
            render_poster(t_movie['Title'], t_tmdb['poster_url'])
            st.markdown(f"**{t_movie['Title']}**")
            st.markdown(f"⭐ {t_movie['AvgRating']:.1f}/5")
            
    # RECENT SEARCHES
    if st.session_state.recent_searches:
        st.markdown("### 🕒 Recently Searched")
        r_cols = st.columns(5)
        for i, r_movie in enumerate(st.session_state.recent_searches):
            r_tmdb = tmdb_client.get_movie_details(r_movie['Title'])
            with r_cols[i]:
                render_poster(r_movie['Title'], r_tmdb['poster_url'])
                st.markdown(f"**{r_movie['Title']}**")
                st.markdown(f"⭐ {r_movie['AvgRating']:.1f}/5")


with tab2:
    st.header("Analytics Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    stats = recommender.stats
    
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{stats["movies"]:,}</div><div class="kpi-label">Movies</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{stats["users"]:,}</div><div class="kpi-label">Users</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{stats["ratings"]:,}</div><div class="kpi-label">Ratings</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{stats["sparsity"]:.2f}%</div><div class="kpi-label">Matrix Sparsity</div></div>', unsafe_allow_html=True)
        
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(analytics.plot_genre_distribution(recommender.movies_df), use_container_width=True)
    with c2:
        st.plotly_chart(analytics.plot_ratings_distribution(recommender.ratings_df), use_container_width=True)


with tab3:
    st.header("🌳 Ball Tree Metadata Explorer")
    
    st.markdown("The Ball Tree is a space-partitioning data structure that organizes points in a multi-dimensional space, optimized for nearest neighbor searches. Here are the internal statistics of our constructed tree:")
    
    c1, c2, c3 = st.columns(3)
    stats = recommender.stats
    with c1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{stats["leaf_size"]}</div><div class="kpi-label">Leaf Size</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{stats["build_time"]:.2f}s</div><div class="kpi-label">Build Time</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{stats["height"]}</div><div class="kpi-label">Tree Height</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{stats["matrix_dims"][0]} x {stats["matrix_dims"][1]}</div><div class="kpi-label">Matrix Dims</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{stats["nodes"]:,}</div><div class="kpi-label">Total Nodes</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">Euclidean</div><div class="kpi-label">Distance Metric</div></div>', unsafe_allow_html=True)


with tab4:
    st.header("Formal Validation")
    st.markdown("Evaluating the recommendation system using Precision and Recall metrics over a sample of active users.")
    
    if not st.session_state.evaluator.metrics['Evaluated']:
        if st.button("Run Evaluation on Sample Data"):
            with st.spinner("Evaluating model... This might take a minute."):
                st.session_state.evaluator.evaluate(sample_size=50)
                st.rerun()
    else:
        m = st.session_state.evaluator.metrics
        st.success("Evaluation Complete!")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Precision@5", f"{m['Precision@5']:.4f}")
        c2.metric("Precision@10", f"{m['Precision@10']:.4f}")
        c3.metric("Recall@10", f"{m['Recall@10']:.4f}")
        
        st.plotly_chart(analytics.plot_precision_metrics(m), use_container_width=True)
        
        st.markdown("### Interpretation")
        st.info("""
        - **Precision@K**: The fraction of recommended items in the top-K set that are relevant.
        - **Recall@K**: The fraction of relevant items that are successfully recommended in the top-K set.
        """)
