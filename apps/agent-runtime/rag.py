"""Multi-engine RAG: Qdrant (local) / RAGFlow / AnythingLLM."""

from __future__ import annotations

import logging
import os
import uuid

import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "spark_media_factory"

RAG_ENGINE = os.getenv("RAG_ENGINE", "local").lower()
RAGFLOW_URL = os.getenv("RAGFLOW_URL", "http://localhost:9380")
RAGFLOW_API_KEY = os.getenv("RAGFLOW_API_KEY", "")
RAGFLOW_DATASET_ID = os.getenv("RAGFLOW_DATASET_ID", "")

ANYTHINGLLM_URL = os.getenv("ANYTHINGLLM_URL", "http://localhost:3001")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY", "")
ANYTHINGLLM_WORKSPACE = os.getenv("ANYTHINGLLM_WORKSPACE", "spark")


async def get_embedding(text: str) -> list[float]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/embed",
            json={"model": "nomic-embed-text:v1.5", "input": text},
        )
        r.raise_for_status()
        data = r.json()
        embeddings = data.get("embeddings", [])
        if embeddings:
            return embeddings[0]
        if "embedding" in data:
            return data["embedding"]
        raise Exception("No embeddings in response")


async def ensure_collection():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
            if r.status_code == 200:
                return
            await client.put(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}",
                json={"vectors": {"size": 768, "distance": "Cosine"}},
            )
    except Exception as e:
        logger.warning(f"Qdrant ensure_collection: {e}")


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i : i + chunk_size])
        i += chunk_size - overlap
    return chunks


async def ingest(
    text: str,
    metadata: dict | None = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 100,
) -> dict:
    if not text.strip():
        return {"status": "ignored", "reason": "empty text"}

    if RAG_ENGINE == "anythingllm" and ANYTHINGLLM_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {ANYTHINGLLM_API_KEY}"}
            payload = {
                "textContent": text,
                "title": f"ingest_{uuid.uuid4().hex[:8]}.txt",
                "metadata": metadata or {},
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    f"{ANYTHINGLLM_URL}/api/v1/document/raw-text",
                    json=payload, headers=headers,
                )
                if r.status_code == 200:
                    doc_location = r.json().get("location")
                    await client.post(
                        f"{ANYTHINGLLM_URL}/api/v1/workspace/{ANYTHINGLLM_WORKSPACE}/update-embeddings",
                        json={"adds": [doc_location]}, headers=headers,
                    )
                    return {"status": "success", "engine": "anythingllm", "chunks_ingested": 1}
        except Exception as e:
            logger.warning(f"AnythingLLM failed, falling back to local: {e}")

    if RAG_ENGINE == "ragflow" and RAGFLOW_API_KEY and RAGFLOW_DATASET_ID:
        try:
            import tempfile
            headers = {"Authorization": f"Bearer {RAGFLOW_API_KEY}"}
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write(text)
                temp_path = f.name
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    with open(temp_path, "rb") as fb:
                        files = {"file": (f"ingest_{uuid.uuid4().hex[:8]}.txt", fb, "text/plain")}
                        r = await client.post(
                            f"{RAGFLOW_URL}/api/v1/datasets/{RAGFLOW_DATASET_ID}/documents",
                            files=files, headers=headers,
                        )
                    if r.status_code == 200:
                        return {"status": "success", "engine": "ragflow", "chunks_ingested": 1}
            finally:
                os.unlink(temp_path)
        except Exception as e:
            logger.warning(f"RAGFlow failed, falling back to local: {e}")

    # Local Qdrant ingestion
    await ensure_collection()
    chunks = chunk_text(text, chunk_size, chunk_overlap)
    points = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, chunk in enumerate(chunks):
            vector = await get_embedding(chunk)
            payload = {"text": chunk, "chunk_index": i, "total_chunks": len(chunks)}
            if metadata:
                payload.update(metadata)
            points.append({"id": str(uuid.uuid4()), "vector": vector, "payload": payload})

        r = await client.put(
            f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points",
            json={"points": points},
        )
        if r.status_code != 200:
            logger.error(f"Qdrant upsert failed: {r.text}")
            return {"status": "error", "reason": r.text}

    return {"status": "success", "engine": "local", "chunks_ingested": len(chunks)}


async def query(search_text: str, limit: int = 3) -> list[dict]:
    if RAG_ENGINE == "anythingllm" and ANYTHINGLLM_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {ANYTHINGLLM_API_KEY}"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"{ANYTHINGLLM_URL}/api/v1/workspace/{ANYTHINGLLM_WORKSPACE}/chat",
                    json={"message": search_text, "mode": "query"}, headers=headers,
                )
                if r.status_code == 200:
                    res = r.json()
                    hits = []
                    for idx, src in enumerate(res.get("sources", [])[:limit]):
                        hits.append({
                            "text": src.get("text", ""),
                            "score": 0.9 - (idx * 0.1),
                            "source": src.get("title", "AnythingLLM"),
                        })
                    return hits
        except Exception as e:
            logger.warning(f"AnythingLLM query failed: {e}")

    if RAG_ENGINE == "ragflow" and RAGFLOW_API_KEY and RAGFLOW_DATASET_ID:
        try:
            headers = {"Authorization": f"Bearer {RAGFLOW_API_KEY}"}
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(
                    f"{RAGFLOW_URL}/api/v1/datasets/{RAGFLOW_DATASET_ID}/documents",
                    headers=headers,
                )
                if r.status_code == 200:
                    docs = r.json().get("data", [])
                    return [
                        {"text": d.get("name", ""), "score": 0.8, "source": d.get("name", "")}
                        for d in docs[:limit]
                    ]
        except Exception as e:
            logger.warning(f"RAGFlow query failed: {e}")

    # Local Qdrant search
    await ensure_collection()
    vector = await get_embedding(search_text)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search",
                json={"vector": vector, "limit": limit, "with_payload": True},
            )
            if r.status_code != 200:
                return []
            hits = []
            for hit in r.json().get("result", []):
                p = hit.get("payload", {})
                hits.append({
                    "text": p.get("text", ""),
                    "score": hit.get("score", 0.0),
                    "source": p.get("source_file", "unknown"),
                })
            return hits
    except Exception as e:
        logger.error(f"Qdrant search error: {e}")
        return []
