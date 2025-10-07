# SQLAlchemy ORM Models

from sqlalchemy import ForeignKey, Integer, String, Boolean, UniqueConstraint, text, TIMESTAMP, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from .database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from typing import Optional

class GlobalRoles(Enum):
    SUPERUSER = 1 # site-wide admin
    USER = 0

class ClubRoles(Enum):
    ADMIN = 3
    MODERATOR = 2
    MEMBER = 1

class ItemStatus(Enum):
    AVAILABLE = "available"
    OUT_OF_SERVICE = "out_of_service"

class ItemStatus(Enum):
    AVAILABLE = "available"
    OUT_OF_SERVICE = "out_of_service"
    BORROWED = "borrowed"
    PENDING_RETURN = "pending_return"

class BorrowStatus(Enum):
    PENDING_ADMIN_APPROVAL = "pending_admin_approval"
    APPROVED = "approved"
    PENDING_CONDITION_CHECK = "pending_condition_check"
    COMPLETED = "completed"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id : Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    email : Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name : Mapped[str] = mapped_column(String, nullable=False)
    created_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    provider_id : Mapped[str] = mapped_column(String, nullable=False, unique=True)
    provider : Mapped[str] = mapped_column(String, nullable=False)
    picture : Mapped[str] = mapped_column(String, nullable=True)
    global_role : Mapped[GlobalRoles] = mapped_column(Integer, nullable=False, default=GlobalRoles.USER.value)
    memberships : Mapped[list["Membership"]] = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    transactions_as_operator: Mapped[list["ItemBorrowingTransaction"]] = relationship("ItemBorrowingTransaction",back_populates="operator",cascade="all, delete-orphan")
    logs: Mapped[list["Logging"]] = relationship("Logging", back_populates="user", cascade="all, delete-orphan")

class Club(Base):
    __tablename__ = "clubs"
    id : Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    name : Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description : Mapped[str] = mapped_column(String, nullable=True)
    created_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    memberships : Mapped[list["Membership"]] = relationship("Membership", back_populates="club", cascade="all, delete-orphan")

    items : Mapped[list["Item"]] = relationship("Item", back_populates="club")

class Membership(Base):
    __tablename__ = "memberships"
    user_id : Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    club_id : Mapped[int] = mapped_column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), primary_key=True)
    role : Mapped[ClubRoles] = mapped_column(Integer, nullable=False, default=ClubRoles.MEMBER)
    joined_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    # relationships
    user : Mapped["User"] = relationship("User", back_populates="memberships")
    club : Mapped["Club"] = relationship("Club", back_populates="memberships")

    # Prevent duplicate memberships
    __table_args__ = (
        UniqueConstraint('user_id', 'club_id', name='uix_user_club'),
    )

# items can be without a club, and items are transferrable between clubs
class Item(Base):
    __tablename__ = "items"
    id : Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    name : Mapped[str] = mapped_column(String, nullable=False)
    description : Mapped[str] = mapped_column(String, nullable=True)
    club_id : Mapped[int] = mapped_column(Integer, ForeignKey("clubs.id", ondelete="SET NULL"), nullable=True, index=True)
    is_high_risk : Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    created_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    status : Mapped[ItemStatus] = mapped_column(String, nullable=False, server_default=ItemStatus.AVAILABLE.value)
    club: Mapped["Club"] = relationship("Club", back_populates="items")
    borrowing_requests: Mapped[list["ItemBorrowingRequest"]] = relationship("ItemBorrowingRequest", back_populates="item", cascade="all, delete-orphan")

class ItemBorrowingRequest(Base):
    __tablename__ = "item_borrowing_requests"
    id : Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    item_id : Mapped[int] = mapped_column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False)
    borrower_id : Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    return_date : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now() + interval \'7 days\''))
    created_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    borrower : Mapped["User"] = relationship("User")
    item : Mapped["Item"] = relationship("Item")
    transactions : Mapped[list["ItemBorrowingTransaction"]] = relationship("ItemBorrowingTransaction", back_populates="item_borrowing_request", cascade="all, delete-orphan")

class ItemBorrowingTransaction(Base):
    __tablename__ = "item_borrowing_transactions"
    id : Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    item_borrowing_request_id : Mapped[int] = mapped_column(Integer, ForeignKey("item_borrowing_requests.id", ondelete="CASCADE"), nullable=False)
    processed_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    operator_id : Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status : Mapped[BorrowStatus] = mapped_column(String, nullable=False)
    remarks : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    item_borrowing_request : Mapped["ItemBorrowingRequest"] = relationship("ItemBorrowingRequest", back_populates="transactions")
    operator : Mapped["User"] = relationship("User")

class Logging(Base):
    __tablename__ = "logging"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tstamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    tablename: Mapped[str] = mapped_column(String, nullable=False)
    operation: Mapped[str] = mapped_column(String, nullable=False)
    who: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    new_val: Mapped[dict] = mapped_column(JSON, nullable=False)
    old_val: Mapped[dict] = mapped_column(JSON, nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="logs")