from fastapi import FastAPI

from .api import router


tags_metadata = [
    {
        "name": "",
        "description": ""
    },
    ...
]


app = FastAPI(
    title="",
    description="",
    version="0.0.0",
    openari_tags=tags_metadata,
)

app.include_router(router=router)



# app = FastAPI(title="Family Chat (FastAPI + Postgres + WebSockets)")
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # tighten in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.on_event("startup")
# async def on_startup() -> None:
#     # Create tables automatically for the prototype
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
