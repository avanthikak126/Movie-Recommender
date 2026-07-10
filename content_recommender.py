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
        self.vectorizer = None


    def load_data(self):

        print("CONTENT: Loading data...")

        movies_path = os.path.join(DATA_DIR, "movies.dat")

        print("CONTENT: Checking file:", movies_path)

        if not os.path.exists(movies_path):
            raise FileNotFoundError(
                f"Movie file missing: {movies_path}"
            )


        self.movies_df = pd.read_csv(
            movies_path,
            sep="::",
            engine="python",
            names=[
                "MovieID",
                "Title",
                "Genres"
            ],
            encoding="latin-1"
        )


        print(
            "CONTENT: Movies loaded:",
            len(self.movies_df)
        )


        genres = (
            self.movies_df["Genres"]
            .fillna("")
            .str.replace(
                "|",
                " ",
                regex=False
            )
        )


        self.movies_df["Content"] = (
            self.movies_df["Title"].fillna("")
            + " "
            + genres
        )


        print("CONTENT: Text features created")

        return True



    def build_model(self):

        print("CONTENT: Building model...")


        if self.movies_df is None:
            self.load_data()


        print("CONTENT: Starting TF-IDF")


        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000
        )


        self.tfidf_matrix = self.vectorizer.fit_transform(
            self.movies_df["Content"]
        )


        print(
            "CONTENT: TF-IDF completed:",
            self.tfidf_matrix.shape
        )


        self.movie_id_to_index = {
            int(movie_id): index
            for index, movie_id in enumerate(
                self.movies_df["MovieID"]
            )
        }


        print("CONTENT: Model ready")

        return True



    def get_content_recommendations(
            self,
            movie_id,
            n=10
    ):

        print(
            "CONTENT: Recommendation request:",
            movie_id
        )


        if self.tfidf_matrix is None:
            self.build_model()



        movie_id = int(movie_id)


        if movie_id not in self.movie_id_to_index:
            return []



        idx = self.movie_id_to_index[movie_id]


        similarity_scores = cosine_similarity(
            self.tfidf_matrix[idx],
            self.tfidf_matrix
        ).flatten()



        similar_movies = sorted(
            enumerate(similarity_scores),
            key=lambda x:x[1],
            reverse=True
        )


        recommendations = []


        for movie_index, score in similar_movies:

            if movie_index == idx:
                continue


            movie = self.movies_df.iloc[movie_index]


            recommendations.append(
                {
                    "MovieID": int(movie["MovieID"]),
                    "Title": movie["Title"],
                    "Genres": movie["Genres"],
                    "Content Similarity Score": float(score)
                }
            )


            if len(recommendations) == n:
                break



        return recommendations