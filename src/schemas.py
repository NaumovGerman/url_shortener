from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class Login(BaseModel):
    email: EmailStr
    password: str

class LinkCreate(BaseModel):
    original_url: str
    expires_at: datetime | None = (datetime.now() + timedelta(hours=3))

class LinkUpdate(BaseModel):
    new_url: str

class LinkStats(BaseModel):
    original_url: str
    created_at: datetime
    click_count: int
    last_used_at: datetime | None