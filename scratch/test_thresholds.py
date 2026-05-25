import sys
import os

from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.services import vector_store

def test_queries():
    queries = [
        "How do I reset my password?",
        "how to change password",
        "how do i delete my account?",
        "can I connect slack workspace?",
        "what is your refund policy?",
        "tell me about billing tiers",
        "how can I export workspace data?",
        "what are the admin permissions?",
        "how do i enable two-factor authentication?",
        # Off-topic queries to verify grounding block
        "what is a database?",
        "who was Albert Einstein?",
        "tell me a joke"
    ]
    
    print("==================================================")
    print("Testing OpenAI Similarity Scores for Various Queries")
    print("==================================================")
    
    for q in queries:
        print(f"\nQuery: '{q}'")
        matches = vector_store.similarity_search(q, threshold=0.0, top_k=3)
        if matches:
            best = matches[0]
            print(f"  Best Match: [{best['title']}] | Score: {best['score']:.4f}")
            print(f"  Snippet: '{best['content'][:80]}...'")
        else:
            print("  No matches found in database.")

if __name__ == "__main__":
    test_queries()
