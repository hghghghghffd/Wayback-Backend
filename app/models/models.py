from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


def gen_id():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    app_owner = "app_owner"
    user = "user"


class ServerRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class ChannelType(str, enum.Enum):
    text = "text"
    voice = "voice"
    announcement = "announcement"


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=gen_id)
    username = Column(String(32), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    display_name = Column(String(64), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.user, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    memberships = relationship("ServerMember", back_populates="user", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="author", cascade="all, delete-orphan")
    voice_sessions = relationship("VoiceSession", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(String(36), primary_key=True, default=gen_id)
    token = Column(String(512), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="refresh_tokens")


class Server(Base):
    __tablename__ = "servers"
    id = Column(String(36), primary_key=True, default=gen_id)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(String(512), nullable=True)
    invite_code = Column(String(32), unique=True, nullable=False, index=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    members = relationship("ServerMember", back_populates="server", cascade="all, delete-orphan")
    channels = relationship("Channel", back_populates="server", cascade="all, delete-orphan")


class ServerMember(Base):
    __tablename__ = "server_members"
    id = Column(String(36), primary_key=True, default=gen_id)
    server_id = Column(String(36), ForeignKey("servers.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    role = Column(SAEnum(ServerRole), default=ServerRole.member, nullable=False)
    nickname = Column(String(64), nullable=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    server = relationship("Server", back_populates="members")
    user = relationship("User", back_populates="memberships")


class Channel(Base):
    __tablename__ = "channels"
    id = Column(String(36), primary_key=True, default=gen_id)
    server_id = Column(String(36), ForeignKey("servers.id"), nullable=False)
    name = Column(String(100), nullable=False)
    topic = Column(String(255), nullable=True)
    channel_type = Column(SAEnum(ChannelType), default=ChannelType.text, nullable=False)
    position = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    server = relationship("Server", back_populates="channels")
    messages = relationship("Message", back_populates="channel", cascade="all, delete-orphan")
    voice_sessions = relationship("VoiceSession", back_populates="channel", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    id = Column(String(36), primary_key=True, default=gen_id)
    channel_id = Column(String(36), ForeignKey("channels.id"), nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    is_edited = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    channel = relationship("Channel", back_populates="messages")
    author = relationship("User", back_populates="messages")


class VoiceSession(Base):
    __tablename__ = "voice_sessions"
    id = Column(String(36), primary_key=True, default=gen_id)
    channel_id = Column(String(36), ForeignKey("channels.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    is_muted = Column(Boolean, default=False, nullable=False)
    is_deafened = Column(Boolean, default=False, nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    channel = relationship("Channel", back_populates="voice_sessions")
    user = relationship("User", back_populates="voice_sessions")


class SuspiciousIP(Base):
    __tablename__ = "suspicious_ips"
    id = Column(String(36), primary_key=True, default=gen_id)
    ip_address = Column(String(45), nullable=False, index=True)
    attempt_count = Column(Integer, default=1, nullable=False)
    last_attempt = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IPBan(Base):
    __tablename__ = "ip_bans"
    id = Column(String(36), primary_key=True, default=gen_id)
    ip_address = Column(String(45), nullable=False, unique=True, index=True)
    reason = Column(String(255), nullable=True)
    banned_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
