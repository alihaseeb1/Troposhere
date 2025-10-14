from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy import Enum, select, desc, func
from ..dependencies import require_global_role, is_item_exist, is_club_exist, require_club_role
from .. import models
from .. import schemas
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from fastapi import status
import logging

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
        if isinstance(value, Enum):
            value = value.value
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return item        

# Approve or reject a borrowing or return transaction by moderator (of each club) or admin (superuser)
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
            raise HTTPException(status_code=404, detail="Transaction not found")

        borrow_request = transaction.item_borrowing_request
        item = borrow_request.item
        borrower = borrow_request.borrower

        logging.debug(f"Transaction fetched: {transaction.id}, Status: {transaction.status}")
        logging.debug(f"Item: ({item.id}, '{item.name}'), Club: ({item.club.id}, '{item.club.name}')")
        logging.debug(f"Approver: ({user.id}, '{user.name}'), Global role: {user.global_role}")

        if user.global_role != models.GlobalRoles.SUPERUSER:
            # Normal user → must be MODERATOR of this club
            membership = (
                db.query(models.Membership)
                .filter(
                    models.Membership.user_id == user.id,
                    models.Membership.club_id == item.club_id
                )
                .first()
            )
            if not membership:
                raise HTTPException(status_code=403, detail="You are not a member of this club.")

            role_value = membership.role.value if hasattr(membership.role, "value") else membership.role

            if role_value < models.ClubRoles.MODERATOR.value:
                raise HTTPException(status_code=403, detail="Only moderators can approve.")

            logging.debug(f"Approver’s membership → User: {membership.user_id}, Club: {membership.club_id}, Role: {membership.role}")
        else:
            logging.debug("Superuser detected — skipping membership check.")

        current_status = transaction.status
        action = approve.action.lower()
        logging.debug(f"Action: {action}, Current status: {current_status}, Item status: {item.status}")

        if current_status == models.BorrowStatus.PENDING_APPROVAL:
            if action == "approve":
                transaction.status = models.BorrowStatus.APPROVED
                item.status = models.ItemStatus.UNAVAILABLE
            else:
                raise HTTPException(status_code=400, detail="Invalid action")

        elif current_status == models.BorrowStatus.PENDING_CONDITION_CHECK:
            if action == "approve":
                transaction.status = models.BorrowStatus.COMPLETED
                item.status = models.ItemStatus.AVAILABLE
            elif action == "reject":
                transaction.status = models.BorrowStatus.REJECTED
                item.status = models.ItemStatus.UNAVAILABLE
            else:
                raise HTTPException(status_code=400, detail="Invalid action")

        else:
            raise HTTPException(
                status_code=400,
                detail="Transaction cannot be approved or rejected in its current state",
            )

        logging.debug(f"Transaction updated → Status: {transaction.status}, Item: {item.status}")
        transaction.operator_id = user.id

        # response message
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
        return resp

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logging.exception(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# Get all items in a club
@router.get("/club/{club_id}", response_model=list[schemas.ClubItemSummaryOut])
def get_items_in_club(
    club_id: int,
    user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)),
    club: models.Club = Depends(is_club_exist), 
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(10, gt=0, le=100, description="Number of items to return per page"),
):

    logging.info(f"Fetching items for club_id={club_id}")

    items_query = (
        select(models.Item)
        .where(models.Item.club_id == club_id)
        .order_by(models.Item.id.asc())
        .offset(skip)
        .limit(limit)
    )

    items = db.execute(items_query).scalars().all()

    if not items:
        raise HTTPException(status_code=404, detail="No items found for this club")

    item_list = []
    for item in items:
        item_data = schemas.ClubItemSummaryOut.model_validate(item, from_attributes=True)
        item_list.append(item_data)

    return item_list

# Get item details by item ID
@router.get("/{item_id}", response_model=schemas.ItemOut)
def get_item_detail(
    item_id: int,
    db: Session = Depends(get_db),
):

    item = (
        db.execute(
            select(models.Item)
            .where(models.Item.id == item_id)
        )
        .scalars()
        .first()
    )

    if not item:
        raise HTTPException(status_code=400, detail="Item not found")

    return schemas.ItemOut.model_validate(item, from_attributes=True)

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
        if user.global_role != models.GlobalRoles.SUPERUSER:
            membership = (
                db.query(models.Membership)
                .filter(
                    models.Membership.user_id == user.id,
                    models.Membership.club_id == club_id
                )
                .first()
            )
            if not membership:
                raise HTTPException(status_code=403, detail="You are not a member of this club.")

            role_value = membership.role.value if hasattr(membership.role, "value") else membership.role
            if role_value < models.ClubRoles.MODERATOR.value:
                raise HTTPException(status_code=403, detail="Only moderators can view approval requests.")

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
            raise HTTPException(status_code=404, detail="No pending approval requests found for this club")

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
        raise HTTPException(status_code=500, detail="Internal Server Error")
