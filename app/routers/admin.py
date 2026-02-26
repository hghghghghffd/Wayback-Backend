from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import User, Server, Message, IPBan, SuspiciousIP
from app.schemas.schemas import AdminStatsOut, IPBanOut, BanUserRequest, BanIPRequest
from app.exceptions import not_found
from app.dependencies import get_current_superuser

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsOut)
def get_stats(db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    return AdminStatsOut(
        total_users=db.query(User).count(),
        active_users=db.query(User).filter(User.is_active == True, User.is_banned == False).count(),
        banned_users=db.query(User).filter(User.is_banned == True).count(),
        total_servers=db.query(Server).count(),
        total_messages=db.query(Message).count(),
        banned_ips=db.query(IPBan).filter(IPBan.is_active == True).count(),
        suspicious_ips=db.query(SuspiciousIP).count()
    )


@router.post("/users/ban")
def ban_user(data: BanUserRequest, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        not_found("User not found")
    user.is_banned = True
    db.commit()
    return {"status": "success", "message": f"User {user.username} banned"}


@router.post("/users/unban")
def unban_user(data: BanUserRequest, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        not_found("User not found")
    user.is_banned = False
    db.commit()
    return {"status": "success", "message": f"User {user.username} unbanned"}


@router.post("/ip/ban")
def ban_ip(data: BanIPRequest, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    existing = db.query(IPBan).filter(IPBan.ip_address == data.ip_address).first()
    if existing:
        existing.is_active = True
        existing.reason = data.reason
    else:
        db.add(IPBan(ip_address=data.ip_address, reason=data.reason))
    db.commit()
    return {"status": "success", "message": f"IP {data.ip_address} banned"}


@router.post("/ip/unban")
def unban_ip(data: BanIPRequest, db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    ban = db.query(IPBan).filter(IPBan.ip_address == data.ip_address).first()
    if not ban:
        not_found("IP ban not found")
    ban.is_active = False
    db.commit()
    return {"status": "success", "message": f"IP {data.ip_address} unbanned"}


@router.get("/ip/bans", response_model=List[IPBanOut])
def list_ip_bans(db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    return db.query(IPBan).filter(IPBan.is_active == True).all()


@router.get("/ip/suspicious")
def list_suspicious(db: Session = Depends(get_db), _: User = Depends(get_current_superuser)):
    return [
        {"id": s.id, "ip_address": s.ip_address, "attempt_count": s.attempt_count, "last_attempt": str(s.last_attempt)}
        for s in db.query(SuspiciousIP).order_by(SuspiciousIP.attempt_count.desc()).all()
    ]
