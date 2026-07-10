import os
import pandas as pd
import logging
import traceback
from sklearn.feature_extraction.text import TfidfVectorizer

DATA_DIR = "data/ml-1m"

class ContentRecommender:
    def __init__(self):
        self.movies_df = None
        self.tfidf_matrix = None
        self.movie_id_to_index = {}
        
    def load_data(self):
        try:
            logging.info("Starting load_data for ContentRecommender")
            movies_path = os.path.join(DATA_DIR, "movies.dat")
            if not os.path.exists(movies_path):
                logging.error(f"Movies file not found: {movies_path}")
                return False
                
            # Load movies
            logging.info(f"Loading movies from {movies_path} for content recommendation")
            self.movies_df = pd.read_csv(
                movies_path, 
                sep="::", 
                engine='python', 
                names=['MovieID', 'Title', 'Genres'],
                encoding='latin-1'
            )
            
            # Create combined text feature
            logging.info("Creating combined text features for content recommendation")
            genres_spaced = self.movies_df['Genres'].str.replace('|', ' ', regex=False)
            self.movies_df['Content'] = self.movies_df['Title'] + ' ' + genres_spaced
            
            logging.info("Successfully finished load_data for ContentRecommender")
            return True
        except Exception:
            logging.exception(f"Failed to load MovieLens data for content recommendations: {traceback.format_exc()}")
            return False
            
    def build_model(self):
        try:
            logging.info("Starting build_model for ContentRecommender")
            if self.movies_df is None:
                logging.info("Data not loaded, calling load_data()")
                if not self.load_data():
                    return False
                
            logging.info("Fitting TF-IDF Vectorizer")
            vectorizer = TfidfVectorizer()
            self.tfidf_matrix = vectorizer.fit_transform(self.movies_df['Content'])
            
            # We no longer precompute the full N x N cosine similarity matrix
            # to save memory. It will be computed on-the-fly per request.
            
            # Mapping from MovieID to DataFrame index
            self.movie_id_to_index = {
                movie_id: idx 
                for idx, movie_id in enumerate(self.movies_df['MovieID'])
            }
            
            logging.info("Successfully finished build_model for ContentRecommender")
            return True
        except Exception:
            logging.exception(f"Failed to build content recommender TF-IDF model: {traceback.format_exc()}")
            return False
            
    def get_content_recommendations(self, movie_id, n=10):
        try:
            logging.info(f"Starting get_content_recommendations for movie_id: {movie_id}")
            if self.tfidf_matrix is None:
                logging.info("TF-IDF matrix is None, calling build_model()")
                self.build_model()
                
            if movie_id not in self.movie_id_to_index:
                logging.warning(f"Movie ID {movie_id} not found in content index")
                return []
                
            idx = self.movie_id_to_index[movie_id]
            
            # Compute pairwise similarity scores on the fly for just this movie
            # This takes virtually no memory and is very fast
            logging.info("Computing cosine similarity vector using SciPy dot product")
            cosine_sim_vector = self.tfidf_matrix[idx].dot(self.tfidf_matrix.T).toarray().flatten()
            
            sim_scores = list(enumerate(cosine_sim_vector))
            
            # Sort the movies based on similarity scores
            logging.info("Sorting and selecting top recommendations")
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            
            # Filter out the movie itself and get the top n
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