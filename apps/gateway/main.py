from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(settings.postgres_url)
    await init_pool(settings.postgres_url)
    yield
    await close_pool()


app = FastAPI(
    title="Spark Media Factory V2",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_size)
app.add_middleware(APIKeyMiddleware, api_key=settings.api_key)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

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
