# SQLAlchemy ORM Models

from sqlalchemy import ForeignKey, Integer, String, Boolean, UniqueConstraint, text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from .database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

class GlobalRoles(Enum):
    SUPERUSER = "superuser" # site-wide admin
    USER = "user"

class ClubRoles(Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"

class User(Base):
    __tablename__ = "users"

    id : Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    email : Mapped[str] = mapped_column(String, nullable=False, unique=True)
    name : Mapped[str] = mapped_column(String, nullable=False)
    created_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    provider_id : Mapped[str] = mapped_column(String, nullable=False, unique=True)
    provider : Mapped[str] = mapped_column(String, nullable=False)
    picture : Mapped[str] = mapped_column(String, nullable=True)
    global_role : Mapped[GlobalRoles] = mapped_column(String, nullable=False, default=GlobalRoles.USER.value)
    memberships : Mapped[list["Membership"]] = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    
class Club(Base):
    __tablename__ = "clubs"
    id : Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    name : Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description : Mapped[str] = mapped_column(String, nullable=True)
    created_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    memberships : Mapped[list["Membership"]] = relationship("Membership", back_populates="club", cascade="all, delete-orphan")

class Membership(Base):
    __tablename__ = "memberships"
    user_id : Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    club_id : Mapped[int] = mapped_column(Integer, ForeignKey("clubs.id", ondelete="CASCADE"), primary_key=True)
    role : Mapped[ClubRoles] = mapped_column(String, nullable=False, default=ClubRoles.MEMBER)
    joined_at : Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))
    
    # relationships
    user : Mapped["User"] = relationship("User", back_populates="memberships")
    club : Mapped["Club"] = relationship("Club", back_populates="memberships")

    # Prevent duplicate memberships
    __table_args__ = (
        UniqueConstraint('user_id', 'club_id', name='uix_user_club'),
    )