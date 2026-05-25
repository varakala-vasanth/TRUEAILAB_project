import os
import sqlite3
import json
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rag_app.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Documents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        source TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 3. Chunks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        content TEXT NOT NULL,
        embedding TEXT NOT NULL, -- Stored as a JSON string of float list
        FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
    )
    """)
    
    # 4. Chat Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_sessions (
        id TEXT PRIMARY KEY, -- Session UUID/ID
        user_id INTEGER,
        title TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """)
    
    # 5. Chat Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL, -- 'user' or 'assistant'
        content TEXT NOT NULL,
        tokens_used INTEGER DEFAULT 0,
        retrieved_chunks_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

# User Helpers
def create_user(username, password_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None

# Document Helpers
def has_documents():
    conn = get_db_connection()
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    conn.close()
    return count > 0

def save_document_and_chunks(title, raw_content, source, chunks_list):
    """
    Saves a document and all its chunks in a single transaction.
    chunks_list format: [{'chunk_index': 0, 'content': '...', 'embedding': [...]}]
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Insert document
        cursor.execute(
            "INSERT INTO documents (title, content, source) VALUES (?, ?, ?)",
            (title, raw_content, source)
        )
        doc_id = cursor.lastrowid
        
        # Insert chunks
        for chunk in chunks_list:
            cursor.execute(
                "INSERT INTO chunks (document_id, chunk_index, content, embedding) VALUES (?, ?, ?, ?)",
                (doc_id, chunk["chunk_index"], chunk["content"], json.dumps(chunk["embedding"]))
            )
        conn.commit()
        return doc_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_chunks():
    """
    Retrieves all chunks along with parent document metadata for vector similarity search.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT c.id as chunk_id, c.content as chunk_content, c.embedding, 
               d.title as doc_title, d.source as doc_source
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
    """).fetchall()
    conn.close()
    
    chunks = []
    for r in rows:
        chunks.append({
            "chunk_id": r["chunk_id"],
            "content": r["chunk_content"],
            "embedding": json.loads(r["embedding"]),
            "metadata": {
                "title": r["doc_title"],
                "source": r["doc_source"]
            }
        })
    return chunks

# Chat Session Helpers
def create_session(session_id, user_id, title):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO chat_sessions (id, user_id, title) VALUES (?, ?, ?)",
            (session_id, user_id, title)
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

def get_sessions_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def delete_session(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

# Message Helpers
def create_message(session_id, role, content, tokens_used=0, retrieved_chunks_count=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO chat_messages (session_id, role, content, tokens_used, retrieved_chunks_count)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, role, content, tokens_used, retrieved_chunks_count))
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        print(f"Error saving message: {e}")
        return None
    finally:
        conn.close()

def get_messages_by_session(session_id, limit=6):
    """
    Fetches the last N messages for context building (e.g. 6 messages = last 3 pairs).
    Ordered ascending by time so they flow naturally in the prompt history.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # First get the last N message IDs, then fetch and sort them chronologically
    rows = cursor.execute("""
        SELECT * FROM (
            SELECT * FROM chat_messages 
            WHERE session_id = ? 
            ORDER BY created_at DESC, id DESC 
            LIMIT ?
        ) ORDER BY created_at ASC, id ASC
    """, (session_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
