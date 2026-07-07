"""Content extraction — PDF, OCR, link, YouTube."""

import asyncio
import logging
import os
import re
from html.parser import HTMLParser

import httpx

logger = logging.getLogger("spark.media.extraction")

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/output")


def clean_extracted_text(
    text: str,
    clean_spacing: bool = False,
    fix_broken_sentences: bool = False,
    preserve_paragraphs: bool = False,
) -> str:
    if not text:
        return ""
    if fix_broken_sentences:
        text = re.sub(r"(?<![.!?])\n", " ", text)
    if preserve_paragraphs:
        text = re.sub(r"\n{2,}", "\n\n", text)
    if clean_spacing:
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r" \n", "\n", text)
        text = re.sub(r"\n ", "\n", text)
    return text.strip()


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result: list[str] = []
        self.tag_stack: list[str] = []
        self.ignore_tags = {
            "script", "style", "head", "title", "meta", "link",
            "svg", "path", "nav", "footer", "aside", "header",
        }
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        if tag == "title":
            self.in_title = True
        if tag in {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"}:
            self.result.append("\n")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        while self.tag_stack and self.tag_stack[-1] != tag:
            self.tag_stack.pop()
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()
        if tag in {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"}:
            self.result.append("\n")

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        elif not any(t in self.ignore_tags for t in self.tag_stack):
            cleaned = re.sub(r"\s+", " ", data.strip())
            if cleaned:
                self.result.append(cleaned + " ")

    def get_text(self):
        raw_text = "".join(self.result)
        cleaned_text = re.sub(r"\n\s*\n+", "\n\n", raw_text).strip()
        title_prefix = f"# Webpage: {self.title.strip()}\n\n" if self.title.strip() else ""
        return title_prefix + cleaned_text


async def ocr_image(
    job_id: str,
    payload: dict,
    output_dir: str,
    ollama_url: str = "http://localhost:11434",
) -> dict:
    image_data = payload.get("image_data", "")
    if not image_data:
        raise ValueError("Image data (base64 or URL) is required")

    base64_str = image_data.split(",", 1)[1] if "," in image_data else image_data

    payload_ollama = {
        "model": "qwen2.5-vl:7b-instruct-q4_k_m",
        "messages": [
            {
                "role": "user",
                "content": "Extract all text from this image exactly as it appears. Preserve layout. Output markdown.",
                "images": [base64_str],
            }
        ],
        "stream": False,
    }

    text = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=payload_ollama)
            if r.status_code == 200:
                text = r.json().get("message", {}).get("content", "").strip()
            else:
                text = f"OCR Mock Fallback: Ollama returned {r.status_code}"
    except Exception as e:
        logger.warning(f"Ollama OCR error: {e}")
        text = f"OCR Mock Fallback: {e}"

    filename = f"{job_id}.txt"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

    return {
        "output_files": [filepath],
        "output_url": f"/output/{filename}",
        "text": text,
    }


async def extract_pdf(
    job_id: str,
    file_content: bytes,
    filename: str,
    output_dir: str,
) -> dict:
    try:
        import fitz
        doc = fitz.open(stream=file_content, filetype="pdf")
        extracted = [f"# PDF Extraction: {filename}\n"]
        for idx, page in enumerate(doc):
            page_text = page.get_text()
            if page_text:
                extracted.append(f"## Page {idx + 1}\n{page_text}\n")
        text = "\n".join(extracted)
    except ImportError:
        text = f"# PDF Extraction: {filename}\n\nPyMuPDF (fitz) not installed."
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        text = f"# PDF Extraction: {filename}\n\nError: {e}"

    out_filename = f"{job_id}.txt"
    filepath = os.path.join(output_dir, out_filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(text)

    return {
        "output_files": [filepath],
        "output_url": f"/output/{out_filename}",
        "text": text,
    }


async def extract_link(
    job_id: str,
    url: str,
    output_dir: str,
) -> dict:
    if not url.startswith(("http://", "https://")):
        raise ValueError("Invalid URL format")

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            r = await client.get(url, headers=headers)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}")

            html_content = r.text

        parser = HTMLTextExtractor()
        parser.feed(html_content)
        raw_text = parser.get_text()
        title = parser.title.strip() or url

        if not raw_text.strip() or len(raw_text.strip()) <= len(title) + 20:
            raw_text = f"# Webpage: {title}\n\nNo significant text content extracted."

        text = clean_extracted_text(raw_text)

        out_filename = f"{job_id}.txt"
        filepath = os.path.join(output_dir, out_filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)

        return {
            "output_files": [filepath],
            "output_url": f"/output/{out_filename}",
            "text": text,
            "title": title,
        }
    except Exception as e:
        logger.error(f"Link extraction error: {e}")
        raise


async def extract_youtube(
    job_id: str,
    youtube_url: str,
    output_dir: str,
) -> dict:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        vid_match = re.search(
            r"(?:v=|youtu\.be/|/shorts/|/embed/|/v/)([A-Za-z0-9_\-]{11})",
            youtube_url,
        )
        if not vid_match:
            raise ValueError("Could not extract valid YouTube video ID")
        video_id = vid_match.group(1)

        transcript_list = await asyncio.to_thread(
            YouTubeTranscriptApi.get_transcript, video_id,
        )

        lines = []
        for entry in transcript_list:
            start_sec = int(entry.get("start", 0))
            minutes = start_sec // 60
            seconds = start_sec % 60
            text_line = entry.get("text", "").strip().replace("\n", " ")
            lines.append(f"[{minutes:02d}:{seconds:02d}] {text_line}")

        full_text = f"# YouTube Transcript\nURL: {youtube_url}\nVideo ID: {video_id}\n\n" + "\n".join(lines)

        out_filename = f"{job_id}.txt"
        filepath = os.path.join(output_dir, out_filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_text)

        return {
            "output_files": [filepath],
            "output_url": f"/output/{out_filename}",
            "text": full_text,
        }
    except ImportError:
        raise RuntimeError("youtube-transcript-api not installed")
    except Exception as e:
        logger.error(f"YouTube extraction error: {e}")
        raise
