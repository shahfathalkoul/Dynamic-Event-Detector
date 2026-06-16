"""
Dynamic Event Detector Source Package
"""

from .preprocessing import clean_text, load_dataset
from .models import train_lda_model, compute_coherence_score, predict_topic
from .visualization import (
    plot_topic_distribution,
    plot_ablation_comparison,
    plot_category_distribution,
    plot_model_comparison_table
)
from .gdelt import verify_with_gdelt, batch_verify_topics

__all__ = [
    "clean_text",
    "load_dataset",
    "train_lda_model",
    "compute_coherence_score",
    "predict_topic",
    "plot_topic_distribution",
    "plot_ablation_comparison",
    "plot_category_distribution",
    "plot_model_comparison_table",
    "verify_with_gdelt",
    "batch_verify_topics",
]
