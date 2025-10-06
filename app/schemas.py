# this will be holding pydantic models for request and response bodies

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from .models import ClubRoles, ItemStatus

class User(BaseModel):
    email : EmailStr
    name : str
    picture : Optional[str]
    global_role : int

class UserOut(BaseModel):
    id : int
    email : EmailStr
    name : str
    picture : Optional[str]

    model_config = {
        "from_attributes": True
    }

class Club(BaseModel):
    name : str
    description : Optional[str] = ""

class ClubOut(BaseModel):
    id : int
    name : str
    description : Optional[str] = ""
    created_at : datetime

    model_config = {
        "from_attributes": True
    }


class MembershipIn(BaseModel):
    role : ClubRoles

    @field_validator("role", mode="before")
    def map_str_to_enum(cls, v):
        if isinstance(v, str):
            v = v.lower()
            mapping = {
                "admin": ClubRoles.ADMIN,
                "moderator": ClubRoles.MODERATOR,
                "member": ClubRoles.MEMBER,
            }
            if v in mapping:
                return mapping[v]
        return v

class MembershipOut(BaseModel):
    user_id : int
    club_id : int
    role : int
    joined_at : datetime

    model_config = {
        "from_attributes": True
    }

class ClubMembersOut(BaseModel):
    User: UserOut
    Membership: MembershipOut
    model_config = {
        "from_attributes": True
    }

class Item(BaseModel):
    name : str
    description : Optional[str] = ""
    is_high_risk : Optional[bool] = False
    status : Optional[str] = ItemStatus.AVAILABLE

class ItemOut(Item):
    id : int
    created_at : datetime
    club_id : Optional[int]

    model_config = {
        "from_attributes": True
    }

class ItemTransferIn(BaseModel):
    club_id : Optional[int] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ItemStatus] = None
    is_high_risk: Optional[bool] = None
