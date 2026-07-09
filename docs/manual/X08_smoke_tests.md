# X08 — Smoke Tests

**Purpose:** Run automated tests to verify the system is working correctly.  
**Estimated time:** 10 minutes

---

## Running Tests

```bash
# Full test suite
pytest tests/ -v

# Quick run (no verbose)
pytest tests/ -q

# Sandbox escape tests only
pytest tests/sandbox_escape/ -v

# Pipeline tests only
pytest tests/integration/test_pipeline.py -v

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest tests/ --cov=apps --cov=packages
```

---

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures (mock LLM, workspace, etc.)
├── unit/
│   ├── test_tools.py              # Tool handler tests (18 tools)
│   ├── test_sandbox.py            # Sandbox policy tests
│   └── test_security.py           # Security scanner tests
├── integration/
│   ├── test_pipeline.py           # Pipeline state machine tests
│   ├── test_agent.py              # Agent state machine tests
│   ├── test_rag.py                # RAG query tests
│   └── test_router.py             # Intent routing tests
├── sandbox_escape/
│   └── test_escape_patterns.py    # Path traversal, network escape, shell audit
└── golden_trajectories/
    └── test_replay.py             # Golden trajectory replay tests
```

---

## Test Categories

### Unit Tests (`tests/unit/`)
- **test_tools.py** — All 18 tool handlers: file ops, search, shell, git, analysis, meta
- **test_sandbox.py** — Sandbox policy validation, path containment, command validation
- **test_security.py** — Command audit patterns, allowed commands, path traversal

### Integration Tests (`tests/integration/`)
- **test_pipeline.py** — Pipeline stages, state transitions, runner execution
- **test_agent.py** — Agent state machine, tool dispatch, stuck-loop detection
- **test_rag.py** — Document chunking, semantic search, RAG queries
- **test_router.py** — Intent classification, routing to correct handler

### Sandbox Escape Tests (`tests/sandbox_escape/`)
- **test_escape_patterns.py** — Tests that verify:
  - Network commands blocked when policy says no network
  - File paths outside workspace are rejected
  - Symlink escapes are caught
  - Shell commands are audit-checked
  - Docker is NOT in the allow-list
  - `_policy_precheck` blocks violations before handler runs

---

## Expected Results

All tests should pass. Current baseline: **266 tests, all passing.**

```bash
pytest tests/ -q
# ======================== 266 passed in 7.00s ========================
```

---

## Writing New Tests

### Test a Tool Handler
```python
def test_my_tool(workspace):
    from packages.tool_registry.tools.my_module import my_tool
    result = my_tool(path="test.txt")
    assert "expected output" in result
```

### Test Sandbox Policy
```python
def test_path_blocked():
    from packages.tool_registry.sandbox import Sandbox
    from packages.schemas.models import SandboxPolicy
    sandbox = Sandbox(workspace_root="/workspace")
    policy = SandboxPolicy(filesystem_scope="workspace")
    assert sandbox.validate_path("/etc/passwd", policy) is False
```

### Test Pipeline Stage
```python
@pytest.mark.asyncio
async def test_my_stage():
    from apps.agent_runtime.pipeline import PipelineState, PipelineRunner
    state = PipelineState("p1", "ch1", "topic")
    runner = PipelineRunner(state)
    await runner._stage_topic()
    assert state.stages["topic"]["status"] == "passed"
```

---

## CI Integration

Add to your CI pipeline:

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -q
```
