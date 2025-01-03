from typing import Optional, Union, List
from datetime import date, datetime
from pydantic import BaseModel

class UserBase(BaseModel):
    eid: str
    name: str

class UserCreate(UserBase):
    name: str
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_on: datetime
    last_login: Optional[datetime]
    login_count: int

    class Config:
        from_attributes = True
