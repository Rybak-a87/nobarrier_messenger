from fastapi import APIRouter


router = APIRouter(
    prefix="/security",
    tags=["Security"],
    # dependencies=[Depends(get_current_user)]
)


# @router.post("/refresh-token", response_model=Token)
# async def refresh_token(request: Request, service: Annotated[AuthService, Depends(get_auth_service)]):
#     await session.execute(delete(RefreshToken).where(RefreshToken.expires_at <= datetime.utcnow()))
#     await session.commit()



#     refresh_token = request.cookies.get("refresh_token")
#     if not refresh_token:
#         raise HTTPException(401, detail="No refresh token")
#
#     try:
#         payload = jwt.decode(refresh_token, service.security.secret_key, algorithms=[service.security.algorithm])
#         if payload.get("type") != "refresh":
#             raise HTTPException(401, detail="Invalid token type")
#
#         user_id = payload.get("sub")
#         stored_token = redis.get(f"refresh:{user_id}")
#         if stored_token != refresh_token:
#             raise HTTPException(401, detail="Token mismatch or expired")
#
#         user = await service.get_user_by_id(user_id)
#         new_access_token = service.security.create_access_token(user)
#         return Token(access_token=new_access_token)
#
#     except JWTError:
#         raise HTTPException(401, detail="Invalid refresh token")
