from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from ..database import get_db
from ..config import settings
from ..models import User
import jwt
from datetime import datetime, timedelta, timezone

security = HTTPBearer()
def get_current_user(db: Session = Depends(get_db), token: str = Depends(security)):
    try:
        payload = jwt.decode()
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.select(User).filter(User.id == int(payload.get("user_id"))).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
def create_jwt(user_id : int):
    payload = {
        "user_id": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)