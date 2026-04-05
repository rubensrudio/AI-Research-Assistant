from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.user import User
from app.schemas import UserCreate, TokenOut
from app.auth import hash_password, verify_password, create_access_token, _check_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenOut)
def register(request: Request, payload: UserCreate, db: Session = Depends(get_db)):
    _check_rate_limit(f"register:{request.client.host}")

    exists = db.query(User).filter(User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()

    token = create_access_token(subject=user.email)
    return TokenOut(access_token=token)

@router.post("/login", response_model=TokenOut)
def login(request: Request, payload: UserCreate, db: Session = Depends(get_db)):
    _check_rate_limit(f"login:{request.client.host}")

    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=user.email)
    return TokenOut(access_token=token)