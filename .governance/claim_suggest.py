#!/usr/bin/env python3
"""
Capability-based claim suggestion system.

Analyzes packet required_capabilities against agent profiles and recommends
best match. Advisory only - humans make final decision (Article VI).

ORCH-014: Implement capability-based claim suggestion
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

GOV = Path(__file__).parent
AGENTS_FILE = GOV / "agents.json"
WBS_FILE = GOV / "wbs.json"
STATE_FILE = GOV / "wbs-state.json"


def load_agents() -> Dict:
    """Load agent profiles from agents.json."""
    if not AGENTS_FILE.exists():
        return {"agents": []}
    with open(AGENTS_FILE) as f:
        return json.load(f)


def load_wbs() -> Dict:
    """Load WBS definition."""
    if not WBS_FILE.exists():
        return {"packets": []}
    with open(WBS_FILE) as f:
        return json.load(f)


def load_state() -> Dict:
    """Load WBS state."""
    if not STATE_FILE.exists():
        return {"packets": {}}
    with open(STATE_FILE) as f:
        return json.load(f)


def get_packet_by_id(packet_id: str, wbs: Dict) -> Dict:
    """
    Get packet definition by ID.

    Args:
        packet_id: Packet ID to find
        wbs: WBS definition dict

    Returns:
        Packet dict or None if not found
    """
    for packet in wbs.get("packets", []):
        if packet.get("id") == packet_id:
            return packet
    return None


def calculate_capability_match(
    required: List[str], agent_capabilities: List[str]
) -> Tuple[float, List[str], List[str]]:
    """
    Calculate capability match score between requirements and agent.

    Args:
        required: List of required capability names
        agent_capabilities: List of agent's capability names

    Returns:
        Tuple of (match_score, matched_capabilities, missing_capabilities)
        - match_score: 0.0 to 1.0, percentage of requirements met
        - matched: List of capabilities agent has
        - missing: List of capabilities agent lacks
    """
    if not required:
        return 1.0, [], []  # No requirements = perfect match

    required_set = set(required)
    agent_set = set(agent_capabilities)

    matched = list(required_set & agent_set)
    missing = list(required_set - agent_set)

    match_score = len(matched) / len(required) if required else 1.0

    return match_score, matched, missing


def get_agent_workload(agent_id: str, state: Dict) -> int:
    """
    Get current workload for an agent (number of in_progress packets).

    Args:
        agent_id: Agent ID
        state: WBS state dict

    Returns:
        Number of packets currently in_progress for this agent
    """
    workload = 0
    for packet_state in state.get("packets", {}).values():
        if (
            packet_state.get("status") == "in_progress"
            and packet_state.get("assigned_to") == agent_id
        ):
            workload += 1
    return workload


def suggest_agents_for_packet(packet_id: str, verbose: bool = False) -> List[Dict]:
    """
    Suggest agents for a packet based on capability matching.

    Args:
        packet_id: Packet ID to analyze
        verbose: If True, print detailed analysis

    Returns:
        List of agent suggestions, ranked by match score.
        Each suggestion is a dict with:
        - agent_id: Agent ID
        - agent_type: Agent type (llm-claude, etc.)
        - match_score: 0.0 to 1.0
        - matched_capabilities: List of matched capabilities
        - missing_capabilities: List of missing capabilities
        - workload: Current number of in_progress packets
        - recommendation: Human-readable recommendation text
    """
    # Load data
    agents_data = load_agents()
    wbs = load_wbs()
    state = load_state()

    # Find packet
    packet = get_packet_by_id(packet_id, wbs)
    if not packet:
        if verbose:
            print(f"❌ Packet {packet_id} not found")
        return []

    # Get required capabilities
    required_capabilities = packet.get("required_capabilities", [])
    if not required_capabilities:
        if verbose:
            print(f"ℹ️  Packet {packet_id} has no required_capabilities specified")
            print("   Any agent can claim this packet")
        required_capabilities = []

    # Analyze each agent
    suggestions = []

    for agent in agents_data.get("agents", []):
        agent_id = agent.get("id")
        agent_type = agent.get("type", "unknown")
        agent_capabilities = agent.get("capabilities", [])

        # Calculate match
        match_score, matched, missing = calculate_capability_match(
            required_capabilities, agent_capabilities
        )

        # Get workload
        workload = get_agent_workload(agent_id, state)
        max_workload = agent.get("constraints", {}).get("max_concurrent_packets", 999)

        # Generate recommendation text
        if match_score == 1.0:
            recommendation = "Perfect match - all required capabilities available"
        elif match_score >= 0.7:
            recommendation = f"Good match - has {len(matched)}/{len(required_capabilities)} capabilities"
        elif match_score > 0:
            recommendation = f"Partial match - missing {len(missing)} capabilities"
        else:
            recommendation = "No matching capabilities"

        # Check workload
        if workload >= max_workload:
            recommendation += f" (at capacity: {workload}/{max_workload})"
        elif workload > 0:
            recommendation += f" (workload: {workload})"

        suggestions.append(
            {
                "agent_id": agent_id,
                "agent_type": agent_type,
                "match_score": match_score,
                "matched_capabilities": matched,
                "missing_capabilities": missing,
                "workload": workload,
                "max_workload": max_workload,
                "recommendation": recommendation,
            }
        )

    # Sort by match score (descending), then by workload (ascending)
    suggestions.sort(key=lambda x: (-x["match_score"], x["workload"]))

    return suggestions


def print_suggestions(packet_id: str, suggestions: List[Dict], packet: Dict):
    """
    Print agent suggestions in human-readable format.

    Args:
        packet_id: Packet ID
        suggestions: List of agent suggestion dicts
        packet: Packet definition dict
    """
    print(f"\n📋 Claim Suggestions for {packet_id}")
    print(f"   Title: {packet.get('title', 'Unknown')}")

    required = packet.get("required_capabilities", [])
    if required:
        print(f"   Required capabilities: {', '.join(required)}")
    else:
        print("   Required capabilities: (none specified)")

    print("\n🤖 Recommended Agents (ranked):\n")

    if not suggestions:
        print("   No agents available")
        return

    for i, suggestion in enumerate(suggestions, 1):
        agent_id = suggestion["agent_id"]
        match_score = suggestion["match_score"]
        recommendation = suggestion["recommendation"]

        # Status emoji
        if match_score == 1.0:
            emoji = "✅"
        elif match_score >= 0.7:
            emoji = "✓"
        elif match_score > 0:
            emoji = "⚠️"
        else:
            emoji = "❌"

        print(f"   {i}. {emoji} {agent_id:15} - {recommendation}")

        # Show capability details if not perfect match
        if match_score < 1.0 and match_score > 0:
            if suggestion["matched_capabilities"]:
                print(f"      Has: {', '.join(suggestion['matched_capabilities'])}")
            if suggestion["missing_capabilities"]:
                print(f"      Missing: {', '.join(suggestion['missing_capabilities'])}")

    print(
        "\n💡 This is an advisory suggestion. Human makes final claim decision per Article VI."
    )


def main():
    """Main entry point for claim-suggest command."""
    if len(sys.argv) < 2:
        print("Usage: python3 claim_suggest.py <packet-id>")
        print("       python3 .governance/wbs_cli.py claim-suggest <packet-id>")
        sys.exit(1)

    packet_id = sys.argv[1]

    # Load packet
    wbs = load_wbs()
    packet = get_packet_by_id(packet_id, wbs)

    if not packet:
        print(f"❌ Packet {packet_id} not found in WBS definition")
        sys.exit(1)

    # Get suggestions
    suggestions = suggest_agents_for_packet(packet_id, verbose=True)

    # Print results
    print_suggestions(packet_id, suggestions, packet)


if __name__ == "__main__":
    main()
