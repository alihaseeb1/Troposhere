from typing import Optional
from fastapi.security import HTTPAuthorizationCredentials
import jwt
from fastapi import Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from .database import get_db
from .config import settings
from . import models
from .auth.oauth import security

# Dependency to get the current user from the JWT token (check if user is logged in)
def get_current_user(db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.PyJWTError:
        print("here")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(models.User).filter(models.User.id == int(payload.get("user_id"))).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# Dependecy to check if user has a specific role in a club to access certain routes as well as if they are logged in
def require_club_role(role: int):
    def role_checker(club_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
        # allow access if user is a superuser
        if current_user.global_role == models.GlobalRoles.SUPERUSER.value:
            return current_user
        
        # print("Checking for club", club_id)
        if club_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser role required")
        # else make sure appropriate club role is present

        membership = db.query(models.Membership).filter(
            models.Membership.user_id == current_user.id,
            models.Membership.club_id == club_id
        ).first()
        # if they have no membership at all in the current club then we provide no access
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient Permissions! Not a member of the Club")
        # we need the role to be higher or equal to the required role
        if role <= membership.role:
            return current_user
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient Permissions!")

    return role_checker


# Dependecy to check if user has a required global role in a club to access certain routes as well as if they are logged in
def require_global_role(role: int):
    def role_checker(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
        # allow access if user is a superuser
        if current_user.global_role >= role:
            return current_user
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient Global Permissions!")

    return role_checker