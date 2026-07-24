# Recflix - Movie Recommender

Recflix is a movie recommendation web application built with Streamlit. It provides personalized movie recommendations, user authentication, analytics, and integrates with the TMDB API to fetch movie details.

## Features

- **Personalized Recommendations**: Uses machine learning (collaborative filtering and content-based filtering) to suggest movies.
- **User Authentication**: Secure user registration and login system.
- **TMDB Integration**: Fetches up-to-date movie metadata, posters, and details from the TMDB API.
- **Analytics & Dashboards**: View recommendation metrics and user analytics.
- **Interactive UI**: Built with Streamlit for a fast and interactive user experience.

## Project Structure

- `app.py`: Main entry point for the Streamlit application.
- `recommender.py` / `content_recommender.py`: Core recommendation engine logic.
- `tmdb.py`: Integration with TMDB API.
- `database.py`: Database models and connection setup using SQLAlchemy.
- `auth.py`: User authentication and session management.
- `analytics.py`: Data visualization and analytics dashboards.
- `evaluation.py`: Model evaluation and metrics.
- `requirements.txt`: Python dependencies.

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Recflix
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the root directory and add any required API keys (e.g., TMDB API key) and database credentials.

## Usage

Run the Streamlit application locally:

```bash
streamlit run app.py
```

The application will open in your default web browser (typically at `http://localhost:8501`).

## Dependencies

See `requirements.txt` for the full list of dependencies, which include:
- `streamlit`
- `pandas`
- `scikit-learn`
- `sqlalchemy`
- `requests`
- `plotly`
