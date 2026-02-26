from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.database import get_db
from app.models.models import User, Channel, ServerMember, VoiceSession, ChannelType
from app.schemas.schemas import VoiceSessionOut
from app.exceptions import not_found, forbidden, bad_request
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/voice", tags=["voice"])


def _build_session_out(vs: VoiceSession, db: Session) -> VoiceSessionOut:
    user = db.query(User).filter(User.id == vs.user_id).first()
    return VoiceSessionOut(
        id=vs.id, channel_id=vs.channel_id, user_id=vs.user_id,
        username=user.username if user else "deleted",
        is_muted=vs.is_muted, is_deafened=vs.is_deafened,
        joined_at=vs.joined_at, is_active=vs.is_active
    )


@router.post("/join/{channel_id}", response_model=VoiceSessionOut)
def join_voice(channel_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        not_found("Channel not found")
    if channel.channel_type != ChannelType.voice:
        bad_request("Not a voice channel")
    member = db.query(ServerMember).filter(ServerMember.server_id == channel.server_id, ServerMember.user_id == current_user.id).first()
    if not member:
        forbidden("Not a member of this server")
    existing = db.query(VoiceSession).filter(VoiceSession.channel_id == channel_id, VoiceSession.user_id == current_user.id, VoiceSession.is_active == True).first()
    if existing:
        return _build_session_out(existing, db)
    old = db.query(VoiceSession).filter(VoiceSession.user_id == current_user.id, VoiceSession.is_active == True).first()
    if old:
        old.is_active = False
        old.left_at = datetime.now(timezone.utc)
    vs = VoiceSession(channel_id=channel_id, user_id=current_user.id)
    db.add(vs)
    db.commit()
    db.refresh(vs)
    return _build_session_out(vs, db)


@router.post("/leave/{channel_id}")
def leave_voice(channel_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    vs = db.query(VoiceSession).filter(VoiceSession.channel_id == channel_id, VoiceSession.user_id == current_user.id, VoiceSession.is_active == True).first()
    if not vs:
        not_found("No active voice session in this channel")
    vs.is_active = False
    vs.left_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "success", "message": "Left voice channel"}


@router.post("/mute/{channel_id}")
def toggle_mute(channel_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    vs = db.query(VoiceSession).filter(VoiceSession.channel_id == channel_id, VoiceSession.user_id == current_user.id, VoiceSession.is_active == True).first()
    if not vs:
        not_found("No active voice session")
    vs.is_muted = not vs.is_muted
    db.commit()
    return {"status": "success", "is_muted": vs.is_muted}


@router.post("/deafen/{channel_id}")
def toggle_deafen(channel_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    vs = db.query(VoiceSession).filter(VoiceSession.channel_id == channel_id, VoiceSession.user_id == current_user.id, VoiceSession.is_active == True).first()
    if not vs:
        not_found("No active voice session")
    vs.is_deafened = not vs.is_deafened
    db.commit()
    return {"status": "success", "is_deafened": vs.is_deafened}


@router.get("/{channel_id}/members", response_model=List[VoiceSessionOut])
def get_voice_members(channel_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        not_found("Channel not found")
    member = db.query(ServerMember).filter(ServerMember.server_id == channel.server_id, ServerMember.user_id == current_user.id).first()
    if not member:
        forbidden("Not a member of this server")
    sessions = db.query(VoiceSession).filter(VoiceSession.channel_id == channel_id, VoiceSession.is_active == True).all()
    return [_build_session_out(vs, db) for vs in sessions]
