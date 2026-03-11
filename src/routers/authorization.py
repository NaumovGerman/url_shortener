from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from src.models import User
import src.schemas as schemas
from src.auth import hash_password, verify_password, create_token
from src.utils import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):

    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(400, "User already exists")

    db_user = User(
        email=user.email,
        password_hash=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()

    return {"status": "ok"}


@router.post("/login")
def login(data: schemas.Login, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(400, "No such user found in database")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(400, "Wrong email or password")

    token = create_token(user.id)

    return {"token": token}
