"""Release scheduler — manages scheduled publishing jobs."""

import asyncio
import datetime
import logging

logger = logging.getLogger("spark.media.scheduler")


class ReleaseScheduler:
    """Manages a queue of scheduled video releases."""

    def __init__(self):
        self._queue: list[dict] = []
        self._running = False

    async def add(self, job: dict) -> dict:
        entry = {
            "id": job.get("publish_id", f"sched_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "title": job.get("title", ""),
            "publish_at": job.get("scheduled_time", ""),
            "payload": job,
            "status": "scheduled",
            "created_at": datetime.datetime.now().isoformat(),
        }
        self._queue.append(entry)
        logger.info(f"Scheduled release: {entry['id']} at {entry['publish_at']}")
        return entry

    async def list_pending(self) -> list[dict]:
        return [j for j in self._queue if j["status"] == "scheduled"]

    async def list_all(self) -> list[dict]:
        return list(self._queue)

    async def cancel(self, job_id: str) -> bool:
        for entry in self._queue:
            if entry["id"] == job_id and entry["status"] == "scheduled":
                entry["status"] = "cancelled"
                return True
        return False

    async def check_and_dispatch(self) -> list[dict]:
        now = datetime.datetime.now(datetime.UTC)
        dispatched = []
        for entry in self._queue:
            if entry["status"] != "scheduled":
                continue
            try:
                publish_at = datetime.datetime.fromisoformat(entry["publish_at"])
                if publish_at.tzinfo is None:
                    publish_at = publish_at.replace(tzinfo=datetime.UTC)
                if publish_at <= now:
                    entry["status"] = "dispatched"
                    dispatched.append(entry)
            except (ValueError, TypeError):
                logger.warning(f"Invalid scheduled_time for {entry['id']}: {entry['publish_at']}")
        return dispatched

    async def run_loop(self, check_interval: int = 60):
        self._running = True
        while self._running:
            try:
                dispatched = await self.check_and_dispatch()
                if dispatched:
                    logger.info(f"Dispatched {len(dispatched)} scheduled releases")
            except Exception as e:
                logger.error(f"Scheduler check error: {e}")
            await asyncio.sleep(check_interval)

    def stop(self):
        self._running = False


_scheduler: ReleaseScheduler | None = None


def get_scheduler() -> ReleaseScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = ReleaseScheduler()
    return _scheduler
