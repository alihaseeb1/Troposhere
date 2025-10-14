from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import  require_club_role, is_club_exist
from .. import models
from .. import schemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import status
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, desc

router = APIRouter(prefix="/clubs/{club_id}/return", tags=["Club Management", "Return"])

@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.BorrowItemOut)
def return_item_by_qr(
    club_id: int,
    body: schemas.ReturnByQRIn,
    club: models.Club = Depends(is_club_exist),
    user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)),
    db: Session = Depends(get_db),
):
    try:
        item = (
            db.execute(
                select(models.Item)
                .where(models.Item.qr_code == body.qr_code)
                .with_for_update()
            ).scalars().first()
        )

        if not item:
            raise HTTPException(status_code=400, detail="Item with this QR code not found")
        if item.club_id != club_id:
            raise HTTPException(status_code=400, detail="Item does not belong to this club")
        if item.status != models.ItemStatus.UNAVAILABLE:
            raise HTTPException(status_code=400, detail="Item is not currently borrowed")
        
        membership = (
            db.query(models.Membership)
            .filter(
                models.Membership.user_id == user.id,
                models.Membership.club_id == club.id,
            )
            .first()
        )
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this club")

        borrowing_transaction= (
            db.execute(
                select(models.ItemBorrowingTransaction)
                .join(models.ItemBorrowingRequest)
                .where(models.ItemBorrowingRequest.item_id == item.id)
                .order_by(desc(models.ItemBorrowingTransaction.processed_at))
        )).scalars().first()

        if borrowing_transaction.status != models.BorrowStatus.APPROVED:
            raise HTTPException(status_code=400, detail="Item borrowing not approved yet")
        
        if borrowing_transaction.item_borrowing_request.borrower_id != user.id:
            raise HTTPException(status_code=403, detail="You do not have permission to return this item")
        
        return_status = (models.BorrowStatus.PENDING_CONDITION_CHECK if item.is_high_risk 
                         else models.BorrowStatus.COMPLETED)
        
        return_transaction = models.ItemBorrowingTransaction(
            item_borrowing_request_id= borrowing_transaction.item_borrowing_request_id,
            operator_id = None,
            status= return_status,
            remarks = "Item returned, pending condition check" if item.is_high_risk else "Item returned by user"
        )

        if not item.is_high_risk:
            item.status = models.ItemStatus.AVAILABLE

        db.add(return_transaction)
        db.commit()

        message = "Item returned, pending condition check" if item.is_high_risk else "Item successfully returned"

        resp = schemas.BorrowItemOut.model_validate(
            {"message": message, "item_name": item.name},
            from_attributes=True,
        )   

        return resp
        
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
        