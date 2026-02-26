from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, UserRole
from app.security import decode_token
from app.exceptions import unauthorized, forbidden

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login/form")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        unauthorized("Invalid access token")
    user_id = payload.get("sub")
    if not user_id:
        unauthorized("Invalid token payload")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        unauthorized("User not found")
    if not user.is_active:
        unauthorized("Account is disabled")
    if user.is_banned:
        forbidden("Account is banned")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.app_owner:
        forbidden("App owner access required")
    return current_user
