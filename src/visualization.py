"""
Visualization utilities for the Streamlit dashboard using Plotly.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os

# Professional dark theme colors
COLORS = {
    'primary':    '#63b3ed',
    'secondary':  '#4fd1c5',
    'accent':     '#f6ad55',
    'success':    '#68d391',
    'bg_dark':    '#1a202c',
    'bg_card':    '#2d3748',
    'text_light': '#e2e8f0',
    'text_muted': '#a0aec0',
}

PLOTLY_TEMPLATE = dict(
    layout=go.Layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', color=COLORS['text_light']),
        xaxis=dict(gridcolor='#2d3748', zerolinecolor='#2d3748'),
        yaxis=dict(gridcolor='#2d3748', zerolinecolor='#2d3748'),
        margin=dict(l=20, r=20, t=50, b=20),
    )
)

def plot_topic_distribution(topic_dist: np.ndarray, topic_names: dict) -> go.Figure:
    """
    Bar chart of topic probability distribution for a prediction.
    
    Args:
        topic_dist (np.ndarray): Array of topic probabilities.
        topic_names (dict): Mapping from topic index to topic name.
        
    Returns:
        go.Figure: Plotly figure.
    """
    best_topic_id = int(np.argmax(topic_dist))
    
    colors = [
        COLORS['success'] if i == best_topic_id else COLORS['primary']
        for i in range(len(topic_dist))
    ]
    
    fig = go.Figure(go.Bar(
        x=list(topic_names.values()),
        y=topic_dist,
        marker=dict(color=colors, opacity=0.85),
        text=[f"{d:.1%}" for d in topic_dist],
        textposition='outside',
        textfont=dict(size=10),
    ))
    
    fig.update_layout(
        **PLOTLY_TEMPLATE['layout'].to_plotly_json(),
        title="Topic Probability Distribution",
        xaxis_title="",
        yaxis_title="Probability",
        height=350,
        xaxis_tickangle=-45,
    )
    return fig

def plot_ablation_comparison(results_path: str | None = None) -> go.Figure:
    """
    Ablation study bar chart.
    
    Args:
        results_path (str, optional): Path to results CSV. Defaults to None.
        
    Returns:
        go.Figure: Plotly figure.
    """
    # Use default data if path not provided or file doesn't exist
    if results_path and os.path.exists(results_path):
        df = pd.read_csv(results_path)
    else:
        df = pd.DataFrame({
            'Model': ['LDA (Baseline)', 'BERTopic', 'Hybrid (Proposed)'],
            'Coherence': [0.3573, 0.4781, 0.4981]
        })
        
    colors = [COLORS['primary'], COLORS['secondary'], COLORS['success']]
    
    fig = go.Figure(go.Bar(
        x=df['Model'],
        y=df['Coherence'],
        marker=dict(color=colors, opacity=0.9),
        text=[f"{c:.4f}" for c in df['Coherence']],
        textposition='outside',
        textfont=dict(size=14, color=COLORS['text_light']),
    ))
    
    fig.update_layout(
        **PLOTLY_TEMPLATE['layout'].to_plotly_json(),
        title="Topic Coherence Score (C_v) — Higher is Better",
        yaxis_title="Coherence Score",
        height=420,
    )
    fig.update_yaxes(range=[0, 0.6])
    
    return fig

def plot_category_distribution(df: pd.DataFrame) -> go.Figure:
    """
    News category distribution bar chart.
    
    Args:
        df (pd.DataFrame): Dataset containing 'category' column.
        
    Returns:
        go.Figure: Plotly figure.
    """
    cat_counts = df['category'].value_counts().head(15)
    
    fig = go.Figure(go.Bar(
        x=cat_counts.index,
        y=cat_counts.values,
        marker_color=COLORS['primary']
    ))
    
    fig.update_layout(
        **PLOTLY_TEMPLATE['layout'].to_plotly_json(),
        title="Top 15 News Categories",
        xaxis_tickangle=-45,
    )
    return fig

def plot_model_comparison_table(results_path: str | None = None) -> pd.DataFrame:
    """
    Returns a formatted comparison table DataFrame.
    
    Args:
        results_path (str, optional): Path to results CSV.
        
    Returns:
        pd.DataFrame: Formatted comparison table.
    """
    if results_path and os.path.exists(results_path):
        return pd.read_csv(results_path)
        
    # Default ablation data
    return pd.DataFrame({
        'Model':     ['LDA (Baseline)', 'BERTopic', 'Hybrid (Proposed)'],
        'Type':      ['Traditional ML', 'Deep Learning', 'Hybrid Approach'],
        'Coherence': [0.3573, 0.4781, 0.4981],
        'Temporal':  ['No', 'No', 'Yes'],
        'GDELT':     ['No', 'No', 'Yes'],
    })
