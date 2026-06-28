<p align="center">
  <h1 align="center">📰 Dynamic Trend & Event Detector</h1>
  <p align="center">
    <strong>Emerging Topic Detection & News Correlation using NLP & Deep Learning</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.11-3776ab?logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Streamlit-Dashboard-ff4b4b?logo=streamlit&logoColor=white" alt="Streamlit">
    <img src="https://img.shields.io/badge/BERTopic-Topic%20Modeling-4285f4?logo=google&logoColor=white" alt="BERTopic">
    <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  </p>
</p>

---

## Overview

A hybrid NLP system that **detects emerging topics** from 200K+ news articles and determines whether a trend corresponds to a **real-world event** or a **short-lived viral topic**. The system combines traditional topic modeling (LDA), deep learning-based topic modeling (BERTopic), and a novel hybrid approach incorporating **semantic velocity** and **external event verification** via the GDELT database.

> **Enterprise AI upgrade:** See the [Autonomous News Intelligence Platform engineering design](docs/enterprise_news_intelligence_platform.md) for a production-grade roadmap that transforms this research pipeline into an agentic AI system with RAG, tool calling, long-term memory, LangGraph workflows, human review, executive reporting, and a modern web dashboard.

### Key Results

| Model | Coherence (C_v) | Temporal Tracking | GDELT Verification |
|-------|:---:|:---:|:---:|
| LDA (Baseline) | 0.3573 | ❌ | ❌ |
| BERTopic | 0.4781 | ❌ | ❌ |
| **Hybrid (Proposed)** | **0.4981** | ✅ | ✅ |

> **39.4% improvement** in topic coherence over the LDA baseline using the proposed hybrid approach.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE                                │
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────────────┐  │
│  │  Kaggle   │───▶│  Preprocessing│───▶│  Clean Text Corpus    │  │
│  │  209K     │    │  (NLTK)      │    │  (Lemmatized, No SW)  │  │
│  │  Articles │    └──────────────┘    └───────────┬───────────┘  │
│  └──────────┘                                    │              │
│                                                  ▼              │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   TOPIC MODELING LAYER                      │  │
│  │                                                            │  │
│  │  ┌─────────┐     ┌───────────┐     ┌────────────────────┐ │  │
│  │  │  LDA    │     │ BERTopic  │     │  Hybrid Model      │ │  │
│  │  │ (Base)  │     │ (SBERT +  │     │  (BERTopic +       │ │  │
│  │  │ C_v:    │     │  UMAP +   │     │   Temporal +       │ │  │
│  │  │ 0.3573  │     │  HDBSCAN) │     │   GDELT)           │ │  │
│  │  │         │     │ C_v:      │     │  C_v: 0.4981       │ │  │
│  │  │         │     │ 0.4781    │     │                    │ │  │
│  │  └─────────┘     └───────────┘     └────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                 ANALYSIS LAYER                              │  │
│  │                                                            │  │
│  │  ┌──────────────────┐    ┌───────────────────────────────┐ │  │
│  │  │ Temporal Tracking │    │  GDELT Event Verification    │ │  │
│  │  │ (Semantic         │    │  (API Cross-Reference)       │ │  │
│  │  │  Velocity)        │    │                              │ │  │
│  │  └──────────────────┘    └───────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                   │
│                              ▼                                   │
│           ┌──────────────────────────────────┐                   │
│           │   Streamlit Dashboard (app.py)    │                   │
│           │   • Live Topic Detection          │                   │
│           │   • EDA & Insights                │                   │
│           │   • Model Comparison              │                   │
│           │   • Temporal Analysis              │                   │
│           └──────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/shahfathalkoul/Dynamic-Event-Detector.git
cd Dynamic-Event-Detector

# Install dependencies
pip install -r requirements.txt

# Download the dataset from Kaggle (link below) and place in data/
# https://www.kaggle.com/datasets/rmisra/news-category-dataset

# Launch the interactive dashboard
streamlit run app.py
```

### Agentic Platform Backend

This repo now includes the first production-oriented platform layer described in the enterprise design document:

- `packages/schemas/` contains typed domain records for articles, topic clusters, candidate events, evidence, agent decisions, and reports.
- `services/topic_discovery/` wraps the existing NLP research pipeline as a service-oriented Topic Discovery Engine.
- `services/retrieval/` provides a dependency-light hybrid retriever that can later be backed by Qdrant and PostgreSQL full-text search.
- `services/memory/` provides searchable long-term memory primitives for events, reflections, and analyst feedback.
- `services/tools/` provides a retrying tool gateway for future external API calls.
- `services/agents/` provides a deterministic event-intelligence workflow that maps directly to future LangGraph nodes.
- `services/storage/` provides durable SQLite persistence that mirrors the future PostgreSQL repository boundary.
- `apps/api/` contains a FastAPI backend scaffold with event detection, event analysis, and chat retrieval endpoints.
- `tests/` contains regression tests for the upgraded platform layer.

Run the platform tests:

```bash
python -m unittest discover -s tests -v
```

After installing the expanded backend dependencies, start the API:

```bash
uvicorn apps.api.main:app --reload
```

---

## Project Structure

```
Dynamic-Event-Detector/
├── apps/
│   └── api/                         # FastAPI backend scaffold
├── packages/
│   └── schemas/                     # Shared typed platform records
├── services/
│   ├── agents/                      # Event intelligence workflow
│   ├── memory/                      # Long-term memory prototype
│   ├── retrieval/                   # Hybrid retrieval prototype
│   ├── storage/                     # SQLite persistence adapter
│   ├── tools/                       # Tool-calling gateway
│   └── topic_discovery/             # Service wrapper around existing NLP pipeline
├── app.py                          # Streamlit multi-tab dashboard
├── requirements.txt                # Pinned dependencies
├── LICENSE                         # MIT License
├── .gitignore
│
├── src/                            # Reusable Python modules
│   ├── __init__.py
│   ├── preprocessing.py            # Text cleaning & data loading
│   ├── models.py                   # LDA training, coherence, prediction
│   ├── visualization.py            # Plotly chart generators
│   └── gdelt.py                    # GDELT API verification
│
├── notebooks/                      # Jupyter analysis notebooks
│   ├── clean.ipynb                 # Data cleaning pipeline
│   ├── eda_plan.ipynb              # Exploratory Data Analysis
│   ├── LDA.ipynb                   # LDA topic modeling & evaluation
│   ├── BERTopic.ipynb              # BERTopic + temporal + velocity
│   └── GDELTVerification.ipynb     # External event verification
│
├── graphs/                         # Generated visualizations
│   ├── eda1_categories.png
│   ├── eda2_yearly.png
│   ├── eda3_wordcount.png
│   ├── eda4_topwords.png
│   ├── lda_topics.png
│   ├── semantic_velocity.png
│   ├── ablation_graph.png
│   └── topics_over_time.html       # Interactive BERTopic visualization
│
├── data/                           # Dataset (not tracked in git)
│   ├── News_Category_Dataset_v3.json
│   └── clean_data.csv
│
└── reports/
    ├── ablation_table.csv
    └── ieee_format_report.tex      # IEEE-format research paper
```

---

## Methodology

### 1. Data Preprocessing
- **Dataset:** 209,527 news articles from the Kaggle News Category Dataset (2012–2022)
- **Cleaning:** URL removal, non-alphabetic character stripping, stopword removal, WordNet lemmatization
- **Sampling:** 10,000 articles for model training, 5,000 for the live demo

### 2. Baseline — LDA Topic Modeling
- Latent Dirichlet Allocation with 20 components
- CountVectorizer (10K features, min_df=5, max_df=0.95)
- Achieves **C_v coherence of 0.3573**

### 3. Deep Learning — BERTopic
- Sentence-BERT embeddings → UMAP dimensionality reduction → HDBSCAN clustering
- Captures deep semantic relationships between articles
- Achieves **C_v coherence of 0.4781** (+33.8% over LDA)

### 4. Hybrid Approach (Proposed)
- Extends BERTopic with **temporal topic tracking** across time intervals
- Introduces **semantic velocity** — measures the rate of change in topic frequency
- Cross-references topics against the **GDELT Project** database for real-world event verification
- Achieves **C_v coherence of 0.4981** (+39.4% over LDA)

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Baseline** | LDA (scikit-learn) | Traditional probabilistic topic modeling |
| **Embeddings** | Sentence-BERT | Dense semantic document representations |
| **Dim. Reduction** | UMAP | High-dimensional embedding projection |
| **Clustering** | HDBSCAN | Density-based topic cluster discovery |
| **Topic Modeling** | BERTopic | Neural topic modeling framework |
| **Event Verification** | GDELT API | External real-world event cross-reference |
| **Dashboard** | Streamlit + Plotly | Interactive web application |
| **NLP** | NLTK + Gensim | Text preprocessing & coherence evaluation |

---

## Dataset

- **Source:** [Kaggle — News Category Dataset](https://www.kaggle.com/datasets/rmisra/news-category-dataset)
- **Size:** 209,527 articles across 42 categories
- **Period:** 2012–2022
- **Fields:** headline, short_description, category, authors, date

---

## References

1. Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). *Latent Dirichlet Allocation.* JMLR, 3, 993–1022.
2. Grootendorst, M. (2022). *BERTopic: Neural topic modeling with a class-based TF-IDF procedure.* arXiv:2203.05794.
3. Reimers, N. & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* arXiv:1908.10084.
4. McInnes, L. & Healy, J. (2017). *HDBSCAN: Hierarchical density-based clustering.* JOSS, 2(11), 205.
5. Misra, R. (2022). *News Category Dataset.* Kaggle.

---

## Author

**Shah Fathal Koul**

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
