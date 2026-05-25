import os
import httpx
from typing import Tuple

# Load environment configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def generate_completion(prompt: str) -> Tuple[str, int]:
    """
    Sends the fully built prompt to the configured LLM API provider.
    Enforces a low temperature (0.2) to prevent hallucinations.
    Handles timeouts, rate limits, and authentication errors gracefully.
    Returns: Tuple[reply_text, tokens_used]
    """
    if not prompt.strip():
        raise ValueError("Prompt content cannot be empty")

    if LLM_PROVIDER == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured in the environment variables")
            
        # Call Gemini 1.5 Flash API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                
                # Check specific errors
                if response.status_code == 400:
                    raise Exception(f"Bad Request: {response.text}")
                elif response.status_code == 401:
                    raise Exception("Invalid API Key: Unauthorized access to Gemini LLM API")
                elif response.status_code == 429:
                    raise Exception("Rate Limit Exceeded: Too many requests for Gemini LLM completions")
                
                response.raise_for_status()
                res_data = response.json()
                
                # Parse candidates and usage
                try:
                    candidates = res_data.get("candidates", [])
                    if not candidates:
                        raise Exception("Gemini returned an empty completion candidate list")
                        
                    reply = candidates[0]["content"]["parts"][0]["text"]
                    
                    # Parse usage metadata
                    tokens = res_data.get("usageMetadata", {}).get("totalTokenCount", 0)
                    return reply, tokens
                except (KeyError, IndexError) as e:
                    raise Exception(f"Failed to parse Gemini API response: {e}. Raw response: {res_data}")
                    
        except httpx.TimeoutException:
            raise Exception("Timeout Exception: Gemini LLM service request timed out")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP Error from Gemini LLM: {e.response.status_code} - {e.response.text}")
            
    elif LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured in the environment variables")
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=payload)
                
                if response.status_code == 401:
                    raise Exception("Invalid API Key: Unauthorized access to OpenAI LLM API")
                elif response.status_code == 429:
                    raise Exception("Rate Limit Exceeded: Too many requests for OpenAI LLM completions")
                
                response.raise_for_status()
                res_data = response.json()
                
                try:
                    reply = res_data["choices"][0]["message"]["content"]
                    tokens = res_data.get("usage", {}).get("total_tokens", 0)
                    return reply, tokens
                except (KeyError, IndexError) as e:
                    raise Exception(f"Failed to parse OpenAI API response: {e}. Raw response: {res_data}")
                    
        except httpx.TimeoutException:
            raise Exception("Timeout Exception: OpenAI LLM service request timed out")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP Error from OpenAI LLM: {e.response.status_code} - {e.response.text}")
            
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER configured: '{LLM_PROVIDER}'")
