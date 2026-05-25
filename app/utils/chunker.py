import re
from typing import List, Dict, Any

def chunk_text(text: str, chunk_size_words: int = 200, overlap_words: int = 40) -> List[str]:
    """
    Chunks a block of text into overlapping segments based on word counts.
    Ensures context continuity across chunk boundaries.
    """
    # Clean whitespace and split into individual words
    words = [w for w in re.split(r'\s+', text.strip()) if w]
    
    if not words:
        return []
        
    if len(words) <= chunk_size_words:
        return [text.strip()]
        
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size_words, len(words))
        chunk_words = words[start:end]
        
        # Assemble chunk
        chunk_text = " ".join(chunk_words)
        chunks.append(chunk_text)
        
        # Advance by (chunk_size - overlap)
        start += (chunk_size_words - overlap_words)
        
        # Break if we have reached the end of the text
        if end == len(words):
            break
            
    return chunks
