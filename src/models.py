"""
Model training and evaluation utilities.
"""

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from gensim.models.coherencemodel import CoherenceModel
from gensim.corpora import Dictionary

def train_lda_model(documents: list[str], n_topics: int = 10, max_features: int = 2000, max_iter: int = 15) -> tuple:
    """
    Trains an LDA model on the provided documents.
    
    Args:
        documents (list[str]): List of preprocessed text documents.
        n_topics (int): Number of topics to extract.
        max_features (int): Maximum number of features for CountVectorizer.
        max_iter (int): Maximum number of iterations for LDA.
        
    Returns:
        tuple: (lda_model, vectorizer, topic_names_dict)
    """
    vectorizer = CountVectorizer(max_features=max_features, min_df=5, max_df=0.9)
    dtm = vectorizer.fit_transform(documents)

    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=42,
        max_iter=max_iter,
    )
    lda.fit(dtm)

    vocab = vectorizer.get_feature_names_out()
    topic_names = {}
    for i, topic in enumerate(lda.components_):
        top_words = [vocab[j] for j in topic.argsort()[-5:][::-1]]
        topic_names[i] = f"Topic {i + 1}: " + ", ".join(top_words).title()

    return lda, vectorizer, topic_names

def compute_coherence_score(topics: list[list[str]], texts: list[list[str]]) -> float:
    """
    Compute C_V coherence using gensim.
    
    Args:
        topics (list[list[str]]): List of topics, where each topic is a list of words.
        texts (list[list[str]]): Tokenized documents.
        
    Returns:
        float: The C_V coherence score.
    """
    dictionary = Dictionary(texts)
    cm = CoherenceModel(topics=topics, texts=texts, dictionary=dictionary, coherence='c_v')
    return cm.get_coherence()

def predict_topic(text: str, model, vectorizer, topic_names: dict) -> tuple[str | None, np.ndarray | None]:
    """
    Predict the topic for a new text.
    
    Args:
        text (str): Cleaned text.
        model: Trained topic model (e.g., LDA).
        vectorizer: Fitted vectorizer.
        topic_names (dict): Mapping from topic index to topic name.
        
    Returns:
        tuple: (topic_name, probability_distribution)
    """
    if not text.strip():
        return None, None
        
    vec = vectorizer.transform([text])
    topic_dist = model.transform(vec)[0]
    best_topic_id = int(np.argmax(topic_dist))
    return topic_names.get(best_topic_id), topic_dist
