# ADR-002: Native Model Tool-Calling Only

**Status:** Accepted  
**Date:** 2026-07-04  
**Deciders:** Spark Engineering

## Context

V1's coding agent used a 3-stage JSON parser with regex fallbacks to extract tool calls from model output. This was the single biggest bug class:
- Models sometimes output malformed JSON
- Regex patterns broke on edge cases (nested objects, multiline strings)
- Pydantic validation caught some issues but not all
- Tool call parsing was fragile and model-dependent

## Decision

Use only native model tool-calling APIs (Ollama's `tools` parameter, OpenAI-compatible function calling). No regex/JSON parsing fallbacks.

## Consequences

**Positive:**
- Eliminates entire class of parsing bugs
- Model outputs structured tool calls natively (no ambiguity)
- Gateway validates against JSON schemas, not raw text
- Easier to add new tools (define schema, model calls it)
- Works across providers (Ollama, vLLM, OpenAI) with same interface

**Negative:**
- Requires models that support tool-calling (qwen3, llama3.1, mistral, etc.)
- Older/smaller models may not support tool-calling well
- Slightly higher token usage for tool-call formatting

**Mitigations:**
- All target models (qwen3:8b, llama3.1:8b, gemma4:12b) support tool-calling
- Fallback to chat-only mode for models without tool support
- Token overhead is minimal vs parsing reliability gains

## Alternatives Considered

1. **JSON + regex parsing** — V1 approach, proven fragile
2. **Structured output (grammar-constrained)** — emerging but not widely supported
3. **Custom fine-tune for tool calling** — too expensive for this project
