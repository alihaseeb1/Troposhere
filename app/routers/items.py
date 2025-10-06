from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from ..dependencies import require_global_role, require_club_role, is_item_exist, is_club_exist
from .. import models
from .. import schemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import status

router = APIRouter(prefix="/items", tags=["Item Management"])



# Create an item without a club (requires SUPERUSER role)
@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.ItemOut)
def add_item(item : schemas.Item, 
             user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)), 
             db: Session = Depends(get_db)):
    new_item = models.Item(**item.model_dump(), club_id = None)
    print(new_item)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


# Delete an item
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)), 
    db: Session = Depends(get_db),
    item : models.Item = Depends(is_item_exist)
    ):
    
    db.delete(item)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# change ownership of item from a club
@router.patch("/{item_id}", response_model=schemas.ItemOut)
def change_ownership(to_club: schemas.ItemTransferIn,
                     user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)),
                     item : models.Item = Depends(is_item_exist), 
                     db: Session = Depends(get_db)):

    if to_club.club_id is not None:
        club = db.query(models.Club).filter(models.Club.id == to_club.club_id).first()
        if not club:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club does not exist")                 
    
    if item.club_id == to_club.club_id:
        if item.club_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item already in the club")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove from a club, since it has no club")

    item.club_id = to_club.club_id
    db.commit()
    db.refresh(item)

    return item

# Update an item without a club (requires SUPERUSER role) 
@router.put("/{item_id}", status_code=status.HTTP_200_OK, response_model=schemas.ItemOut)
def update_item(new_item : schemas.ItemUpdate, 
             user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)), 
             item : models.Item = Depends(is_item_exist),
             db: Session = Depends(get_db)):
    
    for field, value in new_item.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return item        

