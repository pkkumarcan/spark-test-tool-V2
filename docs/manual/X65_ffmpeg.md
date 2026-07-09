# X65 — FFmpeg Cookbook

**Purpose:** Common FFmpeg commands used in Spark V2.  
**Estimated time:** 10 minutes

---

## Installation

FFmpeg is installed in the gateway and media-workers containers:
```dockerfile
RUN apt-get update && apt-get install -y ffmpeg
```

---

## Audio Operations

### Generate Silent Audio
```bash
ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=mono -t 15 output.wav
```

### Concatenate WAV Files
```bash
ffmpeg -y -i "concat:S01.wav|S02.wav|S03.wav" -c copy combined.wav
```

### Convert WAV to MP3
```bash
ffmpeg -y -i input.wav -codec:a libmp3lame -qscale:a 2 output.mp3
```

### Get Audio Duration
```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.wav
```

---

## Video Operations

### Image to Video (15 seconds)
```bash
ffmpeg -y -loop 1 -i image.png -t 15 -c:v libx264 -pix_fmt yuv420p output.mp4
```

### Generate Solid Color Video
```bash
ffmpeg -y -f lavfi -i "color=c=#1a1a2e:s=1920x1080:d=60" -c:v libx264 -pix_fmt yuv420p output.mp4
```

### Merge Audio + Video
```bash
ffmpeg -y -i video.mp4 -i audio.wav -c:v copy -c:a aac -shortest final.mp4
```

### Add Subtitles
```bash
ffmpeg -y -i video.mp4 -vf "subtitles=subs.srt:force_style='FontSize=24'" -c:v copy output.mp4
```

### Extract Audio from Video
```bash
ffmpeg -y -i video.mp4 -vn -acodec pcm_s16le -ar 44100 -ac 1 audio.wav
```

### Resize Video
```bash
ffmpeg -y -i input.mp4 -vf "scale=1920:1080" -c:v libx264 output.mp4
```

### Trim Video
```bash
ffmpeg -y -i input.mp4 -ss 00:00:10 -to 00:00:30 -c copy output.mp4
```

---

## Image Operations

### Create Placeholder Image
```bash
ffmpeg -y -f lavfi -i "color=c=#1a1a2e:s=1024x576:d=1" -vframes 1 output.png
```

### Resize Image
```bash
ffmpeg -y -i input.png -vf "scale=1920:1080" output.png
```

---

## Quality Checks

### Validate Video File
```bash
ffprobe -v error -show_format -show_streams video.mp4
```

### Check Video Duration
```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 video.mp4
```

### Check for Audio Stream
```bash
ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 video.mp4
```
