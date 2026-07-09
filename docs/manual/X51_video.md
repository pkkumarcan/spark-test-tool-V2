# X51 — Video Generation

**Purpose:** Video assembly via DaVinci Resolve with Ken Burns, chapter markers, and export settings.  
**Updated:** 2026-07-09 (V3 — DaVinci Resolve workflow per vidIQ)  
**Estimated time:** 15 minutes

---

## Overview

Video assembly combines voiceover + keyframes into a finished video using DaVinci Resolve (free version).

---

## Assembly Flow

```
Voiceover MP3 + Keyframe PNGs → DaVinci Resolve Template → Ken Burns Motion
→ Chapter Markers → Lower-Thirds Text → Outro Card → Export 1080p H.264
```

---

## Step-by-Step Assembly

### 1. Import Assets
- Import voiceover MP3(s)
- Import keyframe PNGs
- Import outro card template

### 2. Build Timeline
- Place voiceover on audio track
- Drop keyframe images onto video track
- Auto-duration: each image lasts until next image starts (based on TTS timing)

### 3. Apply Ken Burns Effect
DaVinci Resolve built-in effect:
- Select clip → Inspector → Zoom/Position keyframes
- Start: 100% zoom, centered
- End: 110% zoom, slightly offset
- Creates subtle motion on still images

### 4. Add Chapter Markers
Based on script sections:
- HOOK (0-30s)
- INTRO (30-60s)
- BODY (60s-4min)
- CTA (final 30s)

### 5. Add Lower-Thirds Text
Key points from script displayed as text overlays:
- Position: Lower third of frame
- Duration: 3-5 seconds
- Font: Clean sans-serif (Inter, Roboto)
- Color: White with dark shadow

### 6. Add Outro Card
Pre-made template per channel:
- Subscribe button animation
- Next video thumbnail placeholder
- Channel logo

### 7. Export Settings
```
Format: MP4
Codec: H.264
Resolution: 1920x1080
Frame Rate: 30fps
Bitrate: 15-20 Mbps
Audio: AAC 320kbps
```

---

## FFmpeg Alternative (Automated)

For fully automated pipeline (no DaVinci):

### Merge Audio + Images
```bash
# Create video from image with duration matching audio
ffmpeg -y -loop 1 -i keyframe.png -i voiceover.mp3 \
  -c:v libx264 -tune stillimage -c:a aac -b:a 192k \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
  -pix_fmt yuv420p -shortest output.mp4
```

### Concatenate Segments
```bash
# Create file list
echo "file 'seg1.mp4'" > list.txt
echo "file 'seg2.mp4'" >> list.txt
echo "file 'seg3.mp4'" >> list.txt

# Concatenate
ffmpeg -y -f concat -safe 0 -i list.txt -c copy final.mp4
```

### Add Ken Burns (Zoom Pan)
```bash
# Slow zoom in over 15 seconds
ffmpeg -y -loop 1 -i image.png -t 15 \
  -vf "zoompan=z='min(zoom+0.001,1.1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=450:s=1920x1080" \
  -c:v libx264 -pix_fmt yuv420p output.mp4
```

### Add Subtitles
```bash
ffmpeg -y -i video.mp4 -vf "subtitles=subs.srt:force_style='FontSize=24,PrimaryColour=&HFFFFFF'" \
  -c:v copy output.mp4
```

---

## Output Structure

```
output/jobs/pipe_abc12345/
├── audio/
│   └── voice/
│       ├── S01.mp3
│       ├── S02.mp3
│       └── ...
├── visuals/
│   ├── keyframes/
│   │   ├── keyframe_00001_.png
│   │   └── ...
│   └── upscaled/
│       └── ...
├── final/
│   ├── video_final.mp4          # Main output
│   ├── video_final.srt          # Subtitles (if generated)
│   └── segments/                # Individual segments
│       ├── seg_hook.mp4
│       ├── seg_intro.mp4
│       └── ...
└── metadata/
    ├── channel.json
    ├── brief.json
    └── script.json
```

---

## Video Specs by Channel

| Channel | Duration | Resolution | FPS | Notes |
|---------|----------|------------|-----|-------|
| DFW | 1-4 hours | 1920x1080 | 30 | Looping visual + music |
| STM | 5-10 min | 1920x1080 | 30 | Ken Burns on stills |
| ODA | 8-15 min | 1920x1080 | 30 | Dramatic reveals |
| PKP | 5-10 min | 1920x1080 | 30 | Data overlays |
| DKS | 5-10 min | 1920x1080 | 30 | Dark, moody |
| GDB | 5-10 min | 1920x1080 | 30 | Maps, infographics |
| ISL | 5-10 min | 1920x1080 | 30 | Nature, temples |
| NHZ | 5-10 min | 1920x1080 | 30 | Sci-fi visuals |
| RMR | 5-10 min | 1920x1080 | 30 | Destination footage |
| BWA | 5-15 min | 1920x1080 | 30 | Screen recordings |

---

## Quality Checks

Before export:
- [ ] Audio syncs with visuals (offset < 80ms)
- [ ] All keyframes present and correct
- [ ] No black frames between segments
- [ ] Outro card displays correctly
- [ ] Total duration matches script timing
- [ ] Export at 15-20 Mbps (not too compressed)

---

## Fallback

If DaVinci Resolve is unavailable, use FFmpeg automated assembly:
1. Generate silent video from each keyframe (duration = section length)
2. Concatenate all segments
3. Merge with voiceover audio
4. Export final MP4

This produces a functional but less polished video.
