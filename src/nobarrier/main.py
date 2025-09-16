from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nobarrier.api.routers import routers
from nobarrier.api.websockets import routers as websockets_routers
from nobarrier.core.settings import settings


# from contextlib import asynccontextmanager
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     from nobarrier.database.session import engine
#     if settings.database_url.startswith("sqlite+aiosqlite:///"):
#         path = settings.database_url.split("///./")[-1]
#         import os
#         if not os.path.isfile(path):
#
#             async with engine.begin() as conn:
#                 from nobarrier.database.session import Base
#                 await conn.run_sync(Base.metadata.create_all)
#                 print("--- Create tables ---")
#
#     yield  # <--- здесь приложение работает
#
#     # код, который выполняется при остановке приложения
#     # например, engine.dispose()
#     await engine.dispose()




tags_metadata = [
    # {
    #     "name": "name_tags_metadata",
    #     "description": "description_tags_metadata"
    # },
    # {
    #     "name": "name_tags_metadata2",
    #     "description": "description_tags_metadata2"
    # },
]


app = FastAPI(
    title="NB",
    description="draft",
    version="0.0.0",
    openapi_tags=tags_metadata,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
    # lifespan=lifespan,
)

app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=routers)
app.include_router(router=websockets_routers)


if not settings.is_production:
    @app.get("/")
    def welcome():
        return {
            "docs_url": f"http://{settings.server_host}:{settings.server_port}/docs",
            "redoc_url": f"http://{settings.server_host}:{settings.server_port}/redoc",
            "openapi_url": f"http://{settings.server_host}:{settings.server_port}/openapi.json",
        }


    @app.get("/check-health-db")
    async def health():
        try:
            from nobarrier.database.session import engine
            async with engine.connect() as conn:
                from sqlalchemy import text
                await conn.execute(text("SELECT 1"))
            status_db = "ok"
        except Exception as e:
            status_db = f"error: {e}"
        return {"status": "ok", "database": status_db}
