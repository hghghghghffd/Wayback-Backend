from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import User, Channel, ServerMember, Message, ServerRole
from app.schemas.schemas import MessageCreate, MessageEdit, MessageOut
from app.exceptions import not_found, forbidden
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/channels/{channel_id}/messages", tags=["messages"])


def _get_channel_and_member(db, channel_id, user_id):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        return None, None
    member = db.query(ServerMember).filter(
        ServerMember.server_id == channel.server_id,
        ServerMember.user_id == user_id
    ).first()
    return channel, member


def _build_message_out(msg: Message, db: Session) -> MessageOut:
    author = db.query(User).filter(User.id == msg.author_id).first()
    return MessageOut(
        id=msg.id, channel_id=msg.channel_id, author_id=msg.author_id,
        author_username=author.username if author else "deleted",
        author_display_name=author.display_name if author else None,
        content=msg.content, is_deleted=msg.is_deleted, is_edited=msg.is_edited,
        created_at=msg.created_at, updated_at=msg.updated_at
    )


@router.get("/", response_model=List[MessageOut])
def get_messages(channel_id: str, limit: int = Query(50, le=100), before: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    channel, member = _get_channel_and_member(db, channel_id, current_user.id)
    if not channel:
        not_found("Channel not found")
    if not member:
        forbidden("Not a member of this server")
    query = db.query(Message).filter(Message.channel_id == channel_id, Message.is_deleted == False)
    if before:
        ref = db.query(Message).filter(Message.id == before).first()
        if ref:
            query = query.filter(Message.created_at < ref.created_at)
    messages = query.order_by(Message.created_at.desc()).limit(limit).all()
    return [_build_message_out(m, db) for m in reversed(messages)]


@router.post("/", response_model=MessageOut)
def send_message(channel_id: str, data: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    channel, member = _get_channel_and_member(db, channel_id, current_user.id)
    if not channel:
        not_found("Channel not found")
    if not member:
        forbidden("Not a member of this server")
    msg = Message(channel_id=channel_id, author_id=current_user.id, content=data.content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return _build_message_out(msg, db)


@router.patch("/{message_id}", response_model=MessageOut)
def edit_message(channel_id: str, message_id: str, data: MessageEdit, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    msg = db.query(Message).filter(Message.id == message_id, Message.channel_id == channel_id).first()
    if not msg:
        not_found("Message not found")
    if msg.author_id != current_user.id:
        forbidden("Cannot edit another user's message")
    msg.content = data.content
    msg.is_edited = True
    db.commit()
    db.refresh(msg)
    return _build_message_out(msg, db)


@router.delete("/{message_id}")
def delete_message(channel_id: str, message_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    msg = db.query(Message).filter(Message.id == message_id, Message.channel_id == channel_id).first()
    if not msg:
        not_found("Message not found")
    channel, member = _get_channel_and_member(db, channel_id, current_user.id)
    if msg.author_id != current_user.id:
        if not member or member.role not in (ServerRole.owner, ServerRole.admin):
            forbidden("Cannot delete another user's message")
    msg.is_deleted = True
    msg.content = "[Message deleted]"
    db.commit()
    return {"status": "success", "message": "Message deleted"}
