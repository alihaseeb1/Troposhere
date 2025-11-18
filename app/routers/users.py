from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
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
            item_id=record.item_borrowing_request.item.id,
            item_club_id=record.item_borrowing_request.item.club.id if record.item_borrowing_request.item.club else None,
            item_qr_code=record.item_borrowing_request.item.qr_code,
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

@router.get(
    "/clubs",
    response_model=schemas.UserClubResponse,
    status_code=status.HTTP_200_OK
)
def get_user_clubs(
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.USER.value)),
    db: Session = Depends(get_db)
):

    logging.info(f"Fetching clubs for user_id={user.id} (global_role={user.global_role})")

    if user.global_role == models.GlobalRoles.SUPERUSER.value:
        clubs = db.query(models.Club).order_by(models.Club.id.asc()).all()
    else:

        clubs = (
            db.query(models.Club)
            .join(models.Membership)
            .filter(models.Membership.user_id == user.id)
            .order_by(models.Club.id.asc())
            .all()
        )

    if not clubs:
        return schemas.UserClubResponse(
            message="No clubs found.",
            data=[]
        )
    
    return schemas.UserClubResponse(
        message="Successfully retrieved clubs.",
        data=[
            schemas.UserClubItem(
                club_id=club.id,
                club_name=club.name,
                image_path=club.image_path
            )
            for club in clubs
        ]
    )

@router.get(
    "/profile",
    response_model=schemas.UserProfile,
    status_code=status.HTTP_200_OK
)
def get_user_basic_info(
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.USER.value)),
    db: Session = Depends(get_db)
):

    # logging.info(f"Fetching basic user info for user_id={user.id}")

    # user_data = (
    #     db.query(models.User)
    #     .filter(models.User.id == user.id)
    #     .first()
    # )
    return schemas.UserProfile.model_validate(user) 

@router.get("/search/", response_model=schemas.UserOut)
def get_a_user(
    q: str = Query(..., min_length=1, description="Search user by exact name or student ID"),
    db: Session = Depends(get_db),
    user: models.User = Depends(require_global_role(role=models.GlobalRoles.USER.value))):


    user = db.query(models.User).filter(
        (func.upper(models.User.name) == func.upper(q)) | (func.split_part(models.User.email, "@", 1) == q)
    ).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user