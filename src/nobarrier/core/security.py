import datetime
from typing import Optional

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import ValidationError

from nobarrier.core.settings import settings
from nobarrier.schemas.accounts import UserCheck
from nobarrier.shared.exceptions import InvalidCredentials, NotAuthenticated, NotAuthenticatedAdmin

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/sign-in-admin/")


class TokenExtractor:
    def __init__(self, cookie_name: str = "access_token", query_param: str = "token"):
        self.cookie_name = cookie_name
        self.query_param = query_param

    async def __call__(self, request: Request, bearer_token: Optional[str] = Depends(oauth2_scheme)) -> str:
        token = bearer_token or request.cookies.get(self.cookie_name) or request.query_params.get(self.query_param)
        if not token:
            raise NotAuthenticated()
        return token


class SecurityService:
    def __init__(self):
        self.password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days

    def __create_token(self, user, expires: int | None = None, token_type: str = "access") -> str:
        now = datetime.datetime.now(datetime.timezone.utc)
        if token_type == "refresh":
            delta = datetime.timedelta(days=expires or self.refresh_token_expire_days)
        else:
            delta = datetime.timedelta(minutes=expires or self.access_token_expire_minutes)
        expire = now + delta
        user_data = UserCheck.from_orm(user)

        payload = {
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "type": token_type,
            "sub": str(user.id),
            "user": user_data.dict(),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def __validate_access_token(self, token: str) -> UserCheck:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_data = payload.get("user")
            return UserCheck.parse_obj(user_data)
        except (JWTError, ValidationError):
            raise InvalidCredentials()

    def hash_password(self, password: str) -> str:
        return self.password_context.hash(password)

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        return self.password_context.verify(plain_password, password_hash)

    def create_access_token(self, user, expires_minutes: int | None = None) -> str:
        return self.__create_token(user, expires_minutes, "access")

    def create_refresh_token(self, user, expires_days: int | None = None) -> str:
        return self.__create_token(user, expires_days, "refresh")

    def get_current_user(self, token: str = Depends(TokenExtractor())) -> UserCheck:
        return self.__validate_access_token(token)

    def get_current_admin(self, token: str = Depends(TokenExtractor())) -> UserCheck:
        user = self.__validate_access_token(token)
        if not getattr(user, "admin", False):
            raise NotAuthenticatedAdmin()
        return user
