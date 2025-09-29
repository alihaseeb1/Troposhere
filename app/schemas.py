# this will be holding pydantic models for request and response bodies

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class User:
    id : int
    email : EmailStr