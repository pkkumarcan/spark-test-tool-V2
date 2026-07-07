"""Weekly pipeline scheduler — enqueues jobs on a weekly cadence."""

import datetime
import logging

from apps.agent_runtime.pipeline import PipelineRunner, create_pipeline

logger = logging.getLogger("spark.pipeline.weekly")

WEEKLY_CHANNELS = [
    {"channel_id": "MLN", "topic": "macroeconomics global finance crypto trends"},
]


class WeeklyScheduler:
    def __init__(
        self,
        channels: list[dict] | None = None,
        ollama_url: str = "http://localhost:11434",
        f5_tts_url: str = "http://f5-tts:8000",
        whisper_url: str = "http://whisper:9000",
        comfyui_url: str = "http://localhost:8188",
        output_dir: str = "/app/output",
    ):
        self.channels = channels or WEEKLY_CHANNELS
        self.ollama_url = ollama_url
        self.f5_tts_url = f5_tts_url
        self.whisper_url = whisper_url
        self.comfyui_url = comfyui_url
        self.output_dir = output_dir
        self._running = False
        self._history: list[dict] = []

    async def enqueue_weekly_jobs(self) -> list[str]:
        pipeline_ids = []
        for ch in self.channels:
            state = create_pipeline(ch["channel_id"], ch["topic"])
            pipeline_ids.append(state.pipeline_id)
            logger.info(f"Enqueued weekly pipeline {state.pipeline_id} for {ch['channel_id']}")
        return pipeline_ids

    async def run_pipeline(self, pipeline_id: str):
        from apps.agent_runtime.pipeline import get_pipeline
        state = get_pipeline(pipeline_id)
        if state is None:
            logger.error(f"Pipeline {pipeline_id} not found")
            return

        runner = PipelineRunner(
            state,
            ollama_url=self.ollama_url,
            f5_tts_url=self.f5_tts_url,
            whisper_url=self.whisper_url,
            comfyui_url=self.comfyui_url,
            output_dir=self.output_dir,
        )

        try:
            await runner.run_full()
            self._history.append({
                "pipeline_id": pipeline_id,
                "status": "completed",
                "completed_at": datetime.datetime.now(datetime.UTC).isoformat(),
            })
            logger.info(f"Pipeline {pipeline_id} completed successfully")
        except Exception as e:
            self._history.append({
                "pipeline_id": pipeline_id,
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.datetime.now(datetime.UTC).isoformat(),
            })
            logger.error(f"Pipeline {pipeline_id} failed: {e}")

    async def run_all_weekly(self):
        ids = await self.enqueue_weekly_jobs()
        for pid in ids:
            await self.run_pipeline(pid)

    def get_history(self) -> list[dict]:
        return list(self._history)


_weekly_scheduler: WeeklyScheduler | None = None


def get_weekly_scheduler() -> WeeklyScheduler:
    global _weekly_scheduler
    if _weekly_scheduler is None:
        _weekly_scheduler = WeeklyScheduler()
    return _weekly_scheduler
