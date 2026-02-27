#!/usr/bin/env python3
"""
Substrate Governance MCP Server

Exposes WBS governance operations as MCP tools for native Claude Code integration.
This provides a cleaner interface than bash-wrapped CLI commands.

Usage:
    # Start the server (stdio mode for Claude Code)
    python3 .governance/mcp_server.py

    # Add to Claude Code MCP config (~/.claude/mcp_servers.json):
    {
      "servers": {
        "substrate-governance": {
          "command": "python3",
          "args": [".governance/mcp_server.py"],
          "cwd": "/path/to/project"
        }
      }
    }

Constitutional authority: constitution.md
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

# Add src to path for imports
GOV = Path(__file__).parent
SRC_PATH = GOV.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from wbs_common import (
    WBS_DEF, WBS_STATE,
    load_definition, load_state, get_counts
)
from governed_platform.governance.engine import GovernanceEngine
from governed_platform.governance.state_manager import StateManager


class SubstrateGovernanceMCP:
    """MCP server exposing Substrate governance tools."""

    def __init__(self):
        self.name = "substrate-governance"
        self.version = "1.0.0"

    def _get_engine(self) -> GovernanceEngine:
        """Build governance engine from current state."""
        definition = load_definition()
        sm = StateManager(WBS_STATE)
        state = sm.load()
        # Ensure all packets exist in state
        for packet in definition.get("packets", []):
            pid = packet["id"]
            state.setdefault("packets", {})
            if pid not in state["packets"]:
                state["packets"][pid] = {
                    "status": "pending",
                    "assigned_to": None,
                    "started_at": None,
                    "completed_at": None,
                    "notes": None,
                }
        sm.save(state)
        return GovernanceEngine(definition, sm)

    def _get_definition(self) -> dict:
        """Load WBS definition."""
        return load_definition()

    def _get_state(self) -> dict:
        """Load current state."""
        return load_state()

    # ─────────────────────────────────────────────────────────────
    # MCP Tool Definitions
    # ─────────────────────────────────────────────────────────────

    def get_tools(self) -> list:
        """Return MCP tool definitions."""
        return [
            {
                "name": "wbs_ready",
                "description": "List packets that are ready to claim (status=pending, dependencies met). Use this to find available work.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "wbs_status",
                "description": "Get current governance status showing all packets grouped by state (in_progress, pending, done, failed, blocked).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "packet_id": {
                            "type": "string",
                            "description": "Optional: get status for a specific packet"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "wbs_claim",
                "description": "Claim a packet for execution. Transitions packet from PENDING to IN_PROGRESS. Requires dependencies to be met.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "packet_id": {
                            "type": "string",
                            "description": "The packet ID to claim (e.g., 'UPG-001')"
                        },
                        "agent": {
                            "type": "string",
                            "description": "Agent identifier (default: 'claude')",
                            "default": "claude"
                        }
                    },
                    "required": ["packet_id"]
                }
            },
            {
                "name": "wbs_done",
                "description": "Mark a packet as complete with evidence. Requires specific artifact paths and validation results per constitution.md Article III.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "packet_id": {
                            "type": "string",
                            "description": "The packet ID to complete"
                        },
                        "agent": {
                            "type": "string",
                            "description": "Agent identifier (default: 'claude')",
                            "default": "claude"
                        },
                        "evidence": {
                            "type": "string",
                            "description": "Completion evidence: artifact paths, validation results, test outputs. Must be specific, not vague."
                        }
                    },
                    "required": ["packet_id", "evidence"]
                }
            },
            {
                "name": "wbs_fail",
                "description": "Mark a packet as failed with reason. Use when work cannot be completed. Blocks downstream dependents.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "packet_id": {
                            "type": "string",
                            "description": "The packet ID to fail"
                        },
                        "agent": {
                            "type": "string",
                            "description": "Agent identifier (default: 'claude')",
                            "default": "claude"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Failure reason explaining why work cannot be completed"
                        }
                    },
                    "required": ["packet_id", "reason"]
                }
            },
            {
                "name": "wbs_note",
                "description": "Add evidence notes to a packet without changing status. Use to document additional artifacts or clarifications.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "packet_id": {
                            "type": "string",
                            "description": "The packet ID to annotate"
                        },
                        "agent": {
                            "type": "string",
                            "description": "Agent identifier (default: 'claude')",
                            "default": "claude"
                        },
                        "notes": {
                            "type": "string",
                            "description": "Additional evidence or notes to append"
                        }
                    },
                    "required": ["packet_id", "notes"]
                }
            },
            {
                "name": "wbs_scope",
                "description": "Get the scope definition for a packet including required_actions, validation_checks, and exit_criteria.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "packet_id": {
                            "type": "string",
                            "description": "The packet ID to inspect"
                        }
                    },
                    "required": ["packet_id"]
                }
            },
            {
                "name": "wbs_log",
                "description": "View the immutable activity log showing all state transitions with timestamps and agents.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "description": "Number of recent entries to show (default: 20)",
                            "default": 20
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "wbs_progress",
                "description": "Get completion metrics: total packets, done count, percentage complete, packets by status.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]

    # ─────────────────────────────────────────────────────────────
    # Tool Implementations
    # ─────────────────────────────────────────────────────────────

    def call_tool(self, name: str, arguments: dict) -> dict:
        """Execute a tool and return result."""
        try:
            if name == "wbs_ready":
                return self._tool_ready()
            elif name == "wbs_status":
                return self._tool_status(arguments.get("packet_id"))
            elif name == "wbs_claim":
                return self._tool_claim(
                    arguments["packet_id"],
                    arguments.get("agent", "claude")
                )
            elif name == "wbs_done":
                return self._tool_done(
                    arguments["packet_id"],
                    arguments.get("agent", "claude"),
                    arguments["evidence"]
                )
            elif name == "wbs_fail":
                return self._tool_fail(
                    arguments["packet_id"],
                    arguments.get("agent", "claude"),
                    arguments["reason"]
                )
            elif name == "wbs_note":
                return self._tool_note(
                    arguments["packet_id"],
                    arguments.get("agent", "claude"),
                    arguments["notes"]
                )
            elif name == "wbs_scope":
                return self._tool_scope(arguments["packet_id"])
            elif name == "wbs_log":
                return self._tool_log(arguments.get("count", 20))
            elif name == "wbs_progress":
                return self._tool_progress()
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": str(e)}

    def _tool_ready(self) -> dict:
        """List ready packets."""
        engine = self._get_engine()
        state = self._get_state()
        definition = self._get_definition()

        ready_packets = []
        deps = definition.get("dependencies", {})

        for pkt in definition.get("packets", []):
            pid = pkt["id"]
            pkt_state = state.get("packets", {}).get(pid, {})
            if pkt_state.get("status") != "pending":
                continue
            # Check dependencies
            pkt_deps = deps.get(pid, [])
            deps_met = all(
                state.get("packets", {}).get(d, {}).get("status") == "done"
                for d in pkt_deps
            )
            if deps_met:
                ready_packets.append({
                    "id": pid,
                    "title": pkt.get("title", ""),
                    "scope": pkt.get("scope", pkt.get("purpose", "")),
                    "wbs_ref": pkt.get("wbs_ref", ""),
                    "dependencies": pkt_deps
                })

        return {
            "ready_count": len(ready_packets),
            "packets": ready_packets,
            "hint": "Use wbs_claim to claim a packet before starting work"
        }

    def _tool_status(self, packet_id: str = None) -> dict:
        """Get current status."""
        state = self._get_state()
        definition = self._get_definition()

        if packet_id:
            # Single packet status
            pkt_state = state.get("packets", {}).get(packet_id)
            if not pkt_state:
                return {"error": f"Packet {packet_id} not found"}

            pkt_def = next(
                (p for p in definition.get("packets", []) if p["id"] == packet_id),
                {}
            )
            return {
                "packet_id": packet_id,
                "title": pkt_def.get("title", ""),
                "status": pkt_state.get("status"),
                "assigned_to": pkt_state.get("assigned_to"),
                "started_at": pkt_state.get("started_at"),
                "completed_at": pkt_state.get("completed_at"),
                "notes": pkt_state.get("notes")
            }

        # Full status grouped by state
        grouped = {"in_progress": [], "pending": [], "done": [], "failed": [], "blocked": []}
        for pid, pkt_state in state.get("packets", {}).items():
            status = pkt_state.get("status", "pending")
            grouped.setdefault(status, []).append({
                "id": pid,
                "assigned_to": pkt_state.get("assigned_to"),
                "notes": pkt_state.get("notes")
            })

        counts = get_counts(state)
        return {
            "summary": counts,
            "in_progress": grouped.get("in_progress", []),
            "pending": grouped.get("pending", []),
            "blocked": grouped.get("blocked", []),
            "failed": grouped.get("failed", []),
            "done_count": len(grouped.get("done", []))
        }

    def _tool_claim(self, packet_id: str, agent: str) -> dict:
        """Claim a packet."""
        engine = self._get_engine()
        success, message = engine.claim(packet_id, agent)
        return {
            "success": success,
            "message": message,
            "packet_id": packet_id,
            "agent": agent,
            "next_step": "Execute packet scope, then use wbs_done with evidence" if success else "Check wbs_ready for available packets"
        }

    def _tool_done(self, packet_id: str, agent: str, evidence: str) -> dict:
        """Mark packet complete."""
        # Validate evidence quality
        if len(evidence.strip()) < 20:
            return {
                "success": False,
                "message": "Evidence too short. Must include specific artifact paths and validation results.",
                "hint": "Good evidence: 'Created src/auth.py (150 lines), tests pass (pytest tests/test_auth.py), validated schema'"
            }

        engine = self._get_engine()
        success, message = engine.done(packet_id, agent, evidence)
        return {
            "success": success,
            "message": message,
            "packet_id": packet_id,
            "evidence_recorded": evidence if success else None
        }

    def _tool_fail(self, packet_id: str, agent: str, reason: str) -> dict:
        """Mark packet failed."""
        engine = self._get_engine()
        success, message = engine.fail(packet_id, agent, reason)
        return {
            "success": success,
            "message": message,
            "packet_id": packet_id,
            "reason": reason,
            "note": "Downstream dependents are now blocked" if success else None
        }

    def _tool_note(self, packet_id: str, agent: str, notes: str) -> dict:
        """Add notes to packet."""
        engine = self._get_engine()
        success, message = engine.note(packet_id, agent, notes)
        return {
            "success": success,
            "message": message,
            "packet_id": packet_id
        }

    def _tool_scope(self, packet_id: str) -> dict:
        """Get packet scope definition."""
        definition = self._get_definition()
        pkt = next(
            (p for p in definition.get("packets", []) if p["id"] == packet_id),
            None
        )
        if not pkt:
            return {"error": f"Packet {packet_id} not found in definition"}

        return {
            "packet_id": packet_id,
            "title": pkt.get("title", ""),
            "purpose": pkt.get("purpose", pkt.get("scope", "")),
            "required_actions": pkt.get("required_actions", []),
            "required_outputs": pkt.get("required_outputs", []),
            "validation_checks": pkt.get("validation_checks", []),
            "exit_criteria": pkt.get("exit_criteria", []),
            "preconditions": pkt.get("preconditions", []),
            "halt_conditions": pkt.get("halt_conditions", [])
        }

    def _tool_log(self, count: int) -> dict:
        """Get activity log."""
        state = self._get_state()
        log = state.get("log", [])
        recent = log[-count:] if count < len(log) else log
        return {
            "total_entries": len(log),
            "showing": len(recent),
            "entries": recent
        }

    def _tool_progress(self) -> dict:
        """Get progress metrics."""
        state = self._get_state()
        counts = get_counts(state)
        total = sum(counts.values())
        done = counts.get("done", 0)
        pct = round((done / total * 100), 1) if total > 0 else 0

        return {
            "total_packets": total,
            "completed": done,
            "percentage": pct,
            "by_status": counts
        }

    # ─────────────────────────────────────────────────────────────
    # MCP Protocol Implementation (stdio JSON-RPC)
    # ─────────────────────────────────────────────────────────────

    def handle_request(self, request: dict) -> dict:
        """Handle a JSON-RPC request."""
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version
                    },
                    "capabilities": {
                        "tools": {}
                    }
                }
            }
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": self.get_tools()
                }
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = self.call_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }

    def run_stdio(self):
        """Run server in stdio mode for Claude Code integration."""
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                request = json.loads(line)
                response = self.handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except json.JSONDecodeError:
                continue
            except KeyboardInterrupt:
                break


def main():
    """Entry point."""
    server = SubstrateGovernanceMCP()

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode: run a sample tool
        print("Testing wbs_ready:")
        print(json.dumps(server.call_tool("wbs_ready", {}), indent=2))
        print("\nTesting wbs_progress:")
        print(json.dumps(server.call_tool("wbs_progress", {}), indent=2))
    else:
        # Run as MCP server
        server.run_stdio()


if __name__ == "__main__":
    main()
