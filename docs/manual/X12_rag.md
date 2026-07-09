# X12 — RAG & Knowledge Base

**Purpose:** How the Retrieval-Augmented Generation system works.  
**Estimated time:** 15 minutes

---

## Overview

RAG (Retrieval-Augmented Generation) allows the agent and pipeline to query a knowledge base of documents, providing context-aware responses grounded in factual data.

---

## Architecture

```
Documents → Chunking → Embeddings → Vector Store → Query → Relevant Chunks → LLM Context
```

1. **Ingestion:** Documents are chunked and embedded
2. **Storage:** Embeddings stored in Postgres (pgvector)
3. **Query:** User query is embedded, similarity search finds relevant chunks
4. **Context:** Top chunks are injected into LLM prompt

---

## API Endpoints

### Ingest Documents
```bash
POST /api/rag/ingest
{
  "content": "Document text here...",
  "metadata": {
    "channel": "MLN",
    "topic": "central bank policy",
    "source": "research_brief.md"
  }
}
```

### Query
```bash
POST /api/rag/query
{
  "query": "What are central banks buying gold for?",
  "limit": 5,
  "channel": "MLN"  // optional filter
}
```

### List Documents
```bash
GET /api/rag/documents?channel=MLN
```

---

## Chunking Strategy

Documents are split into chunks of ~500 tokens with 50-token overlap. This ensures:
- Each chunk is self-contained enough for context
- Overlap prevents information loss at boundaries
- Chunks fit within typical LLM context windows

---

## Usage in Pipeline

When a pipeline runs, it:
1. Queries RAG with the topic + channel niche
2. Retrieves top 5 relevant chunks
3. Injects them as context in the LLM prompt
4. LLM generates research brief grounded in retrieved facts

---

## Ingesting V1 Research

V1 research documents can be ingested into V2's RAG:

```bash
# From the V1 research directory
for f in ~/AGGY/spark-test-tool/research/Q3_2026/*/00_master_brief.md; do
  channel=$(basename $(dirname $f))
  content=$(cat "$f")
  curl -X POST http://localhost:8080/api/rag/ingest \
    -H "Content-Type: application/json" \
    -d "{\"content\": \"$content\", \"metadata\": {\"channel\": \"$channel\"}}"
done
```
