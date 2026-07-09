"""Integration tests for pipeline state machine transitions."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.agent_runtime.pipeline import (
    STAGE_ORDER,
    PipelineRunner,
    PipelineStage,
    PipelineState,
    create_pipeline,
    get_pipeline,
    list_pipelines,
)


class TestPipelineState:
    def test_initial_state(self):
        state = PipelineState("pipe_123", "tech_channel", "AI Trends")
        assert state.pipeline_id == "pipe_123"
        assert state.channel_id == "tech_channel"
        assert state.topic == "AI Trends"
        assert state.stage == PipelineStage.TOPIC
        assert state.error is None

    def test_all_stages_initialized(self):
        state = PipelineState("p1", "ch1", "topic1")
        for stage in STAGE_ORDER:
            assert stage.value in state.stages
            assert state.stages[stage.value]["status"] == "pending"

    def test_set_stage(self):
        state = PipelineState("p1", "ch1", "topic1")
        state.set_stage(PipelineStage.SCRIPT, "running", 50, "Generating...")
        assert state.stage == PipelineStage.SCRIPT
        assert state.stages["script"]["status"] == "running"
        assert state.stages["script"]["progress"] == 50
        assert state.stages["script"]["msg"] == "Generating..."

    def test_to_dict(self):
        state = PipelineState("p1", "ch1", "topic1")
        d = state.to_dict()
        assert d["pipeline_id"] == "p1"
        assert d["job_id"] == "p1"
        assert d["job_code"] == "p1"
        assert d["channel_id"] == "ch1"
        assert d["topic"] == "topic1"
        assert d["status"] == "pending"
        assert d["current_step"] == "topic: Waiting to start"
        assert d["progress_pct"] == 0
        assert d["stage"] == "topic"
        assert "stages" in d
        assert "data" in d

    def test_to_dict_running_stage(self):
        state = PipelineState("p1", "ch1", "topic1")
        state.set_stage(PipelineStage.SCRIPT, "running", 50, "Generating...")
        d = state.to_dict()
        assert d["status"] == "running"
        assert "script" in d["current_step"]
        assert d["progress_pct"] > 0

    def test_to_dict_failed_stage(self):
        state = PipelineState("p1", "ch1", "topic1")
        state.set_stage(PipelineStage.FAILED, "failed", 0, "Failed: test error")
        d = state.to_dict()
        assert d["status"] == "failed"

    def test_to_dict_completed_stage(self):
        state = PipelineState("p1", "ch1", "topic1")
        state.set_stage(PipelineStage.COMPLETED, "passed", 100, "Done")
        d = state.to_dict()
        assert d["status"] == "completed"
        assert d["progress_pct"] == 100

    def test_to_dict_has_timestamps(self):
        state = PipelineState("p1", "ch1", "topic1")
        d = state.to_dict()
        assert d["created_at"] is not None
        assert d["updated_at"] is not None


class TestPipelineFunctions:
    def test_create_pipeline(self):
        state = create_pipeline("tech", "AI in 2025")
        assert state.pipeline_id.startswith("pipe_")
        assert state.channel_id == "tech"
        assert state.topic == "AI in 2025"

    def test_get_pipeline(self):
        state = create_pipeline("tech", "topic")
        retrieved = get_pipeline(state.pipeline_id)
        assert retrieved is not None
        assert retrieved.pipeline_id == state.pipeline_id

    def test_get_pipeline_not_found(self):
        assert get_pipeline("nonexistent") is None

    def test_list_pipelines(self):
        create_pipeline("ch1", "t1")
        create_pipeline("ch2", "t2")
        pipelines = list_pipelines()
        assert len(pipelines) >= 2

    def test_list_pipelines_returns_dicts(self):
        create_pipeline("ch", "topic")
        pipelines = list_pipelines()
        for p in pipelines:
            assert isinstance(p, dict)
            assert "pipeline_id" in p
            assert "job_id" in p
            assert "status" in p
            assert "progress_pct" in p
            assert "current_step" in p


class TestPipelineStageOrder:
    def test_stage_order_starts_with_topic(self):
        assert STAGE_ORDER[0] == PipelineStage.TOPIC

    def test_stage_order_ends_with_completed(self):
        assert STAGE_ORDER[-1] == PipelineStage.COMPLETED

    def test_approval_after_script(self):
        script_idx = STAGE_ORDER.index(PipelineStage.SCRIPT)
        approval_idx = STAGE_ORDER.index(PipelineStage.APPROVAL)
        assert approval_idx == script_idx + 1

    def test_voiceover_after_approval(self):
        approval_idx = STAGE_ORDER.index(PipelineStage.APPROVAL)
        voiceover_idx = STAGE_ORDER.index(PipelineStage.VOICEOVER)
        assert voiceover_idx == approval_idx + 1

    def test_visuals_after_voiceover(self):
        voiceover_idx = STAGE_ORDER.index(PipelineStage.VOICEOVER)
        visuals_idx = STAGE_ORDER.index(PipelineStage.VISUALS)
        assert visuals_idx == voiceover_idx + 1

    def test_publish_before_completed(self):
        publish_idx = STAGE_ORDER.index(PipelineStage.PUBLISH)
        completed_idx = STAGE_ORDER.index(PipelineStage.COMPLETED)
        assert publish_idx < completed_idx

    def test_failed_not_in_stage_order(self):
        assert PipelineStage.FAILED not in STAGE_ORDER

    def test_all_stages_covered(self):
        all_stages_in_order = {s for s in STAGE_ORDER}
        all_enum_stages = {s for s in PipelineStage}
        non_order_stages = all_enum_stages - all_stages_in_order
        assert non_order_stages == {PipelineStage.FAILED}


@pytest.mark.asyncio
class TestPipelineRunner:
    @patch("apps.agent_runtime.pipeline.PipelineRunner._query_ollama")
    async def test_stage_topic_generates_brief(self, mock_ollama):
        state = PipelineState("p1", "ch1", "AI Trends")
        runner = PipelineRunner(state)

        mock_ollama.return_value = '{"title_variants": ["Title 1"], "thumbnail_concepts": ["Concept 1"], "target_duration_seconds": 60}'

        await runner._stage_topic()
        assert "brief" in state.data
        assert state.stages["topic"]["status"] == "passed"

    @patch("apps.agent_runtime.pipeline.PipelineRunner._query_ollama")
    async def test_stage_topic_fallback_mock(self, mock_ollama):
        state = PipelineState("p1", "ch1", "AI Trends")
        runner = PipelineRunner(state)

        mock_ollama.side_effect = Exception("Ollama down")

        await runner._stage_topic()
        assert "brief" in state.data
        assert len(state.data["brief"]["title_variants"]) == 3
        assert state.stages["topic"]["status"] == "passed"

    @patch("apps.agent_runtime.pipeline.PipelineRunner._query_ollama")
    async def test_stage_script(self, mock_ollama):
        state = PipelineState("p1", "ch1", "AI Trends")
        state.data["brief"] = {"title_variants": ["AI Trends 2025"]}
        runner = PipelineRunner(state)

        mock_ollama.return_value = '{"mode": "narrator-led", "sections": [{"section_id": "S01", "label": "HOOK", "narration": "Hook text", "target_duration_seconds": 10}]}'

        await runner._stage_script()
        assert "script" in state.data
        assert state.stages["script"]["status"] == "passed"

    @patch("apps.agent_runtime.pipeline.PipelineRunner._query_ollama")
    async def test_stage_script_fallback(self, mock_ollama):
        state = PipelineState("p1", "ch1", "AI Trends")
        state.data["brief"] = {"title_variants": ["Title"]}
        runner = PipelineRunner(state)

        mock_ollama.side_effect = Exception("Ollama down")

        await runner._stage_script()
        assert "script" in state.data
        assert len(state.data["script"]["sections"]) >= 3

    async def test_stage_approval_auto(self):
        state = PipelineState("p1", "ch1", "topic")
        runner = PipelineRunner(state)

        await runner._stage_approval()
        assert state.stages["approval"]["status"] == "passed"
        assert state.data["approval"]["status"] == "auto_approved"

    async def test_failure_sets_failed_state(self, tmp_path):
        state = PipelineState("p1", "ch1", "topic")
        runner = PipelineRunner(state, output_dir=str(tmp_path))

        with patch.object(runner, "_stage_script", side_effect=Exception("Script failed")):
            with pytest.raises(Exception, match="Script failed"):
                await runner.run_stage(PipelineStage.SCRIPT)

        assert state.stage == PipelineStage.FAILED
        assert state.error == "Script failed"

    async def test_run_full_stops_on_failure(self, tmp_path):
        state = PipelineState("p1", "ch1", "topic")
        runner = PipelineRunner(state, output_dir=str(tmp_path))

        with patch.object(runner, "_stage_script", side_effect=Exception("Script failed")):
            with pytest.raises(Exception):
                await runner.run_full()

        assert state.stage == PipelineStage.FAILED
