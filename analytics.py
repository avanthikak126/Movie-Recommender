import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# ==========================================
# Shared chart layout defaults
# ==========================================
_CHART_LAYOUT = dict(
    autosize=True,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(255,255,255,0.03)',
    font=dict(
        family='Inter, sans-serif',
        color='rgba(255,255,255,0.9)',
        size=13,
    ),
    title=dict(
        font=dict(size=16, color='#ffffff'),
        x=0.02,
        xanchor='left',
    ),
    margin=dict(l=16, r=16, t=48, b=16),
    xaxis=dict(
        gridcolor='rgba(255,255,255,0.06)',
        zerolinecolor='rgba(255,255,255,0.08)',
        tickfont=dict(size=11, color='rgba(255,255,255,0.7)'),
        title_font=dict(size=12, color='rgba(255,255,255,0.5)'),
    ),
    yaxis=dict(
        gridcolor='rgba(255,255,255,0.06)',
        zerolinecolor='rgba(255,255,255,0.08)',
        tickfont=dict(size=11, color='rgba(255,255,255,0.7)'),
        title_font=dict(size=12, color='rgba(255,255,255,0.5)'),
    ),
)


def _apply_layout(fig, **overrides):
    """Apply shared layout defaults then any per-chart overrides."""
    layout = {**_CHART_LAYOUT, **overrides}
    fig.update_layout(**layout)
    return fig


# ==========================================
# Genre Distribution (horizontal bar)
# ==========================================
def plot_genre_distribution(movies_df):
    genres_series = movies_df['Genres'].str.split('|').explode()
    genre_counts = genres_series.value_counts().reset_index()
    genre_counts.columns = ['Genre', 'Count']

    fig = px.bar(
        genre_counts, x='Count', y='Genre', orientation='h',
        title='Genre Distribution',
        color='Count', color_continuous_scale='Reds',
    )
    fig.update_coloraxes(showscale=False)
    _apply_layout(
        fig,
        height=460,
        margin=dict(l=16, r=16, t=48, b=16),
        yaxis=dict(
            categoryorder='total ascending',
            gridcolor='rgba(255,255,255,0.04)',
            tickfont=dict(size=11, color='rgba(255,255,255,0.8)'),
        ),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.06)',
            title_text='',
            tickfont=dict(size=11, color='rgba(255,255,255,0.6)'),
        ),
    )
    fig.update_traces(marker_line_width=0)
    return fig


# ==========================================
# Ratings Distribution (vertical bar)
# ==========================================
def plot_ratings_distribution(ratings_df):
    rating_counts = ratings_df['Rating'].value_counts().reset_index().sort_values('Rating')

    fig = px.bar(
        rating_counts, x='Rating', y='count',
        title='Ratings Distribution',
        color='count', color_continuous_scale='Reds',
    )
    fig.update_coloraxes(showscale=False)
    _apply_layout(
        fig,
        height=460,
        xaxis=dict(
            tickmode='linear', tick0=1, dtick=1,
            title_text='Rating',
            gridcolor='rgba(255,255,255,0.04)',
            tickfont=dict(size=12, color='rgba(255,255,255,0.8)'),
        ),
        yaxis=dict(
            title_text='Count',
            gridcolor='rgba(255,255,255,0.06)',
            tickfont=dict(size=11, color='rgba(255,255,255,0.6)'),
        ),
    )
    fig.update_traces(marker_line_width=0)
    return fig


# ==========================================
# Similarity Gauge
# ==========================================
def plot_similarity_gauge(similarity_score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=similarity_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Match Score", 'font': {'size': 14, 'color': 'rgba(255,255,255,0.7)'}},
        number={'font': {'size': 32, 'color': '#ffffff'}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': 'rgba(255,255,255,0.4)'},
            'bar': {'color': '#e50914'},
            'bgcolor': 'rgba(255,255,255,0.05)',
            'steps': [
                {'range': [0, 50], 'color': 'rgba(255,0,0,0.15)'},
                {'range': [50, 80], 'color': 'rgba(255,255,0,0.15)'},
                {'range': [80, 100], 'color': 'rgba(0,255,0,0.15)'},
            ],
            'threshold': {
                'line': {'color': 'white', 'width': 4},
                'thickness': 0.75,
                'value': similarity_score,
            },
        },
    ))
    fig.update_layout(
        autosize=True,
        paper_bgcolor='rgba(255,255,255,0.03)',
        font_color='white',
        height=250,
        margin=dict(l=24, r=24, t=36, b=12),
    )
    return fig


# ==========================================
# Precision Metrics (evaluation bar)
# ==========================================
def plot_precision_metrics(metrics):
    df = pd.DataFrame({
        'Metric': ['Precision@5', 'Precision@10', 'Recall@10'],
        'Value': [metrics['Precision@5'], metrics['Precision@10'], metrics['Recall@10']],
    })

    fig = px.bar(
        df, x='Metric', y='Value', text_auto='.2f',
        title='Evaluation Metrics',
        color='Value', color_continuous_scale='Reds',
    )
    fig.update_coloraxes(showscale=False)
    fig.update_traces(
        textposition='outside',
        textfont=dict(size=12, color='rgba(255,255,255,0.9)'),
        marker_line_width=0,
    )
    _apply_layout(
        fig,
        height=380,
        yaxis_range=[0, 1],
        xaxis=dict(title_text=''),
        yaxis=dict(title_text='Score'),
    )
    return fig


# ==========================================
# Advanced Validation (radar / polar)
# ==========================================
def plot_advanced_validation_metrics(metrics):
    fig = go.Figure()

    categories = ['Precision@10', 'Recall@10', 'User Coverage', 'Catalog Cov.']
    values = [
        metrics.get('Precision@10', 0) * 100,
        metrics.get('Recall@10', 0) * 100,
        metrics.get('User Coverage', 0) * 100,
        metrics.get('Catalog Coverage', 0) * 100,
    ]

    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(229, 9, 20, 0.25)',
        line=dict(color='#e50914', width=3),
        marker=dict(size=6, color='#ff6b6b'),
        name='System Performance',
    ))

    max_val = max(values) if values else 100
    upper_bound = 100 if max_val <= 100 else max_val * 1.2

    fig.update_layout(
        autosize=True,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, upper_bound],
                tickfont=dict(color='rgba(255,255,255,0.5)', size=10),
                gridcolor='rgba(255,255,255,0.08)',
            ),
            angularaxis=dict(
                tickfont=dict(color='rgba(255,255,255,0.9)', size=12),
                gridcolor='rgba(255,255,255,0.08)',
            ),
            bgcolor='rgba(0,0,0,0)',
        ),
        paper_bgcolor='rgba(255,255,255,0.03)',
        font=dict(family='Inter, sans-serif', color='white'),
        height=420,
        margin=dict(l=60, r=60, t=40, b=40),
        showlegend=False,
    )
    return fig


# ==========================================
# Query Benchmark (Ball Tree vs Brute Force)
# ==========================================
def plot_query_benchmark(ball_tree_time, brute_force_time):
    df = pd.DataFrame({
        'Method': ['Ball Tree', 'Brute Force'],
        'Time (sec)': [ball_tree_time, brute_force_time],
    })

    fig = px.bar(
        df,
        x='Method',
        y='Time (sec)',
        title='Query Execution Time Comparison',
        color='Method',
        color_discrete_map={'Ball Tree': '#46d369', 'Brute Force': '#e50914'},
        text=[f'{ball_tree_time:.3f}s', f'{brute_force_time:.3f}s'],
    )
    fig.update_traces(
        textposition='outside',
        textfont=dict(size=13, color='rgba(255,255,255,0.9)'),
        marker_line_width=0,
    )
    _apply_layout(
        fig,
        height=380,
        showlegend=False,
        yaxis_title='Execution Time (seconds)',
        xaxis_title='',
    )
    return fig
