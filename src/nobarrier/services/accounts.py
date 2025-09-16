from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nobarrier.database.models.accounts import User


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def update_user(self, user_id: int) -> User:
        pass

    async def delete_user(self, user_id: int) -> User:
        pass

    async def get_all_users(self) -> Sequence[User]:
        users = (await self.session.scalars(select(User))).all()
        return users

    async def get_user_by_id(self, user_id: int) -> User:
        user = (await self.session.scalar(select(User).where(User.id == user_id)))
        return user
