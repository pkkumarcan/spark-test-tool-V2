# Spark Media Factory V2 — Manual Index

**Version:** 3.0 (Updated with vidIQ V3 master reference)  
**Last Updated:** 2026-07-09  
**Codebase:** spark-test-tool-V2  
**Channels:** 10 active (reduced from 12 — MLN merged into GDB, CCL removed)

---

## Chapter Index

### Foundation & Setup (X01-X10)

| Ch | Title | File |
|----|-------|------|
| X00 | Pipeline Architecture | [X00_pipeline_architecture.md](X00_pipeline_architecture.md) |
| X01 | Orientation & Quickstart | [X01_orientation.md](X01_orientation.md) |
| X02 | System Architecture | [X02_system_architecture.md](X02_system_architecture.md) |
| X03 | Hardware Requirements | [X03_hardware.md](X03_hardware.md) |
| X05 | Model Registry | [X05_model_registry.md](X05_model_registry.md) |
| X06 | Installation Guide | [X06_install.md](X06_install.md) |
| X07 | Operations Runbook | [X07_operations_runbook.md](X07_operations_runbook.md) |
| X08 | Smoke Tests | [X08_smoke_tests.md](X08_smoke_tests.md) |
| X09 | Logging & Observability | [X09_logging.md](X09_logging.md) |
| X10 | Reliability | [X10_reliability.md](X10_reliability.md) |

### Planning & Knowledge (X11-X12)

| Ch | Title | File |
|----|-------|------|
| X11 | Research Workflow | [X11_research.md](X11_research.md) |
| X12 | RAG & Knowledge Base | [X12_rag.md](X12_rag.md) |

### Audio Production (X21-X22)

| Ch | Title | File |
|----|-------|------|
| X21 | STT (Whisper) | [X21_stt.md](X21_stt.md) |
| X22 | TTS (F5-TTS) | [X22_tts.md](X22_tts.md) |

### Visual Production (X41-X51)

| Ch | Title | File |
|----|-------|------|
| X41 | ComfyUI Integration | [X41_comfyui.md](X41_comfyui.md) |
| X42 | Image Generation | [X42_image_gen.md](X42_image_gen.md) |
| X51 | Video Generation | [X51_video.md](X51_video.md) |

### Assembly (X65)

| Ch | Title | File |
|----|-------|------|
| X65 | FFmpeg Cookbook | [X65_ffmpeg.md](X65_ffmpeg.md) |

### Publishing & Channels (X71-X75)

| Ch | Title | File |
|----|-------|------|
| X71 | Channel Setup & Publishing | [X71_channels.md](X71_channels.md) |
| X73 | Scheduling & Calendar | [X73_scheduling.md](X73_scheduling.md) |
| X75 | Release Checklist | [X75_release_checklist.md](X75_release_checklist.md) |

### Post-Publishing (X81-X85)

| Ch | Title | File |
|----|-------|------|
| X81 | KPI Dashboard | [X81_kpi_dashboard.md](X81_kpi_dashboard.md) |
| X85 | Community Operations | [X85_community_ops.md](X85_community_ops.md) |

### Governance (X91-X98)

| Ch | Title | File |
|----|-------|------|
| X91 | Legal & Compliance | [X91_legal.md](X91_legal.md) |
| X92 | Security | [X92_security.md](X92_security.md) |
| X93 | Monetization Overview | [X93_monetization.md](X93_monetization.md) |
| X95 | Tracking & Attribution | [X95_tracking.md](X95_tracking.md) |
| X96 | Costing & ROI | [X96_costing.md](X96_costing.md) |
| X98 | Incident Response | [X98_incidents.md](X98_incidents.md) |

### AI Agent & Integration Layer (X101-X113)

| Ch | Title | File |
|----|-------|------|
| X101 | Mail Agent | [X101_mail_agent.md](X101_mail_agent.md) |
| X102 | Mixture of Agents (MoA) | [X102_moa_chat.md](X102_moa_chat.md) |
| X107 | Voice Agent | [X107_voice_agent.md](X107_voice_agent.md) |
| X110 | Coding Agent | [X110_coding_agent.md](X110_coding_agent.md) |
| X113 | Security Scanner | [X113_security_scanner.md](X113_security_scanner.md) |

---

## How to Use This Manual

1. **New to Spark V2?** Start with [X01 Orientation](X01_orientation.md)
2. **Setting up?** Follow [X06 Installation](X06_install.md)
3. **Understanding the system?** Read [X02 System Architecture](X02_system_architecture.md)
4. **Running the pipeline?** See [X00 Pipeline Architecture](X00_pipeline_architecture.md)
5. **Something broken?** Check [X07 Operations Runbook](X07_operations_runbook.md)
6. **Security concerns?** Read [X92 Security](X92_security.md)

---

## V1 to V2 Mapping

| V1 Chapter | V2 Equivalent | Notes |
|------------|---------------|-------|
| X01 Orientation | X01 Orientation | Updated for Docker Compose V2 |
| X02 Factory Contract | X02 System Architecture | Renamed, expanded |
| X03 Hardware | X03 Hardware | Updated for multi-GPU |
| X05 Model Registry | X05 Model Registry | Updated for Ollama + vLLM |
| X06 Install | X06 Install | Simplified (single command) |
| X07 Operations | X07 Operations | New runbook for V2 services |
| X08 Smoke Tests | X08 Smoke Tests | New test suite |
| X09 Logging | X09 Logging | Updated for OpenTelemetry |
| X10 Reliability | X10 Reliability | New retry/circuit-breaker patterns |
| X11 Research | X11 Research | Updated for V2 RAG |
| X12 RAG | X12 RAG | New chapter |
| X21-X26 Speech | X21-X22 Speech | Consolidated |
| X41-X47 Images | X41-X42 Images | Consolidated |
| X51-X57 Video | X51 Video | Consolidated |
| X65 FFmpeg | X65 FFmpeg | Updated |
| X71 Channel Setup | X71 Channels | Updated for V2 publishing |
| X92 Security | X92 Security | New sandbox model |
| X96 Costing | X96 Costing | New chapter |
| X98 Incidents | X98 Incidents | New chapter |
