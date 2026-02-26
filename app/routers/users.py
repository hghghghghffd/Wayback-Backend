from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import User
from app.schemas.schemas import UserOut, UserUpdate, PasswordChange
from app.security import verify_password, hash_password
from app.exceptions import not_found, bad_request
from app.dependencies import get_current_active_user, get_current_superuser

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.patch("/me", response_model=UserOut)
def update_me(data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if data.display_name is not None:
        current_user.display_name = data.display_name
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/password")
def change_password(data: PasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not verify_password(data.current_password, current_user.hashed_password):
        bad_request("Current password is incorrect")
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"status": "success", "message": "Password updated"}


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        not_found("User not found")
    return user


@router.get("/", response_model=List[UserOut])
def list_users(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_superuser)):
    return db.query(User).offset(skip).limit(limit).all()
