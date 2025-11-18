from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from ..dependencies import require_global_role, require_club_role, is_club_exist, is_item_exist
from .. import models
from .. import schemas
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from fastapi import status
import logging
from ..utils.upload_file import upload_file_to_s3, delete_old_file_from_s3, create_unique_filename
from typing import List, Union
from ..utils.log import log_operation

router = APIRouter(prefix="/clubs", tags=["Club Management"])

def is_existing_membership(user_id: int, club_id: int, db: Session):
    return db.query(models.Membership).filter(models.Membership.user_id == user_id, models.Membership.club_id == club_id).first()

# search clubs by name 
@router.get("/search", response_model=list[schemas.ClubSimpleOut], status_code=status.HTTP_200_OK)
def search_clubs_by_name(
    query: str = "",
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.USER.value)),
    db: Session = Depends(get_db)
):
    logging.info(f"Searching clubs with query: '{query}'")
    clubs_query = db.query(models.Club)

    if query.strip():
        clubs_query = clubs_query.filter(
            func.lower(models.Club.name).like(f"%{query.lower()}%")
        )

    clubs = clubs_query.order_by(models.Club.id.asc()).all()

    if not clubs:
        return []

    return [
        schemas.ClubSimpleOut(
            id=club.id,
            name=club.name,
            description=club.description,
            image_path=club.image_path
        )
        for club in clubs
    ]

# upsert the club image (superuser only)
@router.post("/{club_id}/upload-image", status_code=status.HTTP_200_OK)
def upload_club_image(
    club_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value))
):
    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=404, detail="Club not found")

    old_data = club.__dict__

    if club.image_path:
        delete_old_file_from_s3(club.image_path)

    file_name = f"clubs/{create_unique_filename(file.filename)}"
    image_url = upload_file_to_s3(file, file_name)

    club.image_path = image_url
    db.commit()
    db.refresh(club)

    log_operation(
        db,
        tablename="clubs",
        operation="UPDATE",
        who_id=user.id,
        old_val=old_data,
        new_val=club
    )

    return {
        "message": f"Image for '{club.name}' uploaded successfully",
        "club_id": club.id,
        "image_url": image_url
    }

# Create a club (superuser only)
@router.post("/", response_model=schemas.ClubOut, status_code=status.HTTP_201_CREATED)
def create_club(club : schemas.Club, user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)), db: Session = Depends(get_db)):
    new_club = models.Club(name=club.name, description=club.description)
    # check if club name exists
    existing_club = db.query(models.Club).filter(models.Club.name == club.name).first()
    if existing_club:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Club with this name already exists")
    
    db.add(new_club)
    db.commit()
    db.refresh(new_club)

    log_operation(
        db,
        tablename="clubs",
        operation="CREATE",
        who_id=user.id,
        new_val=new_club
    )

    return new_club

# delete an existing club (superuser only)
@router.delete("/{club_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_club(user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)), 
                db: Session = Depends(get_db), 
                club : models.Club = Depends(is_club_exist)):
    
    old_data = club.__dict__.copy()

    db.delete(club)
    db.commit()
    
    log_operation(
        db,
        tablename="clubs",
        operation="DELETE",
        who_id=user.id,
        old_val=old_data
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# delete the club image (superuser only)
@router.delete("/{club_id}/delete-image", status_code=status.HTTP_200_OK)
def delete_club_image(
    club_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value))
):

    club = db.query(models.Club).filter(models.Club.id == club_id).first()
    if not club:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Club not found")

    if not club.image_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No image found for this club")

    old_data = club.__dict__

    delete_old_file_from_s3(club.image_path)

    club.image_path = None
    db.commit()
    db.refresh(club)

    log_operation(
        db,
        tablename="clubs",
        operation="UPDATE",
        who_id=user.id,
        old_val=old_data,
        new_val=club
    )

    return {
        "message": f"Image for '{club.name}' deleted successfully",
        "club_id": club.id
    }

# get all club members
@router.get("/{club_id}/members", response_model=schemas.ClubMembersResponse)
def get_club_members(
    club_id: int,
    user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)),
    db: Session = Depends(get_db)
):
    query = (
        db.query(models.User)
        .join(models.Membership, models.User.id == models.Membership.user_id)
        .filter(models.Membership.club_id == club_id)
    )

    total_members = query.count()
    members = query.all()

    if total_members == 0:
        return schemas.ClubMembersResponse(
            message="No members found in this club.",
            total_members=0,
            data=[]
        )

    members_data = [
        schemas.ClubMembersOut(
            user_id=member.id,
            name=member.name,
            email=member.email
        )
        for member in members
    ]

    return schemas.ClubMembersResponse(
        message="Successfully retrieved club members.",
        total_members=total_members,
        data=members_data
    )

# Get a single user membership from a club
@router.get("/{club_id}/members/{user_id}", response_model=schemas.ClubMembersOut)
def get_club_members(club_id : int, 
                     user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)), 
                     db: Session = Depends(get_db)):
    
    member = db.query(models.User, models.Membership).join(
        models.Membership, models.User.id==models.Membership.user_id
        ).filter(
            models.Membership.club_id == club_id and models.User.id == user.id
            ).first()

    return member

# Modify user roles or add a user to a club
# Moderator can only add members and admin can add moderators and members and the superuser can add any role
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
                
            old_data = existing_member.__dict__
            existing_member.role = set_role.role.value
            db.commit()
            db.refresh(existing_member)

            log_operation(
                db,
                tablename="memberships",
                operation="UPDATE",
                who_id=user.id,
                old_val=old_data,
                new_val=existing_member
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(existing_member))
        
    new_membership = models.Membership(user_id=user_id, club_id=club_id, role=set_role.role.value)
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    
    log_operation(
        db,
        tablename="memberships",
        operation="CREATE",
        who_id=user.id,
        new_val=new_membership
    )

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
        old_data = existing_member.__dict__.copy()
        changer_membership = is_existing_membership(user.id, club_id, db)
        if user.global_role != models.GlobalRoles.SUPERUSER.value:
            if not changer_membership or changer_membership.role <= existing_member.role:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient Permissions to remove this user")
        
        db.delete(existing_member)
        db.commit()

        log_operation(
            db,
            tablename="memberships",
            operation="DELETE",
            who_id=user.id,
            old_val=old_data
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

# admin can add the item belongs to their club or superuser can add item in any club
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

    log_operation(
        db,
        tablename="items",
        operation="CREATE",
        who_id=user.id,
        new_val=new_item
    )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "message": "Successfully added item",
            "data": jsonable_encoder(new_item)
        }
    )

# Only admin/superuser can update an item in a club
@router.put("/{club_id}/items/{item_id}", status_code=status.HTTP_200_OK, response_model=schemas.ItemOut, tags =["Item Management"])
def update_item(club_id : int, 
                new_item : schemas.ItemUpdate, 
                user: models.User = Depends(require_club_role(role=models.ClubRoles.ADMIN.value)), 
                item : models.Item = Depends(is_item_exist),
                db: Session = Depends(get_db)):
    
    if item.club_id != club_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item does not belong to this club")
    
    old_data = item.__dict__.copy()

    for field, value in new_item.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    log_operation(
        db,
        tablename="items",
        operation="UPDATE",
        who_id=user.id,
        old_val=old_data,
        new_val=item
    )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Successfully updated item",
            "data": jsonable_encoder(item)
        }
    )   

# admin/superuser can upload item image (single/multiple file)
@router.post("/{club_id}/items/{item_id}/upload-images", status_code=status.HTTP_200_OK)
def upload_item_images(
    club_id: int,
    item_id: int,
    files: Union[List[UploadFile], UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_club_role(role=models.ClubRoles.ADMIN.value))
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if isinstance(files, UploadFile):
        files = [files]

    uploaded_images = []

    for file in files:
        file_name = f"items/{create_unique_filename(file.filename)}"
        image_url = upload_file_to_s3(file, file_name)

        new_image = models.ItemImage(
            item_id=item.id,
            image_url=image_url
        )
        db.add(new_image)
        uploaded_images.append(image_url)

    db.commit()

    log_operation(
        db,
        tablename="item_images",
        operation="CREATE",
        who_id=user.id,
        new_val={"item_id": item.id, "images": uploaded_images}
    )

    response_data = {
        "message": f"Uploaded {len(uploaded_images)} image(s) for item '{item.name}' successfully",
        "club_id": club_id,
        "item_id": item.id,
        "images": uploaded_images
    }

    return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)

# superuser/admin can delete image(s) of an item (by image URL)
@router.delete("/{club_id}/items/{item_id}/delete-images", status_code=status.HTTP_200_OK)
def delete_item_images(
    club_id: int,
    item_id: int,
    request: schemas.DeleteItemImagesRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_club_role(role=models.ClubRoles.ADMIN.value))
):
    
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    image_urls = request.image_urls
    if not image_urls:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No image URLs provided")

    deleted_images = []

    for image_url in image_urls:
        image_record = db.query(models.ItemImage).filter(
            models.ItemImage.item_id == item_id,
            models.ItemImage.image_url == image_url
        ).first()

        if image_record:
            delete_old_file_from_s3(image_url)

            db.delete(image_record)
            deleted_images.append(image_url)

    db.commit()

    if not deleted_images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching images found for deletion")

    log_operation(
        db,
        tablename="item_images",
        operation="DELETE",
        who_id=user.id,
        old_val={"item_id": item.id, "deleted_images": deleted_images}
    )

    return {
        "message": f"Deleted {len(deleted_images)} image(s) for item '{item.name}' successfully",
        "item_id": item.id,
        "deleted_images": deleted_images
    }

@router.get("/{club_id}/details", response_model=schemas.ClubSimpleDetailsResponse, status_code=status.HTTP_200_OK)
def get_club_details(
    club_id: int,
    user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)),
    club: models.Club = Depends(is_club_exist),
    db: Session = Depends(get_db)
):
    member_count = (
        db.query(models.Membership)
        .filter(models.Membership.club_id == club_id)
        .count()
    )

    response_content = {
        "message": "Successfully retrieved club details.",
        "data": {
            "name": club.name,
            "description": club.description,
            "image_path": club.image_path,
            "total_members": member_count
        }
    }

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response_content
    )

@router.get("/", response_model=schemas.AllClubsResponse, status_code=status.HTTP_200_OK)
def get_all_clubs(
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)),
    db: Session = Depends(get_db)
):
    clubs = db.query(models.Club).order_by(models.Club.id.asc()).all()

    if not clubs:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "No clubs found.",
                "data": []
            }
        )

    results = []
    for club in clubs:
        member_count = (
            db.query(models.Membership)
            .filter(models.Membership.club_id == club.id)
            .count()
        )

        results.append({
            "name": club.name,
            "description": club.description,
            "image_path": club.image_path,
            "total_members": member_count
        })

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Successfully retrieved all clubs.",
            "data": results
        }
    )