# X95 — Tracking & Attribution

**Purpose:** vidIQ analytics, CTR/retention benchmarks, A/B testing, performance optimization.  
**Created:** 2026-07-09 (V3 — vidIQ-integrated performance tracking)  
**Estimated time:** 15 minutes

---

## Overview

Performance tracking uses vidIQ analytics to optimize every video. The agent automatically pulls metrics and flags underperformers for improvement.

---

## Key Metrics

### Primary KPIs

| Metric | Target | Flag If | Action |
|--------|--------|---------|--------|
| **CTR** (Click-Through Rate) | >3% | <3% | Thumbnail A/B test |
| **Retention** (Average % viewed) | >40% | <40% | Script structure review |
| **Views** (first 48 hours) | >500 | <100 | Title/thumbnail re-evaluation |
| **Watch Time** (total hours) | Growing | Declining | Content quality review |
| **Subscribers** (per video) | >5 | 0 | CTA effectiveness review |

### Secondary KPIs

| Metric | Target | Notes |
|--------|--------|-------|
| Like/Dislike ratio | >95% | Content quality signal |
| Comments per video | >10 | Engagement signal |
| Share rate | >1% | Virality potential |
| End screen CTR | >2% | Navigation effectiveness |
| Card CTR | >3% | Cross-promotion effectiveness |

---

## vidIQ Integration

### Pulling Analytics

```python
# Agent prompt for weekly analytics review
"""
Pull vidIQ analytics for [CHANNEL] for the last 7 days.
For each video published in this period, extract:
- Views (total and last 7 days)
- CTR (click-through rate)
- Average retention (%)
- Watch time (hours)
- Subscriber gain
- Like/dislike ratio

Flag any video with:
- CTR <3% (needs thumbnail A/B test)
- Retention <40% (needs script review)
- Views <100 in 48 hours (needs title/thumbnail re-evaluation)
"""
```

### vidIQ Title Scorer

Before publishing, score every title:

```
Title: "The Sleep Protocol That Extends Lifespan"
vidIQ Score: 72/100
Breakdown:
- Keyword strength: 8/10
- Competition: 6/10
- Engagement potential: 7/10
- Length: 9/10
```

**Target:** 70+ score before publishing

---

## A/B Testing Framework

### Thumbnail A/B Testing

When CTR <3%:
1. Generate 2-3 alternative thumbnails
2. Upload as unlisted
3. After 48 hours, compare CTR
4. Replace underperformer with winner

**What to vary:**
- Text (different words, same message)
- Face (different expression)
- Color (high contrast vs. muted)
- Composition (close-up vs. wide)

### Title A/B Testing

When views <100 in 48 hours:
1. Generate 2-3 alternative titles
2. Change title on existing video
3. After 48 hours, compare view rate
4. Keep winner

**What to vary:**
- Number vs. no number
- Question vs. statement
- Emotional trigger word
- Keyword placement

---

## Weekly Performance Review

### Agent-Automated Review (Every Sunday)

```
CHANNEL: [CHANNEL NAME]
PERIOD: Last 7 days

FOR EACH VIDEO PUBLISHED THIS WEEK:
1. Pull vidIQ analytics
2. Compare to channel averages
3. Flag underperformers (CTR <3%, retention <40%)
4. Identify top performer
5. Extract what worked (title pattern, topic, hook style)
6. Brief 3 similar videos for next week

OUTPUT: Performance summary + next week's content brief
```

### Monthly Deep Dive

```
CHANNEL: [CHANNEL NAME]
PERIOD: Last 30 days

ANALYSIS:
1. Top 3 performing videos — what patterns?
2. Bottom 3 performing videos — what went wrong?
3. CTR trend — improving or declining?
4. Retention trend — improving or declining?
5. Subscriber growth rate
6. Revenue per video trend

RECOMMENDATIONS:
1. Content strategy adjustments
2. Thumbnail style changes
3. Title formula updates
4. Posting schedule optimization
```

---

## Benchmark Targets by Channel

| Channel | CTR Target | Retention Target | Views Target (48hr) |
|---------|-----------|------------------|---------------------|
| DFW | 2% (lower for lofi) | 60%+ (long videos) | 200+ |
| STM | 4% | 45% | 300+ |
| ODA | 5% (high curiosity) | 40% | 500+ |
| PKP | 3% | 45% | 200+ |
| DKS | 4% | 40% | 300+ |
| GDB | 3% | 45% | 200+ |
| ISL | 3% | 50% (loyal audience) | 150+ |
| NHZ | 4% | 45% | 200+ |
| RMR | 3% | 40% | 150+ |
| BWA | 5% (high intent) | 50% (tutorial) | 200+ |

---

## Revenue Tracking

### Per-Video Revenue

```python
# Track revenue per video
revenue_per_video = {
    "video_id": "abc123",
    "channel": "STM",
    "adsense_revenue": 12.50,
    "affiliate_revenue": 3.20,
    "total_revenue": 15.70,
    "cost_to_produce": 0.10,  # TTS + electricity
    "roi": 15600  # percentage
}
```

### Monthly Revenue Dashboard

| Channel | Videos | Views | Revenue | Cost | Profit | ROI |
|---------|--------|-------|---------|------|--------|-----|
| DFW | 12 | 60,000 | $360 | $2 | $358 | 17,900% |
| STM | 8 | 16,000 | $192 | $1 | $191 | 19,100% |
| ODA | 8 | 24,000 | $240 | $1 | $239 | 23,900% |
| **Total** | **28** | **100,000** | **$792** | **$4** | **$788** | **19,700%** |

---

## Optimization Checklist

### Before Publishing
- [ ] Title scored 70+ with vidIQ
- [ ] Thumbnail follows channel template
- [ ] Description includes timestamps + affiliate links
- [ ] Tags: top 15 by vidIQ score
- [ ] AI disclosure enabled

### After Publishing (48 hours)
- [ ] Check CTR — if <3%, plan A/B test
- [ ] Check retention — if <40%, note for script review
- [ ] Respond to all comments
- [ ] Share on social media

### After Publishing (7 days)
- [ ] Full analytics review
- [ ] Compare to channel average
- [ ] Identify what worked
- [ ] Brief 3 similar videos
- [ ] Update content strategy if needed
