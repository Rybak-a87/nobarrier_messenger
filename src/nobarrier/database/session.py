import datetime
from typing import AsyncGenerator

from sqlalchemy import func

from sqlalchemy.orm import  DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from nobarrier.core.settings import settings


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), nullable=False, onupdate=func.now()
    )


engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True
)
# session_factory = async_sessionmaker(engine, expire_on_commit=False)
#
# async def get_session() -> AsyncSession:
#     async with session_factory() as session:
#         yield session

async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
