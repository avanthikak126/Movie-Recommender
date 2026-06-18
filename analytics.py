import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def plot_genre_distribution(movies_df):
    # Split genres and count
    genres_series = movies_df['Genres'].str.split('|').explode()
    genre_counts = genres_series.value_counts().reset_index()
    genre_counts.columns = ['Genre', 'Count']
    
    fig = px.bar(genre_counts, x='Count', y='Genre', orientation='h', 
                 title='Genre Distribution',
                 color='Count', color_continuous_scale='Reds')
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        yaxis={'categoryorder':'total ascending'}
    )
    return fig

def plot_ratings_distribution(ratings_df):
    rating_counts = ratings_df['Rating'].value_counts().reset_index().sort_values('Rating')
    
    fig = px.bar(rating_counts, x='Rating', y='count', 
                 title='Ratings Distribution',
                 color='count', color_continuous_scale='Reds')
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        xaxis=dict(tickmode='linear', tick0=1, dtick=1)
    )
    return fig

def plot_similarity_gauge(similarity_score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = similarity_score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Match Score"},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': "#e50914"},
            'bgcolor': "rgba(255,255,255,0.1)",
            'steps': [
                {'range': [0, 50], 'color': "rgba(255,0,0,0.2)"},
                {'range': [50, 80], 'color': "rgba(255,255,0,0.2)"},
                {'range': [80, 100], 'color': "rgba(0,255,0,0.2)"}],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': similarity_score}
        }
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=250
    )
    return fig

def plot_precision_metrics(metrics):
    df = pd.DataFrame({
        'Metric': ['Precision@5', 'Precision@10', 'Recall@10'],
        'Value': [metrics['Precision@5'], metrics['Precision@10'], metrics['Recall@10']]
    })
    
    fig = px.bar(df, x='Metric', y='Value', text_auto='.2f',
                 title='Evaluation Metrics',
                 color='Value', color_continuous_scale='Reds')
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        yaxis_range=[0,1]
    )
    return fig
