import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config import settings
from src.database import SessionLocal, init_db
from src.errors import register_exception_handlers
from src.router import books_router, libraries_router, lookup_router
from src.seed import seed_reference_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEALTH_PATH = "/manage/health"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        init_db()
        if settings.seed_on_startup:
            with SessionLocal() as session:
                seed_reference_data(session)
    except Exception:
        logger.exception("Не удалось подготовить БД")
        raise
    yield


app = FastAPI(title="Library Service", version="v1", lifespan=lifespan)
register_exception_handlers(app)
app.include_router(libraries_router)
app.include_router(books_router)
app.include_router(lookup_router)


@app.get(HEALTH_PATH, summary="Health check", tags=["Manage"])
def health() -> dict[str, str]:
    return {"status": "UP"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.port)
