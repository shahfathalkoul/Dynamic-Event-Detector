"""
Dynamic Trend & Event Detector — Interactive Dashboard
======================================================
A multi-tab Streamlit application for detecting emerging topics from
news articles using LDA topic modeling, with EDA visualizations,
model comparison, and temporal analysis.

Author: Shah Fathal Koul
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import re
import nltk
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

# ─────────────────────────────────────────────────────────────
# NLTK SETUP
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def _download_nltk_data():
    """Download required NLTK resources (cached to avoid re-downloading)."""
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)

_download_nltk_data()

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


# ─────────────────────────────────────────────────────────────
# PAGE CONFIG & THEME
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dynamic Trend & Event Detector",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional dark-themed styling
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 2rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    .main-header h1 {
        color: #ffffff;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #94a3b8;
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2d3748;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
    .metric-card h3 {
        color: #63b3ed;
        font-size: 1.8rem;
        margin: 0;
        font-weight: 700;
    }
    .metric-card p {
        color: #a0aec0;
        font-size: 0.85rem;
        margin: 0.3rem 0 0 0;
    }

    /* Result card */
    .result-card {
        background: linear-gradient(135deg, #0d3b2e 0%, #1a4a3a 100%);
        border: 1px solid #2d6a4f;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .result-card h3 {
        color: #4ade80;
        margin: 0 0 0.5rem 0;
    }

    /* Section headers */
    .section-header {
        color: #e2e8f0;
        font-size: 1.1rem;
        font-weight: 600;
        border-bottom: 2px solid #2d3748;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0 1rem 0;
    }

    /* Sidebar styling */
    .sidebar-badge {
        display: inline-block;
        background: #2d3748;
        color: #63b3ed;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        margin: 0.15rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px;
        font-weight: 500;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>📰 Dynamic Trend & Event Detector</h1>
    <p>Emerging Topic Detection & News Correlation using NLP & Deep Learning</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 About This Project")
    st.markdown(
        "This system detects emerging topics from large-scale news articles "
        "and classifies trends as **real-world events** vs. **short-lived viral topics** "
        "using a hybrid NLP pipeline."
    )

    st.markdown("---")
    st.markdown("### 🛠️ Tech Stack")
    tech_items = [
        "Python", "Streamlit", "scikit-learn", "BERTopic",
        "Sentence-BERT", "UMAP", "HDBSCAN", "GDELT API",
        "Plotly", "NLTK", "Gensim"
    ]
    badges_html = " ".join(
        f'<span class="sidebar-badge">{t}</span>' for t in tech_items
    )
    st.markdown(badges_html, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Key Results")
    st.metric("Hybrid Coherence", "0.4981", "+39.4% vs LDA")
    st.metric("BERTopic Coherence", "0.4781", "+33.8% vs LDA")
    st.metric("LDA Baseline", "0.3573")

    st.markdown("---")
    st.markdown("### 📂 Dataset")
    st.markdown(
        "**Kaggle** — [News Category Dataset]"
        "(https://www.kaggle.com/datasets/rmisra/news-category-dataset)  \n"
        "209,527 articles (2012–2022)"
    )

    st.markdown("---")
    st.markdown(
        "<p style='color: #64748b; font-size: 0.75rem; text-align: center;'>"
        "Built by Shah Fathal Koul</p>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# DATA & MODEL LOADING
# ─────────────────────────────────────────────────────────────
_lemmatizer = WordNetLemmatizer()
_stop_words = set(stopwords.words('english'))
_custom_stops = {'new', 'say', 'said', 'make', 'one', 'would', 'could', 'also', 'get', 'like', 'time', 'year', 'day', 'first', 'people', 'two', 'know', 'want', 'even', 'take'}
_stop_words = _stop_words.union(_custom_stops)


def clean_text(text: str) -> str:
    """Preprocess text: lowercase, remove URLs/non-alpha, lemmatize, drop stopwords."""
    text = str(text).lower()
    text = re.sub(r'http\S+|[^a-z\s]', '', text)
    words = [
        _lemmatizer.lemmatize(w)
        for w in text.split()
        if w not in _stop_words and len(w) > 2
    ]
    return ' '.join(words)


@st.cache_resource
def load_data():
    """Load the cleaned news dataset."""
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'clean_data.csv')
    return pd.read_csv(data_path)


@st.cache_resource
def train_model():
    """Train an LDA model on a sample of the real news dataset."""
    df = load_data()
    df_sample = df.sample(n=min(10000, len(df)), random_state=42).copy()
    docs = df_sample['clean_text'].fillna('').tolist()

    vectorizer = CountVectorizer(max_features=2000, min_df=5, max_df=0.9)
    dtm = vectorizer.fit_transform(docs)

    lda = LatentDirichletAllocation(
        n_components=15,
        random_state=42,
        max_iter=15,
    )
    lda.fit(dtm)

    vocab = vectorizer.get_feature_names_out()
    topic_names = {}
    for i, topic in enumerate(lda.components_):
        top_words = [vocab[j] for j in topic.argsort()[-5:][::-1]]
        topic_names[i] = f"Topic {i + 1}: " + ", ".join(top_words).title()

    return lda, vectorizer, topic_names


# Load everything
with st.spinner("Loading data and training model — this may take a moment on first run..."):
    full_df = load_data()
    lda_model, vectorizer, topic_names = train_model()


def predict_topic(text: str):
    """Predict the topic of a given text. Returns (topic_id, topic_dist) or (None, None)."""
    clean = clean_text(text)
    if not clean.strip():
        return None, None
    vec = vectorizer.transform([clean])
    topic_dist = lda_model.transform(vec)[0]
    best_topic_id = np.argmax(topic_dist)
    return best_topic_id, topic_dist


# ─────────────────────────────────────────────────────────────
# COLOR PALETTE
# ─────────────────────────────────────────────────────────────
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


# ═══════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 Topic Detection",
    "📊 EDA & Insights",
    "🧠 Model Comparison",
    "📈 Temporal Analysis",
])

# ───────────────────────────────────────
# TAB 1 — TOPIC DETECTION (Live Demo)
# ───────────────────────────────────────
with tab1:
    col_input, col_result = st.columns([3, 2])

    with col_input:
        st.markdown('<p class="section-header">Enter a News Headline or Article Snippet</p>', unsafe_allow_html=True)
        user_input = st.text_area(
            "Type or paste text here:",
            placeholder="e.g., The stock market saw a massive crash today as tech companies reported lower than expected earnings...",
            height=150,
            label_visibility="collapsed",
        )

        detect_clicked = st.button("🚀 Detect Topic", type="primary", use_container_width=True)

    with col_result:
        st.markdown('<p class="section-header">Discovered Topics</p>', unsafe_allow_html=True)
        st.markdown("The model dynamically discovered these topics from the real dataset:")
        for t_id, t_name in topic_names.items():
            st.markdown(f"- **{t_name}**")

    if detect_clicked:
        if user_input.strip():
            topic_id, dist = predict_topic(user_input)
            if topic_id is not None:
                st.markdown("---")
                res_col1, res_col2 = st.columns([1, 2])

                with res_col1:
                    confidence = dist[topic_id] * 100
                    st.markdown(
                        f"""<div class="result-card">
                            <h3>✅ {topic_names[topic_id]}</h3>
                            <p style="color: #e2e8f0;">Confidence: <strong>{confidence:.1f}%</strong></p>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                with res_col2:
                    # Topic probability distribution chart
                    fig = go.Figure(go.Bar(
                        x=list(topic_names.values()),
                        y=dist,
                        marker=dict(
                            color=[
                                COLORS['success'] if i == topic_id else COLORS['primary']
                                for i in range(len(dist))
                            ],
                            opacity=0.85,
                        ),
                        text=[f"{d:.1%}" for d in dist],
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
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(
                    "The text didn't contain enough meaningful keywords to detect a topic. "
                    "Please provide more context."
                )
        else:
            st.warning("Please enter some text to analyze!")


# ───────────────────────────────────────
# TAB 2 — EDA & INSIGHTS
# ───────────────────────────────────────
with tab2:
    # Dataset overview metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="metric-card"><h3>{len(full_df):,}</h3><p>Total Articles</p></div>',
            unsafe_allow_html=True,
        )
    with m2:
        n_categories = full_df['category'].nunique() if 'category' in full_df.columns else 0
        st.markdown(
            f'<div class="metric-card"><h3>{n_categories}</h3><p>News Categories</p></div>',
            unsafe_allow_html=True,
        )
    with m3:
        if 'date' in full_df.columns:
            try:
                dates = pd.to_datetime(full_df['date'], errors='coerce')
                year_range = f"{dates.dt.year.min():.0f}–{dates.dt.year.max():.0f}"
            except Exception:
                year_range = "N/A"
        else:
            year_range = "N/A"
        st.markdown(
            f'<div class="metric-card"><h3>{year_range}</h3><p>Date Range</p></div>',
            unsafe_allow_html=True,
        )
    with m4:
        avg_len = full_df['clean_text'].dropna().str.split().str.len().mean()
        st.markdown(
            f'<div class="metric-card"><h3>{avg_len:.0f}</h3><p>Avg Words/Article</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # EDA Graphs in 2-column layout
    eda_col1, eda_col2 = st.columns(2)

    graphs_dir = os.path.join(os.path.dirname(__file__), 'graphs')

    with eda_col1:
        st.markdown('<p class="section-header">📊 Category Distribution</p>', unsafe_allow_html=True)
        eda1_path = os.path.join(graphs_dir, 'eda1_categories.png')
        if os.path.exists(eda1_path):
            st.image(eda1_path, use_container_width=True)

        st.markdown('<p class="section-header">📈 Word Count Distribution</p>', unsafe_allow_html=True)
        eda3_path = os.path.join(graphs_dir, 'eda3_wordcount.png')
        if os.path.exists(eda3_path):
            st.image(eda3_path, use_container_width=True)

    with eda_col2:
        st.markdown('<p class="section-header">📅 Articles Over Time</p>', unsafe_allow_html=True)
        eda2_path = os.path.join(graphs_dir, 'eda2_yearly.png')
        if os.path.exists(eda2_path):
            st.image(eda2_path, use_container_width=True)

        st.markdown('<p class="section-header">🔤 Most Frequent Words</p>', unsafe_allow_html=True)
        eda4_path = os.path.join(graphs_dir, 'eda4_topwords.png')
        if os.path.exists(eda4_path):
            st.image(eda4_path, use_container_width=True)


# ───────────────────────────────────────
# TAB 3 — MODEL COMPARISON
# ───────────────────────────────────────
with tab3:
    st.markdown('<p class="section-header">Ablation Study — Model Comparison</p>', unsafe_allow_html=True)

    # Ablation data
    ablation_data = {
        'Model':     ['LDA (Baseline)', 'BERTopic', 'Hybrid (Proposed)'],
        'Type':      ['Traditional ML', 'Deep Learning', 'Hybrid Approach'],
        'Coherence': [0.3573, 0.4781, 0.4981],
        'Temporal':  ['No', 'No', 'Yes'],
        'GDELT':     ['No', 'No', 'Yes'],
    }
    ablation_df = pd.DataFrame(ablation_data)

    comp_col1, comp_col2 = st.columns([3, 2])

    with comp_col1:
        # Interactive ablation chart
        colors_bar = [COLORS['primary'], COLORS['secondary'], COLORS['success']]
        fig_ablation = go.Figure(go.Bar(
            x=ablation_df['Model'],
            y=ablation_df['Coherence'],
            marker=dict(color=colors_bar, opacity=0.9),
            text=[f"{c:.4f}" for c in ablation_df['Coherence']],
            textposition='outside',
            textfont=dict(size=14, color=COLORS['text_light']),
        ))
        fig_ablation.update_layout(
            **PLOTLY_TEMPLATE['layout'].to_plotly_json(),
            title="Topic Coherence Score (C_v) — Higher is Better",
            yaxis_title="Coherence Score",
            height=420,
        )
        fig_ablation.update_yaxes(range=[0, 0.6])
        # Add improvement annotation
        fig_ablation.add_annotation(
            x='Hybrid (Proposed)', y=0.52,
            text="<b>+39.4% improvement</b><br>over LDA baseline",
            showarrow=True, arrowhead=2,
            font=dict(color=COLORS['success'], size=12),
            arrowcolor=COLORS['success'],
            ax=0, ay=-40,
        )
        st.plotly_chart(fig_ablation, use_container_width=True)

    with comp_col2:
        st.markdown('<p class="section-header">Comparison Details</p>', unsafe_allow_html=True)

        # Styled metrics
        for _, row in ablation_df.iterrows():
            temporal_icon = "✅" if row['Temporal'] == 'Yes' else "❌"
            gdelt_icon = "✅" if row['GDELT'] == 'Yes' else "❌"
            st.markdown(
                f"""<div class="metric-card" style="margin-bottom: 0.8rem;">
                    <h3 style="font-size: 1.4rem;">{row['Coherence']:.4f}</h3>
                    <p><strong>{row['Model']}</strong></p>
                    <p style="font-size: 0.78rem;">{row['Type']} · Temporal: {temporal_icon} · GDELT: {gdelt_icon}</p>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # LDA Topics Visualization
    st.markdown('<p class="section-header">LDA Topic Word Distributions</p>', unsafe_allow_html=True)
    lda_path = os.path.join(graphs_dir, 'lda_topics.png')
    if os.path.exists(lda_path):
        st.image(lda_path, use_container_width=True)


# ───────────────────────────────────────
# TAB 4 — TEMPORAL ANALYSIS
# ───────────────────────────────────────
with tab4:
    temp_col1, temp_col2 = st.columns(2)

    with temp_col1:
        st.markdown('<p class="section-header">Semantic Velocity — Topic Growth Rate</p>', unsafe_allow_html=True)
        velocity_path = os.path.join(graphs_dir, 'semantic_velocity.png')
        if os.path.exists(velocity_path):
            st.image(velocity_path, use_container_width=True)

        st.markdown(
            "> **Semantic velocity** measures how rapidly a topic's discussion frequency "
            "changes over time. Higher velocity indicates fast-emerging trends that may "
            "correspond to breaking news events."
        )

    with temp_col2:
        st.markdown('<p class="section-header">Topics Over Time (Interactive)</p>', unsafe_allow_html=True)
        topics_html_path = os.path.join(graphs_dir, 'topics_over_time.html')
        if os.path.exists(topics_html_path):
            with open(topics_html_path, 'r') as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=500, scrolling=True)
        else:
            st.info("Interactive temporal visualization not available. Run the BERTopic notebook to generate it.")

    st.markdown("---")

    # GDELT Verification Section
    st.markdown('<p class="section-header">🌍 GDELT Event Verification</p>', unsafe_allow_html=True)
    st.markdown(
        "Topics detected by the model are cross-referenced against the "
        "[GDELT Project](https://www.gdeltproject.org/) database to verify whether "
        "they correspond to **real-world events** or are merely **short-lived viral trends**."
    )

    gdelt_data = {
        'Topic':    ['Politics (Trump/GOP)', 'Health (COVID/Hospital)', 'Climate/Environment', 'Economy/Market'],
        'Keywords': ['trump donald gop', 'health covid hospital', 'climate environment carbon', 'economy market business'],
        'Status':   ['✅ VERIFIED', '✅ VERIFIED', '✅ VERIFIED', '✅ VERIFIED'],
        'Insight':  [
            'Strong correlation with US election cycles and policy debates',
            'Peaks align with pandemic waves and public health announcements',
            'Consistent presence with spikes during UN climate summits',
            'Correlates with market crashes, Fed announcements, and earnings seasons',
        ],
    }
    gdelt_df = pd.DataFrame(gdelt_data)
    st.dataframe(
        gdelt_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Topic':    st.column_config.TextColumn('Topic', width='medium'),
            'Keywords': st.column_config.TextColumn('Search Keywords', width='medium'),
            'Status':   st.column_config.TextColumn('Verification', width='small'),
            'Insight':  st.column_config.TextColumn('Key Insight', width='large'),
        },
    )
