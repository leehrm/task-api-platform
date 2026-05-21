from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.database import database
from app.routes.health_routes import router as health_router
from app.routes.task_routes import router as task_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(
    title="Task API Platform",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(task_router)
