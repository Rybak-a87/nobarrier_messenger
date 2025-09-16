from typing import Annotated, Sequence

from fastapi import APIRouter, Depends

from nobarrier.api.dependencies import get_user_service, get_current_user
from nobarrier.database.models.accounts import User
from nobarrier.schemas.accounts import UserCreate, UserCheck, UserRead
from nobarrier.services.accounts import UserService


router = APIRouter(
    prefix="/users",
    tags=["Accounts"],
    # dependencies=[Depends(get_current_user)]
)

@router.get("/current-user", response_model=UserCheck)
async def current_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    """
    ## Return current user
    \f
    """
    return user

@router.get("/full-list", response_model=Sequence[UserRead])
async def get_all_users(service: Annotated[UserService, Depends(get_user_service)] = None) -> Sequence[User]:
    """
    ## Return all users
    \f
    """
    return await service.get_all_users()


@router.get("/me", response_model=UserCheck)
async def me(current: Annotated[User, Depends(get_current_user)]):
    return current


# @router.put("/update", response_model=UserCreate)
# return service.update(user_id=user.id, operation_id=operation_id, operation_data=operation_data)
# @router.delete("/delete")
#     service.delete(user_id=user.id, operation_id=operation_id)
#     return Response(status_code=status.HTTP_204_NO_CONTENT)    # операция удаления возвращает код 204
