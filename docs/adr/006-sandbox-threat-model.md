# ADR-006: Sandbox Threat Model and Defense Layers

**Status:** Accepted  
**Date:** 2026-07-09  
**Deciders:** Spark Engineering

## Context

After the security remediation (PR1–PR5), the codebase has multiple overlapping
security layers. This ADR documents what each layer protects against and — more
importantly — what it does NOT protect against, so future contributors don't
develop a false sense of safety.

## Defense Layers

### Layer 1: Process allow-list (`shell.py` ALLOWED_COMMANDS)
- **Protects against:** Arbitrary binary execution (nmap, sudo, chmod, kill, etc.)
- **Does NOT protect against:** Commands within the allow-list doing arbitrary
  things (e.g. `python -c "import os; os.system('whoami')"` is allowed).
- **Scope:** First gate in the shell tool; blocks unknown commands before they
  reach the OS.

### Layer 2: Command audit (`_audit_command` regexes)
- **Protects against:** Known dangerous patterns (curl|bash, /etc/passwd reads,
  base64 obfuscation, inline network calls in interpreters, command substitution).
- **Does NOT protect against:** Novel obfuscation, multi-stage payloads, or
  interpreters making network calls via libraries not matched by regex.
- **Scope:** Defense-in-depth within the shell tool; catches patterns the
  allow-list misses.

### Layer 3: Sandbox policy pre-check (`_policy_precheck` in state_machine.py)
- **Protects against:** Tool calls that violate their declared `SandboxPolicy`
  (filesystem_scope, network_access) before the handler body runs.
- **Does NOT protect against:** Tools whose handler body does something the
  policy doesn't cover (e.g. a tool that reads env vars but declares
  `filesystem_scope="workspace"`).
- **Scope:** Central gate in the agent dispatch path; catches policy violations
  before any tool handler code executes.

### Layer 4: Per-tool path containment (`paths.is_within_root`)
- **Protects against:** Path traversal attacks (../../etc/passwd, symlink escapes,
  sibling-directory prefix matches like /workspace-evil).
- **Does NOT protect against:** TOCTOU races (unlikely in single-threaded
  tool execution) or tools that don't use the shared path validation.
- **Scope:** Used by all file-operation tools (file_ops, search, analysis,
  security). Single source of truth — no duplicate logic.

### Layer 5: Container-level isolation (ADR-004, not yet implemented)
- **Protects against:** Network exfiltration via interpreters (python, node),
  host filesystem access, privilege escalation, resource exhaustion.
- **Does NOT protect against:** Side-channel attacks, container escape via
  kernel vulnerabilities, or Docker daemon misconfigurations.
- **Scope:** When implemented, this is the strongest isolation layer. Until then,
  network isolation for interpreters is NOT enforced — the regex audit in
  Layer 2 is the only (weak) defense.

## Key Insight

**String matching is NOT network isolation.** The `_audit_command` regexes
catch obvious patterns like `curl ... | bash` and `python -c "import socket"`,
but they cannot prevent all network calls from interpreters. True network
isolation requires `--network=none` at the container level (Layer 5).

Until Layer 5 is implemented, the system relies on:
1. The shell allow-list blocking unknown binaries
2. The audit catching known patterns
3. The assumption that LLM-generated code won't use novel evasion techniques

This is acceptable for development/single-user deployments but is NOT
sufficient for multi-tenant or untrusted-input scenarios.

## Recommendations

1. **Implement Layer 5 (container sandbox)** before exposing the agent to
   untrusted input or running in production.
2. **Never re-add `docker`/`docker-compose` to the shell allow-list.** If
   Docker access is needed, create a narrow structured tool (e.g. `docker_build`)
   that takes fixed args and shells out to a hardcoded command template.
3. **All path validation must go through `packages/tool_registry/paths.py`.**
   Never hand-roll `startswith(root)` checks.
4. **The `/output/` auth bypass is safe** because output filenames are UUIDs
   (`{job_id}.ext`), making enumeration impractical.
