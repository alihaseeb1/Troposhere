from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models 
from ..schemas import User as UserSchema
from ..auth.google import oauth
from starlette.requests import Request
from starlette.responses import RedirectResponse
from ..config import settings
from ..auth.google import oauth
from ..auth.oauth import create_jwt

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/")
async def google_login(request: Request):
    # print("Session before login:", request.session)
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    # print("Session on callback:", request.session)
    token = await oauth.google.authorize_access_token(request)

    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    # print(user_info)
    user = db.query(models.User).filter(models.User.provider_id == user_info["sub"]).first()
    # create the user if not present
    if not user:
        user = models.User(
            name = user_info["name"],
            picture=user_info["picture"],
            email=user_info["email"],
            provider_id=user_info["sub"],
            provider="google"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    jwt_token = create_jwt(user.id)

    return {"access_token": jwt_token, "token_type": "bearer"}
