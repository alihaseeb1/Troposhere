from fastapi import APIRouter, Depends, HTTPException, Response, Query, UploadFile, File
from sqlalchemy import Enum, select, func, or_
from ..dependencies import require_global_role, is_item_exist, is_club_exist, require_club_role
from .. import models
from .. import schemas
from sqlalchemy.orm import Session, joinedload, selectinload
from ..database import get_db
from fastapi import status
import logging
from typing import List, Union
from ..utils.upload_file import upload_file_to_s3, delete_old_file_from_s3, generate_safe_filename
from fastapi.responses import JSONResponse
from ..utils.log import log_operation

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

    log_operation(
        db,
        tablename="items",
        operation="INSERT",
        who_id=user.id,
        new_val=new_item.__dict__,
    )

    return new_item

# superuser can upload the image that doesn't belong to each club
@router.post("/{item_id}/upload-images", status_code=status.HTTP_200_OK)
def upload_item_images(
    item_id: int,
    files: Union[List[UploadFile], UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value))
):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if isinstance(files, UploadFile):
        files = [files]

    uploaded_images = []

    for file in files:
        file_name = f"items/{file.filename}"
        image_url = upload_file_to_s3(file, file_name)

        new_image = models.ItemImage(
            item_id=item.id,
            image_url=image_url
        )
        db.add(new_image)
        uploaded_images.append(image_url)

    log_operation(
        db,
        tablename="item_images",
        operation="INSERT",
        who_id=user.id,
        new_val={"item_id": item.id, "images": uploaded_images},
    )

    db.commit()

    response_data = {
        "message": f"Uploaded {len(uploaded_images)} image(s) for item '{item.name}' successfully",
        "item_id": item.id,
        "images": uploaded_images
    }

    return JSONResponse(content=response_data, status_code=status.HTTP_200_OK)

# superuser can delete image(s) of an item (by image URL)
@router.delete("/{item_id}/delete-images", status_code=status.HTTP_200_OK)
def delete_item_images(
    item_id: int,
    request: schemas.DeleteItemImagesRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value))
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
    
    if not deleted_images:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching images found for deletion")

    db.commit()

    log_operation(
        db,
        tablename="item_images",
        operation="DELETE",
        who_id=user.id,
        old_val={"item_id": item.id, "deleted_images": deleted_images},
    )


    return {
        "message": f"Deleted {len(deleted_images)} image(s) for item '{item.name}' successfully",
        "item_id": item.id,
        "deleted_images": deleted_images
    }

# Delete an item
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)), 
    db: Session = Depends(get_db),
    item : models.Item = Depends(is_item_exist)
    ):
    old_val = item.__dict__.copy()
    db.delete(item)
    db.commit()

    log_operation(
        db,
        tablename="items",
        operation="DELETE",
        who_id=user.id,
        old_val=old_val,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# change ownership of item from a club
@router.patch("/{item_id}", response_model=schemas.ItemOut)
def change_ownership(to_club: schemas.ItemTransferIn,
                     user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)),
                     item : models.Item = Depends(is_item_exist), 
                     db: Session = Depends(get_db)):

    old_val = {"item_id" : item.id, "club_id": item.club_id}

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

    log_operation(
        db,
        tablename="items",
        operation="UPDATE",
        who_id=user.id,
        old_val=old_val,
        new_val={"item_id" : item.id, "club_id": item.club_id},
    )
    
    return item

# Superusers can update an item without a club 
@router.put("/{item_id}", status_code=status.HTTP_200_OK, response_model=schemas.ItemOut)
def update_item(new_item : schemas.ItemUpdate, 
             user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)), 
             item : models.Item = Depends(is_item_exist),
             db: Session = Depends(get_db)):
    
    old_val = item.__dict__.copy()

    for field, value in new_item.model_dump(exclude_unset=True).items():
        if isinstance(value, Enum):
            value = value.value
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    print(item.__dict__)
    log_operation(
        db,
        tablename="items",
        operation="UPDATE",
        who_id=user.id,
        old_val=old_val,
        new_val=item.__dict__,
    )

    return item        

# Approve or reject a borrowing or return transaction by moderator (of each club) or superuser
@router.put("/clubs/{club_id}/approval/{transaction_id}", response_model=schemas.ItemBorrowingTransactionOut)
def approve_item_transaction(
    club_id: int,
    transaction_id: int,
    approve: schemas.ApproveIn,
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.USER.value)),
    db: Session = Depends(get_db),
):
    logging.info(f"Approval request received: club_id={club_id}, transaction_id={transaction_id}")

    try:
        transaction = (
            db.query(models.ItemBorrowingTransaction)
            .options(
                joinedload(models.ItemBorrowingTransaction.item_borrowing_request)
                .joinedload(models.ItemBorrowingRequest.item)
                .joinedload(models.Item.club),
                joinedload(models.ItemBorrowingTransaction.item_borrowing_request)
                .joinedload(models.ItemBorrowingRequest.borrower),
            )
            .filter(models.ItemBorrowingTransaction.id == transaction_id)
            .first()
        )

        if not transaction:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Transaction not found")

        borrow_request = transaction.item_borrowing_request
        item = borrow_request.item
        borrower = borrow_request.borrower

        logging.debug(f"Transaction fetched: {transaction.id}, Status: {transaction.status}")
        logging.debug(f"Item: ({item.id}, '{item.name}'), Club: ({item.club.id}, '{item.club.name}')")
        logging.debug(f"Approver: ({user.id}, '{user.name}'), Global role: {user.global_role}")

        if user.global_role == models.GlobalRoles.SUPERUSER.value:
            logging.debug("Superuser detected — bypassing club role check.")
        else:
            # Normal user → must be MODERATOR only
            membership = (
                db.query(models.Membership)
                .filter(
                    models.Membership.user_id == user.id,
                    models.Membership.club_id == item.club_id
                )
                .first()
            )

            role_value = membership.role.value if hasattr(membership.role, "value") else membership.role

            if role_value != models.ClubRoles.MODERATOR.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only moderators or superusers can approve transactions."
                )

            logging.debug(f"Membership verified: Role {role_value} (Moderator)")

        current_status = transaction.status
        action = approve.action.lower()

        if current_status == models.BorrowStatus.PENDING_APPROVAL:
            if action == "approve":
                transaction.status = models.BorrowStatus.APPROVED
                item.status = models.ItemStatus.UNAVAILABLE
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action for this status.")

        elif current_status == models.BorrowStatus.PENDING_CONDITION_CHECK:
            if action == "approve":
                transaction.status = models.BorrowStatus.COMPLETED
                item.status = models.ItemStatus.AVAILABLE
            elif action == "reject":
                transaction.status = models.BorrowStatus.REJECTED
                item.status = models.ItemStatus.UNAVAILABLE
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action for this status.")

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction cannot be approved or rejected in its current state.",
            )

        transaction.operator_id = user.id

        if transaction.status == models.BorrowStatus.REJECTED:
            message = f"The request for '{item.name}' has been rejected."
        elif transaction.status == models.BorrowStatus.APPROVED:
            message = f"Borrowing of '{item.name}' approved."
        elif transaction.status == models.BorrowStatus.COMPLETED:
            message = f"Return of '{item.name}' approved and item is now available."
        else:
            message = "Transaction processed successfully."

        resp = schemas.ItemBorrowingTransactionOut.model_validate(
            {
                "message": message,
                "item_name": item.name,
                "status": transaction.status.value,
            },
            from_attributes=True,
        )

        db.commit()

        log_operation(
            db,
            tablename="item_borrowing_transaction",
            operation="UPDATE",
            who_id=user.id,
            new_val={"transaction_id": transaction_id, "status": transaction.status.value},
            old_val={"previous_status": current_status.value if hasattr(current_status, "value") else current_status},
        )
        return resp

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logging.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")

@router.get(
    "/club/{club_id}",
    response_model=schemas.ItemSearchResponse,
    status_code=status.HTTP_200_OK
)
def get_or_search_items_in_club(
    club_id: int,
    query: str | None = Query(None, description="Search keyword (optional, matches name or description)"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, gt=0, le=100, description="Number of items to return per page"),
    user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)),
    club: models.Club = Depends(is_club_exist),
    db: Session = Depends(get_db),
):

    logging.info(f"Fetching items for club_id={club_id}, query='{query}'")

    q = db.query(models.Item).options(selectinload(models.Item.images)).filter(models.Item.club_id == club_id)

    if query:
        q = q.filter(
            or_(
                models.Item.name.ilike(f"%{query}%"),
                models.Item.description.ilike(f"%{query}%")
            )
        )

    items = q.order_by(models.Item.id.asc()).offset(skip).limit(limit).all()

    if not items:
        logging.info("No items found for this club.")
        return schemas.ItemSearchResponse(message="No items found.", data=[])

    results = []
    for item in items:
        image_urls = [img.image_url for img in item.images] if item.images else []
        logging.info(f"Item {item.id} ({item.name}) has {len(image_urls)} image(s): {image_urls}")

        results.append(
            schemas.ItemSearchOut(
                id=item.id,
                name=item.name,
                description=item.description,
                status=item.status.value if hasattr(item.status, "value") else item.status,
                is_high_risk=item.is_high_risk,
                qr_code=getattr(item, "qr_code", None),
                images=image_urls
            )
        )

    return schemas.ItemSearchResponse(
        message="Successfully retrieved items." if not query else "Successfully retrieved search results.",
        data=results
    )

@router.get("/{item_id}", response_model=schemas.ItemOut)
def get_item_detail(
    item_id: int,
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.Item)
        .options(selectinload(models.Item.images))
        .filter(models.Item.id == item_id)
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Item not found"
        )

    item_data = schemas.ItemOut(
        id=item.id,
        name=item.name,
        description=item.description,
        status=item.status.value if hasattr(item.status, "value") else item.status,
        is_high_risk=item.is_high_risk,
        qr_code=item.qr_code,
        created_at=item.created_at,
        club_id=item.club_id,
        images=[img.image_url for img in item.images] if item.images else []
    )

    return item_data

# Get latest pending approval or condition check of items in each club
@router.get("/clubs/{club_id}/approval", response_model=list[schemas.PendingApprovalOut])
def get_latest_pending_transactions(
    club_id: int,
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.USER.value)),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination"),
    limit: int = Query(10, gt=0, le=100, description="Number of records to return per page"),
):
    logging.info(f"Fetching latest pending approvals for club_id={club_id}, skip={skip}, limit={limit}")

    try:
        if user.global_role == models.GlobalRoles.SUPERUSER.value:
            logging.debug("Superuser detected — bypassing club role check.")
        else:
            membership = (
                db.query(models.Membership)
                .filter(
                    models.Membership.user_id == user.id,
                    models.Membership.club_id == club_id
                )
                .first()
            )

            role_value = membership.role.value if hasattr(membership.role, "value") else membership.role
            logging.debug(f"User membership role in club {club_id}: {role_value}")
            if role_value != models.ClubRoles.MODERATOR.value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only moderators or superusers can approve transactions."
                )

            logging.debug(f"Membership verified: Role {role_value} (Moderator)")

        subq = (
            select(
                models.ItemBorrowingTransaction.item_borrowing_request_id,
                func.max(models.ItemBorrowingTransaction.id).label("latest_transaction_id")
            )
            .join(models.ItemBorrowingRequest)
            .join(models.Item)
            .where(models.Item.club_id == club_id)
            .group_by(models.ItemBorrowingTransaction.item_borrowing_request_id)
            .subquery()
        )

        latest_transactions = (
            db.query(models.ItemBorrowingTransaction)
            .join(subq, models.ItemBorrowingTransaction.id == subq.c.latest_transaction_id)
            .join(models.ItemBorrowingTransaction.item_borrowing_request)
            .join(models.ItemBorrowingRequest.item)
            .options(
                joinedload(models.ItemBorrowingTransaction.item_borrowing_request)
                .joinedload(models.ItemBorrowingRequest.item)
                .joinedload(models.Item.club),
                joinedload(models.ItemBorrowingTransaction.item_borrowing_request)
                .joinedload(models.ItemBorrowingRequest.borrower),
            )
            .filter(
                models.ItemBorrowingTransaction.status.in_([
                    models.BorrowStatus.PENDING_APPROVAL,
                    models.BorrowStatus.PENDING_CONDITION_CHECK,
                ])
            )
            .order_by(models.ItemBorrowingTransaction.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        if not latest_transactions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pending approval requests found for this club")

        transaction_list = []
        for tx in latest_transactions:
            item = tx.item_borrowing_request.item
            borrower = tx.item_borrowing_request.borrower

            if tx.status == models.BorrowStatus.PENDING_APPROVAL:
                message = f"Borrow request for '{item.name}' is waiting for approval."
            elif tx.status == models.BorrowStatus.PENDING_CONDITION_CHECK:
                message = f"Return request for '{item.name}' is waiting for condition check."
            else:
                message = "Transaction in progress."

            tx_data = schemas.PendingApprovalOut.model_validate(
                {
                    "transaction_id": tx.id,
                    "item_id": item.id,
                    "item_name": item.name,
                    "borrower_name": borrower.name if borrower else "Unknown",
                    "status": tx.status.value,
                    "requested_at": getattr(tx, "processed_at", None),
                    "message": message,
                },
                from_attributes=True,
            )

            transaction_list.append(tx_data)

        return transaction_list

    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Unexpected error while fetching approvals for club {club_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")