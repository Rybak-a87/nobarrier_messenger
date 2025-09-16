from typing import Annotated

from fastapi import APIRouter, Depends, Form
# from fastapi.security import OAuth2PasswordRequestForm

from nobarrier.api.dependencies import get_auth_service, get_current_admin
from nobarrier.database.models import User
from nobarrier.schemas.accounts import UserCreate
from nobarrier.schemas.oauth2_form import OAuth2AdminForm
from nobarrier.schemas.security import TokenOut
from nobarrier.services.auth import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Registration / Authentication"],
)

@router.post("/sign-up", response_model=TokenOut, status_code=201)
async def sign_up(payload: UserCreate, service: Annotated[AuthService, Depends(get_auth_service)]) -> TokenOut:
    """
    ## Create new user
    \f
    :param payload:
    :param service:
    :return: Token
    """
    return await service.register_user(payload.username, payload.password)


@router.post("/sign-in", response_model=TokenOut)
async def sign_in(payload: UserCreate, service: Annotated[AuthService, Depends(get_auth_service)]) -> TokenOut:
    """
    ## Login user
    \f
    :param payload:
    :param service:
    :return: Token
    """
    return await service.authenticate_user(username=payload.username, password=payload.password)


@router.post("/sign-in-admin", response_model=TokenOut)
async def sign_in_admin(
        # payload: OAuth2AdminForm = Depends(),
        service: Annotated[AuthService, Depends(get_auth_service)],
        # payload: Annotated[OAuth2AdminForm, Depends(get_auth_service)],
        payload: OAuth2AdminForm = Depends(),

) -> TokenOut:
    """
    ## Login admin
    \f
    :param payload:
    :param service:
    :return: Token
    """
    return await service.authenticate_user(username=payload.username, password=payload.password)


# @router.post("/logout")
# async def logout(request: Request):
#     refresh_token = request.cookies.get("refresh_token")
#     if refresh_token:
#         try:
#             payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
#             user_id = payload.get("sub")
#             redis.delete(f"refresh:{user_id}")
#         except JWTError:
#             pass
#
#     response = JSONResponse(content={"detail": "Logged out"})
#     response.delete_cookie("refresh_token")
#     return response

