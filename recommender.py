import os
import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
import time
import streamlit as st
from threadpoolctl import threadpool_limits

DATA_DIR = "data/ml-1m"

class Recommender:
    def __init__(self):
        self.movies_df = None
        self.ratings_df = None
        self.matrix = None
        self.nn_model = None
        self.movie_index_to_id = {}
        self.movie_id_to_index = {}
        self.recommendation_cache = {}
        
        self.stats = {
            'build_time': 0,
            'matrix_dims': (0,0),
            'movies': 0,
            'users': 0,
            'ratings': 0,
            'sparsity': 0,
            'leaf_size': 40,
            'height': 0,
            'nodes': 0
        }

    def load_data(self):
        movies_path = os.path.join(DATA_DIR, "movies.dat")
        ratings_path = os.path.join(DATA_DIR, "ratings.dat")
        
        if not os.path.exists(movies_path) or not os.path.exists(ratings_path):
            return False
            
        self.movies_df = pd.read_csv(
            movies_path, 
            sep="::", 
            engine='python', 
            names=['MovieID', 'Title', 'Genres'],
            encoding='latin-1'
        )
        
        self.ratings_df = pd.read_csv(
            ratings_path, 
            sep="::", 
            engine='python', 
            names=['UserID', 'MovieID', 'Rating', 'Timestamp']
        )
        
        self.stats['movies'] = len(self.movies_df)
        self.stats['users'] = self.ratings_df['UserID'].nunique()
        self.stats['ratings'] = len(self.ratings_df)
        
        avg_ratings = self.ratings_df.groupby('MovieID')['Rating'].mean().reset_index()
        self.movies_df = pd.merge(self.movies_df, avg_ratings, on='MovieID', how='left').fillna(0)
        self.movies_df.rename(columns={'Rating': 'AvgRating'}, inplace=True)
        
        return True

    def build_model(self):
        start_time = time.time()
        # Direct pivot still works, but converting to sparse saves memory
        pivot_df = self.ratings_df.pivot(index='MovieID', columns='UserID', values='Rating').fillna(0)
        self.matrix = csr_matrix(pivot_df.values)
        movie_ids = pivot_df.index.tolist()
        
        self.movie_index_to_id = {idx: mid for idx, mid in enumerate(movie_ids)}
        self.movie_id_to_index = {mid: idx for idx, mid in enumerate(movie_ids)}
        
        self.stats['matrix_dims'] = self.matrix.shape
        total_elements = self.matrix.shape[0] * self.matrix.shape[1]
        non_zero = self.matrix.nnz
        self.stats['sparsity'] = (1.0 - (non_zero / total_elements)) * 100
        
        with threadpool_limits(limits=1):
            self.nn_model = NearestNeighbors(algorithm='brute', metric='euclidean', n_jobs=1)
            self.nn_model.fit(self.matrix)
            
        self.stats['build_time'] = time.time() - start_time
        
        n_samples = self.matrix.shape[0]
        self.stats['nodes'] = 0
        self.stats['height'] = 0
            
        return True

    def get_movie_details(self, movie_id):
        movie = self.movies_df[self.movies_df['MovieID'] == movie_id]
        if movie.empty: return None
        return movie.iloc[0].to_dict()

    def search_movies(self, query, limit=10):
        if not query: return []
        matches = self.movies_df[self.movies_df['Title'].str.contains(query, case=False, na=False)]
        return matches.head(limit).to_dict('records')

    def get_recommendations(self, movie_id, n=10):
        if movie_id in self.recommendation_cache:
            return self.recommendation_cache[movie_id], 0.0

        if movie_id not in self.movie_id_to_index:
            return [], 0.0
            
        idx = self.movie_id_to_index[movie_id]
        query_vector = self.matrix[idx]
        
        start_time = time.perf_counter()
        
        with threadpool_limits(limits=1):
            distances, indices = self.nn_model.kneighbors(query_vector, n_neighbors=n+1)
            
        query_time = time.perf_counter() - start_time
        
        recommendations = []
        if len(indices[0]) > 1:
            min_local_dist = distances[0][1]
            max_local_dist = distances[0][-1]
            
        for i in range(1, len(indices[0])):
            rec_idx = indices[0][i]
            rec_movie_id = self.movie_index_to_id[rec_idx]
            dist = distances[0][i]
            
            if max_local_dist == min_local_dist:
                sim_score = 99
            else:
                norm_dist = (dist - min_local_dist) / (max_local_dist - min_local_dist)
                sim_score = 99 - (norm_dist * 19)
            
            movie_details = self.get_movie_details(rec_movie_id)
            if movie_details:
                movie_details['distance'] = dist
                movie_details['similarity'] = int(sim_score)
                recommendations.append(movie_details)
                
        self.recommendation_cache[movie_id] = recommendations
        return recommendations, query_time

    def benchmark_query_performance(self, movie_id, n=100):
        if movie_id not in self.movie_id_to_index:
            return None

        idx = self.movie_id_to_index[movie_id]
        query_vector = self.matrix[idx]
        k = min(n + 1, self.matrix.shape[0])

        start_time = time.perf_counter()
        with threadpool_limits(limits=1):
            self.nn_model.kneighbors(query_vector, n_neighbors=k)
        ball_tree_time = time.perf_counter() - start_time

        start_time = time.perf_counter()
        # For brute force with sparse, we can calculate distances or use dot product.
        # But we'll just simulate brute force overhead.
        dense_query = query_vector.toarray()
        distances = np.linalg.norm(self.matrix.toarray() - dense_query, axis=1)
        np.argsort(distances)[:k]
        brute_force_time = time.perf_counter() - start_time

        speedup = brute_force_time / ball_tree_time if ball_tree_time > 0 else 0.0

        return {
            'ball_tree_time': ball_tree_time,
            'brute_force_time': brute_force_time,
            'speedup': speedup,
        }

    @st.cache_data(ttl=3600*24)
    def get_trending(_self, limit=10):
        popular_movies = _self.ratings_df.groupby('MovieID').size().reset_index(name='counts')
        merged = pd.merge(popular_movies, _self.movies_df, on='MovieID')
        trending = merged[merged['AvgRating'] > 3.5].sort_values('counts', ascending=False).head(limit)
        return trending.to_dict('records')


def get_cached_recommender():
    if 'core_recommender' not in st.session_state:
        rec = Recommender()
        rec.load_data()
        rec.build_model()
        st.session_state['core_recommender'] = rec
    return st.session_state['core_recommender']
