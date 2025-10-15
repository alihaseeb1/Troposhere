from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import  require_global_role, is_club_exist, require_club_role
from .. import models
from sqlalchemy.orm import Session
from ..database import get_db
from fastapi import status
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from .. import schemas

router = APIRouter(prefix="/users", tags=["User Management"])

# Get borrowing history for a user
@router.get("/history", response_model=schemas.BorrowHistoryResponse)
def get_borrow_history(
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.USER.value)),
    db: Session = Depends(get_db)
):
    user_id = user.id
    logging.info(f"Fetching borrowing history for user_id={user_id}")

    history_records = (
        db.query(models.ItemBorrowingTransaction)
        .join(models.ItemBorrowingRequest)
        .join(models.Item)
        .filter(models.ItemBorrowingRequest.borrower_id == user_id)
        .order_by(models.ItemBorrowingTransaction.id.desc())
        .all()
    )

    if not history_records:
        return schemas.BorrowHistoryResponse(
            message="No transaction record found.",
            data=[]
        )

    results = [
        schemas.BorrowHistoryItem(
            transaction_id=record.id,
            item_name=record.item_borrowing_request.item.name,
            status=record.status.value if hasattr(record.status, "value") else record.status,
            borrow_date=getattr(record.item_borrowing_request, "created_at", None),
            return_date=getattr(record.item_borrowing_request, "return_date", None),
        )
        for record in history_records
    ]

    return schemas.BorrowHistoryResponse(
        message="Successfully retrieved borrowing history.",
        data=results
    )

# Get club admins for each club
@router.get(
    "/admin/club/{club_id}",
    response_model=schemas.ClubAdminResponse,
    status_code=status.HTTP_200_OK
)
def get_club_admins(
    club_id: int,
    user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)),
    club: models.Club = Depends(is_club_exist),
    db: Session = Depends(get_db)
):
    logging.info(f"Fetching club admins for club_id={club_id}, requested by user_id={user.id}")

    membership = (
        db.query(models.Membership)
        .filter(
            models.Membership.user_id == user.id,
            models.Membership.club_id == club_id
        )
        .first()
    )

    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    admin_memberships = (
        db.query(models.Membership)
        .join(models.User)
        .filter(
            models.Membership.club_id == club_id,
            models.Membership.role == models.ClubRoles.ADMIN.value
        )
        .all()
    )

    if not admin_memberships:
        return schemas.ClubAdminResponse(
            message="No admin found for this club.",
            data=[]
        )

    admins = [
        schemas.ClubAdminItem(
            user_id=membership.user.id,
            name=membership.user.name,
            email=membership.user.email
        )
        for membership in admin_memberships
    ]

    return schemas.ClubAdminResponse(
        message="Successfully retrieved club admins.",
        data=admins
    )

# Get club moderators for each club
@router.get(
    "/moderator/club/{club_id}",
    response_model=schemas.ClubAdminResponse,
    status_code=status.HTTP_200_OK
)
def get_club_moderator(
    club_id: int,
    user: models.User = Depends(require_club_role(role=models.ClubRoles.MEMBER.value)),
    club: models.Club = Depends(is_club_exist),
    db: Session = Depends(get_db)
):
    logging.info(f"Fetching club moderator for club_id={club_id}, requested by user_id={user.id}")

    membership = (
        db.query(models.Membership)
        .filter(
            models.Membership.user_id == user.id,
            models.Membership.club_id == club_id
        )
        .first()
    )

    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    admin_memberships = (
        db.query(models.Membership)
        .join(models.User)
        .filter(
            models.Membership.club_id == club_id,
            models.Membership.role == models.ClubRoles.MODERATOR.value
        )
        .all()
    )

    if not admin_memberships:
        return schemas.ClubAdminResponse(
            message="No Moderator found for this club.",
            data=[]
        )

    admins = [
        schemas.ClubAdminItem(
            user_id=membership.user.id,
            name=membership.user.name,
            email=membership.user.email
        )
        for membership in admin_memberships
    ]

    return schemas.ClubAdminResponse(
        message="Successfully retrieved club moderators.",
        data=admins
    )

# Get all clubs that a user belongs to
@router.get(
    "/clubs",
    response_model=schemas.UserClubResponse,
    status_code=status.HTTP_200_OK
)
def get_user_clubs(
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.USER.value)),
    db: Session = Depends(get_db)
):
    logging.info(f"Fetching clubs for user_id={user.id}")

    memberships = (
        db.query(models.Membership)
        .join(models.Club)
        .filter(models.Membership.user_id == user.id)
        .all()
    )

    if not memberships:
        return schemas.UserClubResponse(
            message="User does not belong to any club.",
            data=[]
        )
    
    clubs = [
        schemas.UserClubItem(
            club_id=membership.club.id,
            club_name=membership.club.name,
        )
        for membership in memberships
    ]

    return schemas.UserClubResponse(
        message="Successfully retrieved user clubs.",
        data=clubs
    )

# Get user's name and email
@router.get(
    "/info",
    response_model=schemas.UserInfoResponse,
    status_code=status.HTTP_200_OK
)
def get_user_info(
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.USER.value))
):
    logging.info(f"Fetching profile info for user_id={user.id}")

    return schemas.UserInfoResponse(
        message="Successfully retrieved user info.",
        data=schemas.UserInfo(
            name=user.name,
            email=user.email
        )
    )
