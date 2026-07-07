"""Integration tests for RAG: ingest + query via Qdrant/RAGFlow/AnythingLLM."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
class TestRAGChunkText:
    def test_chunk_text_basic(self):
        from apps.agent_runtime.rag import chunk_text
        text = "a" * 2000
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) >= 3

    def test_chunk_text_short(self):
        from apps.agent_runtime.rag import chunk_text
        text = "short text"
        chunks = chunk_text(text, chunk_size=1000, overlap=100)
        assert len(chunks) == 1
        assert chunks[0] == "short text"

    def test_chunk_text_empty(self):
        from apps.agent_runtime.rag import chunk_text
        chunks = chunk_text("", chunk_size=1000, overlap=100)
        assert len(chunks) == 0

    def test_chunk_text_overlap(self):
        from apps.agent_runtime.rag import chunk_text
        text = "A" * 100 + "B" * 100 + "C" * 100
        chunks = chunk_text(text, chunk_size=150, overlap=50)
        assert len(chunks) >= 2

    def test_chunk_text_exact_size(self):
        from apps.agent_runtime.rag import chunk_text
        text = "x" * 1000
        chunks = chunk_text(text, chunk_size=1000, overlap=0)
        assert len(chunks) == 1


@pytest.mark.asyncio
class TestRAGIngest:
    async def test_ingest_empty_text(self):
        from apps.agent_runtime.rag import ingest
        result = await ingest(text="   ")
        assert result["status"] == "ignored"

    @patch("apps.agent_runtime.rag.RAG_ENGINE", "local")
    @patch("apps.agent_runtime.rag.ensure_collection", new_callable=AsyncMock)
    @patch("apps.agent_runtime.rag.get_embedding", new_callable=AsyncMock)
    @patch("httpx.AsyncClient")
    async def test_ingest_local_success(self, mock_client_cls, mock_embed, mock_ensure):
        from apps.agent_runtime.rag import ingest

        mock_embed.return_value = [0.1] * 768

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.put.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await ingest(text="This is test content for RAG.")
        assert result["status"] == "success"
        assert result["engine"] == "local"
        assert result["chunks_ingested"] >= 1

    @patch("apps.agent_runtime.rag.RAG_ENGINE", "local")
    @patch("apps.agent_runtime.rag.ensure_collection", new_callable=AsyncMock)
    @patch("apps.agent_runtime.rag.get_embedding", new_callable=AsyncMock)
    @patch("httpx.AsyncClient")
    async def test_ingest_with_metadata(self, mock_client_cls, mock_embed, mock_ensure):
        from apps.agent_runtime.rag import ingest

        mock_embed.return_value = [0.1] * 768
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.put.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await ingest(
            text="Document content here.",
            metadata={"source_file": "readme.md", "author": "test"},
        )
        assert result["status"] == "success"

    @patch("apps.agent_runtime.rag.RAG_ENGINE", "local")
    @patch("apps.agent_runtime.rag.ensure_collection", new_callable=AsyncMock)
    @patch("apps.agent_runtime.rag.get_embedding", new_callable=AsyncMock)
    @patch("httpx.AsyncClient")
    async def test_ingest_large_text_multiple_chunks(self, mock_client_cls, mock_embed, mock_ensure):
        from apps.agent_runtime.rag import ingest

        mock_embed.return_value = [0.1] * 768
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "ok"
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.put.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        large_text = "This is sentence number X. " * 500
        result = await ingest(text=large_text)
        assert result["status"] == "success"
        assert result["chunks_ingested"] > 1


@pytest.mark.asyncio
class TestRAGQuery:
    @patch("apps.agent_runtime.rag.RAG_ENGINE", "local")
    @patch("apps.agent_runtime.rag.ensure_collection", new_callable=AsyncMock)
    @patch("apps.agent_runtime.rag.get_embedding", new_callable=AsyncMock)
    @patch("httpx.AsyncClient")
    async def test_query_local(self, mock_client_cls, mock_embed, mock_ensure):
        from apps.agent_runtime.rag import query

        mock_embed.return_value = [0.1] * 768

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "result": [
                {
                    "payload": {"text": "Found result", "source_file": "doc.md"},
                    "score": 0.95,
                }
            ]
        }

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        results = await query("search term", limit=3)
        assert len(results) >= 1
        assert results[0]["text"] == "Found result"

    @patch("apps.agent_runtime.rag.RAG_ENGINE", "local")
    @patch("apps.agent_runtime.rag.ensure_collection", new_callable=AsyncMock)
    @patch("apps.agent_runtime.rag.get_embedding", new_callable=AsyncMock)
    @patch("httpx.AsyncClient")
    async def test_query_empty_results(self, mock_client_cls, mock_embed, mock_ensure):
        from apps.agent_runtime.rag import query

        mock_embed.return_value = [0.1] * 768

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"result": []}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        results = await query("nonexistent", limit=5)
        assert len(results) == 0

    @patch("apps.agent_runtime.rag.RAG_ENGINE", "local")
    @patch("apps.agent_runtime.rag.ensure_collection", new_callable=AsyncMock)
    @patch("apps.agent_runtime.rag.get_embedding", new_callable=AsyncMock)
    @patch("httpx.AsyncClient")
    async def test_query_limit_respected(self, mock_client_cls, mock_embed, mock_ensure):
        from apps.agent_runtime.rag import query

        mock_embed.return_value = [0.1] * 768

        hits = [
            {"payload": {"text": f"result {i}", "source_file": "doc.md"}, "score": 0.9 - i * 0.1}
            for i in range(10)
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"result": hits}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        results = await query("test", limit=3)
        assert len(results) == 10
        call_json = mock_client.post.call_args.kwargs.get("json", mock_client.post.call_args[1].get("json", {}))
        assert call_json.get("limit") == 3


@pytest.mark.asyncio
class TestRAGEnsureCollection:
    @patch("apps.agent_runtime.rag.QDRANT_URL", "http://localhost:6333")
    @patch("httpx.AsyncClient")
    async def test_collection_already_exists(self, mock_client_cls):
        from apps.agent_runtime.rag import ensure_collection

        mock_resp = MagicMock()
        mock_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await ensure_collection()
        mock_client.get.assert_called_once()

    @patch("apps.agent_runtime.rag.QDRANT_URL", "http://localhost:6333")
    @patch("httpx.AsyncClient")
    async def test_collection_creates_new(self, mock_client_cls):
        from apps.agent_runtime.rag import ensure_collection

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 404
        mock_put_resp = MagicMock()
        mock_put_resp.status_code = 200

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_get_resp
        mock_client.put.return_value = mock_put_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await ensure_collection()
        mock_client.put.assert_called_once()

    @patch("apps.agent_runtime.rag.QDRANT_URL", "http://localhost:6333")
    @patch("httpx.AsyncClient")
    async def test_collection_handles_connection_error(self, mock_client_cls):
        from apps.agent_runtime.rag import ensure_collection

        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        await ensure_collection()


@pytest.mark.asyncio
class TestRAGGetEmbedding:
    @patch("apps.agent_runtime.rag.OLLAMA_URL", "http://localhost:11434")
    @patch("httpx.AsyncClient")
    async def test_get_embedding(self, mock_client_cls):
        from apps.agent_runtime.rag import get_embedding

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        vec = await get_embedding("test text")
        assert vec == [0.1, 0.2, 0.3]

    @patch("apps.agent_runtime.rag.OLLAMA_URL", "http://localhost:11434")
    @patch("httpx.AsyncClient")
    async def test_get_embedding_fallback_field(self, mock_client_cls):
        from apps.agent_runtime.rag import get_embedding

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"embedding": [0.4, 0.5, 0.6]}
        mock_resp.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        vec = await get_embedding("test text")
        assert vec == [0.4, 0.5, 0.6]
