# X102 — Mixture of Agents (MoA)

**Purpose:** Fan out to multiple LLM models, aggregate responses for higher quality.  
**Created:** 2026-07-09 (V3 — V2 agent integration docs)  
**Estimated time:** 10 minutes

---

## Overview

Mixture of Agents (MoA) queries multiple LLM models in parallel, then aggregates their responses into a single high-quality answer. This improves accuracy and reduces hallucination by leveraging the strengths of different models.

---

## How It Works

```
User Prompt → Fan Out to N Models (parallel) → Collect Responses → Aggregate via Final LLM → Best Answer
```

### Step-by-Step

1. **Fan out:** Send same prompt to 3+ models simultaneously
2. **Collect:** Gather all responses
3. **Aggregate:** Feed all responses to an aggregator model
4. **Synthesize:** Aggregator produces single best answer

---

## Architecture

```python
async def moa_generate(client, prompt, models, aggregator_model):
    # 1. Fan out to all models in parallel
    tasks = [_query_model(client, model, messages) for model in models]
    responses = await asyncio.gather(*tasks)

    # 2. Format candidate responses
    candidates = [f"### {model}\n{resp}" for model, resp in zip(models, responses)]

    # 3. Aggregate via final LLM call
    aggregation_prompt = (
        "You have received multiple candidate responses.\n"
        "Synthesize the best elements into a single, high-quality answer.\n\n"
        "Candidates:\n\n" + "\n\n".join(candidates)
    )

    agg_resp = await client.chat(messages=agg_messages, model=aggregator_model)
    return LLMResponse(content=agg_resp.content)
```

---

## Default Models

| Model | Size | Strength |
|-------|------|----------|
| `qwen3:8b` | 5 GB | Fast, good general |
| `qwen3:14b` | 9 GB | Better reasoning |
| `gemma3:12b` | 8 GB | Creative, different perspective |

**Aggregator:** `qwen3:8b` (fast synthesis)

---

## Usage

### Via API
```bash
POST /api/text/moa
{
  "prompt": "Explain quantum entanglement in simple terms",
  "models": ["qwen3:8b", "qwen3:14b", "gemma3:12b"],
  "aggregator_model": "qwen3:8b"
}
```

### Via Code
```python
from apps.agent_runtime.moa import moa_generate
from apps.agent_runtime.llm_client import LLMClient

client = LLMClient(ollama_url="http://localhost:11434")
result = await moa_generate(
    client=client,
    prompt="Explain quantum entanglement",
    models=["qwen3:8b", "qwen3:14b", "gemma3:12b"],
)
print(result.content)
```

---

## When to Use MoA

| Scenario | Use MoA? | Why |
|----------|----------|-----|
| Complex reasoning question | ✅ Yes | Multiple models catch different angles |
| Creative writing | ✅ Yes | Diverse perspectives improve output |
| Simple factual question | ❌ No | Single model is faster and sufficient |
| Code generation | ⚠️ Maybe | If accuracy is critical |
| Real-time chat | ❌ No | Too slow (3x latency) |

---

## Performance

| Metric | Single Model | MoA (3 models) |
|--------|-------------|-----------------|
| Latency | 2-5s | 6-15s |
| Quality | Good | Better |
| Cost | 1x | 3x |
| Hallucination | Moderate | Lower |

---

## Error Handling

- If a model fails, its response is excluded from aggregation
- If all models fail, returns error message
- If only 1 model succeeds, returns that response directly

---

## Configuration

### Adding Custom Models

```python
# In moa.py
DEFAULT_MODELS = ["qwen3:8b", "qwen3:14b", "gemma3:12b", "your-custom-model"]
```

### Changing Aggregator

```python
# Use a larger model for better synthesis
result = await moa_generate(
    client=client,
    prompt="...",
    aggregator_model="qwen3:14b",  # Better quality, slower
)
```
