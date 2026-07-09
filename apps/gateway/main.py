import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from apps.agent_runtime.session import init_db
from apps.gateway.config import settings
from apps.gateway.jobs import close_pool, init_pool
from apps.gateway.middleware import (
    APIKeyMiddleware,
    BodySizeLimitMiddleware,
    RateLimitMiddleware,
)
from apps.gateway.routes.agent import router as agent_router
from apps.gateway.routes.chat import router as chat_router
from apps.gateway.routes.gems import router as gems_router
from apps.gateway.routes.ide import router as ide_router
from apps.gateway.routes.kpi import router as kpi_router
from apps.gateway.routes.media import router as media_router
from apps.gateway.routes.metrics import router as metrics_router
from apps.gateway.routes.pipeline import router as pipeline_router
from apps.gateway.routes.publish import router as publish_router
from apps.gateway.routes.rag import router as rag_router
from apps.gateway.routes.system import router as system_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.postgres_url)
    await init_pool(settings.postgres_url)
    from apps.agent_runtime.pipeline import set_database_url
    set_database_url(settings.postgres_url)
    yield
    await close_pool()


app = FastAPI(
    title="Spark Media Factory V2",
    version="2.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def dynamic_cors(request: Request, call_next):
    origin = request.headers.get("origin", "")
    if request.method == "OPTIONS":
        resp = Response(status_code=204)
    else:
        resp = await call_next(request)
    resp.headers["Access-Control-Allow-Origin"] = origin
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "*"
    resp.headers["Access-Control-Max-Age"] = "600"
    if origin:
        resp.headers["Vary"] = "Origin"
    return resp
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_size)
app.add_middleware(APIKeyMiddleware, api_key=settings.api_key)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100, trust_proxy_headers=settings.trust_proxy_headers)

if not settings.api_key:
    logger.warning(
        "SPARK_API_KEY is not set — the gateway is running with NO API "
        "authentication. Set SPARK_API_KEY before exposing this service."
    )
if not settings.debug and not settings.api_key:
    raise RuntimeError(
        "SPARK_API_KEY must be set when SPARK_DEBUG is False. "
        "Set SPARK_API_KEY or enable SPARK_DEBUG for development."
    )

app.include_router(system_router)
app.include_router(agent_router)
app.include_router(chat_router)
app.include_router(media_router)
app.include_router(pipeline_router)
app.include_router(publish_router)
app.include_router(ide_router)
app.include_router(rag_router)
app.include_router(gems_router)
app.include_router(kpi_router)
app.include_router(metrics_router)
