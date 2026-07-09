# X113 — Security Scanner

**Purpose:** Static analysis security scanning with bandit and pip-audit.  
**Created:** 2026-07-09 (V3 — V2 agent integration docs)  
**Estimated time:** 10 minutes

---

## Overview

The security scanner runs static analysis on workspace code to identify vulnerabilities, insecure patterns, and dependency issues. It uses bandit (Python security) and pip-audit (dependency vulnerabilities).

---

## Scanners

| Scanner | Purpose | What It Catches |
|---------|---------|-----------------|
| **bandit** | Python static analysis | SQL injection, hardcoded passwords, insecure functions |
| **pip-audit** | Dependency vulnerabilities | Known CVEs in installed packages |

---

## Usage

### Via Tool
```python
from packages.tool_registry.tools.security import security_scan

result = security_scan(path=".", scanner="all")
# Returns: "Security scan found 3 issue(s): ..."
```

### Via API
```bash
POST /api/tools/security-scan
{
  "path": ".",
  "scanner": "all"
}
```

### Via Coding Agent
The agent can call the security scanner as a tool:
```
User: "Run a security scan on the workspace"
Agent: calls security_scan(path=".", scanner="all")
Agent: "Security scan complete. Found 2 issues: ..."
```

---

## Scanner Details

### Bandit

Runs Python static analysis to find:
- Hardcoded passwords/secrets
- SQL injection vulnerabilities
- Insecure function usage (eval, exec, etc.)
- Insecure file permissions
- Debug code in production

```bash
bandit -r /path/to/code -f json -q
```

**Output format:**
```json
{
  "results": [
    {
      "issue_severity": "HIGH",
      "filename": "app/main.py",
      "line_number": 42,
      "issue_text": "Possible hardcoded password: 'secret_key'"
    }
  ]
}
```

### pip-audit

Checks installed packages against known vulnerability databases:

```bash
pip-audit --format json
```

**Output format:**
```json
{
  "dependencies": [
    {
      "name": "requests",
      "version": "2.28.0",
      "vulns": [
        {
          "id": "CVE-2023-XXXXX",
          "description": "Unintended leak of Proxy-Authorization header"
        }
      ]
    }
  ]
}
```

---

## Tool Definition

```python
@tool(
    "security_scan",
    "Run security scanner (bandit, pip-audit) on the workspace.",
    sandbox_policy=SandboxPolicy(
        filesystem_scope="workspace",
        timeout_seconds=120,
    ),
)
def security_scan(path: str = ".", scanner: str = "all") -> str:
    """Scan workspace for security issues.

    Args:
        path: Directory or file to scan (relative to workspace).
        scanner: 'bandit', 'pip_audit', or 'all'.
    """
```

---

## Output Format

```
Security scan found 3 issue(s):

1. [HIGH] app/main.py:42 — Possible hardcoded password: 'secret_key'
2. [MEDIUM] app/utils.py:18 — Use of assert in production code
3. [HIGH] requirements.txt — requests==2.28.0: CVE-2023-XXXXX
```

---

## Integration with CI

### GitHub Actions

```yaml
- name: Security Scan
  run: |
    pip install bandit pip-audit
    bandit -r . -f json -q > bandit.json || true
    pip-audit --format json > audit.json || true
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ["-r", "-q"]
```

---

## Severity Levels

| Level | Description | Action |
|-------|-------------|--------|
| **HIGH** | Critical vulnerability | Fix immediately |
| **MEDIUM** | Potential security issue | Fix before deploy |
| **LOW** | Minor security concern | Fix when convenient |
| **INFO** | Best practice suggestion | Consider fixing |

---

## Configuration

### Bandit Config

```ini
# .bandit
[bandit]
exclude = tests
skips = B101  # Skip assert warnings
```

### Ignoring Specific Issues

```python
# In code
password = "secret"  # nosec B105
```

---

## Common Findings

| Finding | Severity | Fix |
|---------|----------|-----|
| Hardcoded password | HIGH | Use environment variables |
| SQL injection | HIGH | Use parameterized queries |
| Use of eval() | HIGH | Avoid or sandbox |
| Debug code | MEDIUM | Remove before deploy |
| Insecure random | MEDIUM | Use secrets module |
| Missing HTTPS | MEDIUM | Enforce HTTPS |
| Assert in production | LOW | Remove or convert to exception |

---

## Limitations

- **Python only** — bandit only analyzes Python code
- **Static analysis** — can't find runtime vulnerabilities
- **False positives** — some findings are not actual vulnerabilities
- **Dependency scanning** — pip-audit only checks known CVEs
