#!/usr/bin/env python3
"""Generate packet-scoped context bundle markdown from governed context."""

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOV = ROOT / ".governance"
MAX_BYTES_DEFAULT = 24000


def run_context(packet_id: str) -> dict:
    cmd = [
        "python3",
        str(GOV / "wbs_cli.py"),
        "context",
        packet_id,
        "--format",
        "json",
        "--max-events",
        "40",
        "--max-notes-bytes",
        "4000",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def build_bundle(ctx: dict) -> str:
    pkt = ctx.get("packet_definition", {})
    runtime = ctx.get("runtime", {})
    deps = ctx.get("dependencies", {})
    recent = ctx.get("recent_events", [])[:12]

    def lines_list(items):
        items = items or []
        return "\n".join(f"- {item}" for item in items) if items else "- none"

    out = []
    out.append(f"# Packet Context Bundle: {pkt.get('id')}")
    out.append("")
    out.append("## Packet Summary")
    out.append(f"- ID: {pkt.get('id')}")
    out.append(f"- WBS Ref: {pkt.get('wbs_ref')}")
    out.append(f"- Title: {pkt.get('title')}")
    out.append(f"- Area: {pkt.get('area_id')}")
    out.append(f"- Priority: {pkt.get('priority')}")
    out.append(f"- Runtime Status: {runtime.get('status', 'pending')}")
    out.append("")
    out.append("## Scope")
    out.append(pkt.get("scope", ""))
    out.append("")
    out.append("## Purpose")
    out.append(pkt.get("purpose", ""))
    out.append("")
    out.append("## Preconditions")
    out.append(lines_list(pkt.get("preconditions")))
    out.append("")
    out.append("## Required Inputs")
    out.append(lines_list(pkt.get("required_inputs")))
    out.append("")
    out.append("## Required Actions")
    out.append(lines_list(pkt.get("required_actions")))
    out.append("")
    out.append("## Required Outputs")
    out.append(lines_list(pkt.get("required_outputs")))
    out.append("")
    out.append("## Validation Checks")
    out.append(lines_list(pkt.get("validation_checks")))
    out.append("")
    out.append("## Exit Criteria")
    out.append(lines_list(pkt.get("exit_criteria")))
    out.append("")
    out.append("## Halt Conditions")
    out.append(lines_list(pkt.get("halt_conditions")))
    out.append("")
    out.append("## Dependency Context")
    out.append(f"- Depends on: {', '.join(deps.get('depends_on', []) or []) or 'none'}")
    out.append(f"- Dependents: {', '.join(deps.get('dependents', []) or []) or 'none'}")
    out.append("")
    out.append("## Recent Events")
    if recent:
        for e in recent:
            out.append(f"- {e.get('timestamp')} | {e.get('event')} | {e.get('agent')} | {e.get('notes', '')}")
    else:
        out.append("- none")
    out.append("")
    out.append("## Execution Steps")
    out.append("1. Claim packet if not in_progress.")
    out.append("2. Implement only scoped changes.")
    out.append("3. Validate using packet-specific checks.")
    out.append("4. Mark done with evidence and residual risk acknowledgement.")
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("packet_id")
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES_DEFAULT)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    ctx = run_context(args.packet_id)
    bundle = build_bundle(ctx)
    data = bundle.encode("utf-8")
    if len(data) > args.max_bytes:
        raise SystemExit(f"Bundle exceeds max bytes ({len(data)} > {args.max_bytes})")

    out = Path(args.output) if args.output else ROOT / ".governance" / "packets" / args.packet_id / "context.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(bundle, encoding="utf-8")
    print(out)
    print(f"bytes={len(data)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
