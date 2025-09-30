
from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import require_role
from .. import models
from .. import schemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import status
router = APIRouter(prefix="/clubs", tags=["Club Management"])


def is_existing_membership(user_id: int, club_id: int, db: Session):
    return db.query(models.Membership).filter(models.Membership.user_id == user_id, models.Membership.club_id == club_id).first()

# Create a club
@router.post("/", response_model=schemas.ClubOut, status_code=status.HTTP_201_CREATED)
def create_club(club : schemas.Club, user: models.User = Depends(require_role(role=models.GlobalRoles.SUPERUSER.value)), db: Session = Depends(get_db)):
    new_club = models.Club(name=club.name, description=club.description)
    
    db.add(new_club)
    db.commit()
    db.refresh(new_club)

    return new_club

# make a user admin of a club
@router.put("/{club_id}/make_admin/{user_id}", response_model=schemas.MembershipOut, status_code=status.HTTP_201_CREATED)
def make_admin(club_id: int, user_id: int, user: models.User = Depends(require_role(role=models.GlobalRoles.SUPERUSER.value)), db: Session = Depends(get_db)):
    existing_member = is_existing_membership(user_id, club_id, db)
    if existing_member:
        if existing_member.role == models.ClubRoles.ADMIN.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already an admin of the club")
        else:
            # upgrade to an admin only possible if the one making the change is a superuser
            if user.global_role != models.GlobalRoles.SUPERUSER.value:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient Permissions to downgrade this user")

            existing_member.role = models.ClubRoles.ADMIN.value
            db.commit()
            db.refresh(existing_member)
            return existing_member
        
    new_membership = models.Membership(user_id=user_id, club_id=club_id, role=models.ClubRoles.ADMIN.value)
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    
    return new_membership

@router.put("/{club_id}/make_moderator/{user_id}", response_model=schemas.MembershipOut, status_code=status.HTTP_201_CREATED)
def make_moderator(club_id: int, user_id: int, user: models.User = Depends(require_role(role=models.ClubRoles.ADMIN.value)), db: Session = Depends(get_db)):
    existing_member = is_existing_membership(user_id, club_id, db)
    if existing_member:
        if existing_member.role == models.ClubRoles.MODERATOR.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a moderator of the club")
        else:
            changer_membership = is_existing_membership(user.id, club_id, db)
            if user.global_role != models.GlobalRoles.SUPERUSER.value:
                # downgrade/upgrade to moderator only possible if rank lower than the user making the change
                if not changer_membership or changer_membership.role <= existing_member.role:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient Permissions to downgrade this user")
                
            existing_member.role = models.ClubRoles.MODERATOR.value
            db.commit()
            db.refresh(existing_member)
            return existing_member
    
    new_membership = models.Membership(user_id=user_id, club_id=club_id, role=models.ClubRoles.ADMIN.value)
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    
    return new_membership

@router.put("/{club_id}/make_member/{user_id}", response_model=schemas.MembershipOut, status_code=status.HTTP_201_CREATED)
def add_member(club_id: int, user_id: int, user: models.User = Depends(require_role(role=models.ClubRoles.MODERATOR.value)), db: Session = Depends(get_db)):
    existing_member = is_existing_membership(user_id, club_id, db)
    if is_existing_membership(user_id, club_id, db):
        if existing_member.role == models.ClubRoles.MEMBER.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of the club")
        else:
            # downgrade only possible if rank lower than the user making the change
            changer_membership = is_existing_membership(user.id, club_id, db)
            if user.global_role != models.GlobalRoles.SUPERUSER.value:
                if not changer_membership or changer_membership.role <= existing_member.role:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient Permissions to downgrade this user")
                
            existing_member.role = models.ClubRoles.MEMBER.value
            db.commit()
            db.refresh(existing_member)
            return existing_member
    new_membership = models.Membership(user_id=user_id, club_id=club_id, role=models.ClubRoles.MEMBER.value)
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)

    return new_membership

# remove a user from a club
@router.delete("/{club_id}/delete_user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(club_id: int, user_id: int, user: models.User = Depends(require_role(role=models.ClubRoles.MEMBER.value)), db: Session = Depends(get_db)):
    existing_member = is_existing_membership(user_id, club_id, db)
    if not existing_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not a member of the club")
    else:
        # removal only possible if rank lower than the user making the change
        changer_membership = is_existing_membership(user.id, club_id, db)
        if user.global_role != models.GlobalRoles.SUPERUSER.value:
            if not changer_membership or changer_membership.role <= existing_member.role:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient Permissions to remove this user")
        
        db.delete(existing_member)
        db.commit()
        return status.HTTP_204_NO_CONTENT