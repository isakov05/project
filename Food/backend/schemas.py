from pydantic import BaseModel, EmailStr
from typing import Optional

class UserPublic(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None

class ChangePassword(BaseModel):
    old_password: str
    new_password: str
