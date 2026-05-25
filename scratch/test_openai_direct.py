import httpx
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def test_direct():
    print("Testing direct OpenAI API connection...")
    print(f"API Key start: {OPENAI_API_KEY[:10]}...{OPENAI_API_KEY[-10:]}")
    
    # 1. Test Embedding
    url_emb = "https://api.openai.com/v1/embeddings"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    payload_emb = {
        "model": "text-embedding-3-small",
        "input": "Hello world"
    }
    
    print("\nSending embedding request...")
    try:
        resp = httpx.post(url_emb, headers=headers, json=payload_emb, timeout=10.0)
        print(f"Embedding Response Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Embedding success!")
        else:
            print(f"Embedding error response: {resp.text}")
    except Exception as e:
        print(f"Embedding exception: {e}")
        
    # 2. Test LLM Completion
    url_chat = "https://api.openai.com/v1/chat/completions"
    payload_chat = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "Say hello!"}],
        "temperature": 0.2
    }
    
    print("\nSending chat completion request...")
    try:
        resp = httpx.post(url_chat, headers=headers, json=payload_chat, timeout=15.0)
        print(f"Chat Response Status: {resp.status_code}")
        if resp.status_code == 200:
            print("Chat success!")
            print(f"Reply: {resp.json()['choices'][0]['message']['content']}")
        else:
            print(f"Chat error response: {resp.text}")
    except Exception as e:
        print(f"Chat exception: {e}")

if __name__ == "__main__":
    test_direct()
