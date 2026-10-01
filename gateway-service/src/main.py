import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.clients import close_client, open_client
from src.config import settings
from src.errors import register_exception_handlers
from src.router import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEALTH_PATH = "/manage/health"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    open_client()
    try:
        yield
    finally:
        await close_client()


app = FastAPI(title="Gateway Service", version="v1", lifespan=lifespan)
register_exception_handlers(app)
app.include_router(router)


@app.get(HEALTH_PATH, summary="Health check", tags=["Manage"])
def health() -> dict[str, str]:
    """Отвечает только за сам шлюз: состояние сервисов ниже сюда не подмешивается,
    иначе их перезапуск перезапускал бы и живой шлюз."""
    return {"status": "UP"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port)
