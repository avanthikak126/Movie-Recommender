import os

# Limit BLAS/OpenMP threads (helps avoid native crashes on Streamlit Cloud)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import pandas as pd

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

        print("========== LOAD DATA START ==========")

        movies_path = os.path.join(DATA_DIR, "movies.dat")

        print("STEP L1: Checking file:", movies_path)

        if not os.path.exists(movies_path):
            raise FileNotFoundError(
                f"Movie file missing: {movies_path}"
            )

        print("STEP L2: Reading movies.dat")

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

        print("STEP L3: Movies loaded:", len(self.movies_df))

        genres = (
            self.movies_df["Genres"]
            .fillna("")
            .str.replace(
                "|",
                " ",
                regex=False
            )
        )

        print("STEP L4: Creating Content column")

        self.movies_df["Content"] = (
            self.movies_df["Title"].fillna("")
            + " "
            + genres
        )

        print("========== LOAD DATA FINISHED ==========")

        return True


    def build_model(self):

        try:
            print("========== BUILD MODEL START ==========")

            print("STEP 1: Checking data")

            if self.movies_df is None:
                print("STEP 2: Calling load_data()")
                self.load_data()

            print("STEP 3: Data loaded")

            print("STEP 4: Creating TF-IDF Vectorizer")

            self.vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=5000
            )

            print("STEP 5: Vectorizer created")

            print("STEP 6: Starting fit_transform()")

            self.tfidf_matrix = self.vectorizer.fit_transform(
                self.movies_df["Content"]
            )

            print("STEP 7: fit_transform() completed")
            print("TF-IDF Shape:", self.tfidf_matrix.shape)

            print("STEP 8: Building movie index")

            self.movie_id_to_index = {
                int(movie_id): index
                for index, movie_id in enumerate(
                    self.movies_df["MovieID"]
                )
            }

            print("STEP 9: Movie index completed")

            print("========== BUILD MODEL FINISHED ==========")

            return True

        except Exception as e:
            print("ERROR OCCURRED")
            print(e)

            import traceback
            traceback.print_exc()

            return False


    def get_content_recommendations(
            self,
            movie_id,
            n=10
    ):

        print("Recommendation requested:", movie_id)

        if self.tfidf_matrix is None:
            self.build_model()

        movie_id = int(movie_id)

        if movie_id not in self.movie_id_to_index:
            return []

        idx = self.movie_id_to_index[movie_id]

        print("STEP R1: Computing cosine similarity")

        similarity_scores = cosine_similarity(
            self.tfidf_matrix[idx],
            self.tfidf_matrix
        ).flatten()

        print("STEP R2: Similarity computed")

        similar_movies = sorted(
            enumerate(similarity_scores),
            key=lambda x: x[1],
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

        print("STEP R3: Recommendations ready")

        return recommendations