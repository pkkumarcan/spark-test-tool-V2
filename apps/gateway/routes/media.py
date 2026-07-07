"""Media routes — image/video/audio/3d/music/tts/stt/meme/postprocess/extraction endpoints."""


from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from apps.gateway.jobs import cancel_job, create_job, get_job, list_jobs

router = APIRouter(prefix="/api", tags=["media"])


class ImageGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str = "blurry, low quality, distorted"
    steps: int = 8
    width: int = 1024
    height: int = 1024
    model: str = "flux1-schnell-q8.gguf"
    seed: int | None = None


class VideoGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str = "blurry, low quality, distorted"
    steps: int = 20
    width: int = 480
    height: int = 320
    frames: int = 49
    model: str = "wan2.2_14b_q4.gguf"
    seed: int | None = None
    cfg: float | None = None
    mode: str = "t2v"
    start_image: str = ""
    end_image: str = ""
    vae_tiling: bool = False


class MusicGenerateRequest(BaseModel):
    prompt: str
    lyrics: str = ""
    model: str = "ace-step-1.5-base"
    steps: int = 27


class TTSRequest(BaseModel):
    text: str
    voice: str = "default"
    speed: float = 1.0


class STTRequest(BaseModel):
    audio_path: str
    language: str = "en"


class MemeRequest(BaseModel):
    prompt: str
    image_model: str = "flux1-schnell-q8.gguf"


class UpscaleRequest(BaseModel):
    image_url: str
    scale: int = 4


class LipsyncRequest(BaseModel):
    video_url: str
    audio_url: str


class OCRRRequest(BaseModel):
    image_data: str


class LinkExtractRequest(BaseModel):
    url: str


class YouTubeExtractRequest(BaseModel):
    url: str


class JobResponse(BaseModel):
    job_id: str
    status: str
    kind: str


@router.post("/image/generate", response_model=JobResponse)
async def generate_image_endpoint(req: ImageGenerateRequest):
    job_id = await create_job(kind="image", payload=req.model_dump())
    return JobResponse(job_id=job_id, status="pending", kind="image")


@router.post("/video/generate", response_model=JobResponse)
async def generate_video_endpoint(req: VideoGenerateRequest):
    job_id = await create_job(kind="video", payload=req.model_dump())
    return JobResponse(job_id=job_id, status="pending", kind="video")


@router.post("/music/generate", response_model=JobResponse)
async def generate_music_endpoint(req: MusicGenerateRequest):
    job_id = await create_job(kind="music", payload=req.model_dump())
    return JobResponse(job_id=job_id, status="pending", kind="music")


@router.post("/tts/synthesize", response_model=JobResponse)
async def synthesize_tts_endpoint(req: TTSRequest):
    job_id = await create_job(kind="tts", payload=req.model_dump())
    return JobResponse(job_id=job_id, status="pending", kind="tts")


@router.post("/stt/transcribe", response_model=JobResponse)
async def transcribe_stt_endpoint(req: STTRequest):
    job_id = await create_job(kind="stt", payload=req.model_dump())
    return JobResponse(job_id=job_id, status="pending", kind="stt")


@router.post("/meme/generate", response_model=JobResponse)
async def generate_meme_endpoint(req: MemeRequest):
    job_id = await create_job(kind="meme", payload=req.model_dump())
    return JobResponse(job_id=job_id, status="pending", kind="meme")


@router.post("/postprocess/upscale", response_model=JobResponse)
async def upscale_endpoint(req: UpscaleRequest):
    job_id = await create_job(kind="postprocess", payload={"action": "upscale", **req.model_dump()})
    return JobResponse(job_id=job_id, status="pending", kind="postprocess")


@router.post("/postprocess/lipsync", response_model=JobResponse)
async def lipsync_endpoint(req: LipsyncRequest):
    job_id = await create_job(kind="postprocess", payload={"action": "lipsync", **req.model_dump()})
    return JobResponse(job_id=job_id, status="pending", kind="postprocess")


@router.post("/extract/ocr", response_model=JobResponse)
async def ocr_endpoint(req: OCRRRequest):
    job_id = await create_job(kind="extraction", payload={"action": "ocr", **req.model_dump()})
    return JobResponse(job_id=job_id, status="pending", kind="extraction")


@router.post("/extract/pdf")
async def extract_pdf_endpoint(
    file: UploadFile = File(...),
    ocr_all: bool = Form(False),
):
    job_id = await create_job(
        kind="extraction",
        payload={"action": "pdf", "filename": file.filename, "ocr_all": ocr_all},
    )
    return JobResponse(job_id=job_id, status="pending", kind="extraction")


@router.post("/extract/link", response_model=JobResponse)
async def extract_link_endpoint(req: LinkExtractRequest):
    job_id = await create_job(kind="extraction", payload={"action": "link", **req.model_dump()})
    return JobResponse(job_id=job_id, status="pending", kind="extraction")


@router.post("/extract/youtube", response_model=JobResponse)
async def extract_youtube_endpoint(req: YouTubeExtractRequest):
    job_id = await create_job(kind="extraction", payload={"action": "youtube", **req.model_dump()})
    return JobResponse(job_id=job_id, status="pending", kind="extraction")


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = await get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/jobs")
async def list_recent_jobs(
    status: str | None = None,
    kind: str | None = None,
    limit: int = 50,
):
    return await list_jobs(status=status, kind=kind, limit=limit)


@router.post("/jobs/{job_id}/cancel")
async def cancel_existing_job(job_id: str):
    cancelled = await cancel_job(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=400,
            detail="Job not found or cannot be cancelled",
        )
    return {"job_id": job_id, "status": "cancelled"}


# ── V1-compatible routes ──────────────────────────────────────────────────────

@router.post("/video/test-frame")
async def video_test_frame(req: VideoGenerateRequest):
    """Synchronous test frame generation (V1 compat)."""
    job_id = await create_job(kind="video_test", payload=req.model_dump())
    return JobResponse(job_id=job_id, status="pending", kind="video_test")


class ThreeDGenerateRequest(BaseModel):
    prompt: str
    model: str = "triposr"
    steps: int = 20


@router.post("/3d/generate")
async def generate_3d_endpoint(req: ThreeDGenerateRequest):
    job_id = await create_job(kind="3d", payload=req.model_dump())
    return JobResponse(job_id=job_id, status="pending", kind="3d")


class AudioTranscribeRequest(BaseModel):
    audio_path: str
    language: str = "en"


@router.post("/audio/transcribe")
async def audio_transcribe_endpoint(req: AudioTranscribeRequest):
    job_id = await create_job(kind="stt", payload=req.model_dump())
    return JobResponse(job_id=job_id, status="pending", kind="stt")


class AudioSpeakRequest(BaseModel):
    text: str
    voice: str = "default"
    speed: float = 1.0


@router.post("/audio/speak")
async def audio_speak_endpoint(req: AudioSpeakRequest):
    job_id = await create_job(kind="tts", payload=req.model_dump())
    return JobResponse(job_id=job_id, status="pending", kind="tts")
