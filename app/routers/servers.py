from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import secrets
from app.database import get_db
from app.models.models import User, Server, ServerMember, Channel, ServerRole, ChannelType
from app.schemas.schemas import ServerCreate, ServerUpdate, ServerOut, MemberOut, JoinServerRequest, KickMemberRequest, ChangeMemberRoleRequest, NicknameRequest
from app.exceptions import not_found, forbidden, conflict, bad_request
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/servers", tags=["servers"])


def _get_member(db, server_id, user_id):
    return db.query(ServerMember).filter(ServerMember.server_id == server_id, ServerMember.user_id == user_id).first()


def _build_server_out(server: Server, db: Session) -> ServerOut:
    count = db.query(ServerMember).filter(ServerMember.server_id == server.id).count()
    return ServerOut(
        id=server.id, name=server.name, description=server.description,
        icon_url=server.icon_url, invite_code=server.invite_code,
        owner_id=server.owner_id, is_public=server.is_public,
        member_count=count, created_at=server.created_at
    )


@router.post("/", response_model=ServerOut)
def create_server(data: ServerCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    server = Server(
        name=data.name, description=data.description,
        is_public=data.is_public, invite_code=secrets.token_urlsafe(8),
        owner_id=current_user.id
    )
    db.add(server)
    db.flush()
    db.add(ServerMember(server_id=server.id, user_id=current_user.id, role=ServerRole.owner))
    db.add(Channel(server_id=server.id, name="general", channel_type=ChannelType.text, position=0))
    db.add(Channel(server_id=server.id, name="General Voice", channel_type=ChannelType.voice, position=1))
    db.commit()
    db.refresh(server)
    return _build_server_out(server, db)


@router.get("/", response_model=List[ServerOut])
def list_my_servers(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    memberships = db.query(ServerMember).filter(ServerMember.user_id == current_user.id).all()
    result = []
    for m in memberships:
        s = db.query(Server).filter(Server.id == m.server_id).first()
        if s:
            result.append(_build_server_out(s, db))
    return result


@router.get("/{server_id}", response_model=ServerOut)
def get_server(server_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        not_found("Server not found")
    if not _get_member(db, server_id, current_user.id):
        forbidden("You are not a member of this server")
    return _build_server_out(server, db)


@router.patch("/{server_id}", response_model=ServerOut)
def update_server(server_id: str, data: ServerUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        not_found("Server not found")
    member = _get_member(db, server_id, current_user.id)
    if not member or member.role not in (ServerRole.owner, ServerRole.admin):
        forbidden("Insufficient permissions")
    if data.name is not None:
        server.name = data.name
    if data.description is not None:
        server.description = data.description
    if data.is_public is not None:
        server.is_public = data.is_public
    db.commit()
    db.refresh(server)
    return _build_server_out(server, db)


@router.delete("/{server_id}")
def delete_server(server_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        not_found("Server not found")
    if server.owner_id != current_user.id:
        forbidden("Only the server owner can delete it")
    db.delete(server)
    db.commit()
    return {"status": "success", "message": "Server deleted"}


@router.post("/join", response_model=ServerOut)
def join_server(data: JoinServerRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    server = db.query(Server).filter(Server.invite_code == data.invite_code).first()
    if not server:
        not_found("Invalid invite code")
    if _get_member(db, server.id, current_user.id):
        conflict("Already a member of this server")
    db.add(ServerMember(server_id=server.id, user_id=current_user.id, role=ServerRole.member))
    db.commit()
    return _build_server_out(server, db)


@router.post("/{server_id}/leave")
def leave_server(server_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        not_found("Server not found")
    if server.owner_id == current_user.id:
        bad_request("Owner cannot leave. Transfer ownership or delete the server.")
    member = _get_member(db, server_id, current_user.id)
    if not member:
        not_found("You are not a member of this server")
    db.delete(member)
    db.commit()
    return {"status": "success", "message": "Left server"}


@router.post("/{server_id}/invite/regenerate", response_model=ServerOut)
def regen_invite(server_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        not_found("Server not found")
    member = _get_member(db, server_id, current_user.id)
    if not member or member.role not in (ServerRole.owner, ServerRole.admin):
        forbidden("Insufficient permissions")
    server.invite_code = secrets.token_urlsafe(8)
    db.commit()
    db.refresh(server)
    return _build_server_out(server, db)


@router.get("/{server_id}/members", response_model=List[MemberOut])
def get_members(server_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if not _get_member(db, server_id, current_user.id):
        forbidden("Not a member")
    members = db.query(ServerMember).filter(ServerMember.server_id == server_id).all()
    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            result.append(MemberOut(
                id=m.id, user_id=m.user_id, username=user.username,
                display_name=user.display_name, avatar_url=user.avatar_url,
                role=m.role, nickname=m.nickname, joined_at=m.joined_at
            ))
    return result


@router.post("/{server_id}/members/kick")
def kick_member(server_id: str, data: KickMemberRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        not_found("Server not found")
    my_member = _get_member(db, server_id, current_user.id)
    if not my_member or my_member.role not in (ServerRole.owner, ServerRole.admin):
        forbidden("Insufficient permissions")
    target = _get_member(db, server_id, data.user_id)
    if not target:
        not_found("Member not found")
    if server.owner_id == data.user_id:
        forbidden("Cannot kick the server owner")
    db.delete(target)
    db.commit()
    return {"status": "success", "message": "Member kicked"}


@router.post("/{server_id}/members/role")
def change_role(server_id: str, data: ChangeMemberRoleRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        not_found("Server not found")
    my_member = _get_member(db, server_id, current_user.id)
    if not my_member or my_member.role != ServerRole.owner:
        forbidden("Only the server owner can change roles")
    target = _get_member(db, server_id, data.user_id)
    if not target:
        not_found("Member not found")
    if data.role == ServerRole.owner:
        bad_request("Cannot assign owner role this way")
    target.role = data.role
    db.commit()
    return {"status": "success", "message": "Role updated"}


@router.post("/{server_id}/members/nickname")
def set_nickname(server_id: str, data: NicknameRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    my_member = _get_member(db, server_id, current_user.id)
    if not my_member:
        forbidden("Not a member")
    if data.user_id != current_user.id and my_member.role not in (ServerRole.owner, ServerRole.admin):
        forbidden("Insufficient permissions")
    target = _get_member(db, server_id, data.user_id)
    if not target:
        not_found("Member not found")
    target.nickname = data.nickname
    db.commit()
    return {"status": "success", "message": "Nickname updated"}
