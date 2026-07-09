# X00 — Pipeline Architecture

**Purpose:** End-to-end content pipeline design with vidIQ integration.  
**Updated:** 2026-07-09 (V3 — based on vidIQ master reference)  
**Estimated time:** 25 minutes

---

## Pipeline Overview (V3 — 10 Steps)

```
STEP 1: Topic Selection (vidIQ + Agent)
STEP 2: Research Brief (Gemini Pro / LLM)
STEP 3: Script Generation (LLM)
STEP 4: Human Approval ← GATE
STEP 5: Voiceover (ElevenLabs TTS)
STEP 6: Visual Generation (Stable Diffusion XL)
STEP 7: Video Assembly (DaVinci Resolve)
STEP 8: Thumbnail (SD + Photopea)
STEP 9: Metadata & SEO (Agent + vidIQ)
STEP 10: Schedule & Publish
```

---

## Step-by-Step Details

### Step 1: Topic Selection (Agent + vidIQ)

**Input:** Channel niche keywords  
**Output:** Topic brief with keyword, angle, hook idea

**Process:**
1. Query vidIQ for trending topics in channel niche
2. Filter: search volume >10K, competition <55, published in last 30 days
3. Cross-reference with Reddit (200+ upvotes in last 14 days)
4. Gap analysis: fewer than 20 YouTube videos on exact topic in last 30 days
5. Select top 3 candidates, score with vidIQ title scorer
6. Output: Topic brief with keyword, angle, hook idea

**The "3-Source Braid" Method:**
Every video idea must come from 3 sources confirming demand:
1. **Search signal**: vidIQ shows >10K monthly searches
2. **Community signal**: Reddit post has >200 upvotes in last 30 days
3. **Gap signal**: Fewer than 20 YouTube videos cover this exact angle

When all 3 align → immediate green light. When 2 of 3 → queue for next slot.

---

### Step 2: Research Brief (LLM)

**Input:** Topic + channel niche  
**Output:** Structured research brief

**Prompt template:**
```
"You are a [CHANNEL PERSONA] researcher. Generate a research brief for
the topic: [TOPIC]. Include: 5 key facts, 3 surprising angles, primary
search intent, competing video angles to avoid. Format: bullet points."
```

---

### Step 3: Script Generation (LLM)

**Input:** Research brief + channel tone  
**Output:** Narrator-led script with timing

**Prompt template:**
```
"Write a [DURATION]-minute YouTube script for [CHANNEL NAME] on [TOPIC].
Structure: HOOK (0-30s, open loop), INTRO (30-60s, context),
BODY (4-6 main points with transitions), CTA (final 30s, subscribe + next video tease).
Tone: [CHANNEL TONE]. Do not mention AI generation."
```

**Script structure per section:**
- HOOK (0-30s) — Open loop, personal stakes, curiosity gap
- INTRO (30-60s) — Channel branding, topic context
- BODY (4-6 points) — Core content, data, examples, transitions
- CTA (final 30s) — Subscribe, next video tease

---

### Step 4: Human Approval ← GATE

**Input:** Complete script  
**Output:** Approved/rejected

- Pipeline **pauses** at this stage
- Status changes to `pending_approval`
- Human reviews via dashboard
- Click **Approve** to continue or **Reject** with feedback

---

### Step 5: Voiceover (ElevenLabs TTS)

**Input:** Approved script  
**Output:** MP3 file

- Use channel-specific voice ID (see Channel Profiles)
- Output: `[CHANNEL]_[DATE]_[TOPIC-SLUG].mp3`
- Fallback: F5-TTS (local) if ElevenLabs is unavailable

**Voice assignments per channel:**
| Channel | Voice Style | ElevenLabs Voice |
|---------|-------------|------------------|
| DFW | None (music only) | — |
| STM | Deep, measured male | "George" or "Daniel" |
| ODA | Slightly tense storytelling | "Adam" or "Josh" |
| PKP | Confident, knowledgeable | Custom |
| DKS | Low, measured, slightly ominous | "Liam" |
| GDB | Authoritative, measured | "Brian" or "Antoni" |
| ISL | Warm, calm, resonant | "Freya" or "Patrick" |
| NHZ | Wonder-driven | Custom |
| RMR | Conversational, practical | Custom |
| BWA | Tutorial-friendly | Custom |

---

### Step 6: Visual Generation (Stable Diffusion XL)

**Input:** Script sections + scene descriptions  
**Output:** 8-15 keyframe images per video

**Process:**
1. For each script section, construct image prompt:
   ```
   "[Channel visual style prompt] + [scene description]"
   ```
2. Generate via Stable Diffusion XL on RTX 3090
3. Upscale to 1920x1080 using built-in SD upscaler
4. For lofi channels: generate looping anime-style scene (Deforum SD)

**Channel visual styles:**
| Channel | Visual Style |
|---------|-------------|
| DFW | Anime cozy room loops (rain window, city night, spaceship) |
| STM | Muted earth tones, marble, classical art, nature |
| ODA | Dark cinematic, archival footage aesthetic |
| PKP | Clean clinical, data overlays, body/brain graphics |
| DKS | Dark moody, silhouettes, dramatic lighting |
| GDB | Maps, trade routes, satellite imagery, navy/gold |
| ISL | Warm golds, temple imagery, sacred geometry |
| NHZ | Dark space, neon accents, particle effects, 3D renders |
| RMR | Destination B-roll, cost comparison graphics |
| BWA | Screen-share, terminal, architecture diagrams |

---

### Step 7: Video Assembly (DaVinci Resolve)

**Input:** Voiceover MP3 + keyframe images  
**Output:** Assembled video

**Process:**
1. Import voiceover MP3
2. Drop keyframe images onto timeline (auto-duration from TTS length)
3. Apply Ken Burns motion to stills (built-in Resolve effect)
4. Add chapter markers based on script sections
5. Add lower-thirds text for key points
6. Add outro card (pre-made template per channel)
7. Export: 1920x1080 H.264, target 15-20 Mbps

---

### Step 8: Thumbnail (SD + Photopea)

**Input:** Video topic + channel style  
**Output:** Click-worthy thumbnail

**Process:**
1. Generate base image via Stable Diffusion XL
2. Add bold text overlay in Photopea (web-based, free)
3. Follow channel thumbnail template

**Thumbnail rules:**
- Face or emotional expression when possible
- 3-5 words max on thumbnail
- High contrast, readable at small size
- Consistent channel branding

---

### Step 9: Metadata & SEO (Agent + vidIQ)

**Input:** Video + research brief  
**Output:** Title, description, tags

**Process:**
1. Title: Generate 3 options → score with vidIQ → pick highest
2. Description: Generate with LLM → add timestamps + affiliate links
3. Tags: Query vidIQ related keywords → select top 15 by overall score
4. Upload generated thumbnail

---

### Step 10: Schedule & Publish

**Input:** Complete upload package  
**Output:** Published video

**Process:**
1. Upload to YouTube Studio
2. Schedule per channel cadence (see Channel Profiles)
3. Add to playlist, set end screen, add cards
4. Enable "Contains AI-generated content" disclosure

---

## Pipeline State Machine

```python
class PipelineStage(str, Enum):
    TOPIC = "topic"         # Step 1
    SCRIPT = "script"       # Steps 2-3
    APPROVAL = "approval"   # Step 4 (pause)
    VOICEOVER = "voiceover" # Step 5
    VISUALS = "visuals"     # Step 6
    UPSCALE = "upscale"     # Part of Step 6
    STITCH = "stitch"       # Step 7
    QC = "qc"              # Validation
    PUBLISH = "publish"     # Steps 8-10
    COMPLETED = "completed"
    FAILED = "failed"
```

---

## Performance Review (Weekly, Agent-Automated)

After each video is published:
1. Pull vidIQ analytics: views, CTR, retention by video
2. Flag any video with CTR <3% for thumbnail A/B test
3. Flag any video with retention <40% for script structure review
4. Identify top-performing topic pattern → brief 3 more similar videos

---

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/pipeline/create` | POST | Create new pipeline |
| `/api/pipeline/list` | GET | List all pipelines |
| `/api/pipeline/{id}` | GET | Get pipeline details |
| `/api/pipeline/{id}/run` | POST | Start pipeline execution |
| `/api/pipeline/{id}/approve` | POST | Approve/reject at approval gate |
| `/api/pipeline/{id}/run-stage/{stage}` | POST | Run specific stage |

---

## Progress Calculation

```python
active_stages = [s for s in STAGE_ORDER if s not in (FAILED, COMPLETED)]
idx = active_stages.index(current_stage)
stage_progress = stages[current_stage]["progress"]  # 0-100
progress_pct = int(((idx + stage_progress / 100) / len(active_stages)) * 100)
```
