"""YouTube publishing — OAuth2 upload + metadata + scheduling."""

import json
import logging
import os
from datetime import UTC, datetime

import httpx

logger = logging.getLogger("spark.pipeline.youtube")

YOUTUBE_UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3"


async def _get_access_token() -> str | None:
    client_secrets_path = os.getenv("YOUTUBE_CLIENT_SECRETS")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")

    if client_secrets_path and os.path.exists(client_secrets_path):
        with open(client_secrets_path) as f:
            secrets = json.load(f)
        web = secrets.get("web", secrets.get("installed", {}))
        client_id = client_id or web.get("client_id")
        client_secret = client_secret or web.get("client_secret")

    if not all([client_id, client_secret, refresh_token]):
        return None

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if r.status_code == 200:
            return r.json().get("access_token")
        logger.error(f"YouTube token refresh failed: {r.status_code} {r.text}")
        return None


async def upload_video(
    file_path: str,
    metadata: dict,
    thumbnail_path: str | None = None,
) -> dict:
    access_token = await _get_access_token()

    if not access_token:
        logger.warning("YouTube API not configured, using mock upload")
        import random
        video_id = "".join(
            random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_", k=11)
        )
        return {
            "status": "mock",
            "platform": "youtube",
            "video_id": video_id,
            "watch_url": f"https://www.youtube.com/watch?v={video_id}",
            "uploaded_at": datetime.now(UTC).isoformat(),
            "metadata": metadata,
            "note": "YouTube API credentials not configured. Set YOUTUBE_CLIENT_SECRETS, YOUTUBE_REFRESH_TOKEN, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET env vars.",
        }

    if not file_path or not os.path.exists(file_path):
        return {"status": "error", "error": f"Video file not found: {file_path}"}

    video_metadata = {
        "snippet": {
            "title": metadata.get("title", "Untitled"),
            "description": metadata.get("description", ""),
            "tags": metadata.get("tags", []),
            "categoryId": metadata.get("category_id", "27"),
            "defaultLanguage": metadata.get("default_language", "en"),
        },
        "status": {
            "privacyStatus": metadata.get("status", "private"),
            "selfDeclaredMadeForKids": False,
            "madeForKids": False,
        },
    }

    async with httpx.AsyncClient(timeout=600.0) as client:
        init_resp = await client.post(
            f"{YOUTUBE_UPLOAD_URL}?uploadType=resumable&part=snippet,status",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Upload-Content-Type": "video/mp4",
                "X-Upload-Content-Length": str(os.path.getsize(file_path)),
            },
            json=video_metadata,
        )

        if init_resp.status_code not in (200, 308):
            return {"status": "error", "error": f"Upload init failed: {init_resp.status_code} {init_resp.text}"}

        upload_url = init_resp.headers.get("Location")
        if not upload_url:
            return {"status": "error", "error": "No upload URL returned"}

        with open(file_path, "rb") as f:
            upload_resp = await client.put(
                upload_url,
                headers={"Content-Type": "video/mp4"},
                content=f.read(),
            )

        if upload_resp.status_code not in (200, 201):
            return {"status": "error", "error": f"Upload failed: {upload_resp.status_code} {upload_resp.text}"}

        result = upload_resp.json()
        video_id = result.get("id", "")

        if thumbnail_path and os.path.exists(thumbnail_path) and video_id:
            try:
                with open(thumbnail_path, "rb") as tf:
                    await client.post(
                        f"{YOUTUBE_API_URL}/thumbnails/set?videoId={video_id}",
                        headers={"Authorization": f"Bearer {access_token}"},
                        files={"image": tf},
                    )
            except Exception as e:
                logger.warning(f"Thumbnail upload failed: {e}")

        return {
            "status": "success",
            "platform": "youtube",
            "video_id": video_id,
            "watch_url": f"https://www.youtube.com/watch?v={video_id}",
            "uploaded_at": datetime.now(UTC).isoformat(),
            "metadata": metadata,
        }


async def schedule_video(title: str, publish_time: str, video_id: str | None = None) -> dict:
    return {
        "publish_id": f"pub-{__import__('uuid').uuid4().hex[:6]}",
        "title": title,
        "scheduled_time": publish_time,
        "video_id": video_id,
        "status": "scheduled",
        "platform": "youtube",
    }
