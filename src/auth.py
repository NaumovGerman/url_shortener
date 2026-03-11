from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi.security import HTTPBearer
from src.config import SECRET_KEY, ALGORITHM


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

security = HTTPBearer(auto_error=False)


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str):
    return pwd_context.verify(password, password_hash)


def create_token(user_id: int):

    payload = {
        "user_id": user_id,
        "exp": datetime.now() + timedelta(hours=24)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


