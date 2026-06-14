from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.config.database import database
from app.metrics import HTTP_REQUEST_TOTAL
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


@app.middleware("http")
async def prometheus_http_metrics_middleware(request: Request, call_next):
    # Prometheus scrape 자체가 request metric에 섞이지 않도록 제외
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method

    try:
        response = await call_next(request)

        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        status = str(response.status_code)

        HTTP_REQUEST_TOTAL.labels(
            method=method,
            path=path,
            status=status,
        ).inc()

        return response

    except Exception:
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)

        HTTP_REQUEST_TOTAL.labels(
            method=method,
            path=path,
            status="500",
        ).inc()
        raise


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


app.include_router(health_router)
app.include_router(task_router)
