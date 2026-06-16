"""
GDELT API verification utilities.
"""

import requests
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_with_gdelt(keywords: list[str], year: str = '2020') -> list[dict]:
    """
    Query GDELT API for matching articles based on keywords.
    
    Args:
        keywords (list[str]): List of keywords to search for.
        year (str): The year to restrict the search to.
        
    Returns:
        list[dict]: List of matched articles.
    """
    query = ' '.join(keywords[:3])
    url = (
        f'https://api.gdeltproject.org/api/v2/doc/doc'
        f'?query={query}&mode=artlist&maxrecords=5'
        f'&format=json'
        f'&startdatetime={year}0101000000'
        f'&enddatetime={year}1231235959'
    )
    
    for attempt in range(3):
        try:
            # Note: In a production environment, verify=True is strongly recommended
            response = requests.get(url, timeout=10, verify=True)
            if response.status_code == 200:
                data = response.json()
                return data.get('articles', [])
        except requests.RequestException as e:
            logger.warning(f"GDELT request failed (attempt {attempt+1}/3): {e}")
            time.sleep(2)
            
    return []

def batch_verify_topics(topics: dict[str, list[str]], year: str = '2020') -> pd.DataFrame:
    """
    Verify multiple topics and return results as a DataFrame.
    
    Args:
        topics (dict[str, list[str]]): Dictionary mapping topic names to lists of keywords.
        year (str): The year to search in GDELT.
        
    Returns:
        pd.DataFrame: DataFrame containing the verification results.
    """
    results = []
    
    for name, keywords in topics.items():
        logger.info(f"Verifying {name}...")
        articles = verify_with_gdelt(keywords, year=year)
        
        status = 'VERIFIED' if articles else 'NOT FOUND'
        
        results.append({
            'Topic': name,
            'Keywords': ', '.join(keywords),
            'Matches': len(articles),
            'Status': status
        })
        
        time.sleep(1) # Be nice to the API
        
    return pd.DataFrame(results)
