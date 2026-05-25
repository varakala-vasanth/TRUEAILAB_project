import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple
from app.utils import db, chunker
from app.services import embedding_service

# Load configuration parameters
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.70"))
TOP_K = int(os.getenv("TOP_K", "3"))

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Computes standard cosine similarity between two vector lists.
    """
    arr1 = np.array(v1, dtype=np.float32)
    arr2 = np.array(v2, dtype=np.float32)
    
    dot_product = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)
    
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return float(dot_product / (norm1 * norm2))

def index_docs_json():
    """
    Readsdocs.json and indexes documents and their embeddings into SQLite if the database is empty.
    Allows for automatic startup indexing.
    """
    if db.has_documents():
        print("[VectorStore] Database already indexed. Skipping initial setup.")
        return
        
    docs_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs.json")
    if not os.path.exists(docs_file_path):
        print(f"[VectorStore] docs.json not found at {docs_file_path}. Skipping automatic indexing.")
        return
        
    try:
        with open(docs_file_path, "r") as f:
            documents = json.load(f)
    except Exception as e:
        print(f"[VectorStore] Failed to read docs.json: {e}")
        return
        
    print(f"[VectorStore] Beginning indexing of {len(documents)} documents...")
    
    for idx, doc in enumerate(documents):
        title = doc.get("title", f"Document-{idx}")
        content = doc.get("content", "")
        source = doc.get("source", "Unknown Source")
        
        if not content.strip():
            continue
            
        print(f"[VectorStore] Chunking and embedding: '{title}'...")
        
        # 1. Chunk document
        chunks = chunker.chunk_text(content, chunk_size_words=200, overlap_words=40)
        chunks_to_save = []
        
        for c_idx, c_text in enumerate(chunks):
            try:
                # 2. Generate embedding for chunk
                vector = embedding_service.generate_embedding(c_text)
                chunks_to_save.append({
                    "chunk_index": c_idx,
                    "content": c_text,
                    "embedding": vector
                })
            except Exception as e:
                print(f"[VectorStore] Error generating embedding for '{title}' chunk {c_idx}: {e}")
                raise e
                
        # 3. Save document and chunks in SQLite transaction
        db.save_document_and_chunks(title, content, source, chunks_to_save)
        print(f"[VectorStore] Successfully saved document '{title}' with {len(chunks_to_save)} chunks.")
        
    print("[VectorStore] Automatic database indexing successfully completed.")

def similarity_search(query: str, threshold: float = None, top_k: int = None) -> List[Dict[str, Any]]:
    """
    Performs dense vector similarity search over the indexed database chunks.
    Generates embedding for the user query, compares against database vectors using cosine similarity,
    applies the threshold, logs results, and returns top K matches.
    """
    if threshold is None:
        threshold = SIMILARITY_THRESHOLD
    if top_k is None:
        top_k = TOP_K
        
    # 1. Generate query embedding
    query_vector = embedding_service.generate_embedding(query)
    
    # 2. Retrieve all database chunks
    all_chunks = db.get_all_chunks()
    if not all_chunks:
        return []
        
    scored_results = []
    
    # 3. Calculate similarity score for each chunk
    for chunk in all_chunks:
        score = cosine_similarity(query_vector, chunk["embedding"])
        
        # Track matches
        scored_results.append({
            "chunk_id": chunk["chunk_id"],
            "content": chunk["content"],
            "title": chunk["metadata"]["title"],
            "source": chunk["metadata"]["source"],
            "score": score
        })
        
    # 4. Sort results descending by score
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    
    # Log scores (for audit/evaluation purposes)
    print(f"[VectorStore] Query: '{query}'")
    print(f"[VectorStore] Top 5 Raw Similarity Scores:")
    for i, res in enumerate(scored_results[:5]):
        print(f"  {i+1}. [{res['title']}] Score: {res['score']:.4f} | Snippet: {res['content'][:60]}...")
        
    # 5. Filter results based on similarity threshold
    filtered_results = [res for res in scored_results if res["score"] >= threshold]
    print(f"[VectorStore] Filtered matching chunks above threshold ({threshold}): {len(filtered_results)}")
    
    # 6. Retrieve top K matches
    return filtered_results[:top_k]
