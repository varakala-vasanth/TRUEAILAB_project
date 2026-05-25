import httpx
import json

def test_live_rag():
    base_url = "http://127.0.0.1:8000"
    client = httpx.Client(timeout=30.0)
    
    # 1. Register
    username = "live_tester_v"
    password = "testerpassword123"
    
    try:
        reg_resp = client.post(
            f"{base_url}/api/auth/register",
            json={"username": username, "password": password}
        )
        print(f"Register status: {reg_resp.status_code}")
    except Exception as e:
        print(f"User registration mock or actual status: {e}")
        
    # 2. Login
    login_resp = client.post(
        f"{base_url}/api/auth/login",
        json={"username": username, "password": password}
    )
    print(f"Login status: {login_resp.status_code}")
    token = login_resp.json()["accessToken"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Chat: How do I reset my password?
    chat_resp = client.post(
        f"{base_url}/api/chat",
        headers=headers,
        json={
            "sessionId": "test-live-session-123",
            "message": "How do I reset my password?"
        }
    )
    print(f"Chat status: {chat_resp.status_code}")
    chat_data = chat_resp.json()
    print("Reply:")
    print(chat_data["reply"])
    print(f"Tokens used: {chat_data['tokensUsed']} | Retrieved: {chat_data['retrievedChunks']}")

if __name__ == "__main__":
    test_live_rag()
