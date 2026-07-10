import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = "data/ml-1m"

class ContentRecommender:
    def __init__(self):
        self.movies_df = None
        self.tfidf_matrix = None
        self.cosine_sim = None
        self.movie_id_to_index = {}
        
    def load_data(self):
        movies_path = os.path.join(DATA_DIR, "movies.dat")
        if not os.path.exists(movies_path):
            return False
            
        # Load movies
        self.movies_df = pd.read_csv(
            movies_path, 
            sep="::", 
            engine='python', 
            names=['MovieID', 'Title', 'Genres'],
            encoding='latin-1'
        )
        
        # Create combined text feature
        genres_spaced = self.movies_df['Genres'].str.replace('|', ' ', regex=False)
        self.movies_df['Content'] = self.movies_df['Title'] + ' ' + genres_spaced
        
        return True
        
    def build_model(self):
        if self.movies_df is None:
            if not self.load_data():
                return False
            
        vectorizer = TfidfVectorizer()
        self.tfidf_matrix = vectorizer.fit_transform(self.movies_df['Content'])
        
        from threadpoolctl import threadpool_limits
        with threadpool_limits(limits=1):
            self.cosine_sim = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix)
        
        # Mapping from MovieID to DataFrame index
        self.movie_id_to_index = {
            movie_id: idx 
            for idx, movie_id in enumerate(self.movies_df['MovieID'])
        }
        
        return True
        
    def get_content_recommendations(self, movie_id, n=10):
        if self.cosine_sim is None:
            self.build_model()
            
        if movie_id not in self.movie_id_to_index:
            return []
            
        idx = self.movie_id_to_index[movie_id]
        
        # Get pairwise similarity scores
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        
        # Sort the movies based on similarity scores
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
                'Content Similarity Score': similarities[i]
            })
            
        return recommendations
