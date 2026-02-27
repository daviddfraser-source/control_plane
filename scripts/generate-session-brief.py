#!/usr/bin/env python3
"""Generate project-specific session context artifacts for Codex/Claude sessions."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOV = ROOT / ".governance"


def run_cli(*args):
    cmd = [sys.executable, str(GOV / "wbs_cli.py"), *args, "--json"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def main() -> int:
    briefing = run_cli("briefing")
    ready = run_cli("ready")
    progress = run_cli("progress")

    generated_at = datetime.now(timezone.utc).isoformat()
    ready_packets = ready.get("ready", [])
    counts = progress.get("counts", {})

    snapshot = {
        "generated_at": generated_at,
        "project": briefing.get("project", {}),
        "counts": counts,
        "ready_packets": ready_packets,
        "blocked_packets": briefing.get("blocked_packets", []),
        "active_assignments": briefing.get("active_assignments", []),
        "recent_events": briefing.get("recent_events", []),
    }

    (GOV / "session-brief.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")

    lines = []
    lines.append("# Session Brief")
    lines.append("")
    lines.append(f"Generated: {generated_at}")
    lines.append("")
    project = snapshot.get("project", {})
    lines.append(f"Project: {project.get('project_name', '-')}")
    lines.append(f"Approved By: {project.get('approved_by', '-')}")
    lines.append("")
    ontology_path = ROOT / "docs" / "ontology.md"
    if ontology_path.exists():
        lines.append("## Core Ontology")
        lines.append(ontology_path.read_text(encoding="utf-8").strip())
        lines.append("")
    lines.append("## Status Counts")
    for k in sorted(counts.keys()):
        lines.append(f"- {k}: {counts[k]}")
    if not counts:
        lines.append("- (no counts)")
    lines.append("")
    lines.append("## Ready Packets")
    if ready_packets:
        for pkt in ready_packets[:10]:
            lines.append(f"- {pkt.get('id')} ({pkt.get('wbs_ref')}) {pkt.get('title')}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Blocked Packets")
    blocked = snapshot.get("blocked_packets", [])
    if blocked:
        for pkt in blocked[:10]:
            lines.append(f"- {pkt.get('id')} ({pkt.get('wbs_ref')}) {pkt.get('title')}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Startup Path")
    lines.append("1. python3 .governance/wbs_cli.py briefing --format json")
    lines.append("2. python3 .governance/wbs_cli.py ready --json")
    lines.append("3. python3 .governance/wbs_cli.py claim <packet_id> <agent>")
    lines.append("4. python3 .governance/wbs_cli.py context <packet_id> --format json")

    docs_path = ROOT / "docs" / "session-brief.md"
    docs_path.parent.mkdir(parents=True, exist_ok=True)
    docs_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    session_dir = ROOT / ".meta" / "session"
    session_dir.mkdir(parents=True, exist_ok=True)

    agent_supplement = session_dir / "AGENTS.session.md"
    agent_supplement.write_text(
        "\n".join(
            [
                "# AGENTS Session Supplement",
                "",
                f"Generated: {generated_at}",
                "",
                "Use packet-first execution:",
                "- Read docs/session-brief.md",
                "- Adhere to the core definitions in docs/ontology.md",
                "- Claim exactly one ready packet",
                "- Load packet context and execute scoped work",
                "- Record evidence paths before done",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    claude_supplement = session_dir / "CLAUDE.session.md"
    claude_supplement.write_text(
        "\n".join(
            [
                "# CLAUDE Session Supplement",
                "",
                f"Generated: {generated_at}",
                "",
                "Current snapshot:",
                f"- Ready packets: {len(ready_packets)}",
                f"- Counts: {json.dumps(counts, sort_keys=True)}",
                "",
                "Primary source-of-truth:",
                "- .governance/session-brief.json",
                "- docs/session-brief.md",
                "- docs/ontology.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # Cleanup legacy root artifacts from earlier generator behavior.
    for legacy in (ROOT / "AGENTS.session.md", ROOT / "CLAUDE.session.md"):
        if legacy.exists():
            legacy.unlink()

    print(
        "Generated: .governance/session-brief.json, docs/session-brief.md, "
        ".meta/session/AGENTS.session.md, .meta/session/CLAUDE.session.md"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
