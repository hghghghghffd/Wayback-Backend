from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from app.database import get_db
from app.models.models import User, RefreshToken, UserRole
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, RefreshRequest, UserOut
from app.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.exceptions import unauthorized, conflict
from app.dependencies import get_current_active_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user: User, db: Session) -> TokenResponse:
    access = create_access_token({"sub": user.id})
    refresh = create_refresh_token({"sub": user.id})
    exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(token=refresh, user_id=user.id, expires_at=exp))
    db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/register", response_model=UserOut)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        conflict("Username already taken")
    if db.query(User).filter(User.email == data.email).first():
        conflict("Email already registered")
    is_first = db.query(User).count() == 0
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        display_name=data.display_name or data.username,
        role=UserRole.app_owner if is_first else UserRole.user
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        unauthorized("Invalid credentials")
    if not user.is_active:
        unauthorized("Account disabled")
    if user.is_banned:
        unauthorized("Account banned")
    return _issue_tokens(user, db)


@router.post("/login/form", response_model=TokenResponse)
def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        unauthorized("Invalid credentials")
    if not user.is_active:
        unauthorized("Account disabled")
    if user.is_banned:
        unauthorized("Account banned")
    return _issue_tokens(user, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        unauthorized("Invalid refresh token")
    rt = db.query(RefreshToken).filter(RefreshToken.token == data.refresh_token).first()
    if not rt or rt.is_revoked:
        unauthorized("Refresh token revoked or not found")
    if rt.expires_at < datetime.now(timezone.utc):
        unauthorized("Refresh token expired")
    rt.is_revoked = True
    user = db.query(User).filter(User.id == rt.user_id).first()
    if not user:
        unauthorized("User not found")
    result = _issue_tokens(user, db)
    db.commit()
    return result


@router.post("/logout")
def logout(data: RefreshRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    rt = db.query(RefreshToken).filter(RefreshToken.token == data.refresh_token).first()
    if rt:
        rt.is_revoked = True
        db.commit()
    return {"status": "success", "message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_active_user)):
    return current_user
