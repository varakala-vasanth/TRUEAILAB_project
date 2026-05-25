import os
import httpx
from typing import List

# Load environment configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def generate_embedding(text: str) -> List[float]:
    """
    Generates a dense vector embedding for the input text using the configured provider.
    Handles API authentication, timeout safety, and rate limit validation.
    """
    if not text.strip():
        raise ValueError("Input text for embedding cannot be empty")

    if EMBEDDING_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured in the environment variables")
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
        payload = {
            "model": "models/text-embedding-004",
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload)
                
                # Check status
                if response.status_code == 400:
                    raise Exception(f"Bad Request: {response.text}")
                elif response.status_code == 401:
                    raise Exception("Invalid API Key: Unauthorized access to Gemini Embeddings API")
                elif response.status_code == 429:
                    raise Exception("Rate Limit Exceeded: Too many requests for Gemini Embeddings")
                
                response.raise_for_status()
                res_data = response.json()
                
                if "embedding" in res_data and "values" in res_data["embedding"]:
                    return res_data["embedding"]["values"]
                else:
                    raise Exception(f"Unexpected response structure from Gemini API: {res_data}")
                    
        except httpx.TimeoutException:
            raise Exception("Timeout Exception: Gemini Embeddings service timed out")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP Error from Gemini Embeddings: {e.response.status_code} - {e.response.text}")
            
    elif EMBEDDING_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured in the environment variables")
            
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        payload = {
            "model": "text-embedding-3-small",
            "input": text
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, headers=headers, json=payload)
                
                if response.status_code == 401:
                    raise Exception("Invalid API Key: Unauthorized access to OpenAI Embeddings API")
                elif response.status_code == 429:
                    raise Exception("Rate Limit Exceeded: Too many requests for OpenAI Embeddings")
                
                response.raise_for_status()
                res_data = response.json()
                
                if "data" in res_data and len(res_data["data"]) > 0 and "embedding" in res_data["data"][0]:
                    return res_data["data"][0]["embedding"]
                else:
                    raise Exception(f"Unexpected response structure from OpenAI API: {res_data}")
                    
        except httpx.TimeoutException:
            raise Exception("Timeout Exception: OpenAI Embeddings service timed out")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP Error from OpenAI Embeddings: {e.response.status_code} - {e.response.text}")
            
    else:
        raise ValueError(f"Unsupported EMBEDDING_PROVIDER configured: '{EMBEDDING_PROVIDER}'")
