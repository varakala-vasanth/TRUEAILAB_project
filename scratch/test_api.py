import sys
import os
import json
import numpy as np

# Adjust path to import from app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.utils import db, chunker
from app.services import vector_store, auth_service

def test_database():
    print("\n--- 1. Testing SQLite Database Init & CRUD ---")
    db.init_db()
    print("[Pass] Database initialized successfully.")
    
    # Test user creation
    username = "test_agent_v"
    password = "supersecretpassword123"
    
    # Clean previous if exists
    conn = db.get_db_connection()
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    
    hashed = auth_service.hash_password(password)
    user_id = db.create_user(username, hashed)
    assert user_id is not None, "Failed to create user in database"
    print(f"[Pass] Successfully created test user: '{username}' (ID: {user_id})")
    
    # Test retrieve
    user = db.get_user_by_username(username)
    assert user is not None, "Failed to fetch user by username"
    assert auth_service.verify_password(password, user["password_hash"]), "Password hash verification failed"
    print("[Pass] Password hash verification and user lookup verified.")

def test_chunker():
    print("\n--- 2. Testing Text Chunking Utility ---")
    sample_text = (
        "TrueAILab provides high-throughput API endpoints for programmatic access to our model suites. "
        "Developers can generate, rotate, and revoke custom API keys by visiting the Developer Console. "
        "Each active API key has granular permissions, including read-only, write-only, or full administrative scopes. "
        "For security compliance, API keys are only displayed in full once upon initial creation. "
        "Users are strongly advised to store keys securely using dedicated environment variables."
    )
    
    chunks = chunker.chunk_text(sample_text, chunk_size_words=20, overlap_words=5)
    print(f"Generated Chunks count: {len(chunks)}")
    for idx, c in enumerate(chunks):
        print(f"  Chunk {idx+1}: {c[:60]}...")
        
    assert len(chunks) > 0, "Chunk list should not be empty"
    print("[Pass] Document text split chunking validated.")

def test_cosine_similarity():
    print("\n--- 3. Testing Pure Cosine Similarity Matches ---")
    # Define simple orthogonal and parallel vectors
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0] # Parallel
    v3 = [0.0, 1.0, 0.0] # Orthogonal
    v4 = [0.707, 0.707, 0.0] # 45 degrees
    
    score_parallel = vector_store.cosine_similarity(v1, v2)
    score_orthogonal = vector_store.cosine_similarity(v1, v3)
    score_45 = vector_store.cosine_similarity(v1, v4)
    
    print(f"Parallel match score: {score_parallel:.4f} (Expected: 1.0)")
    print(f"Orthogonal match score: {score_orthogonal:.4f} (Expected: 0.0)")
    print(f"45 degree match score: {score_45:.4f} (Expected: ~0.707)")
    
    assert abs(score_parallel - 1.0) < 1e-4, "Parallel similarity calculation incorrect"
    assert abs(score_orthogonal - 0.0) < 1e-4, "Orthogonal similarity calculation incorrect"
    assert abs(score_45 - 0.707) < 1e-2, "45 degree similarity calculation incorrect"
    print("[Pass] Pure numpy-based Cosine Similarity calculation matches mathematically.")

def test_rag_mock_grounding():
    print("\n--- 4. Testing Local RAG Grounding Verification ---")
    
    # Mock some indexed chunk entries
    mock_chunks = [
        {
            "title": "Reset Password Support",
            "content": "Users can reset password from Settings > Security.",
            "embedding": [1.0, 0.0, 0.0]
        },
        {
            "title": "Refund and billing Policy",
            "content": "Refund requests are processed inside 14 business days.",
            "embedding": [0.0, 1.0, 0.0]
        }
    ]
    
    # Query: How do I change password? (Closer to vector v1 [1,0,0])
    query_vector = [0.95, 0.05, 0.0]
    threshold = 0.70
    
    matches = []
    for chunk in mock_chunks:
        score = vector_store.cosine_similarity(query_vector, chunk["embedding"])
        if score >= threshold:
            matches.append((chunk, score))
            
    print(f"Query vector: {query_vector} | Threshold: {threshold}")
    print(f"Matched chunks count: {len(matches)}")
    for chunk, score in matches:
        print(f"  Match: [{chunk['title']}] | Score: {score:.4f} | Snippet: '{chunk['content']}'")
        
    assert len(matches) == 1, "Expected only 1 chunk to match threshold filter"
    assert matches[0][0]["title"] == "Reset Password Support", "Expected password chunk to match"
    print("[Pass] RAG Grounding match filter checked successfully.")

if __name__ == "__main__":
    print("==================================================")
    print("      TrueAILab RAG App Test Validation Suite     ")
    print("==================================================")
    
    try:
        test_database()
        test_chunker()
        test_cosine_similarity()
        test_rag_mock_grounding()
        
        print("\n==================================================")
        print("🎉 SUCCESS: All local validation tests passed successfully!")
        print("==================================================")
        
    except AssertionError as e:
        print(f"\n❌ FAIL: Assertion error during validation testing: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FAIL: Unexpected exception during validation: {e}")
        sys.exit(1)
