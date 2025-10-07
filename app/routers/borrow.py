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


router = APIRouter(prefix="/clubs/{club_id}/items/{item_id}/borrow", tags=["Club Management", "Borrowing"])


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
@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.BorrowItemOut)
def borrow_item(
    club_id : int,
    borrow_data : schemas.BorrowItemIn,
    user: models.User = Depends(require_global_role(role=models.ClubRoles.MEMBER.value)), 
    db: Session = Depends(get_db),
    item : models.Item = Depends(is_item_exist)
    ):

    if item.club_id != club_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item does not belong to the club")
    
    print(item.status, models.ItemStatus.AVAILABLE)
    if item.status != models.ItemStatus.AVAILABLE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item is not available for borrowing")
    
    if borrow_data.return_date is not None:
        if borrow_data.return_date <= datetime.now(datetime.timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Return date must be in the future")
        
    borrowing_request = models.ItemBorrowingRequest(
        item_id = item.id,
        borrower_id = user.id,
        return_date = borrow_data.return_date or datetime.now(timezone.utc) + timedelta(days=7)
    )
    item.status = models.ItemStatus.PENDING_BORROWAL if item.is_high_risk else models.ItemStatus.BORROWED
    db.add(borrowing_request)
    borrow_transaction = models.ItemBorrowingTransaction(
        item_borrowing_request = borrowing_request,
        status = models.BorrowStatus.PENDING_APPROVAL if item.is_high_risk else models.BorrowStatus.APPROVED,
        operator_id = None
        )
    db.add(borrow_transaction)
    db.commit()
    db.refresh(borrowing_request)
    db.refresh(item)
    db.refresh(borrow_transaction)

    return {"ItemBorrowingRequest" : borrowing_request, 
            "ItemBorrowingTransaction" : borrow_transaction}