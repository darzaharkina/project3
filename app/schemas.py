from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional

# Link schemas
class LinkBase(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = Field(None, min_length=3, max_length=50)
    expires_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class LinkCreate(LinkBase):
    pass

class LinkUpdate(BaseModel):
    original_url: HttpUrl

    class Config:
        orm_mode = True

class LinkResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    
    class Config:
        orm_mode = True

class LinkStats(BaseModel):
    original_url: str
    short_code: str
    clicks: int
    created_at: datetime
    last_accessed: Optional[datetime]
    expires_at: Optional[datetime]
    owner_username: Optional[str]
    
    class Config:
        orm_mode = True

class LinkSearchResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    clicks: int
    
    class Config:
        orm_mode = True

# User schemas
class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
