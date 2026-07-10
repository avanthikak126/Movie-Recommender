import os
import pandas as pd
import numpy as np
import logging
import traceback
from sklearn.neighbors import BallTree
import time
import streamlit as st
from threadpoolctl import threadpool_limits

DATA_DIR = "data/ml-1m"

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
        try:
            logging.info("Starting load_data for Recommender")
            movies_path = os.path.join(DATA_DIR, "movies.dat")
            ratings_path = os.path.join(DATA_DIR, "ratings.dat")
            
            if not os.path.exists(movies_path) or not os.path.exists(ratings_path):
                logging.error(f"Data files missing: {movies_path} or {ratings_path}")
                return False
                
            logging.info(f"Loading movies from {movies_path}")
            self.movies_df = pd.read_csv(
                movies_path, 
                sep="::", 
                engine='python', 
                names=['MovieID', 'Title', 'Genres'],
                encoding='latin-1'
            )
            
            logging.info(f"Loading ratings from {ratings_path}")
            self.ratings_df = pd.read_csv(
                ratings_path, 
                sep="::", 
                engine='python', 
                names=['UserID', 'MovieID', 'Rating', 'Timestamp']
            )
            
            self.stats['movies'] = len(self.movies_df)
            self.stats['users'] = self.ratings_df['UserID'].nunique()
            self.stats['ratings'] = len(self.ratings_df)
            
            logging.info("Calculating average ratings")
            avg_ratings = self.ratings_df.groupby('MovieID')['Rating'].mean().reset_index()
            self.movies_df = pd.merge(self.movies_df, avg_ratings, on='MovieID', how='left').fillna(0)
            self.movies_df.rename(columns={'Rating': 'AvgRating'}, inplace=True)
            
            logging.info("Successfully finished load_data for Recommender")
            return True
        except Exception:
            logging.exception(f"Failed to load MovieLens data: {traceback.format_exc()}")
            return False

    def build_model(self):
        try:
            logging.info("Starting build_model for Recommender")
            start_time = time.time()
            logging.info("Pivoting ratings dataframe")
            pivot_df = self.ratings_df.pivot(index='MovieID', columns='UserID', values='Rating').fillna(0)
            # Use float64 and force C-contiguous to avoid memory mapping and alignment issues in Cython BallTree.
            logging.info("Converting pivot table to float64 contiguous matrix")
            self.matrix = np.ascontiguousarray(pivot_df.values.astype(np.float64))
            movie_ids = pivot_df.index.tolist()
            
            self.movie_index_to_id = {idx: mid for idx, mid in enumerate(movie_ids)}
            self.movie_id_to_index = {mid: idx for idx, mid in enumerate(movie_ids)}
            
            self.stats['matrix_dims'] = self.matrix.shape
            total_elements = self.matrix.shape[0] * self.matrix.shape[1]
            non_zero = np.count_nonzero(self.matrix)
            self.stats['sparsity'] = (1.0 - (non_zero / total_elements)) * 100
            
            logging.info(f"Matrix built with shape: {self.stats['matrix_dims']} and sparsity: {self.stats['sparsity']}%")
            logging.info("Constructing BallTree...")
            with threadpool_limits(limits=1):
                self.ball_tree = BallTree(self.matrix, leaf_size=self.stats['leaf_size'], metric='euclidean')
            logging.info("BallTree successfully constructed")
                
            self.stats['build_time'] = time.time() - start_time
            
            n_samples = self.matrix.shape[0]
            self.stats['nodes'] = int(2 * (n_samples / self.stats['leaf_size']) - 1)
            self.stats['height'] = int(np.log2(self.stats['nodes'])) if self.stats['nodes'] > 0 else 0
                
            logging.info("Finished build_model successfully")
            return True
        except Exception:
            logging.exception(f"Failed to build BallTree model: {traceback.format_exc()}")
            return False

    def get_movie_details(self, movie_id):
        movie = self.movies_df[self.movies_df['MovieID'] == movie_id]
        if movie.empty: return None
        return movie.iloc[0].to_dict()

    def search_movies(self, query, limit=10):
        try:
            if not query: return []
            matches = self.movies_df[self.movies_df['Title'].str.contains(query, case=False, na=False)]
            return matches.head(limit).to_dict('records')
        except Exception:
            logging.exception(f"Failed to search movies with query: '{query}'")
            return []

    def get_recommendations(self, movie_id, n=10):
        try:
            logging.info(f"Starting get_recommendations for movie_id: {movie_id}")
            if movie_id in self.recommendation_cache:
                logging.info(f"Returning cached recommendations for movie_id: {movie_id}")
                return self.recommendation_cache[movie_id], 0.0

            if movie_id not in self.movie_id_to_index:
                logging.warning(f"Movie ID {movie_id} not found in index")
                return [], 0.0
                
            idx = self.movie_id_to_index[movie_id]
            logging.info("Reshaping query vector and ensuring contiguity")
            query_vector = np.ascontiguousarray(self.matrix[idx].reshape(1, -1))
            
            start_time = time.perf_counter()
            
            logging.info("Executing BallTree query")
            with threadpool_limits(limits=1):
                distances, indices = self.ball_tree.query(query_vector, k=n+1)
            logging.info("BallTree query executed successfully")
                
            query_time = time.perf_counter() - start_time
            
            logging.info("Processing recommendation results")
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
                    movie_details['distance'] = float(dist)
                    movie_details['similarity'] = int(sim_score)
                    recommendations.append(movie_details)
                    
            self.recommendation_cache[movie_id] = recommendations
            logging.info(f"Finished get_recommendations for movie_id: {movie_id}")
            return recommendations, query_time
        except Exception:
            logging.exception(f"Failed to get recommendations for movie ID: {movie_id}. Traceback: {traceback.format_exc()}")
            return [], 0.0

    def benchmark_query_performance(self, movie_id, n=100):
        try:
            if movie_id not in self.movie_id_to_index:
                return None

            idx = self.movie_id_to_index[movie_id]
            query_vector = self.matrix[idx].reshape(1, -1)
            k = min(n + 1, self.matrix.shape[0])

            start_time = time.perf_counter()
            with threadpool_limits(limits=1):
                self.ball_tree.query(query_vector, k=k)
            ball_tree_time = time.perf_counter() - start_time

            start_time = time.perf_counter()
            distances = np.linalg.norm(self.matrix - query_vector, axis=1)
            np.argsort(distances)[:k]
            brute_force_time = time.perf_counter() - start_time

            speedup = brute_force_time / ball_tree_time if ball_tree_time > 0 else 0.0

            return {
                'ball_tree_time': ball_tree_time,
                'brute_force_time': brute_force_time,
                'speedup': speedup,
            }
        except Exception:
            logging.exception(f"Failed to benchmark query performance for movie ID: {movie_id}")
            return None

    @st.cache_data(ttl=3600*24)
    def get_trending(_self, limit=10):
        try:
            popular_movies = _self.ratings_df.groupby('MovieID').size().reset_index(name='counts')
            merged = pd.merge(popular_movies, _self.movies_df, on='MovieID')
            trending = merged[merged['AvgRating'] > 3.5].sort_values('counts', ascending=False).head(limit)
            return trending.to_dict('records')
        except Exception:
            logging.exception("Failed to get trending movies.")
            return []


@st.cache_resource(show_spinner="Building Global Recommendation Engine...")
def get_cached_recommender():
    rec = Recommender()
    rec.load_data()
    rec.build_model()
    return rec
