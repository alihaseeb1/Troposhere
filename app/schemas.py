# this will be holding pydantic models for request and response bodies

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class User(BaseModel):
    email : EmailStr
    name : str
    picture : Optional[str]
    global_role : int


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

class MembershipOut(BaseModel):
    user_id : int
    club_id : int
    role : int
    joined_at : datetime

    model_config = {
        "from_attributes": True
    }
