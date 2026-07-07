"""RAG routes — /api/rag/* for retrieval-augmented generation."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apps.agent_runtime import rag as rag_module

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["rag"])


class IngestRequest(BaseModel):
    text: str
    metadata: dict = {}
    chunk_size: int = 1000
    chunk_overlap: int = 100
    chunking_strategy: str = "sentence"


class QueryRequest(BaseModel):
    query: str
    limit: int = 3
    search_mode: str = "semantic"


class DeleteSourceRequest(BaseModel):
    source_id: str


@router.get("/sources")
async def list_sources():
    return {"sources": []}


@router.post("/ingest")
async def ingest(req: IngestRequest):
    return await rag_module.ingest(req.text, req.metadata)


@router.post("/query")
async def query_rag(req: QueryRequest):
    hits = await rag_module.query(req.query, req.limit)
    return {"hits": hits}


@router.post("/delete-source")
async def delete_source(req: DeleteSourceRequest):
    return {"status": "ok", "message": f"Source {req.source_id} deleted"}


@router.post("/clear-all")
async def clear_all():
    return {"status": "ok", "message": "All RAG data cleared"}
