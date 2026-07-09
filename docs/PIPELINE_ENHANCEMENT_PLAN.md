# Pipeline Enhancement Plan — Full Content Generation

**Status:** Ready for implementation  
**Created:** 2026-07-09  
**Session:** New session recommended (full context needed)

---

## Current State (Broken)

The pipeline exists but uses mock/fallback data:
- Pipeline stages are stubs (Ollama fallback generates mock briefs/scripts)
- No vidIQ integration for topic research
- No ElevenLabs TTS integration
- No real video assembly (FFmpeg placeholder only)
- No YouTube publishing integration
- Channel dropdown still shows MLN (merged into GDB in V3)
- Pipeline state is in-memory only (lost on gateway restart)
- UI shows "No pipelines found" because in-memory dict resets

---

## V3 Channel Roster (10 Channels)

| Code | Name | Niche | Phase |
|------|------|-------|-------|
| DFW | Drift Wave | Lofi Music | 1 |
| STM | Still Mind | Stoicism | 1 |
| ODA | Odd Archive | Mystery/History | 2 |
| PKP | Peak Protocol | Biohacking | 2 |
| DKS | Dark Signal | Dark Psychology | 3 (rebranded from cybersecurity) |
| GDB | Ground Brief | Geopolitics+Macro | 3 (absorbed MLN) |
| ISL | Inner Scroll | Vedic/Spiritual | 4 |
| NHZ | Next Horizon | Future Tech | 4 |
| RMR | Roam Rich | Digital Nomad | 5 |
| BWA | Build With AI | AI Tutorials | 5 |

**MLN removed** (merged into GDB — only 3,577 monthly searches)  
**CCL removed** (legal commentary hard to automate credibly)

---

## Pipeline Stages (10 Steps)

```
STEP 1: Topic Selection (vidIQ + Agent)
STEP 2: Research Brief (LLM)
STEP 3: Script Generation (LLM)
STEP 4: Human Approval ← GATE
STEP 5: Voiceover (ElevenLabs TTS)
STEP 6: Visual Generation (ComfyUI / SD XL)
STEP 7: Video Assembly (FFmpeg)
STEP 8: Thumbnail (SD XL + text overlay)
STEP 9: Metadata & SEO (LLM + vidIQ scoring)
STEP 10: Schedule & Publish (YouTube API)
```

---

## Implementation Phases

### Phase 1: Fix Channel Roster + Backend Persistence

**Files to modify:**
- `apps/web/app/pipeline/page.tsx` — Update dropdown to 10 channels
- `apps/agent-runtime/pipeline.py` — Persist state to PostgreSQL
- `apps/gateway/routes/pipeline.py` — DB-backed CRUD

**Changes:**
1. Replace in-memory `_pipelines` dict with PostgreSQL storage
2. Add `pipelines` table to database schema
3. Update channel dropdown to show 10 V3 channels
4. Fix `to_dict()` to return UI-compatible fields

**Verification:**
- Create pipeline via UI → persists after gateway restart
- Channel dropdown shows DFW, STM, ODA, PKP, DKS, GDB, ISL, NHZ, RMR, BWA

---

### Phase 2: Real Topic Research (Step 1)

**New file:** `apps/agent-runtime/research.py`

**Changes:**
1. Implement vidIQ API client (or use LLM to simulate research)
2. Query channel research documents from RAG
3. Implement "3-Source Braid" validation:
   - Search signal: keyword volume >10K
   - Community signal: Reddit 200+ upvotes
   - Gap signal: <20 YouTube videos on topic
4. Generate topic brief JSON with title variants, hook ideas

**Research prompt template:**
```
CHANNEL: [CHANNEL NAME]
NICHE: [CHANNEL NICHE]
TASK: Research trending topics for this channel.
1. What are people searching for in this niche?
2. What's trending on Reddit?
3. What topics have low YouTube competition?
Output: Top 3 topic candidates with keyword, angle, hook.
```

**Verification:**
- Pipeline Step 1 produces a real research brief (not mock)
- Brief contains channel-specific niche content

---

### Phase 3: Real Script Generation (Steps 2-3)

**File:** `apps/agent-runtime/pipeline.py` — `_stage_topic()` and `_stage_script()`

**Changes:**
1. Replace mock Ollama calls with proper prompts
2. Per-channel tone and style in system prompts
3. Structured output: HOOK, INTRO, BODY, CTA with timing
4. Validate JSON response, retry on parse failure

**Script prompt template:**
```
You are a YouTube scriptwriter for "[CHANNEL NAME]".
Niche: [CHANNEL NICHE]
Tone: [CHANNEL TONE]

Write a [DURATION]-minute narrator-led script on: [TOPIC]

Structure:
- HOOK (0-30s): Open loop, personal stakes, curiosity gap
- INTRO (30-60s): Channel branding, topic context
- BODY (4-6 points): Core content with transitions
- CTA (final 30s): Subscribe, next video tease

Output JSON with sections array, each containing:
section_id, label, narration, target_duration_seconds
```

**Channel tones:**
| Channel | Tone |
|---------|------|
| DFW | None (music only) |
| STM | Calm, measured, quotable |
| ODA | Suspenseful, "I couldn't sleep after this" |
| PKP | Protocol-driven, research-backed |
| DKS | "Exposé" style, calm but urgent |
| GDB | Briefing style, authoritative |
| ISL | Reverent but accessible |
| NHZ | Wonder-driven, "imagine this" |
| RMR | Conversational, practical |
| BWA | Tutorial-friendly, "let's build" |

**Verification:**
- Pipeline Steps 2-3 produce real scripts with proper structure
- Scripts match channel tone

---

### Phase 4: Real Voiceover (Step 5)

**New file:** `apps/agent-runtime/tts_elevenlabs.py`

**Changes:**
1. Integrate ElevenLabs API (primary, $5/mo)
2. Channel-specific voice assignments
3. Fallback to F5-TTS (local) if ElevenLabs fails
4. Fallback to silence (FFmpeg) if both fail

**Voice assignments:**
| Channel | ElevenLabs Voice |
|---------|------------------|
| DFW | — (no voice) |
| STM | "George" or "Daniel" |
| ODA | "Adam" or "Josh" |
| PKP | Custom clone |
| DKS | "Liam" |
| GDB | "Brian" or "Antoni" |
| ISL | "Freya" or "Patrick" |
| NHZ | Custom clone |
| RMR | Custom clone |
| BWA | Custom clone |

**ElevenLabs API call:**
```python
async def elevenlabs_tts(text, voice_id, api_key):
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key},
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
            }
        )
        return resp.content
```

**Env var needed:** `ELEVENLABS_API_KEY`

**Verification:**
- Pipeline Step 5 produces real voiceover audio
- Audio matches channel voice assignment
- Fallback works when ElevenLabs is unavailable

---

### Phase 5: Real Visual Generation (Step 6)

**File:** `apps/agent-runtime/pipeline.py` — `_stage_visuals()`

**Changes:**
1. Use existing ComfyUI integration (already works)
2. Per-channel visual style prompts
3. Generate 8-15 keyframes per video
4. Proper prompt construction from script sections

**Visual style prompts:**
| Channel | Style |
|---------|-------|
| DFW | "Anime cozy room, rain window, warm lighting, lofi aesthetic" |
| STM | "Ancient Roman philosopher, marble columns, golden hour, muted earth tones" |
| ODA | "Dark cinematic, archival footage aesthetic, dramatic shadows" |
| PKP | "Clean clinical, data overlays, body/brain graphics" |
| DKS | "Dark moody, silhouettes, dramatic lighting" |
| GDB | "Maps, trade routes, satellite imagery, navy/gold" |
| ISL | "Warm golds, temple imagery, sacred geometry" |
| NHZ | "Dark space, neon accents, particle effects, 3D renders" |
| RMR | "Destination landscape, cost comparison graphics" |
| BWA | "Screen-share, terminal, architecture diagrams" |

**Verification:**
- Pipeline Step 6 generates real keyframes via ComfyUI
- Images match channel visual style

---

### Phase 6: Real Video Assembly (Step 7)

**File:** `apps/agent-runtime/pipeline.py` — `_stage_stitch()`

**Changes:**
1. Replace placeholder FFmpeg with real assembly
2. Merge voiceover MP3 + keyframe PNGs
3. Apply Ken Burns (zoom pan) effect on stills
4. Add chapter markers from script sections
5. Export 1920x1080 H.264 at 15-20 Mbps

**FFmpeg assembly:**
```bash
# For each section: image + audio → segment
ffmpeg -y -loop 1 -i keyframe.png -i voiceover.mp3 \
  -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
  -vf "zoompan=z='min(zoom+0.001,1.1)':d=450:s=1920x1080" \
  -pix_fmt yuv420p -shortest segment.mp4

# Concatenate all segments
ffmpeg -y -f concat -safe 0 -i list.txt -c copy final.mp4
```

**Verification:**
- Pipeline Step 7 produces a real video file
- Video has audio + visuals synced
- Resolution is 1920x1080

---

### Phase 7: Thumbnail + Metadata (Steps 8-9)

**New file:** `apps/agent-runtime/thumbnail.py`

**Changes:**
1. Generate thumbnail via SD XL (1280x720)
2. Add bold text overlay (3-5 words)
3. Generate title (3 options, score with LLM)
4. Generate description with timestamps + affiliate links
5. Generate tags (top 15 keywords)

**Verification:**
- Pipeline Step 8 produces thumbnail PNG
- Pipeline Step 9 produces metadata JSON

---

### Phase 8: Publishing (Step 10)

**New file:** `apps/agent-runtime/youtube_publish.py`

**Changes:**
1. YouTube API integration (OAuth2)
2. Upload video with metadata
3. Set thumbnail
4. Add to playlist
5. Enable AI content disclosure
6. Schedule publish time

**Verification:**
- Pipeline Step 10 uploads to YouTube
- Video appears in channel with correct metadata

---

## Environment Variables Needed

```bash
# ElevenLabs (Phase 4)
ELEVENLABS_API_KEY=your-key

# vidIQ (Phase 2) — or use LLM simulation
VIDIQ_API_KEY=your-key

# YouTube API (Phase 8)
YOUTUBE_CLIENT_SECRETS=path/to/client_secrets.json
```

---

## Testing Strategy

### Unit Tests
- Each stage produces valid output
- Fallback mechanisms work
- Error handling works

### Integration Tests
- Full pipeline runs end-to-end
- Output files exist and are valid
- Pipeline state persists to database

### Manual Verification
1. Launch pipeline via UI for DFW (simplest — music only)
2. Verify each stage completes
3. Check output files in `/output/jobs/`
4. Launch for STM (voiceover + visuals)
5. Verify full video is generated

---

## Success Criteria

- [ ] Pipeline launches from UI with real channel/topic
- [ ] Step 1: Real research brief (not mock)
- [ ] Steps 2-3: Real script (not mock)
- [ ] Step 5: Real voiceover audio
- [ ] Step 6: Real keyframe images
- [ ] Step 7: Real assembled video (MP4)
- [ ] Step 8: Real thumbnail
- [ ] Pipeline state persists across restarts
- [ ] All 10 channels in dropdown
- [ ] Channel-specific styles applied
