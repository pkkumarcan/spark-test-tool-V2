# X07 — Operations Runbook

**Purpose:** Day-to-day operations, common tasks, and troubleshooting.  
**Estimated time:** 20 minutes

---

## Service Management

### Start Services
```bash
cd ~/spark-test-tool-V2
./start.sh
```

### Stop Services
```bash
docker compose -f infra/docker-compose.yml down
```

### Restart a Single Service
```bash
docker compose -f infra/docker-compose.yml restart gateway
docker compose -f infra/docker-compose.yml restart web
```

### View Logs
```bash
# All services
docker compose -f infra/docker-compose.yml logs -f

# Specific service
docker compose -f infra/docker-compose.yml logs -f gateway
docker compose -f infra/docker-compose.yml logs -f web

# Last 100 lines
docker compose -f infra/docker-compose.yml logs --tail=100 gateway
```

### Rebuild After Code Changes
```bash
# Web (frontend changes)
docker compose -f infra/docker-compose.yml build web
docker compose -f infra/docker-compose.yml up -d web

# Gateway (backend changes)
docker compose -f infra/docker-compose.yml build gateway
docker compose -f infra/docker-compose.yml up -d gateway
```

---

## Database Operations

### Connect to PostgreSQL
```bash
docker compose -f infra/docker-compose.yml exec postgres psql -U spark -d spark
```

### Common Queries
```sql
-- List sessions
SELECT id, kind, status, created_at FROM sessions ORDER BY created_at DESC LIMIT 10;

-- List recent messages
SELECT m.role, m.content, m.created_at FROM messages m JOIN sessions s ON m.session_id = s.id ORDER BY m.created_at DESC LIMIT 20;

-- List pipeline jobs
SELECT * FROM jobs WHERE kind = 'pipeline' ORDER BY created_at DESC;

-- Check tool calls
SELECT tool_name, status, created_at FROM tool_calls ORDER BY created_at DESC LIMIT 10;
```

### Backup Database
```bash
docker compose -f infra/docker-compose.yml exec postgres pg_dump -U spark spark > backup.sql
```

### Restore Database
```bash
cat backup.sql | docker compose -f infra/docker-compose.yml exec -T postgres psql -U spark -d spark
```

---

## Monitoring

### Check Service Health
```bash
curl http://localhost:8080/health | python -m json.tool
```

### Check GPU Usage
```bash
nvidia-smi
```

### Check Disk Usage
```bash
df -h
du -sh ~/spark-test-tool-V2/output/
```

### Check Container Resources
```bash
docker stats
```

---

## Common Issues

### Gateway Won't Start
**Symptom:** Container exits immediately  
**Cause:** `SPARK_API_KEY` not set and `SPARK_DEBUG` is false  
**Fix:** Set `SPARK_API_KEY` in `.env` or set `SPARK_DEBUG=true`

### Web UI Blank
**Symptom:** Page loads but no content  
**Cause:** Frontend can't reach API  
**Fix:** Check `NEXT_PUBLIC_API_URL=http://localhost:8080` in `.env`

### Ollama Not Reachable
**Symptom:** LLM calls fail with connection error  
**Cause:** Ollama not running on host  
**Fix:** `ollama serve &` on the host

### ComfyUI Not Reachable
**Symptom:** Image/video generation fails  
**Cause:** ComfyUI not running on host  
**Fix:** `python main.py --listen 0.0.0.0 --port 8188 &` in ComfyUI dir

### Pipeline Stuck at Approval
**Symptom:** Pipeline status shows `pending_approval`  
**Cause:** Waiting for human approval  
**Fix:** Click "Approve" in the pipeline dashboard, or approve via API:
```bash
curl -X POST http://localhost:8080/api/pipeline/{pipeline_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

### Out of VRAM
**Symptom:** ComfyUI or Ollama fails with CUDA OOM  
**Cause:** Too many GPU tasks running simultaneously  
**Fix:** Close other GPU applications, or use smaller models

### Database Connection Refused
**Symptom:** Gateway can't connect to PostgreSQL  
**Fix:**
```bash
# Check Postgres is running
docker compose -f infra/docker-compose.yml ps postgres

# Check health
docker compose -f infra/docker-compose.yml exec postgres pg_isready -U spark

# Restart if needed
docker compose -f infra/docker-compose.yml restart postgres
```

---

## Maintenance Tasks

### Weekly
- Check disk space: `df -h`
- Clean old output files: `rm -rf output/jobs/pipe_*/`
- Check GPU health: `nvidia-smi`

### Monthly
- Update Docker images: `docker compose pull && docker compose up -d`
- Update Ollama models: `ollama pull qwen3:8b`
- Review logs for errors
- Backup database

### As Needed
- Rebuild after code changes: `docker compose build && docker compose up -d`
- Clear model cache: `rm -rf model-cache/` (will re-download on next use)
- Reset database: Drop and recreate the `spark` database
