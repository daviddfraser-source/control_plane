#!/usr/bin/env python3
"""
Tag-based dependency resolution for WBS packets.

Implements tag index building and tag-to-packet-ID expansion per
docs/orchestration/tag-dependencies-contract.md (ORCH-009, ORCH-010).

Constitutional compliance:
- Article II §1: Atomic Transitions - expansion happens at load time, logged
- Article IV §1: State Integrity - expanded_dependencies provides audit trail
"""

import re
from typing import Dict, List, Set
import logging

LOGGER = logging.getLogger(__name__)

# Tag syntax validation (from contract)
TAG_PATTERN = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
TAG_REF_PATTERN = re.compile(r'^tag:([a-z0-9]+(-[a-z0-9]+)*)$')


def validate_tag_name(tag_name: str) -> bool:
    """
    Validate tag name matches contract pattern: lowercase alphanumeric with hyphens.

    Args:
        tag_name: Tag name without 'tag:' prefix

    Returns:
        True if valid, False otherwise
    """
    return bool(TAG_PATTERN.match(tag_name))


def is_tag_reference(dependency: str) -> bool:
    """
    Check if dependency string is a tag reference (starts with 'tag:').

    Args:
        dependency: Dependency string (e.g., 'tag:frontend' or 'PACKET-001')

    Returns:
        True if it's a tag reference, False if it's a packet ID
    """
    return dependency.startswith('tag:')


def extract_tag_name(tag_ref: str) -> str:
    """
    Extract tag name from tag reference (removes 'tag:' prefix).

    Args:
        tag_ref: Tag reference string (e.g., 'tag:frontend')

    Returns:
        Tag name (e.g., 'frontend')

    Raises:
        ValueError: If tag_ref doesn't match tag reference pattern
    """
    match = TAG_REF_PATTERN.match(tag_ref)
    if not match:
        raise ValueError(f"Invalid tag reference: {tag_ref}")
    return match.group(1)


class TagIndex:
    """
    Index of packet tags for efficient tag-to-packet-ID resolution.

    Builds an index mapping tag names to lists of packet IDs.
    """

    def __init__(self):
        """Initialize empty tag index."""
        self._index: Dict[str, List[str]] = {}

    def build(self, packets: List[Dict]) -> None:
        """
        Build tag index from packet list.

        Args:
            packets: List of packet definitions from wbs.json

        Example:
            packets = [
                {"id": "FRONT-001", "tags": ["frontend", "ui"]},
                {"id": "FRONT-002", "tags": ["frontend"]},
                {"id": "BACK-001", "tags": ["backend"]}
            ]
            index.build(packets)
            # index['frontend'] = ['FRONT-001', 'FRONT-002']
            # index['ui'] = ['FRONT-001']
            # index['backend'] = ['BACK-001']
        """
        self._index.clear()

        for packet in packets:
            packet_id = packet.get('id')
            tags = packet.get('tags', [])

            if not packet_id:
                LOGGER.warning(f"Skipping packet without ID: {packet}")
                continue

            for tag in tags:
                if not validate_tag_name(tag):
                    LOGGER.warning(f"Invalid tag '{tag}' in packet {packet_id}, skipping")
                    continue

                if tag not in self._index:
                    self._index[tag] = []

                self._index[tag].append(packet_id)

        LOGGER.info(f"Tag index built: {len(self._index)} tags, {len(packets)} packets")

    def resolve(self, tag_name: str) -> List[str]:
        """
        Resolve tag name to list of packet IDs.

        Args:
            tag_name: Tag name (without 'tag:' prefix)

        Returns:
            List of packet IDs with that tag (empty list if tag not found)
        """
        return self._index.get(tag_name, [])

    def all_tags(self) -> List[str]:
        """
        Get list of all tag names in index.

        Returns:
            Sorted list of tag names
        """
        return sorted(self._index.keys())

    def get_packet_tags(self, tag_name: str) -> List[str]:
        """
        Get all packet IDs for a given tag (alias for resolve).

        Args:
            tag_name: Tag name

        Returns:
            List of packet IDs
        """
        return self.resolve(tag_name)


class DependencyExpander:
    """
    Expands tag-based dependencies to explicit packet IDs.

    Implements expansion rules from tag-dependencies-contract.md:
    - Tags expand to all packets with that tag
    - Multiple tags are additive (union)
    - Duplicates are eliminated
    - Tags and explicit IDs can be mixed
    """

    def __init__(self, tag_index: TagIndex):
        """
        Initialize dependency expander with tag index.

        Args:
            tag_index: Built TagIndex for resolving tags
        """
        self.tag_index = tag_index

    def expand(self, dependencies: List[str]) -> List[str]:
        """
        Expand dependency list containing tags and/or packet IDs.

        Args:
            dependencies: List of dependencies (may include 'tag:name' references)

        Returns:
            List of explicit packet IDs (tags expanded, duplicates removed)

        Example:
            dependencies = ['tag:frontend', 'CORE-001', 'tag:backend']
            expanded = expander.expand(dependencies)
            # expanded = ['FRONT-001', 'FRONT-002', 'CORE-001', 'BACK-001']
        """
        expanded: List[str] = []
        seen: Set[str] = set()

        for dep in dependencies:
            if is_tag_reference(dep):
                # Expand tag reference
                try:
                    tag_name = extract_tag_name(dep)
                    packet_ids = self.tag_index.resolve(tag_name)

                    if not packet_ids:
                        LOGGER.warning(f"Tag '{tag_name}' matches no packets")

                    for packet_id in packet_ids:
                        if packet_id not in seen:
                            expanded.append(packet_id)
                            seen.add(packet_id)

                except ValueError as e:
                    LOGGER.error(f"Invalid tag reference: {dep} - {e}")
            else:
                # Explicit packet ID
                if dep not in seen:
                    expanded.append(dep)
                    seen.add(dep)

        return expanded

    def expand_all_dependencies(
        self, dependencies: Dict[str, List[str]], verbose: bool = True
    ) -> Dict[str, List[str]]:
        """
        Expand all dependencies in a dependencies dict.

        Args:
            dependencies: Dict mapping packet_id -> list of dependencies
            verbose: If True, log expansion details

        Returns:
            Dict mapping packet_id -> expanded dependency list

        Example:
            dependencies = {
                "DEPLOY-001": ["tag:frontend", "tag:backend"],
                "TEST-001": ["DEPLOY-001"]
            }
            expanded = expander.expand_all_dependencies(dependencies)
            # expanded = {
            #     "DEPLOY-001": ["FRONT-001", "FRONT-002", "BACK-001"],
            #     "TEST-001": ["DEPLOY-001"]
            # }
        """
        expanded_deps: Dict[str, List[str]] = {}

        for packet_id, deps in dependencies.items():
            expanded = self.expand(deps)
            expanded_deps[packet_id] = expanded

            if verbose:
                # Log expansion if tags were used
                has_tags = any(is_tag_reference(d) for d in deps)
                if has_tags:
                    LOGGER.info(
                        f"Packet {packet_id}: {deps} → {expanded} ({len(expanded)} packets)"
                    )

        return expanded_deps


def detect_circular_dependencies(dependencies: Dict[str, List[str]]) -> List[str]:
    """
    Detect circular dependencies in expanded dependency graph.

    Args:
        dependencies: Dict mapping packet_id -> list of dependency packet IDs

    Returns:
        List representing a cycle if found (e.g., ['A', 'B', 'C', 'A']),
        or empty list if no cycle

    Example:
        dependencies = {
            "A": ["B"],
            "B": ["C"],
            "C": ["A"]
        }
        cycle = detect_circular_dependencies(dependencies)
        # cycle = ['A', 'B', 'C', 'A']
    """
    # DFS-based cycle detection
    visited = set()
    rec_stack = set()
    path = []

    def visit(node):
        if node in rec_stack:
            # Found cycle - return path from cycle start
            cycle_start = path.index(node)
            return path[cycle_start:] + [node]

        if node in visited:
            return None

        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for dep in dependencies.get(node, []):
            cycle = visit(dep)
            if cycle:
                return cycle

        path.pop()
        rec_stack.remove(node)
        return None

    # Check each node (in case graph is disconnected)
    for node in dependencies.keys():
        if node not in visited:
            cycle = visit(node)
            if cycle:
                return cycle

    return []


def expand_dependencies_with_validation(
    packets: List[Dict], dependencies: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """
    Expand tag-based dependencies with full validation.

    This is the main entry point for tag expansion during WBS initialization.

    Args:
        packets: List of packet definitions from wbs.json
        dependencies: Original dependencies dict (may contain tags)

    Returns:
        Expanded dependencies dict (only packet IDs, no tags)

    Raises:
        ValueError: If circular dependency detected after expansion

    Example:
        packets = [
            {"id": "FRONT-001", "tags": ["frontend"]},
            {"id": "BACK-001", "tags": ["backend"]}
        ]
        dependencies = {
            "DEPLOY-001": ["tag:frontend", "tag:backend"]
        }
        expanded = expand_dependencies_with_validation(packets, dependencies)
        # expanded = {"DEPLOY-001": ["FRONT-001", "BACK-001"]}
    """
    LOGGER.info("Expanding tag-based dependencies...")

    # Build tag index
    tag_index = TagIndex()
    tag_index.build(packets)

    # Expand dependencies
    expander = DependencyExpander(tag_index)
    expanded_deps = expander.expand_all_dependencies(dependencies, verbose=True)

    # Validate no circular dependencies after expansion
    cycle = detect_circular_dependencies(expanded_deps)
    if cycle:
        cycle_str = ' → '.join(cycle)
        raise ValueError(f"Circular dependency detected: {cycle_str}")

    LOGGER.info(f"Dependency expansion complete: {len(expanded_deps)} packets with dependencies")

    return expanded_deps
