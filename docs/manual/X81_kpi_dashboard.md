# X81 — KPI Dashboard

**Purpose:** Per-channel KPIs, YPP progress tracking, revenue metrics, and health indicators.  
**Created:** 2026-07-09 (V3 — phased KPI tracking)  
**Estimated time:** 10 minutes

---

## Dashboard Overview

The KPI dashboard tracks channel health, growth, and monetization progress across all 10 channels.

---

## Channel Health Metrics

### Per-Channel Status

| Channel | Phase | Status | Subs | Watch Hours | Revenue/mo | YPP |
|---------|-------|--------|------|-------------|------------|-----|
| DFW | 1 | 🟢 Active | 0 | 0 | $0 | ❌ |
| STM | 1 | 🟢 Active | 0 | 0 | $0 | ❌ |
| ODA | 2 | 🟡 Queued | — | — | — | — |
| PKP | 2 | 🟡 Queued | — | — | — | — |
| DKS | 3 | 🔴 Planned | — | — | — | — |
| GDB | 3 | 🔴 Planned | — | — | — | — |
| ISL | 4 | 🔴 Planned | — | — | — | — |
| NHZ | 4 | 🔴 Planned | — | — | — | — |
| RMR | 5 | 🔴 Planned | — | — | — | — |
| BWA | 5 | 🔴 Planned | — | — | — | — |

### Status Legend
- 🟢 **Active** — Currently producing and publishing
- 🟡 **Queued** — Ready to launch, waiting for previous phase
- 🔴 **Planned** — Not yet in production

---

## YPP Progress Tracker

### Tier 1: Fan Funding (500 subs + 3,000 hours)

| Channel | Subs | Progress | Hours | Progress | ETA |
|---------|------|----------|-------|----------|-----|
| DFW | 0/500 | 0% | 0/3,000 | 0% | Month 2 |
| STM | 0/500 | 0% | 0/3,000 | 0% | Month 3 |

### Tier 2: Ad Revenue (1,000 subs + 4,000 hours)

| Channel | Subs | Progress | Hours | Progress | ETA |
|---------|------|----------|-------|----------|-----|
| DFW | 0/1,000 | 0% | 0/4,000 | 0% | Month 3 |
| STM | 0/1,000 | 0% | 0/4,000 | 0% | Month 4 |

### YPP Milestone Alerts

```
When any channel reaches:
- 500 subs → "Tier 1 eligible — apply for fan funding"
- 1,000 subs + 4,000 hours → "Tier 2 eligible — apply for ad revenue"
- 1,000 subs + 8,000 hours → "Premium eligible — apply for Premium revenue"
```

---

## Revenue Dashboard

### Monthly Revenue Summary

| Month | Channels | Videos | Views | Revenue | Cost | Profit |
|-------|----------|--------|-------|---------|------|--------|
| Month 1 | 2 | 8 | 0 | $0 | $45 | -$45 |
| Month 2 | 2 | 16 | 5,000 | $0 | $45 | -$45 |
| Month 3 | 2 | 24 | 20,000 | $150 | $45 | $105 |
| Month 4 | 4 | 32 | 50,000 | $400 | $50 | $350 |
| Month 5 | 4 | 32 | 80,000 | $600 | $50 | $550 |
| Month 6 | 4 | 32 | 120,000 | $1,000 | $50 | $950 |

### Revenue by Stream

| Stream | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|----------|
| AdSense | $150 | $1,000 | $5,000 |
| Affiliates | $0 | $200 | $1,500 |
| Sponsorships | $0 | $0 | $2,000 |
| Courses | $0 | $0 | $1,000 |
| **Total** | **$150** | **$1,200** | **$9,500** |

---

## Production Metrics

### Weekly Production

| Week | Videos Planned | Videos Published | Completion Rate |
|------|---------------|------------------|-----------------|
| Week 1 | 4 | 0 | 0% |
| Week 2 | 4 | 0 | 0% |
| Week 3 | 4 | 0 | 0% |

### Pipeline Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Avg time per video | <30 min | — | — |
| Pipeline success rate | >90% | — | — |
| Approval rate | >80% | — | — |
| Rework rate | <10% | — | — |

---

## Content Performance

### Top Performing Videos

| Rank | Channel | Title | Views | CTR | Retention |
|------|---------|-------|-------|-----|-----------|
| 1 | — | — | — | — | — |
| 2 | — | — | — | — | — |
| 3 | — | — | — | — | — |

### Underperforming Videos (Need Attention)

| Channel | Title | Issue | Action |
|---------|-------|-------|--------|
| — | — | CTR <3% | A/B test thumbnail |
| — | — | Retention <40% | Review script structure |

---

## Health Indicators

### System Health

| Component | Status | Last Check |
|-----------|--------|------------|
| Gateway | 🟢 Online | — |
| PostgreSQL | 🟢 Online | — |
| Ollama | 🟢 Online | — |
| ComfyUI | 🟢 Online | — |
| ElevenLabs | 🟢 Online | — |
| F5-TTS | 🟢 Online | — |

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Disk usage | >70% | >90% |
| GPU VRAM | >80% | >95% |
| API errors | >5/hour | >20/hour |
| Pipeline failures | >2/week | >5/week |

---

## Weekly Report Template

```
SPARK MEDIA FACTORY — WEEKLY REPORT
Week of: [DATE]

PRODUCTION:
- Videos published: X/X planned
- Pipeline success rate: X%
- Avg production time: X min

CHANNELS:
- DFW: X subs (+X), X watch hours (+X)
- STM: X subs (+X), X watch hours (+X)

REVENUE:
- AdSense: $X
- Affiliates: $X
- Total: $X

TOP PERFORMER:
- [Channel]: "[Title]" — X views, X% CTR

ACTION ITEMS:
1. [ ]
2. [ ]
3. [ ]
```

---

## Dashboard Access

### Web UI
Navigate to http://localhost:3002 and check:
- Dashboard page for system health
- Pipeline page for production status
- KPI route for detailed metrics

### API
```bash
# Get KPI summary
curl http://localhost:8080/api/kpi/summary

# Get channel stats
curl http://localhost:8080/api/kpi/channels

# Get revenue report
curl http://localhost:8080/api/kpi/revenue
```
