from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


# Additional properties stored in DB
class UserInDBBase(UserBase):
    id: Optional[int] = None
    auth_provider: Optional[str] = "local"
    picture: Optional[str] = None

    class Config:
        from_attributes = True


# Properties to return to client
class UserResponse(UserInDBBase):
    pass


# Properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: Optional[str] = None


# Google ID token sign-in payload (sent by frontend after GIS callback)
class GoogleAuthRequest(BaseModel):
    id_token: str = Field(min_length=10)
