import streamlit as st
import pandas as pd
from recommender import get_cached_recommender
from content_recommender import ContentRecommender
from tmdb import tmdb_client
from evaluation import Evaluator
import utils
import analytics
from auth import add_to_watchlist

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
        if st.button("Login", use_container_width=True):
            st.switch_page("pages/login.py")
    with signup_col:
        if st.button("Sign Up", use_container_width=True):
            st.switch_page("pages/Signup.py")

    st.stop()


# Only show sidebar if user is authenticated
if "username" not in st.session_state:
    render_auth_landing_page()

# Only show sidebar if user is authenticated
utils.render_sidebar()

# Load Data and Build Model once via Streamlit cache
recommender = get_cached_recommender()

@st.cache_resource(show_spinner="Building Content Engine...")
def get_cached_content_recommender():
    rec = ContentRecommender()
    rec.build_model()
    return rec

content_recommender = get_cached_content_recommender()

if 'evaluator' not in st.session_state:
    st.session_state.evaluator = Evaluator(recommender)

# --- HELPER: VALIDATED POSTER RENDERING ---
@st.cache_data(show_spinner=False)
def get_cached_tmdb_movie_details(title):
    return tmdb_client.get_movie_details(title)


@st.cache_data(show_spinner=False)
def get_cached_tmdb_similar_movies(tmdb_id):
    return tmdb_client.get_similar_movies(tmdb_id)

def render_poster(title, poster_url):
    fallback_url = "https://via.placeholder.com/500x750/1d1e26/e50914?text=No+Poster+Found"
    st.image(poster_url or fallback_url, use_container_width=True)

def _get_shared_genres(source_genres, target_genres):
    if not source_genres or not target_genres:
        return []
    return sorted(set(source_genres.split('|')) & set(target_genres.split('|')))

def _similarity_bar(pct):
    pct = max(0, min(100, int(pct)))
    filled = round(pct / 10)
    return "█" * filled + "░" * (10 - filled)

def render_why_recommended(rec):
    collab = rec.get('Collaborative Score', 0)
    content = rec.get('Content Similarity Score', 0)
    hybrid = rec.get('Hybrid Score', rec.get('similarity', 0))
    shared_genres = rec.get('_shared_genres', [])
    genre_badges = ''.join(
        f'<span class="why-genre-badge">{g}</span>' for g in shared_genres
    )
    bar = _similarity_bar(hybrid)

    st.markdown(f"""
<div class="why-recommended-panel">
    <div class="why-reason-list">
        <div class="why-reason-item">
            <span class="why-check">✓</span>
            <span class="why-reason-badge collab-badge">👥</span>
            Similar user rating patterns detected
        </div>
        <div class="why-reason-item">
            <span class="why-check">✓</span>
            <span class="why-reason-badge genre-badge">🎭</span>
            Similar genres identified
            {f'<div class="why-genre-row">{genre_badges}</div>' if genre_badges else ''}
        </div>
        <div class="why-reason-item">
            <span class="why-check">✓</span>
            <span class="why-reason-badge tree-badge">🌳</span>
            Retrieved using Ball Tree nearest-neighbor search
        </div>
        <div class="why-reason-item">
            <span class="why-check">✓</span>
            <span class="why-reason-badge hybrid-badge">⚡</span>
            Ranked using Hybrid Recommendation scoring
        </div>
    </div>
    <div class="why-score-grid">
        <div class="why-score-card">
            <span class="why-score-icon">👥</span>
            <span class="why-score-label">Collaborative Score</span>
            <span class="why-score-value">{collab:.1f}</span>
        </div>
        <div class="why-score-card">
            <span class="why-score-icon">🎬</span>
            <span class="why-score-label">Content Similarity Score</span>
            <span class="why-score-value">{content:.1f}</span>
        </div>
        <div class="why-score-card highlight">
            <span class="why-score-icon">⚡</span>
            <span class="why-score-label">Hybrid Score</span>
            <span class="why-score-value">{hybrid:.0f}</span>
        </div>
    </div>
    <div class="why-similarity-section">
        <div class="why-similarity-label">🎯 Similarity: {hybrid:.0f}%</div>
        <div class="why-similarity-bar">{bar}</div>
    </div>
</div>
""", unsafe_allow_html=True)

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
            st.session_state.show_performance_benchmark = False
            st.session_state.benchmark_movie_id = None
            st.session_state.benchmark_results = None
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
        tmdb_data = get_cached_tmdb_movie_details(selected_m['Title'])
        
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
        st.markdown("🟣 **Hybrid AI Recommendations**")
        st.caption("This recommendation engine combines user-rating behavior and movie-content similarity to produce more accurate and diverse recommendations.")
        
        collab_recs, _ = recommender.get_recommendations(selected_m['MovieID'], n=100)
        content_recs = content_recommender.get_content_recommendations(selected_m['MovieID'], n=100)
        
        # Min-Max scale both sets to 0-100 so weights apply fairly
        raw_collab = {r['MovieID']: r['similarity'] for r in collab_recs}
        if raw_collab:
            c_min, c_max = min(raw_collab.values()), max(raw_collab.values())
            collab_map = {k: 100 * (v - c_min) / (c_max - c_min) if c_max > c_min else 100 for k, v in raw_collab.items()}
        else:
            collab_map = {}
            
        raw_content = {r['MovieID']: r['Content Similarity Score'] for r in content_recs}
        if raw_content:
            cont_min, cont_max = min(raw_content.values()), max(raw_content.values())
            content_map = {k: 100 * (v - cont_min) / (cont_max - cont_min) if cont_max > cont_min else 100 for k, v in raw_content.items()}
        else:
            content_map = {}
        
        all_ids = set(collab_map.keys()).union(set(content_map.keys()))
        hybrid_recs = []
        
        source_genres = selected_m.get('Genres', '')
        for mid in all_ids:
            c_score = collab_map.get(mid, 0)
            cont_score = content_map.get(mid, 0)
            
            hybrid_score = (0.7 * c_score) + (0.3 * cont_score)
            
            movie_dict = recommender.get_movie_details(mid)
            if movie_dict:
                movie_dict['Collaborative Score'] = c_score
                movie_dict['Content Similarity Score'] = cont_score
                movie_dict['Hybrid Score'] = hybrid_score
                movie_dict['similarity'] = int(hybrid_score)
                movie_dict['_shared_genres'] = _get_shared_genres(source_genres, movie_dict.get('Genres', ''))
                hybrid_recs.append(movie_dict)
                
        hybrid_recs.sort(key=lambda x: x['similarity'], reverse=True)
        recs = hybrid_recs[:10]
        
        if recs:
            cols = st.columns(5)
            
            rec_tmdbs = [get_cached_tmdb_movie_details(r['Title']) for r in recs[:5]]
            
            for i, rec in enumerate(recs[:5]):
                rec_tmdb = rec_tmdbs[i]
                with cols[i]:
                    render_poster(rec['Title'], rec_tmdb['poster_url'])
                    st.markdown(f"**{rec['Title']}**")
                    st.markdown(f"**Genres:** {rec['Genres']}")
                    
                    avg_rating = rec.get('AvgRating')
                    if avg_rating is None:
                        m_row = recommender.movies_df[recommender.movies_df['MovieID'] == rec['MovieID']]
                        avg_rating = m_row.iloc[0]['AvgRating'] if not m_row.empty else 0
                    st.markdown(f"⭐ {avg_rating:.1f}/5")

                    sim = rec.get('similarity')
                    if sim is not None:
                        st.markdown(f"🎯 **Similarity:** {sim}%")
                    else:
                        c_sim = rec.get('Content Similarity Score', 0)
                        st.markdown(f"🎯 **Similarity:** {int(c_sim * 100)}%")

                    if st.button( "⭐ Add to Watchlist",
                        key=f"watch_{rec['MovieID']}"
                    ):
                        if "username" in st.session_state:
                            added = add_to_watchlist(
                                st.session_state["username"],
                                rec["MovieID"],
                                rec["Title"]
                            )
                            if added:
                                st.success("Added to Watchlist!")
                            else:
                                st.info("Movie already in Watchlist")
                        else:
                            st.warning("Please login first.")

                    with st.expander("Why Recommended?"):
                        render_why_recommended(rec)

        if st.button("⚡ Run Performance Benchmark", use_container_width=False, key="run_benchmark_btn"):
            st.session_state.show_performance_benchmark = True
            st.session_state.benchmark_movie_id = selected_m['MovieID']
            with st.spinner("Running Ball Tree vs Brute Force benchmark..."):
                st.session_state.benchmark_results = recommender.benchmark_query_performance(
                    selected_m['MovieID'], n=100
                )

        if (
            st.session_state.show_performance_benchmark
            and st.session_state.benchmark_movie_id == selected_m['MovieID']
            and st.session_state.benchmark_results
        ):
            benchmark = st.session_state.benchmark_results
            title_col, close_col = st.columns([6, 1])
            with title_col:
                st.markdown("### ⚡ Recommendation Engine Performance")
            with close_col:
                st.write("")
                if st.button("✕ Close", key="close_benchmark_btn", use_container_width=True):
                    st.session_state.show_performance_benchmark = False
                    st.session_state.benchmark_movie_id = None
                    st.session_state.benchmark_results = None
                    st.rerun()

            st.caption(
                f"Nearest-neighbor search benchmark for **{selected_m['Title']}** "
                f"across {recommender.stats['movies']:,} movies."
            )

            b1, b2, b3 = st.columns(3)
            b1.metric(
                "Ball Tree",
                f"{benchmark['ball_tree_time']:.3f} sec",
                help="Time to retrieve nearest neighbors using the Ball Tree index.",
            )
            b2.metric(
                "Brute Force",
                f"{benchmark['brute_force_time']:.3f} sec",
                help="Time to scan every movie vector and sort by Euclidean distance.",
            )
            b3.metric(
                "Speedup",
                f"{benchmark['speedup']:.1f}x Faster",
                help="How many times faster Ball Tree is compared to brute force.",
            )

            st.plotly_chart(
                analytics.plot_query_benchmark(
                    benchmark['ball_tree_time'],
                    benchmark['brute_force_time'],
                ),
                use_container_width=True,
            )

        if recs:
            # TMDB COMPARISON
            st.markdown("### ⚖️ Comparison with TMDB Similar Movies")
            tmdb_similar = get_cached_tmdb_similar_movies(tmdb_data.get('id'))
            
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
    
    trending_tmdbs = [get_cached_tmdb_movie_details(t['Title']) for t in trending]
    
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
            r_tmdb = get_cached_tmdb_movie_details(r_movie['Title'])
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
    st.markdown("Evaluating the recommendation system using comprehensive metrics over a sample of active users.")
    
    if not st.session_state.evaluator.metrics['Evaluated']:
        if st.button("Run Formal Evaluation"):
            with st.spinner("Evaluating model... This might take a minute."):
                st.session_state.evaluator.evaluate(sample_size=50)
                st.rerun()
    else:
        m = st.session_state.evaluator.metrics
        st.success("Evaluation Complete!")
        
        st.markdown("### Ranking Metrics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Precision@5", f"{m.get('Precision@5', 0)*100:.1f}%")
        c2.metric("Precision@10", f"{m.get('Precision@10', 0)*100:.1f}%")
        c3.metric("Recall@10", f"{m.get('Recall@10', 0)*100:.1f}%")
        
        st.markdown("### System Metrics")
        c4, c5, c6, c7 = st.columns(4)
        c4.metric("User Coverage", f"{m.get('User Coverage', 0)*100:.1f}%")
        c5.metric("Catalog Coverage", f"{m.get('Catalog Coverage', 0)*100:.1f}%")
        c6.metric("Diversity", f"{m.get('Diversity', 0):.1f}")
        c7.metric("Avg Rec Rating", f"{m.get('Avg Rec Rating', 0):.2f}/5")
        
        st.markdown("---")
        st.markdown("### Metrics Overview")
        st.plotly_chart(analytics.plot_advanced_validation_metrics(m), use_container_width=True)
        
        st.markdown("### Methodology & Interpretation")
        st.info("""
        **Methodology**:
        We sample highly active users and split their ratings into a 80% train and 20% test set. For each user, we sample up to 3 liked movies from the train set and query the Ball Tree. The recommendations are aggregated, deduplicated, and ranked by their maximum similarity score to form a final Top 10 list. We then check these recommendations against the unseen 20% test set.
        
        **Metrics**:
        - **Precision@K**: The percentage of recommended items in the top-K set that the user actually liked.
        - **Recall@K**: The percentage of relevant items that are successfully recommended in the top-K set.
        - **User Coverage**: The percentage of sampled users for whom we successfully generated recommendations.
        - **Catalog Coverage**: The percentage of the entire movie catalog that was recommended at least once.
        - **Recommendation Diversity**: The average number of distinct genres represented in a user's top 10 recommendations.
        - **Average Recommended Rating**: The global mean rating of the recommended items.
        """)
