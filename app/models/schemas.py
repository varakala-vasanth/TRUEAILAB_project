from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Authentication Schemas
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=6, max_length=100, description="User password")

class LoginRequest(BaseModel):
    username: str = Field(..., description="Registered username")
    password: str = Field(..., description="Password")

class TokenResponse(BaseModel):
    accessToken: str = Field(..., description="JWT Bearer Token")
    tokenType: str = Field("bearer", description="Token scheme")
    username: str = Field(..., description="Authenticated username")

# RAG & Chat Schemas
class SourceMetadata(BaseModel):
    title: str = Field(..., description="Source document title")
    source: str = Field(..., description="Detailed source location reference")
    score: float = Field(..., description="Cosine similarity match score")
    content: str = Field(..., description="Raw text context chunk snippet")

class ChatRequest(BaseModel):
    sessionId: str = Field(..., description="Unique alphanumeric chat session identifier")
    message: str = Field(..., min_length=1, description="The user's query/message")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="The grounded RAG-compliant assistant response")
    tokensUsed: int = Field(..., description="Calculated API consumption tokens count")
    retrievedChunks: int = Field(..., description="Number of matching context chunks fetched")
    sources: List[SourceMetadata] = Field(default=[], description="Source references containing details & match scores")

# Session Info Schemas
class SessionCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Chat session custom Title")

class SessionInfo(BaseModel):
    id: str = Field(..., description="Session identifier")
    title: str = Field(..., description="Custom descriptive session title")
    created_at: str = Field(..., description="Session creation timestamp")

class UserResponse(BaseModel):
    id: int
    username: str
    created_at: str
