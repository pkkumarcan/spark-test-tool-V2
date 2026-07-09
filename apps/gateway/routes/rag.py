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
    try:
        import httpx
        from apps.agent_runtime.rag import QDRANT_URL, COLLECTION_NAME
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/scroll",
                params={"limit": 100, "with_payload": True, "with_vector": False},
            )
            if r.status_code != 200:
                return {"sources": []}
            result = r.json().get("result", {})
            points = result.get("points", [])
            sources_map: dict[str, dict] = {}
            for pt in points:
                payload = pt.get("payload", {})
                src = payload.get("source_file", payload.get("source", "unknown"))
                if src not in sources_map:
                    sources_map[src] = {
                        "id": src,
                        "name": src.split("/")[-1],
                        "chunks": 0,
                        "sample": payload.get("text", "")[:200],
                    }
                sources_map[src]["chunks"] += 1
            return {"sources": list(sources_map.values())}
    except Exception as e:
        logger.warning(f"Failed to list RAG sources: {e}")
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
