from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import User, Server, ServerMember, Channel, ServerRole
from app.schemas.schemas import ChannelCreate, ChannelOut
from app.exceptions import not_found, forbidden
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/servers/{server_id}/channels", tags=["channels"])


def _get_member(db, server_id, user_id):
    return db.query(ServerMember).filter(ServerMember.server_id == server_id, ServerMember.user_id == user_id).first()


@router.get("/", response_model=List[ChannelOut])
def list_channels(server_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not _get_member(db, server_id, current_user.id):
        forbidden("Not a member of this server")
    return db.query(Channel).filter(Channel.server_id == server_id).order_by(Channel.position).all()


@router.post("/", response_model=ChannelOut)
def create_channel(server_id: str, data: ChannelCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        not_found("Server not found")
    member = _get_member(db, server_id, current_user.id)
    if not member or member.role not in (ServerRole.owner, ServerRole.admin):
        forbidden("Insufficient permissions")
    count = db.query(Channel).filter(Channel.server_id == server_id).count()
    channel = Channel(server_id=server_id, name=data.name, topic=data.topic, channel_type=data.channel_type, position=count)
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel


@router.delete("/{channel_id}")
def delete_channel(server_id: str, channel_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    channel = db.query(Channel).filter(Channel.id == channel_id, Channel.server_id == server_id).first()
    if not channel:
        not_found("Channel not found")
    member = _get_member(db, server_id, current_user.id)
    if not member or member.role not in (ServerRole.owner, ServerRole.admin):
        forbidden("Insufficient permissions")
    db.delete(channel)
    db.commit()
    return {"status": "success", "message": "Channel deleted"}
