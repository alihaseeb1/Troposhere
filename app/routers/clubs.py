
from fastapi import APIRouter, Depends
from ..dependencies import require_role
from .. import models

router = APIRouter(prefix="/clubs", tags=["Club Management"])

# Create a club
@router.post("/")
def create_club(user: models.User = Depends(require_role(role=models.GlobalRoles.SUPERUSER.value))):
    return {"message": "Create a new club"}

# make a user admin of a club
@router.post("/{club_id}/make_admin/{user_id}")
def make_admin(club_id: int, user_id: int, user: models.User = Depends(require_role(role=models.GlobalRoles.SUPERUSER.value))):
    return {"message": f"Make user {user_id} an admin of club {club_id}"}

@router.post("/{club_id}/make_moderator/{user_id}")
def make_moderator(club_id: int, user_id: int, user: models.User = Depends(require_role(role=models.ClubRoles.ADMIN.value))):
    return {"message": f"Make user {user_id} a moderator of club {club_id}"}
