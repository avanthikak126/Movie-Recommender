import numpy as np
import pandas as pd
import time
from sklearn.model_selection import train_test_split

class Evaluator:
    def __init__(self, recommender):
        self.recommender = recommender
        self.metrics = {
            'Precision@5': 0.0,
            'Precision@10': 0.0,
            'Recall@10': 0.0,
            'Evaluated': False
        }

    def evaluate(self, sample_size=100):
        if self.recommender.matrix is None:
            return False
            
        print("Starting evaluation...")
        ratings_df = self.recommender.ratings_df
        
        # Select active users for evaluation
        user_counts = ratings_df['UserID'].value_counts()
        active_users = user_counts[user_counts > 20].index.tolist()
        
        sample_users = np.random.choice(active_users, size=min(sample_size, len(active_users)), replace=False)
        
        p5_list, p10_list, r10_list = [], [], []
        
        for user_id in sample_users:
            user_ratings = ratings_df[ratings_df['UserID'] == user_id]
            
            # Split user ratings into train/test
            if len(user_ratings) < 5:
                continue
                
            train_u, test_u = train_test_split(user_ratings, test_size=0.2, random_state=42)
            
            # Find a movie the user liked in train to use as query
            liked_movies = train_u[train_u['Rating'] >= 4.0]['MovieID'].tolist()
            if not liked_movies:
                continue
                
            query_movie = liked_movies[0]
            
            # Get recommendations
            recs, _ = self.recommender.get_recommendations(query_movie, n=10)
            rec_ids = [r['MovieID'] for r in recs]
            
            # Relevant movies in test set (liked by user)
            relevant_test_movies = set(test_u[test_u['Rating'] >= 4.0]['MovieID'].tolist())
            
            if not relevant_test_movies:
                continue
                
            # Calculate Precision@5
            hits_5 = len(set(rec_ids[:5]).intersection(relevant_test_movies))
            p5_list.append(hits_5 / 5.0)
            
            # Calculate Precision@10
            hits_10 = len(set(rec_ids[:10]).intersection(relevant_test_movies))
            p10_list.append(hits_10 / 10.0)
            
            # Calculate Recall@10
            r10_list.append(hits_10 / len(relevant_test_movies))
            
        self.metrics['Precision@5'] = np.mean(p5_list) if p5_list else 0.0
        self.metrics['Precision@10'] = np.mean(p10_list) if p10_list else 0.0
        self.metrics['Recall@10'] = np.mean(r10_list) if r10_list else 0.0
        self.metrics['Evaluated'] = True
        
        return True
