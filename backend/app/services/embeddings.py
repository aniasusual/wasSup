from __future__ import annotations

from typing import List, Optional
import os
import requests
import time

JINA_API_KEY = os.getenv("JINA_API_KEY", "jina_4fc7206db6fa44578d25fb6b1998af3236ImlRRNqLVWcueSv6sqKEeWWhCn")
JINA_MODEL = os.getenv("JINA_MODEL", "jina-embeddings-v2-base-en")


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings using Jina AI embeddings API.

    Returns an empty list if API key is not configured.
    """
    if not isinstance(texts, list) or len(texts) == 0:
        return []

    if not JINA_API_KEY:
        # No API key configured; skip embedding
        return []

    # Retry mechanism for network issues
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            # Jina AI embeddings API endpoint
            url = "https://api.jina.ai/v1/embeddings"
            
            headers = {
                "Authorization": f"Bearer {JINA_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Prepare the request payload
            payload = {
                "input": texts,
                "model": JINA_MODEL
            }
            
            # Make the API request with increased timeout
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            break  # Success, exit retry loop
            
        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                print(f"Jina API request timed out (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                print(f"Jina API request timed out after {max_retries} attempts: {e}")
                print("Consider checking your internet connection or Jina API status")
                return []
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"Jina API request failed (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                print(f"Jina API request failed after {max_retries} attempts: {e}")
                print("Check your internet connection and Jina API key")
                return []
        except Exception as e:
            print(f"Unexpected error during Jina API request: {e}")
            return []
    
    # Parse the response
    result = response.json()
    
    # Debug: log the result structure
    print(f"Jina embedding result type: {type(result)}")
    print(f"Jina embedding result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
    
    # Extract embeddings from Jina response
    if isinstance(result, dict) and "data" in result:
        embeddings = []
        for item in result["data"]:
            if isinstance(item, dict) and "embedding" in item:
                embeddings.append(item["embedding"])
        return embeddings
    else:
        print(f"Unexpected Jina response format: {result}")
        return []


def get_embedding_dimension() -> int:
    """Return the embedding vector dimension for the configured model."""
    # jina-embeddings-v2-base-en produces 768-dimensional vectors
    return 768


