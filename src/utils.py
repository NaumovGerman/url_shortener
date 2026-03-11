import asyncio
from fastapi import Depends, HTTPException
from datetime import datetime, timedelta
from src.database import SessionLocal
from src.models import User, Link
from src.redis_client import redis_client
from fastapi.security import HTTPAuthorizationCredentials
import string
import random
from jose import jwt, JWTError
from src.config import SECRET_KEY, ALGORITHM
from src.auth import security

async def cleanup_expired_links():

    while True:
        db = SessionLocal()
        expired_links = db.query(Link).filter(Link.expires_at < datetime.now()).all()
        for link in expired_links:
            redis_client.delete(f"link:{link.short_code}")
            db.delete(link)

        db.commit()
        db.close()

        await asyncio.sleep(120)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_code(length=6):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def create_and_add_link(db, original_url, expires_at=None, user_id=None):

    while True:
        short_code = generate_code()
        existing = db.query(Link).filter(Link.short_code == short_code).first()

        if not existing:
            break

    if not expires_at:
        expires_at = datetime.now() + timedelta(hours=24)

    link = Link(
        original_url=original_url,
        short_code=short_code,
        expires_at=expires_at,
        user_id=user_id
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    return link

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):

    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = SessionLocal()

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user

def check_user_authorization(
    credentials: HTTPAuthorizationCredentials | None = Depends(security)
):

    if credentials is None:
        return None
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

    except JWTError:
        return None

    db = SessionLocal()
    return db.query(User).filter(User.id == user_id).first()