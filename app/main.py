from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.config.database import database
from app.metrics import HTTP_REQUEST_TOTAL, HTTP_REQUEST_DURATION_SECONDS
from app.routes.health_routes import router as health_router
from app.routes.task_routes import router as task_router
from app.routes.debug_routes import router as debug_router

import time


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    yield


app = FastAPI(
    title="Task API Platform",
    version="0.3.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def prometheus_http_metrics_middleware(request: Request, call_next):
    # Prometheus scrape 자체가 request metric에 섞이지 않도록 제외
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    start_time = time.perf_counter()
    status = "500"

    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response

    except Exception:
        status = "500"
        raise

    finally:
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        duration_seconds = time.perf_counter() - start_time

        HTTP_REQUEST_TOTAL.labels(
            method=method,
            path=path,
            status=status,
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=method,
            path=path,
            status=status,
        ).observe(duration_seconds)


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


app.include_router(health_router)
app.include_router(task_router)
app.include_router(debug_router)
