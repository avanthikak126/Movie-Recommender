import os
import pandas as pd
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_DIR = "data/ml-1m"


class ContentRecommender:
    def __init__(self):
        self.movies_df = None
        self.tfidf_matrix = None
        self.movie_id_to_index = {}

    def load_data(self):
        try:
            print("========== CONTENT RECOMMENDER DEBUG ==========")
            print("Current directory:", os.getcwd())
            print("Files in directory:", os.listdir())
            
            movies_path = os.path.join(DATA_DIR, "movies.dat")

            print("Looking for:", movies_path)
            print("File exists:", os.path.exists(movies_path))

            if not os.path.exists(movies_path):
                raise FileNotFoundError(
                    f"movies.dat not found at {movies_path}"
                )

            print("Loading movies file...")

            self.movies_df = pd.read_csv(
                movies_path,
                sep="::",
                engine="python",
                names=["MovieID", "Title", "Genres"],
                encoding="latin-1"
            )

            print("Movies loaded:", len(self.movies_df))

            print("Creating content features...")

            genres_spaced = self.movies_df["Genres"].str.replace(
                "|",
                " ",
                regex=False
            )

            self.movies_df["Content"] = (
                self.movies_df["Title"] + " " + genres_spaced
            )

            print("Content features created")
            print("==============================================")

            return True

        except Exception as e:
            print("LOAD DATA ERROR:")
            print(e)
            raise e


    def build_model(self):
        try:
            print("Building Content Recommender...")

            if self.movies_df is None:
                print("Loading data first...")
                self.load_data()

            print("Creating TF-IDF matrix...")

            vectorizer = TfidfVectorizer(
                stop_words="english"
            )

            self.tfidf_matrix = vectorizer.fit_transform(
                self.movies_df["Content"]
            )

            print(
                "TF-IDF shape:",
                self.tfidf_matrix.shape
            )

            self.movie_id_to_index = {
                movie_id: idx
                for idx, movie_id in enumerate(
                    self.movies_df["MovieID"]
                )
            }

            print("Movie index created")
            print("Content recommender ready")

            return True

        except Exception as e:
            print("BUILD MODEL ERROR:")
            print(e)
            raise e


    def get_content_recommendations(self, movie_id, n=10):
        try:
            print(
                "Getting recommendations for:",
                movie_id
            )

            if self.tfidf_matrix is None:
                self.build_model()

            if movie_id not in self.movie_id_to_index:
                print("Movie not found")
                return []

            idx = self.movie_id_to_index[movie_id]

            cosine_sim_vector = cosine_similarity(
                self.tfidf_matrix[idx],
                self.tfidf_matrix
            ).flatten()

            scores = list(
                enumerate(cosine_sim_vector)
            )

            scores = sorted(
                scores,
                key=lambda x: x[1],
                reverse=True
            )

            scores = [
                x for x in scores
                if x[0] != idx
            ][:n]

            recommendations = []

            for movie_idx, score in scores:
                movie = self.movies_df.iloc[movie_idx]

                recommendations.append(
                    {
                        "MovieID": int(movie["MovieID"]),
                        "Title": movie["Title"],
                        "Genres": movie["Genres"],
                        "Content Similarity Score": float(score)
                    }
                )

            return recommendations

        except Exception as e:
            print("RECOMMENDATION ERROR:")
            print(e)
            raise e