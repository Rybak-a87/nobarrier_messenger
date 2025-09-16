import uvicorn

from nobarrier.core.settings import settings


uvicorn.run(
    app="nobarrier.main:app",
    host=settings.server_host,
    port=settings.server_port,
    reload=True,
)
