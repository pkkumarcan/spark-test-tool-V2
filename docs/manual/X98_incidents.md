# X98 — Incident Response

**Purpose:** How to handle system failures and incidents.  
**Estimated time:** 15 minutes

---

## Incident Severity Levels

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| P0 | System down | Immediate | Gateway won't start |
| P1 | Major feature broken | < 1 hour | Pipeline fails at every stage |
| P2 | Minor feature degraded | < 4 hours | TTS fallback to silence |
| P3 | Cosmetic / low impact | Next day | Dashboard shows stale data |

---

## Common Incidents

### P0: Gateway Won't Start
**Symptoms:** Container exits, health check fails  
**Diagnosis:**
```bash
docker compose -f infra/docker-compose.yml logs gateway | tail -20
```
**Common causes:**
1. `SPARK_API_KEY` not set → Set it in `.env`
2. PostgreSQL not running → `docker compose up -d postgres`
3. Port 8080 in use → `ss -tlnp | grep 8080`

**Fix:** Set the required env var, restart gateway.

### P0: PostgreSQL Down
**Symptoms:** All DB operations fail  
**Diagnosis:**
```bash
docker compose -f infra/docker-compose.yml ps postgres
docker compose -f infra/docker-compose.yml logs postgres | tail -20
```
**Fix:** `docker compose restart postgres`

### P1: Pipeline Fails at Every Stage
**Symptoms:** All pipelines immediately go to FAILED  
**Diagnosis:**
```bash
docker compose logs gateway | grep "pipeline.*failed"
```
**Common causes:**
1. Ollama not running → Start Ollama
2. ComfyUI not running → Start ComfyUI
3. Database connection lost → Restart gateway

### P1: Ollama Not Reachable
**Symptoms:** LLM calls fail with connection error  
**Diagnosis:**
```bash
curl http://localhost:11434/api/tags
```
**Fix:** `ollama serve &`

### P2: TTS Fallback to Silence
**Symptoms:** Pipeline completes but video has no audio  
**Diagnosis:**
```bash
docker compose logs gateway | grep "F5-TTS"
```
**Fix:** Restart F5-TTS container:
```bash
docker compose restart f5-tts
```

### P2: ComfyUI Timeout
**Symptoms:** Pipeline stuck at VISUALS stage  
**Diagnosis:**
```bash
curl http://localhost:8188/system_stats
nvidia-smi
```
**Fix:** Check GPU memory, restart ComfyUI if needed.

### P3: Dashboard Shows Stale Data
**Symptoms:** Pipeline status not updating  
**Fix:** Click Refresh, or restart gateway.

---

## Escalation Procedure

1. **Check logs** for error messages
2. **Check health endpoint** for service status
3. **Restart the failing service**
4. **If persistent:** Check GPU, disk space, database
5. **If unresolvable:** Document the issue and work around it

---

## Post-Incident

After any P0 or P1 incident:
1. Document what happened
2. Identify root cause
3. Add monitoring/alerting if missing
4. Update this runbook if it's a new failure mode
5. Consider adding automated recovery

---

## Emergency Commands

```bash
# Nuclear option: restart everything
docker compose -f infra/docker-compose.yml down
docker compose -f infra/docker-compose.yml up -d

# Check all container statuses
docker compose -f infra/docker-compose.yml ps

# Force rebuild
docker compose -f infra/docker-compose.yml build --no-cache
docker compose -f infra/docker-compose.yml up -d

# View all logs (last 500 lines)
docker compose -f infra/docker-compose.yml logs --tail=500

# Check disk space
df -h

# Check GPU
nvidia-smi

# Check database
docker compose exec postgres psql -U spark -d spark -c "SELECT 1;"
```
