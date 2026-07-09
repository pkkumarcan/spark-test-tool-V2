# X10 — Reliability

**Purpose:** How Spark V2 handles failures, retries, and degraded states.  
**Estimated time:** 10 minutes

---

## Retry Mechanisms

### LLM Client Retries
- **Attempts:** 3
- **Delays:** 2s, 4s, 8s (exponential backoff)
- **Applies to:** All Ollama API calls (chat, stream)

### Pipeline Stage Retries
- Each stage runs independently
- If a stage fails, the pipeline stops (does not skip)
- Failed pipelines can be re-run from the dashboard

### Tool Call Retries
- The agent state machine retries tool calls automatically
- After 3 consecutive identical tool calls, stuck-loop detection triggers
- Agent is told to try a different approach

---

## Failure Modes

| Failure | Recovery |
|---------|----------|
| Ollama down | LLM calls fail with error, agent stops |
| ComfyUI down | Image/video generation falls back to placeholder |
| F5-TTS down | Voiceover falls back to silence (ffmpeg) |
| PostgreSQL down | Gateway fails to start |
| GPU OOM | ComfyUI request fails, pipeline stage fails |
| Network timeout | Retried 3 times, then fails |
| Invalid JSON from LLM | Fallback mock data used in pipeline |

---

## Stuck Loop Detection

The agent tracks recent tool calls:
```python
if len(recent_tool_calls) == 3 and len(set(recent_tool_calls)) == 1:
    consecutive_errors += 1
    if consecutive_errors >= 2:
        # Stop to prevent infinite loop
        yield error("Stuck loop: repeated tool N times. Stopping.")
        state = FAILED
```

---

## Graceful Degradation

### Pipeline Fallbacks
- **Ollama fails** → Mock brief/script generated (pipeline continues)
- **F5-TTS fails** → Silence audio generated via FFmpeg (pipeline continues)
- **ComfyUI fails** → Placeholder images generated via FFmpeg (pipeline continues)
- **Publishing fails** → Video saved locally, upload retried

### Tool Fallbacks
- **Shell command fails** → Error message returned to agent
- **File not found** → Error message returned to agent
- **Network blocked** → Policy violation error returned

---

## Data Durability

- **Sessions:** Stored in PostgreSQL (survives gateway restart)
- **Pipeline state:** In-memory dict (lost on gateway restart)
- **Output files:** Written to disk (survives restart)
- **Job queue:** Procrastinate uses PostgreSQL (survives restart)

**Note:** Pipeline state is currently in-memory. If the gateway restarts, running pipelines are lost. Use the dashboard to re-run them.
