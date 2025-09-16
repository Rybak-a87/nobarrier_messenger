"""
ICQ-like Minimal Chat Backend (MVP)
FastAPI + PostgreSQL (async) + JWT + WebSockets

Why FastAPI (vs Django) for MVP:
- Легче стартовать, встроенная поддержка WebSocket.
- Простой, быстрый, удобно писать single-file прототип.
- Если захочется Django: можно позже вынести логику в сервис Users/Chats и дать ему Django REST + Channels.

Run locally (Python 3.11+):
    pip install fastapi uvicorn[standard] sqlalchemy asyncpg passlib[bcrypt] python-jose[cryptography]
    export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/chatdb"
    uvicorn fastapi_chat_backend:app --reload

Start Postgres via Docker (dev):
    docker run --name chatdb -e POSTGRES_PASSWORD=pass -e POSTGRES_USER=user -e POSTGRES_DB=chatdb -p 5432:5432 -d postgres:16

WebSocket (example):
    ws://localhost:8000/ws/chats/1?token=YOUR_JWT

Notes:
- Это учебный черновик: нет Alembic миграций, rate limiting, e2e-шифрования.
- Секреты держи в переменных окружения, а не в коде.
"""
from __future__ import annotations

import os
import json
import asyncio
import datetime as dt
from typing import Annotated, Dict, List, Optional, Set

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from jose import jwt, JWTError

from sqlalchemy import (
    String,
    Text,
    Boolean,
    ForeignKey,
    func,
    select,
    text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:pass@localhost:5432/chatdb",
)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ---------------------------------------------------------------------------
# DB models (SQLAlchemy 2.0, async)
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())

    chats: Mapped[List["ChatMember"]] = relationship(back_populates="user")


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())

    members: Mapped[List["ChatMember"]] = relationship(back_populates="chat")
    messages: Mapped[List["Message"]] = relationship(back_populates="chat")


class ChatMember(Base):
    __tablename__ = "chat_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    chat: Mapped[Chat] = relationship(back_populates="members")
    user: Mapped[User] = relationship(back_populates="chats")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    content: Mapped[str] = mapped_column(Text())
    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now())

    chat: Mapped[Chat] = relationship(back_populates="messages")


# Async engine/session
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

# ---------------------------------------------------------------------------
# Security (passwords + JWT)
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str | int, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    now = dt.datetime.utcnow()
    to_encode = {"sub": str(subject), "iat": int(now.timestamp())}
    if expires_minutes:
        expire = now + dt.timedelta(minutes=expires_minutes)
        to_encode.update({"exp": int(expire.timestamp())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class ChatCreate(BaseModel):
    member_ids: List[int] = Field(..., description="Include yourself too or backend will add you")
    is_group: bool = False


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4096)


async def get_session() -> AsyncSession:
    async with session_factory() as session:
        yield session


async def get_current_user(
    authorization: Optional[str] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
) -> User:
    """Extract user from Authorization: Bearer <token> header."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Family Chat (FastAPI + Postgres + WebSockets)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    # Create tables automatically for the prototype
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# --------------------------- Auth -----------------------------------------
@app.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate, session: Annotated[AsyncSession, Depends(get_session)]):
    exists = await session.scalar(select(func.count()).select_from(User).where(User.username == payload.username))
    if exists:
        raise HTTPException(400, detail="Username already taken")
    user = User(username=payload.username, password_hash=hash_password(payload.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@app.post("/login", response_model=Token)
async def login(payload: UserCreate, session: Annotated[AsyncSession, Depends(get_session)]):
    user = await session.scalar(select(User).where(User.username == payload.username))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(user.id)
    return Token(access_token=token)


@app.get("/me", response_model=UserOut)
async def me(current: Annotated[User, Depends(get_current_user)]):
    return current


# --------------------------- Chats ----------------------------------------
@app.post("/chats", response_model=dict)
async def create_chat(
    payload: ChatCreate,
    current: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    # Ensure current user in member list
    members = set(payload.member_ids) | {current.id}
    chat = Chat(is_group=payload.is_group)
    session.add(chat)
    await session.flush()

    for uid in members:
        session.add(ChatMember(chat_id=chat.id, user_id=uid))

    await session.commit()
    return {"chat_id": chat.id, "is_group": chat.is_group, "member_ids": list(members)}


@app.get("/chats", response_model=List[dict])
async def list_chats(
    current: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    q = (
        select(Chat.id, Chat.is_group, func.array_agg(ChatMember.user_id))
        .join(ChatMember, ChatMember.chat_id == Chat.id)
        .where(ChatMember.user_id == current.id)
        .group_by(Chat.id)
        .order_by(Chat.id)
    )
    rows = (await session.execute(q)).all()
    return [
        {"chat_id": r.id, "is_group": r.is_group, "member_ids": [int(x) for x in r.array_agg]}
        for r in rows
    ]


@app.get("/chats/{chat_id}/messages", response_model=List[dict])
async def get_messages(
    chat_id: int,
    limit: int = 50,
    offset: int = 0,
    current: Annotated[User, Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None,
):
    # verify membership
    member = await session.scalar(
        select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == current.id)
    )
    if not member:
        raise HTTPException(403, detail="Not a member of this chat")

    q = (
        select(Message.id, Message.sender_id, Message.content, Message.created_at)
        .where(Message.chat_id == chat_id)
        .order_by(Message.id.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(q)).all()
    return [
        {
            "id": r.id,
            "chat_id": chat_id,
            "sender_id": r.sender_id,
            "content": r.content,
            "created_at": r.created_at.isoformat(),
        }
        for r in reversed(rows)
    ]


# --------------------------- WebSockets -----------------------------------
class ConnectionManager:
    def __init__(self) -> None:
        # chat_id -> set of websockets
        self.rooms: Dict[int, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, chat_id: int, ws: WebSocket) -> None:
        await ws.accept()
        async with self.lock:
            self.rooms.setdefault(chat_id, set()).add(ws)

    async def disconnect(self, chat_id: int, ws: WebSocket) -> None:
        async with self.lock:
            if chat_id in self.rooms and ws in self.rooms[chat_id]:
                self.rooms[chat_id].remove(ws)
                if not self.rooms[chat_id]:
                    self.rooms.pop(chat_id, None)

    async def broadcast(self, chat_id: int, message: dict) -> None:
        conns = list(self.rooms.get(chat_id, []))
        text = json.dumps(message, ensure_ascii=False)
        for ws in conns:
            try:
                await ws.send_text(text)
            except RuntimeError:
                pass


manager = ConnectionManager()


async def authenticate_ws(token: str, session: AsyncSession) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(4401, detail="Invalid token")
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(4401, detail="User not found")
    return user


@app.websocket("/ws/chats/{chat_id}")
async def ws_chat(ws: WebSocket, chat_id: int):
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4401)
        return

    async with session_factory() as session:
        try:
            user = await authenticate_ws(token, session)
            # verify membership
            member = await session.scalar(
                select(ChatMember).where(ChatMember.chat_id == chat_id, ChatMember.user_id == user.id)
            )
            if not member:
                await ws.close(code=4403)
                return

            await manager.connect(chat_id, ws)
            while True:
                data = await ws.receive_json()
                mtype = data.get("type")
                if mtype == "ping":
                    await ws.send_json({"type": "pong", "ts": dt.datetime.utcnow().isoformat()})
                    continue
                if mtype != "message":
                    await ws.send_json({"type": "error", "error": "unknown_type"})
                    continue

                content = (data.get("content") or "").strip()
                if not content:
                    await ws.send_json({"type": "error", "error": "empty_content"})
                    continue

                msg = Message(chat_id=chat_id, sender_id=user.id, content=content)
                session.add(msg)
                await session.commit()
                await session.refresh(msg)

                payload = {
                    "type": "message",
                    "id": msg.id,
                    "chat_id": chat_id,
                    "sender_id": user.id,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                }
                await manager.broadcast(chat_id, payload)

        except WebSocketDisconnect:
            pass
        finally:
            await manager.disconnect(chat_id, ws)


# --------------------------- Health ---------------------------------------
@app.get("/health")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db = "ok"
    except Exception as e:
        db = f"error: {e}"
    return {"status": "ok", "db": db}
