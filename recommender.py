import os
import pandas as pd
import numpy as np
from sklearn.neighbors import BallTree
import pickle
import time
import streamlit as st

DATA_DIR = "data/ml-1m"
CACHE_DIR = "data/cache"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

class Recommender:
    def __init__(self):
        self.movies_df = None
        self.ratings_df = None
        self.matrix = None
        self.ball_tree = None
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

    def build_model(self, force_rebuild=False):
        matrix_path = os.path.join(CACHE_DIR, "movie_matrix.pkl")
        tree_path = os.path.join(CACHE_DIR, "ball_tree.pkl")
        metadata_path = os.path.join(CACHE_DIR, "metadata.pkl")
        
        if not force_rebuild and os.path.exists(matrix_path) and os.path.exists(tree_path) and os.path.exists(metadata_path):
            with open(matrix_path, 'rb') as f:
                self.matrix = pickle.load(f)
            with open(tree_path, 'rb') as f:
                self.ball_tree = pickle.load(f)
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
                self.movie_index_to_id = metadata['index_to_id']
                self.movie_id_to_index = metadata['id_to_index']
                self.stats = metadata['stats']
            return True

        start_time = time.time()
        pivot_df = self.ratings_df.pivot(index='MovieID', columns='UserID', values='Rating').fillna(0)
        self.matrix = pivot_df.values
        movie_ids = pivot_df.index.tolist()
        
        self.movie_index_to_id = {idx: mid for idx, mid in enumerate(movie_ids)}
        self.movie_id_to_index = {mid: idx for idx, mid in enumerate(movie_ids)}
        
        self.stats['matrix_dims'] = self.matrix.shape
        total_elements = self.matrix.shape[0] * self.matrix.shape[1]
        non_zero = np.count_nonzero(self.matrix)
        self.stats['sparsity'] = (1.0 - (non_zero / total_elements)) * 100
        
        self.ball_tree = BallTree(self.matrix, leaf_size=self.stats['leaf_size'], metric='euclidean')
        self.stats['build_time'] = time.time() - start_time
        
        n_samples = self.matrix.shape[0]
        self.stats['nodes'] = int(2 * (n_samples / self.stats['leaf_size']) - 1)
        self.stats['height'] = int(np.log2(self.stats['nodes'])) if self.stats['nodes'] > 0 else 0
        
        with open(matrix_path, 'wb') as f: pickle.dump(self.matrix, f)
        with open(tree_path, 'wb') as f: pickle.dump(self.ball_tree, f)
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'index_to_id': self.movie_index_to_id,
                'id_to_index': self.movie_id_to_index,
                'stats': self.stats
            }, f)
            
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
        # 8. Add recommendation caching
        if movie_id in self.recommendation_cache:
            # Return cached results immediately, tracking query time as 0.0 ms
            return self.recommendation_cache[movie_id], 0.0

        if movie_id not in self.movie_id_to_index:
            return [], 0.0
            
        idx = self.movie_id_to_index[movie_id]
        query_vector = self.matrix[idx].reshape(1, -1)
        
        start_time = time.perf_counter()
        distances, indices = self.ball_tree.query(query_vector, k=n+1)
        query_time = time.perf_counter() - start_time
        
        recommendations = []
        if len(indices[0]) > 1:
            min_local_dist = distances[0][1]
            max_local_dist = distances[0][-1]
            
        for i in range(1, len(indices[0])):
            rec_idx = indices[0][i]
            rec_movie_id = self.movie_index_to_id[rec_idx]
            dist = distances[0][i]
            
            # Normalize distances relative to the returned recommendation set
            # Min-Max scaler projecting to a highly relevant 80%-99% range
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
                
        # Save to cache
        self.recommendation_cache[movie_id] = recommendations
        return recommendations, query_time

    @st.cache_data(ttl=3600*24)
    def get_trending(_self, limit=10):
        popular_movies = _self.ratings_df.groupby('MovieID').size().reset_index(name='counts')
        merged = pd.merge(popular_movies, _self.movies_df, on='MovieID')
        trending = merged[merged['AvgRating'] > 3.5].sort_values('counts', ascending=False).head(limit)
        return trending.to_dict('records')

@st.cache_resource(show_spinner="Building core engine...")
def get_cached_recommender():
    rec = Recommender()
    rec.load_data()
    rec.build_model()
    return rec
