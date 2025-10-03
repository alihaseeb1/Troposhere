
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from ..dependencies import require_global_role, require_club_role, is_club_exist
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
def create_club(club : schemas.Club, user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)), db: Session = Depends(get_db)):
    new_club = models.Club(name=club.name, description=club.description)
    
    db.add(new_club)
    db.commit()
    db.refresh(new_club)

    return new_club

# delete an existing club
@router.delete("/{club_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_club(user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)), 
                db: Session = Depends(get_db), 
                club : models.Club = Depends(is_club_exist)):
    
    db.delete(club)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# get all club members
@router.get("/{club_id}/members", response_model=list[schemas.ClubMembersOut])
def get_club_members(club_id : int, 
                     user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)), 
                     db: Session = Depends(get_db)):
    
    members = db.query(models.User, models.Membership).join(models.Membership, models.User.id==models.Membership.user_id).filter(models.Membership.club_id == club_id).all()

    return members


# Modify user roles or add a user to a club
@router.put("/{club_id}/roles/{user_id}", response_model=schemas.MembershipOut)
def set_roles(club_id: int, 
              user_id: int, set_role: schemas.MembershipIn, 
              user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)), 
              db: Session = Depends(get_db)):
    
    existing_member = is_existing_membership(user_id, club_id, db)
    
    if existing_member:
        if existing_member.role == set_role.role.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User is already a(an) {set_role.role.name} of the club")
        else:
            changer_membership = is_existing_membership(user.id, club_id, db)
            if user.global_role != models.GlobalRoles.SUPERUSER.value:
                # downgrade/upgrade to moderator only possible if rank lower than the user making the change
                if not changer_membership or changer_membership.role <= existing_member.role:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Insufficient Permissions to Set Membership Role to {set_role.role.name} for user_id: {user_id}")
                if set_role.role.value >= changer_membership.role:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Insufficient Permissions to Set Membership Role to {set_role.role.name} for user_id: {user_id}")
                

            existing_member.role = set_role.role.value
            db.commit()
            db.refresh(existing_member)
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(existing_member))
        
    new_membership = models.Membership(user_id=user_id, club_id=club_id, role=set_role.role.value)
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=jsonable_encoder(new_membership))

# remove a user from a club
@router.delete("/{club_id}/roles/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(club_id: int, user_id: int, 
                  user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)), 
                  db: Session = Depends(get_db)):
    
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
        return Response(status.HTTP_204_NO_CONTENT)
    
@router.post("/{club_id}/items", status_code=status.HTTP_201_CREATED, response_model=schemas.ItemOut, tags=["Item Management"])
def add_item(club_id : int, 
             item : schemas.Item, 
             club : models.Club = Depends(is_club_exist),
             user: models.User = Depends(require_club_role(role=models.ClubRoles.ADMIN.value)), 
             db: Session = Depends(get_db)):
    
    new_item = models.Item(**item.model_dump(), club_id = club_id)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item