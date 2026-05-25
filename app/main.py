import os
from dotenv import load_dotenv

# Load environment configuration first before importing services
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes import auth, chat, health
from app.utils import db
from app.services import vector_store

# Initialize FastAPI application
app = FastAPI(
    title="TrueAILab GenAI Support Assistant with RAG",
    description="Production-grade Retrieval-Augmented Generation Chat Assistant",
    version="1.0.0"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, lock this down to your trusted domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(health.router)

# Startup event configuration
@app.on_event("startup")
def on_startup():
    print("[Main] Initializing persistent SQLite database...")
    db.init_db()
    
    print("[Main] Commencing automatic document indexing RAG...")
    try:
        vector_store.index_docs_json()
    except Exception as e:
        print(f"[Main] Critical failure during startup document indexing: {e}")
        print("[Main] Server will start, but RAG capabilities might be degraded until API keys are configured.")

# Serve static frontend assets
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")
    print(f"[Main] Successfully mounted static frontend files from: {frontend_path}")
else:
    print(f"[Main] Warning: Frontend static directory not found at: {frontend_path}")
