import os
import pandas as pd
import logging
import traceback
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer

DATA_DIR = "data/ml-1m"

@st.cache_resource(show_spinner="Loading content data...")
def load_content_data():
    try:
        logging.info("Starting load_content_data")
        movies_path = os.path.join(DATA_DIR, "movies.dat")
        if not os.path.exists(movies_path):
            logging.error(f"Movies file not found: {movies_path}")
            return None, None
            
        logging.info(f"Loading movies from {movies_path} for content recommendation")
        movies_df = pd.read_csv(
            movies_path, 
            sep="::", 
            engine='python', 
            names=['MovieID', 'Title', 'Genres'],
            encoding='latin-1'
        )
        
        logging.info("Creating combined text features for content recommendation")
        genres_spaced = movies_df['Genres'].str.replace('|', ' ', regex=False)
        movies_df['Content'] = movies_df['Title'] + ' ' + genres_spaced
        
        logging.info("Fitting TF-IDF Vectorizer globally to cache the matrix")
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(movies_df['Content'])
        
        return movies_df, tfidf_matrix
    except Exception:
        logging.exception(f"Failed to load MovieLens data for content recommendations: {traceback.format_exc()}")
        return None, None

class ContentRecommender:
    def __init__(self, movies_df, tfidf_matrix):
        self.movies_df = movies_df
        self.tfidf_matrix = tfidf_matrix
        self.movie_id_to_index = {
            movie_id: idx 
            for idx, movie_id in enumerate(self.movies_df['MovieID'])
        } if self.movies_df is not None else {}
            
    def get_content_recommendations(self, movie_id, n=10):
        try:
            logging.info(f"Starting get_content_recommendations for movie_id: {movie_id}")
            if self.tfidf_matrix is None:
                return []
                
            if movie_id not in self.movie_id_to_index:
                logging.warning(f"Movie ID {movie_id} not found in content index")
                return []
                
            idx = self.movie_id_to_index[movie_id]
            
            logging.info("Computing cosine similarity vector using SciPy dot product")
            cosine_sim_vector = self.tfidf_matrix[idx].dot(self.tfidf_matrix.T).toarray().flatten()
            
            sim_scores = list(enumerate(cosine_sim_vector))
            
            logging.info("Sorting and selecting top recommendations")
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            
            sim_scores = [score for score in sim_scores if score[0] != idx][:n]
            
            movie_indices = [i[0] for i in sim_scores]
            similarities = [i[1] for i in sim_scores]
            
            recommendations = []
            for i, m_idx in enumerate(movie_indices):
                movie = self.movies_df.iloc[m_idx]
                recommendations.append({
                    'MovieID': int(movie['MovieID']),
                    'Title': movie['Title'],
                    'Genres': movie['Genres'],
                    'Content Similarity Score': float(similarities[i])
                })
                
            logging.info(f"Successfully finished get_content_recommendations for movie_id: {movie_id}")
            return recommendations
        except Exception:
            logging.exception(f"Failed to generate content recommendations for movie ID: {movie_id}. Traceback: {traceback.format_exc()}")
            return []