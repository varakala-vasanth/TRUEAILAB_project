from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["System Health"])

@router.get("")
def health_check():
    """
    Standard health check endpoint indicating service availability.
    """
    return {"status": "healthy"}
