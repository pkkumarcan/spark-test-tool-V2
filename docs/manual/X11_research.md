# X11 — Research Workflow

**Purpose:** Topic selection using vidIQ + Reddit + gap analysis ("3-Source Braid" method).  
**Updated:** 2026-07-09 (V3 — vidIQ-integrated research framework)  
**Estimated time:** 15 minutes

---

## Overview

Research is the foundation of every video. The "3-Source Braid" method ensures every topic has validated demand before production begins.

---

## The "3-Source Braid" Method

Every video idea must come from 3 sources confirming demand:

| Source | Signal | Threshold | Tool |
|--------|--------|-----------|------|
| **Search** | Monthly search volume | >10,000 | vidIQ |
| **Community** | Reddit engagement | >200 upvotes in 30 days | Reddit |
| **Gap** | Low YouTube competition | <20 videos on exact angle in 30 days | vidIQ |

**Decision matrix:**
- 3/3 signals → **Immediate green light** (produce this week)
- 2/3 signals → **Good idea** (queue for next slot)
- 1/3 signal → **Research further or skip**

---

## Step-by-Step Research Process

### Step 1: Trend Check (vidIQ)

Query vidIQ for trending videos in channel niche:

```
Channel: [CHANNEL NAME]
Niche Keywords: [LIST FROM CHANNEL PROFILE]

Query: What are the top 5 trending videos in [NICHE] in the last 30 days?
Sort by: Views per hour (VPH)
Filter: English language, 5-15 minutes duration
```

**Extract from each trending video:**
- Title structure
- Hook approach
- Thumbnail style
- View count and growth rate

### Step 2: Gap Analysis (vidIQ + YouTube)

From Step 1 results, identify topics that have NOT been covered:

```
For each trending topic:
1. Search YouTube for exact topic + angle
2. Count videos published in last 30 days
3. If fewer than 20 videos → gap exists
4. Check search volume for primary keyword
5. If >10K monthly searches + <20 videos → opportunity
```

### Step 3: Reddit Pulse

Search relevant subreddits for community signal:

```
Channel-specific subreddits:
- DFW: r/lofi, r/studymusic, r/ambientmusic
- STM: r/Stoicism, r/selfimprovement
- ODA: r/UnsolvedMysteries, r/history, r/todayilearned
- PKP: r/longevity, r/biohackers, r/nutrition
- DKS: r/NarcissisticAbuse, r/manipulation
- GDB: r/geopolitics, r/worldnews, r/economics
- ISL: r/hinduism, r/Buddhism, r/spirituality
- NHZ: r/Futurology, r/technology, r/space
- RMR: r/digitalnomad, r/solotravel, r/expats
- BWA: r/LocalLLaMA, r/MachineLearning, r/n8n

Query: Posts with 200+ upvotes in last 14 days
Extract: Questions people are asking that could become video titles
```

### Step 4: Keyword Validation (vidIQ)

Take top 3 topic ideas from Steps 1-3:

```
For each topic:
1. Query vidIQ keyword tool
2. Check: monthly search volume >10K
3. Check: competition score <55
4. Check: overall score >60
5. Select topic with highest score + lowest competition
```

### Step 5: Title Generation

Generate 5 title variations for winning topic:

```
Prompt for LLM:
"Generate 5 YouTube video titles for [CHANNEL] on [TOPIC].
Target audience: [AUDIENCE DESCRIPTION].
Format: Each title must create curiosity without being misleading.
Include: number, 'Why', 'How', or strong emotional trigger word.
Each title addresses a real pain point or burning question."
```

Score each with vidIQ title scorer. Select highest.

---

## Research Output Format

```json
{
  "topic": "The Sleep Protocol That Extends Lifespan",
  "channel": "PKP",
  "primary_keyword": "sleep protocol longevity",
  "search_volume": 15000,
  "competition_score": 42,
  "vidiq_score": 72,
  "reddit_upvotes": 847,
  "gap_analysis": "12 videos in last 30 days (low competition)",
  "title_variants": [
    "The Sleep Protocol That Extends Lifespan (Backed by Science)",
    "5 Sleep Habits That Add Years to Your Life",
    "Why Sleep Is the #1 Longevity Hack (Research Says So)"
  ],
  "selected_title": "The Sleep Protocol That Extends Lifespan (Backed by Science)",
  "hook_idea": "What if the single most powerful thing you could do for your health takes zero effort and costs nothing?",
  "sources": [
    {"type": "vidiq", "data": "trending in longevity niche"},
    {"type": "reddit", "data": "r/longevity post with 847 upvotes"},
    {"type": "gap", "data": "only 12 videos in last 30 days"}
  ]
}
```

---

## Master Research Prompt (Agent)

```
CHANNEL: [CHANNEL NAME]
NICHE KEYWORDS: [LIST FROM CHANNEL PROFILE]

STEP 1 — TREND CHECK
Query vidIQ: What are the top 5 trending videos in [NICHE] in the last 30 days?
Sort by: Views per hour (VPH)
Filter: English language, 5-15 minutes duration

STEP 2 — GAP ANALYSIS
From Step 1 results: What topics have NOT been covered in the last 30 days
that have keyword search volume >10,000 monthly?

STEP 3 — REDDIT PULSE
Search Reddit [RELEVANT SUBREDDITS] for posts with 200+ upvotes in the last 14 days.
What questions are people asking that could become video titles?

STEP 4 — KEYWORD VALIDATION
Take top 3 topic ideas from Steps 1-3.
Query vidIQ keyword tool for each.
Select the topic with: highest overall score + lowest competition +
not already saturated on YouTube (fewer than 20 videos on exact topic in last 30 days).

STEP 5 — TITLE GENERATION
Generate 5 title variations for winning topic.
Score each with vidIQ title scorer.
Select highest-scoring title. Proceed to script generation.
```

---

## Emergency Idea Generation (When Stuck)

Prompt for LLM:

```
"I run a YouTube channel about [NICHE]. My target viewer is [AUDIENCE DESCRIPTION].
Generate 20 video title ideas that:
1. Start with a number, 'Why', 'How', or a strong emotional trigger word
2. Create genuine curiosity without being misleading
3. Have not been done to death on YouTube
4. Could be produced with AI voiceover + generated visuals
5. Each title addresses a real pain point or burning question

Format: Title | Pain point it addresses | Research keywords to check"
```

---

## Per-Channel Research Sources

| Channel | Primary Subreddits | Supplementary Sources |
|---------|-------------------|----------------------|
| DFW | r/lofi, r/studymusic, r/ambientmusic | Last.fm trending, Spotify charts |
| STM | r/Stoicism, r/selfimprovement, r/MentalHealth | Daily Stoic newsletter, Goodreads |
| ODA | r/UnsolvedMysteries, r/history, r/todayilearned | Atlas Obscura, Smithsonian |
| PKP | r/longevity, r/biohackers, r/nutrition | PubMed, Examine.com |
| DKS | r/NarcissisticAbuse, r/manipulation, r/psychology | Psychology Today, APA |
| GDB | r/geopolitics, r/worldnews, r/economics | Reuters, FT, Brookings |
| ISL | r/hinduism, r/Buddhism, r/spirituality | Vedic texts, Wisdom Library |
| NHZ | r/Futurology, r/technology, r/space | MIT Tech Review, arXiv |
| RMR | r/digitalnomad, r/solotravel, r/expats | Numbeo, Nomad List |
| BWA | r/LocalLLaMA, r/MachineLearning, r/n8n | Hugging Face, GitHub trending |

---

## RAG Integration

Research documents are ingested into the RAG system:

```bash
# Ingest channel research
curl -X POST http://localhost:8080/api/rag/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "...", "metadata": {"channel": "STM", "type": "research"}}'
```

Pipeline queries RAG for context when generating scripts.
