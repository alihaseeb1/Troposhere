# SQLAlchemy ORM Models

from sqlalchemy import ForeignKey, Integer, String, Boolean, text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
import datetime
from .database import Base
import enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum

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

