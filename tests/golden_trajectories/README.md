# Golden Trajectory Testing

Golden trajectories are recorded "good" agent runs that serve as regression baselines.
On every model or prompt change, replay recorded user turns and diff the resulting
tool-call sequences against the golden baseline. Flag any divergence for manual review.

## Recording a Trajectory

1. Enable trajectory recording in the agent runtime:
   ```python
   # Set env var before running the agent
   export SPARK_RECORD_TRAJECTORIES=1
   ```

2. Run a normal agent session (via API or frontend).
   The runtime logs every state transition, tool call, and result to a JSON file
   in `tests/golden_trajectories/recordings/`.

3. Review the recording. If the agent performed well, move it to the numbered
   trajectory files:
   ```bash
   mv recordings/session_<uuid>.json trajectory_003.json
   ```

4. Edit the trajectory to add expected metadata:
   - `id`: unique identifier
   - `prompt`: the user's initial request
   - `model`: which model was used
   - `expected_tool_calls`: ordered list of tool calls the agent *should* make
   - `expected_states`: the state transitions expected

## Replaying a Trajectory

Run the replay framework against all golden trajectories:

```bash
cd spark-test-tool-V2
pytest tests/golden_trajectories/ -v
```

## What Gets Checked

- **Tool call names**: The same tools must be called in the same order.
- **Tool call arguments**: Key arguments must match (exact or fuzzy).
- **State transitions**: The agent must follow the expected state path.
- **Completion**: The agent must reach DONE (not FAILED).

## Divergence Handling

- **Benign divergence**: Agent takes a different but valid path (e.g., reads file
  before editing). Mark as acceptable in the trajectory file.
- **Bug divergence**: Agent calls wrong tools, fails to complete, or loops.
  File an issue and fix.
- **Model upgrade divergence**: New model produces better/different output.
  Update the golden trajectory to reflect the new behavior.

## Adding New Trajectories

When you encounter a real-world task the agent handles well, record it as a new
trajectory. Aim for 15-20 trajectories covering:

- File reading and editing
- Search and navigation
- Shell command execution
- Multi-step debugging
- Simple Q&A (no tools)
- Pipeline creation
- Media generation requests
