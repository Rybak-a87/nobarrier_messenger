from typing import Sequence, Any

from fastapi import HTTPException, Depends
from sqlalchemy import select, func, exists
from sqlalchemy.ext.asyncio import AsyncSession

from nobarrier.database.models import RefreshToken
from nobarrier.database.session import get_session
from nobarrier.domain.accounts.entities import UserEntity, WeakPasswordError
from nobarrier.database.models.accounts import User
from nobarrier.core.security import SecurityService
from nobarrier.schemas.security import TokenOut


class AuthService:
    def __init__(self, session: AsyncSession = Depends(get_session)):
        self.session = session
        self.security = SecurityService()

    async def register_user(self, username: str, password: str) -> TokenOut:
        user = await self.session.scalar(
            select(func.count()).select_from(User).where(User.username == username)
        )
        if user:
            raise HTTPException(400, detail="Username already taken")

        # entity = UserEntity(username=username, password=password)
        # try:
        #     entity.validate_password()
        # except WeakPasswordError as e:
        #     raise HTTPException(status_code=400, detail=str(e))

        user = User(username=username, password_hash=self.security.hash_password(password))
        self.session.add(user)
        await self.session.flush()
        refresh = RefreshToken(user_id=user.id, token=self.security.create_refresh_token(user))
        self.session.add(refresh)
        await self.session.commit()
        # async with self.session.begin():  # only at a separate session
        # async with self.session:  # auto session.commit()
        #     self.session.add(user)
        #     await self.session.flush()
        #     refresh = RefreshToken(
        #         user_id=user.id,
        #         token=self.security.create_refresh_token(user),
        #     )
        #     self.session.add(refresh)
        access_token = self.security.create_access_token(user)
        return TokenOut(access_token=access_token)

    async def authenticate_user(self, username: str, password: str) -> TokenOut:
        user: Any | None = await self.session.scalar(select(User).where(User.username == username))
        if not user or not self.security.verify_password(password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        access_token = self.security.create_access_token(user)

        # async with self.session.begin():
        #     has_token: bool = await self.session.scalar(
        #         select(exists().where(RefreshToken.user_id == user.id))
        #     )
        #     if not has_token:
        #         refresh = RefreshToken(user_id=user.id, token=self.security.create_refresh_token(user))
        #         self.session.add(refresh)
        has_token: bool = await self.session.scalar(
            select(exists().where(RefreshToken.user_id == user.id))
        )
        if not has_token:
            refresh = RefreshToken(user_id=user.id, token=self.security.create_refresh_token(user))
            self.session.add(refresh)
            await self.session.commit()

        return TokenOut(access_token=access_token)

    async def authenticate_admin(self, username: str, password: str) -> TokenOut:
        pass
