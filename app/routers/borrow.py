from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from ..dependencies import require_global_role, require_club_role, is_club_exist, is_item_exist
from .. import models
from .. import schemas
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import status
import logging
from fastapi import APIRouter, Depends, HTTPException, status

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
# @router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.BorrowItemOut)
# def borrow_item(
#     club_id : int,
#     borrow_data : schemas.BorrowItemIn,
#     user: models.User = Depends(require_global_role(role=models.ClubRoles.MEMBER.value)), 
#     db: Session = Depends(get_db),
#     item : models.Item = Depends(is_item_exist)
#     ):

#     if item.club_id != club_id:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item does not belong to the club")
    
#     print(item.status, models.ItemStatus.AVAILABLE)
#     if item.status != models.ItemStatus.AVAILABLE:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item is not available for borrowing")
    
#     if borrow_data.return_date is not None:
#         if borrow_data.return_date <= datetime.now(datetime.timezone.utc):
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Return date must be in the future")
        
#     borrowing_request = models.ItemBorrowingRequest(
#         item_id = item.id,
#         borrower_id = user.id,
#         return_date = borrow_data.return_date or datetime.now(timezone.utc) + timedelta(days=7)
#     )
#     item.status = models.ItemStatus.PENDING_BORROWAL if item.is_high_risk else models.ItemStatus.BORROWED
#     db.add(borrowing_request)
#     borrow_transaction = models.ItemBorrowingTransaction(
#         item_borrowing_request = borrowing_request,
#         status = models.BorrowStatus.PENDING_APPROVAL if item.is_high_risk else models.BorrowStatus.APPROVED,
#         operator_id = None
#         )
#     db.add(borrow_transaction)
#     db.commit()
#     db.refresh(borrowing_request)
#     db.refresh(item)
#     db.refresh(borrow_transaction)

#     return {"ItemBorrowingRequest" : borrowing_request, 
#             "ItemBorrowingTransaction" : borrow_transaction}

# Change to borrow by QR code not an ID and the status should be unavailable not borrowed (no need to track many stage in the item status)
@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.BorrowItemOut)
def borrow_item_by_qr(
    club_id: int,
    body: schemas.BorrowByQRIn,
    user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)),
    db: Session = Depends(get_db),
):
    try:
        logging.info(f"[BorrowItem] club_id={club_id}, user_id={user.id}, qr_code={body.qr_code}")

        # Fetch item by QR code
        item = db.query(models.Item).filter(models.Item.qr_code == body.qr_code).first()
        if not item:
            logging.warning(f"[BorrowItem] Item not found for QR code: {body.qr_code}")
            raise HTTPException(status_code=404, detail="Item with this QR code not found")

        logging.debug(f"[BorrowItem] Item found: id={item.id}, status={item.status}, club_id={item.club_id}")

        if item.club_id != club_id:
            logging.warning(f"[BorrowItem] Item club mismatch: expected={club_id}, found={item.club_id}")
            raise HTTPException(status_code=400, detail="Item does not belong to this club")

        if item.status != models.ItemStatus.AVAILABLE:
            logging.warning(f"[BorrowItem] Item not available: status={item.status}")
            raise HTTPException(status_code=400, detail="Item is not available for borrowing")

        if body.return_date and body.return_date <= datetime.now(timezone.utc):
            logging.warning(f"[BorrowItem] Invalid return date: {body.return_date}")
            raise HTTPException(status_code=400, detail="Return date must be in the future")
        
        # Create borrowing request
        borrowing_request = models.ItemBorrowingRequest(
            item_id=item.id,
            borrower_id=user.id,
            return_date=body.return_date or datetime.now(timezone.utc) + timedelta(days=7),
        )

        item.status = models.ItemStatus.UNAVAILABLE

        borrow_transaction = models.ItemBorrowingTransaction(
            item_borrowing_request=borrowing_request,
            status=(
                models.BorrowStatus.PENDING_APPROVAL
                if item.is_high_risk
                else models.BorrowStatus.APPROVED
            ),
            operator_id=None,
        )

        db.add_all([borrowing_request, borrow_transaction])
        db.commit()
        db.refresh(borrowing_request)
        db.refresh(borrow_transaction)

        logging.info(f"[BorrowItem] Success: item_id={item.id}, request_id={borrowing_request.id}")
        return {
            "ItemBorrowingRequest": borrowing_request,
            "ItemBorrowingTransaction": borrow_transaction,
        }

    except HTTPException as e:
        logging.error(f"[BorrowItem] HTTP error: {e.detail}")
        db.rollback()
        raise e

    except Exception as e:
        logging.exception(f"[BorrowItem] Unexpected error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while processing borrow request: {str(e)}",
        )
