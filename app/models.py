# SQLAlchemy ORM Models

from sqlalchemy import ForeignKey, Integer, String, Boolean, UniqueConstraint, text, TIMESTAMP, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from .database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

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
    __tablename__ = "item_borrowing_request"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    issued_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    set_return_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    item: Mapped["Item"] = relationship("Item", back_populates="borrowing_requests")
    transactions: Mapped[list["ItemBorrowingTransaction"]] = relationship("ItemBorrowingTransaction", back_populates="request", cascade="all, delete-orphan")

class ItemBorrowingTransaction(Base):
    __tablename__ = "item_borrowing_transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    req_id: Mapped[int] = mapped_column(Integer, ForeignKey("item_borrowing_request.id"), nullable=False)
    tstamp: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    operator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    request: Mapped["ItemBorrowingRequest"] = relationship("ItemBorrowingRequest", back_populates="transactions")
    operator: Mapped["User"] = relationship("User", back_populates="transactions_as_operator")

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