---
name: deep-code-review
description: Perform a deep, context-aware code review of recent changes
allowed-tools: read_file, grep_search
---

# Deep Code Review

Leverage your large context window to review code changes in the context of the entire relevant module.

1.  **Read Context**:
    *   Read `scaffold.config.json` and `pyproject.toml` to understand project configuration.
    *   Read `README.md` and `docs/architecture.md` (if available) to understand architectural intent.

2.  **Analyze Changes**:
    *   For every modified file, read the **full content**, not just the diff.
    *   Identify potential:
        *   **Architectural Violations**: dependencies that shouldn't exist, logic in the wrong layer.
        *   **Security Issues**: hardcoded secrets, unchecked inputs.
        *   **Governance Gaps**: missing docstrings, type hints, or tests.

3.  **Report Findings**:
    *   Summarize the intent of the changes.
    *   List specific issues with file paths and line numbers.
    *   Provide actionable recommendations.
