import os
from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import jwt
import bcrypt

# Load environment configuration
JWT_SECRET = os.getenv("JWT_SECRET", "bf3f32c918a221f7dbf170a48b301cdfe68b4ef213f569b910ee2aefc8801d01")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using standard bcrypt directly.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a stored bcrypt hash directly.
    """
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Encodes custom payload into a JWT access token.
    Adds expiration timestamps to enforce session security.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a JWT token.
    Returns the token payload if valid, otherwise None.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
