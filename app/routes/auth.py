from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.services import auth_service
from app.utils import db

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to validate JWT tokens. Extracts the username and verifies existence in the database.
    Throws a 401 Unauthorized exception if verification fails.
    """
    token = credentials.credentials
    payload = auth_service.verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identity claims",
        )
        
    user = db.get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token no longer exists",
        )
    return user

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    """
    Registers a new user account. Hashes passwords using standard bcrypt.
    """
    # Check if user already exists
    existing = db.get_user_by_username(req.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered"
        )
        
    hashed_pwd = auth_service.hash_password(req.password)
    user_id = db.create_user(req.username, hashed_pwd)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user due to database constraint violation"
        )
        
    return {"message": "User registered successfully", "userId": user_id}

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """
    Authenticates a user. Returns a signed JWT token if credentials are valid.
    """
    user = db.get_user_by_username(req.username)
    if not user or not auth_service.verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Generate signed JWT token
    access_token = auth_service.create_access_token(data={"sub": user["username"], "uid": user["id"]})
    return {
        "accessToken": access_token,
        "tokenType": "bearer",
        "username": user["username"]
    }
