# X09 — Logging & Observability

**Purpose:** How logging works and how to debug issues.  
**Estimated time:** 10 minutes

---

## Logging Setup

Spark V2 uses Python's built-in `logging` module. Logs are output to stdout (captured by Docker).

### Log Levels
- `ERROR` — Failures that need attention
- `WARNING` — Degraded state but still working
- `INFO` — Normal operations
- `DEBUG` — Detailed tracing (enable with `SPARK_DEBUG=true`)

### Log Format
```
2026-07-09 14:30:00 - spark.pipeline - INFO - Pipeline pipe_abc123 failed at script: Ollama timeout
```

---

## Where Logs Appear

### Container Logs
```bash
# All services
docker compose -f infra/docker-compose.yml logs -f

# Gateway only
docker compose -f infra/docker-compose.yml logs -f gateway

# Last 50 lines
docker compose -f infra/docker-compose.yml logs --tail=50 gateway
```

### Key Log Sources

| Logger | Component | What It Logs |
|--------|-----------|--------------|
| `spark.pipeline` | Pipeline runner | Stage transitions, failures, timing |
| `spark.agent` | Agent runtime | Tool calls, LLM responses, state changes |
| `spark.gateway` | API gateway | Request/response, errors |
| `spark.media` | Media workers | ComfyUI calls, TTS, FFmpeg |

---

## Observability Stack

### OpenTelemetry (Optional)
When `SPARK_OTEL_ENABLED=true`:
- Traces are exported to configured endpoint
- Spans cover LLM calls, tool executions, pipeline stages

### Langfuse (Optional)
When `SPARK_LANGFUSE_URL` and `SPARK_LANGFUSE_KEY` are set:
- LLM calls are traced with cost tracking
- Pipeline runs are logged as traces
- Available at configured Langfuse instance

---

## Debugging

### Enable Debug Logging
```bash
# In .env
SPARK_DEBUG=true

# Or run gateway directly with debug
LOGLEVEL=debug uvicorn apps.gateway.main:app --reload
```

### Trace a Pipeline Run
1. Find the pipeline ID from the dashboard
2. Check gateway logs: `docker compose logs gateway | grep pipe_`
3. Check pipeline stage transitions
4. Check media worker logs for ComfyUI/TTS issues

### Trace a Tool Call
1. Check agent runtime logs: `docker compose logs gateway | grep "tool"`
2. Look for `_policy_precheck` messages (sandbox violations)
3. Look for tool handler errors

### Check Database State
```sql
-- Recent tool calls
SELECT tool_name, status, created_at FROM tool_calls ORDER BY created_at DESC LIMIT 20;

-- Active sessions
SELECT id, kind, status FROM sessions WHERE status = 'active';
```

---

## Metrics

### Key Metrics to Monitor
- Request rate per endpoint
- LLM response time
- Pipeline completion rate
- Tool call success rate
- GPU utilization
- Disk usage in `output/`

### Health Check
```bash
curl http://localhost:8080/health
# Returns: {"services": {"postgres": "online", "ollama": "online", ...}}
```
