# SQLAlchemy ORM Models

from typing import Optional
from sqlalchemy import JSON, ForeignKey, Integer, String, Boolean, UniqueConstraint, text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from .database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from sqlalchemy.types import Enum as SQLEnum

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
    PENDING_BORROWAL = "pending_borrowal"
    BORROWED = "borrowed"
    PENDING_RETURN = "pending_return"

class BorrowStatus(Enum):
    PENDING_APPROVAL = "pending_approval" # for requesting item borrowal
    APPROVED = "approved" # item borrow request approved
    PENDING_CONDITION_CHECK = "pending_condition_check" # item returned, pending condition check
    COMPLETED = "completed" # item returned and condition checked
    REJECTED = "rejected" # item return request rejected (possibly due to item damage)

class User(Base):
    __tablename__ = "users"

    id : Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    email : Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name : Mapped[str] = mapped_column(String, nullable=False)
    created_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    provider_id : Mapped[str] = mapped_column(String, nullable=False, unique=True)
    provider : Mapped[str] = mapped_column(String, nullable=False)
    picture : Mapped[str] = mapped_column(String, nullable=True)
    global_role : Mapped[GlobalRoles] = mapped_column(Integer, nullable=False, default=GlobalRoles.USER)
    memberships : Mapped[list["Membership"]] = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    
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


# items can be without a club, and items are transferrable between clubs
class Item(Base):
    __tablename__ = "items"
    id : Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    name : Mapped[str] = mapped_column(String, nullable=False)
    description : Mapped[str] = mapped_column(String, nullable=True)
    club_id : Mapped[int] = mapped_column(Integer, ForeignKey("clubs.id", ondelete="SET NULL"), nullable=True, index=True)
    is_high_risk : Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    created_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    status : Mapped[ItemStatus] = mapped_column(SQLEnum(ItemStatus, name="itemstatus", create_type=True), nullable=False, server_default=text("AVAILABLE"))
    
    club: Mapped["Club"] = relationship("Club", back_populates="items")


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
    status : Mapped[BorrowStatus] = mapped_column(SQLEnum(BorrowStatus, name="borrowstatus", create_type=True), nullable=False)
    remarks : Mapped[Optional[str]] = mapped_column(String, nullable=True)
    item_borrowing_request : Mapped["ItemBorrowingRequest"] = relationship("ItemBorrowingRequest", back_populates="transactions")
    operator : Mapped["User"] = relationship("User")

class Logging(Base):
    __tablename__ = "logging"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    tablename: Mapped[str] = mapped_column(String, nullable=False)
    operation: Mapped[str] = mapped_column(String, nullable=False)
    who: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    new_val: Mapped[dict] = mapped_column(JSON, nullable=True)
    old_val: Mapped[dict] = mapped_column(JSON, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="logs")