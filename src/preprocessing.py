"""
Data preprocessing utilities.
"""

import re
import os
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Ensure resources are downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)
    
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)

_lemmatizer = WordNetLemmatizer()
_stop_words = set(stopwords.words('english'))

def clean_text(text: str) -> str:
    """
    Preprocess text: lowercase, remove URLs/non-alpha, lemmatize, drop stopwords.
    
    Args:
        text (str): Raw input text.
        
    Returns:
        str: Cleaned text.
    """
    if not isinstance(text, str):
        return ""
        
    text = text.lower()
    text = re.sub(r'http\S+|[^a-z\s]', '', text)
    words = [
        _lemmatizer.lemmatize(w)
        for w in text.split()
        if w not in _stop_words and len(w) > 2
    ]
    return ' '.join(words)

def load_dataset(path: str, sample_size: int | None = None) -> pd.DataFrame:
    """
    Load and optionally sample the news dataset.
    
    Args:
        path (str): Path to the CSV file.
        sample_size (int, optional): Number of rows to sample.
        
    Returns:
        pd.DataFrame: The loaded dataset.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found at {path}")
        
    df = pd.read_csv(path)
    
    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42).copy()
        
    return df
