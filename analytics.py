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

def plot_advanced_validation_metrics(metrics):
    fig = go.Figure()
    
    categories = ['Precision@10', 'Recall@10', 'User Coverage', 'Catalog Cov.']
    values = [
        metrics.get('Precision@10', 0)*100,
        metrics.get('Recall@10', 0)*100,
        metrics.get('User Coverage', 0)*100,
        metrics.get('Catalog Coverage', 0)*100
    ]
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(229, 9, 20, 0.4)',
        line=dict(color='#e50914', width=3),
        name='System Performance'
    ))

    # Determine a good max scale. Usually 100, unless scores are tiny.
    max_val = max(values) if values else 100
    upper_bound = 100 if max_val <= 100 else max_val * 1.2

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, upper_bound],
                tickfont=dict(color="rgba(255, 255, 255, 0.7)"),
                gridcolor="rgba(255, 255, 255, 0.1)"
            ),
            angularaxis=dict(
                tickfont=dict(color="white", size=14, weight="bold"),
                gridcolor="rgba(255, 255, 255, 0.1)"
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        height=400,
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig
