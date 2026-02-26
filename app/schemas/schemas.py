from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    app_owner = "app_owner"
    user = "user"


class ServerRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class ChannelType(str, Enum):
    text = "text"
    voice = "voice"
    announcement = "announcement"


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 32:
            raise ValueError("Username must be 3-32 characters")
        if not v.replace("_", "").replace(".", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, underscores, periods")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ServerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = True


class ServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class ServerOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon_url: Optional[str] = None
    invite_code: str
    owner_id: str
    is_public: bool
    member_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberOut(BaseModel):
    id: str
    user_id: str
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: ServerRole
    nickname: Optional[str] = None
    joined_at: datetime

    model_config = {"from_attributes": True}


class ChannelCreate(BaseModel):
    name: str
    topic: Optional[str] = None
    channel_type: ChannelType = ChannelType.text


class ChannelOut(BaseModel):
    id: str
    server_id: str
    name: str
    topic: Optional[str] = None
    channel_type: ChannelType
    position: int
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str


class MessageEdit(BaseModel):
    content: str


class MessageOut(BaseModel):
    id: str
    channel_id: str
    author_id: str
    author_username: str
    author_display_name: Optional[str] = None
    content: str
    is_deleted: bool
    is_edited: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class VoiceSessionOut(BaseModel):
    id: str
    channel_id: str
    user_id: str
    username: str
    is_muted: bool
    is_deafened: bool
    joined_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class AdminStatsOut(BaseModel):
    total_users: int
    active_users: int
    banned_users: int
    total_servers: int
    total_messages: int
    banned_ips: int
    suspicious_ips: int


class IPBanOut(BaseModel):
    id: str
    ip_address: str
    reason: Optional[str] = None
    banned_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class JoinServerRequest(BaseModel):
    invite_code: str


class KickMemberRequest(BaseModel):
    user_id: str


class ChangeMemberRoleRequest(BaseModel):
    user_id: str
    role: ServerRole


class NicknameRequest(BaseModel):
    user_id: str
    nickname: Optional[str] = None


class BanUserRequest(BaseModel):
    user_id: str
    reason: Optional[str] = None


class BanIPRequest(BaseModel):
    ip_address: str
    reason: Optional[str] = None
