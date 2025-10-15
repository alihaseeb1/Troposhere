from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from ..dependencies import require_global_role, require_club_role, is_club_exist, is_item_exist, require_member_role
from .. import models
from .. import schemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import status
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

router = APIRouter(prefix="/clubs/{club_id}/borrow", tags=["Club Management", "Borrowing"])


# def delete_item(
#     user: models.User = Depends(require_global_role(role=models.GlobalRoles.SUPERUSER.value)), 
#     db: Session = Depends(get_db),
#     item : models.Item = Depends(is_item_exist)
#     ):


"""
if high risk then item status will be borrowed and borrow request will be created 
Additionally a transaction will be created for the borrowing request with status as PENDING_APPROVAL
We will also check if item exists, belongs to a club and is available for borrowing

"""

# Change to borrow by QR code not an ID and the status should be unavailable not borrowed 
# (no need to track many stage in the item status)
@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.BorrowItemOut)
def borrow_item_by_qr(
    club_id: int,
    body: schemas.BorrowByQRIn,
    user: models.User = Depends(require_member_role()),
    club: models.Club = Depends(is_club_exist),
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
        if item.status != models.ItemStatus.AVAILABLE:
            raise HTTPException(status_code=400, detail="Item is not available for borrowing")
        if body.return_date and body.return_date <= datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Return date must be in the future")

        borrowing_request = models.ItemBorrowingRequest(
            item_id=item.id,
            borrower_id=user.id,
            return_date=body.return_date or (datetime.now(timezone.utc) + timedelta(days=7)),
        )

        tx_status = (
            models.BorrowStatus.PENDING_APPROVAL
            if getattr(item, "is_high_risk", False)
            else models.BorrowStatus.APPROVED
        )

        borrow_transaction = models.ItemBorrowingTransaction(
            item_borrowing_request=borrowing_request,
            status=tx_status,
            operator_id=None,
        )

        item.status = models.ItemStatus.UNAVAILABLE
        db.add_all([borrowing_request, borrow_transaction])


        message = "Pending Approval" if getattr(item, "is_high_risk", False) else "Successfully borrowed"
        resp = schemas.BorrowItemOut.model_validate(
            {
                "message": message,
                "item_name": item.name, 
            },
            from_attributes=True,
        )

        db.commit()
        return resp

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
