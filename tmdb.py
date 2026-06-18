import os
import requests
import json
import re
import difflib
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

CACHE_FILE = "data/cache/tmdb_cache.json"

class TMDbClient:
    def __init__(self):
        self.api_key = TMDB_API_KEY
        self.cache = self._load_cache()
        self.headers = {
            "accept": "application/json"
        }
        if self.api_key:
            if len(self.api_key) > 50:
                self.headers["Authorization"] = f"Bearer {self.api_key}"
                self.api_key_param = ""
            else:
                self.api_key_param = f"?api_key={self.api_key}"
        else:
            self.api_key_param = ""

    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f)

    def _parse_title(self, ml_title):
        match = re.match(r"^(.*) \((\d{4})\)$", ml_title)
        if match:
            return match.group(1).strip(), match.group(2)
        return ml_title.strip(), None

    def _get_fallback_poster(self):
        return "https://via.placeholder.com/500x750/1d1e26/e50914?text=No+Poster+Found"

    def _get_fallback_movie(self, title):
        return {
            "title": title,
            "overview": "Synopsis unavailable.",
            "poster_url": self._get_fallback_poster(),
            "id": None
        }

    def _fetch_from_api(self, query, year=None):
        if not self.api_key:
            return []
            
        url = f"{TMDB_BASE_URL}/search/movie"
        if self.api_key_param:
            url += self.api_key_param
            
        req_params = {"query": query}
        if year:
            req_params["year"] = year
            
        try:
            response = requests.get(url, headers=self.headers, params=req_params)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            return []

    def _fuzzy_match_results(self, target_title, results):
        if not results:
            return None
            
        # Get titles from results
        result_titles = [r.get('title', '') for r in results]
        
        # Use difflib to find the closest match
        matches = difflib.get_close_matches(target_title, result_titles, n=1, cutoff=0.4)
        if matches:
            best_match_title = matches[0]
            # Return the full result object for that title
            for r in results:
                if r.get('title') == best_match_title:
                    return r
        
        # If no fuzzy match > cutoff, just return the first one (TMDB's best guess)
        return results[0]

    def get_movie_details(self, ml_title, debug=False):
        if ml_title in self.cache:
            if debug:
                movie = self.cache[ml_title]
                print(f"Movie: {ml_title}")
                print(f"TMDB Query: (Cached)")
                print(f"Results Returned: N/A")
                print(f"Selected TMDB ID: {movie.get('id')}")
                print(f"Poster Found: {'Yes' if 'via.placeholder.com' not in movie.get('poster_url', '') else 'No'}\n")
            return self.cache[ml_title]

        if not self.api_key:
            return self._get_fallback_movie(ml_title)

        # 1. Remove year from title
        title, year = self._parse_title(ml_title)
        
        # Strategies
        # 2. Search using title + year
        # 3. Search title only
        # 4. Strip alternative titles (e.g. "Seven (Se7en)" -> "Seven")
        clean_title = re.sub(r'\(.*?\)', '', title).strip() # Removes (Se7en)
        
        strategies = [
            (title, year, "Title + Year"),
            (title, None, "Title Only"),
            (clean_title, year, "Clean Title + Year"),
            (clean_title, None, "Clean Title Only")
        ]
        
        found_movie = None
        for q_title, q_year, strategy_name in strategies:
            if not q_title:
                continue
                
            results = self._fetch_from_api(q_title, q_year)
            
            if results:
                # 4. Use fuzzy matching to pick the best result
                found_movie = self._fuzzy_match_results(title, results)
                if found_movie:
                    if debug:
                        print(f"Movie: {ml_title}")
                        print(f"TMDB Query: {q_title} (Year: {q_year}) [{strategy_name}]")
                        print(f"Results Returned: {len(results)}")
                        print(f"Selected TMDB ID: {found_movie.get('id')}")
                        poster_found = found_movie.get('poster_path') is not None
                        print(f"Poster Found: {'Yes' if poster_found else 'No'}\n")
                    break
                    
        if found_movie:
            if found_movie.get("poster_path"):
                found_movie["poster_url"] = f"{IMAGE_BASE_URL}{found_movie['poster_path']}"
            else:
                found_movie["poster_url"] = self._get_fallback_poster()
                
            self.cache[ml_title] = found_movie
            self._save_cache()
            return found_movie
        else:
            if debug:
                print(f"Movie: {ml_title}")
                print(f"TMDB Query: {clean_title}")
                print(f"Results Returned: 0")
                print(f"Reason: No TMDB Match\n")
                
            fallback = self._get_fallback_movie(title)
            self.cache[ml_title] = fallback
            self._save_cache()
            return fallback

    def get_similar_movies(self, tmdb_id):
        if not self.api_key or not tmdb_id:
            return []
            
        cache_key = f"similar_{tmdb_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        url = f"{TMDB_BASE_URL}/movie/{tmdb_id}/similar"
        if self.api_key_param:
            url += self.api_key_param
            
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])[:10]
            for r in results:
                if r.get("poster_path"):
                    r["poster_url"] = f"{IMAGE_BASE_URL}{r['poster_path']}"
                else:
                    r["poster_url"] = self._get_fallback_poster()
                    
            self.cache[cache_key] = results
            self._save_cache()
            return results
        except Exception as e:
            pass
            
        return []

tmdb_client = TMDbClient()
