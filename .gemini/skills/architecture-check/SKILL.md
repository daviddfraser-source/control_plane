---
name: architecture-check
description: Verify code changes align with documented architecture and WBS
allowed-tools: read_file, grep_search
---

# Architecture Check

Ensure code changes execution aligns with `docs/architecture.md` and `wbs.json`.

1.  **Read Architecture**:
    *   Read `docs/architecture.md`.
    *   Read `.governance/wbs.json` to understand the current work breakdown.

2.  **Verify Alignment**:
    *   Check if new components are placed in the correct directories (e.g., `src/app` vs `src/governed_platform`).
    *   Check if dependencies flow correctly (e.g., `app` depends on `platform`, not vice-versa).
    *   Verify that work being done corresponds to an active or pending WBS packet.

3.  **Report**:
    *   **PASS/FAIL** status.
    *   If FAIL, explain the specific deviation and how to correct it.
