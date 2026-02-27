#!/usr/bin/env python3
"""
Guided WBS planner helpers.

This module supports both:
1) interactive planning (prompt-driven), and
2) non-interactive planning from a JSON spec (for tests/automation).
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple


def _split_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.replace("|", ",")
        return [item.strip() for item in text.split(",") if item.strip()]
    return []


def _slug(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "-", str(value or "").strip())
    token = re.sub(r"-{2,}", "-", token).strip("-")
    return token.upper()


def _unique_id(base: str, used: set, fallback: str) -> str:
    candidate = _slug(base) or fallback
    if candidate not in used:
        return candidate
    n = 2
    while f"{candidate}-{n}" in used:
        n += 1
    return f"{candidate}-{n}"


def normalize_area_id(raw: Any, area_index: int, used: set) -> str:
    token = str(raw or "").strip()
    if re.fullmatch(r"\d+", token):
        token = f"{int(token)}.0"
    elif token and re.fullmatch(r"\d+\.0", token):
        token = token
    elif not token:
        token = f"{area_index}.0"
    else:
        token = _slug(token)
    area_id = _unique_id(token, used, fallback=f"{area_index}.0")
    used.add(area_id)
    return area_id


def normalize_packet_id(raw: Any, area_index: int, packet_index: int, used: set) -> str:
    token = _slug(str(raw or ""))
    fallback = f"PKT-{area_index:02d}-{packet_index:02d}"
    packet_id = _unique_id(token, used, fallback=fallback)
    used.add(packet_id)
    return packet_id


def detect_cycle(dependencies: Dict[str, List[str]]) -> List[str]:
    visited = set()
    rec_stack = set()
    path: List[str] = []

    def dfs(node: str) -> List[str]:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        for neighbor in dependencies.get(node, []):
            if neighbor not in visited:
                found = dfs(neighbor)
                if found:
                    return found
            elif neighbor in rec_stack:
                i = path.index(neighbor)
                return path[i:] + [neighbor]
        path.pop()
        rec_stack.remove(node)
        return []

    for node in dependencies:
        if node not in visited:
            cycle = dfs(node)
            if cycle:
                return cycle
    return []


def _normalize_dependency_token(token: str, aliases: Dict[str, str]) -> str:
    dep = str(token or "").strip()
    if not dep:
        return dep
    for key in (dep, dep.lower(), _slug(dep)):
        if key in aliases:
            return aliases[key]
    return dep


def _register_alias(aliases: Dict[str, str], raw: str, normalized: str) -> None:
    aliases[normalized] = normalized
    if not raw:
        return
    aliases[raw] = normalized
    aliases[raw.lower()] = normalized
    aliases[_slug(raw)] = normalized


def _coerce_to_plan_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accept either:
    1) planner spec shape (areas with nested packets), or
    2) WBS-like shape (top-level packets/areas/dependencies), and coerce to planner spec.
    """
    if not isinstance(spec, dict):
        return {}

    area_specs = spec.get("work_areas")
    has_nested_packets = isinstance(area_specs, list) and any(
        isinstance(area, dict) and isinstance(area.get("packets"), list) for area in area_specs
    )
    if has_nested_packets:
        return spec

    if not isinstance(area_specs, list) or not isinstance(spec.get("packets"), list):
        return spec

    area_map: Dict[str, Dict[str, Any]] = {}
    area_order: List[str] = []
    for area in area_specs:
        if not isinstance(area, dict):
            continue
        aid = str(area.get("id") or "").strip()
        if not aid:
            continue
        entry = {
            "id": aid,
            "title": str(area.get("title") or aid).strip(),
            "description": str(area.get("description") or "").strip(),
            "packets": [],
        }
        area_map[aid] = entry
        area_order.append(aid)

    dependencies = spec.get("dependencies", {})
    if not isinstance(dependencies, dict):
        dependencies = {}

    for pkt in spec.get("packets", []):
        if not isinstance(pkt, dict):
            continue
        aid = str(pkt.get("area_id") or "").strip() or "1.0"
        if aid not in area_map:
            area_map[aid] = {"id": aid, "title": aid, "description": "", "packets": []}
            area_order.append(aid)
        packet_entry = {
            "id": pkt.get("id"),
            "wbs_ref": pkt.get("wbs_ref"),
            "title": pkt.get("title"),
            "scope": pkt.get("scope"),
        }
        dep_list = dependencies.get(str(pkt.get("id") or "").strip(), [])
        if isinstance(dep_list, list) and dep_list:
            packet_entry["depends_on"] = dep_list
        for key in ("required_capabilities", "import_confidence", "import_notes", "import_requires_review"):
            if key in pkt:
                packet_entry[key] = pkt.get(key)
        area_map[aid]["packets"].append(packet_entry)

    coerced_areas = [area_map[aid] for aid in area_order]
    coerced = dict(spec)
    metadata = spec.get("metadata", {})
    if isinstance(metadata, dict):
        for key in ("project_name", "approved_by", "approved_at", "planning_source", "planning_generated_at"):
            if key not in coerced and str(metadata.get(key) or "").strip():
                coerced[key] = metadata.get(key)
    coerced["work_areas"] = coerced_areas
    return coerced


def import_markdown_to_spec(markdown_path: Path) -> Dict[str, Any]:
    """
    Experimental markdown importer.
    Produces a planner spec with explicit confidence markers for each inferred packet.
    """
    content = Path(markdown_path).read_text()
    lines = content.splitlines()
    stem = Path(markdown_path).stem.replace("-", " ").replace("_", " ").strip() or "Imported Project"

    project_name = stem
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            project_name = stripped[2:].strip() or project_name
            break

    areas: List[Dict[str, Any]] = []
    warnings: List[str] = []
    current_area: Dict[str, Any] = {}

    def ensure_area(default_title: str = "Imported Scope") -> Dict[str, Any]:
        nonlocal current_area
        if current_area:
            return current_area
        area = {"id": "", "title": default_title, "description": "", "packets": []}
        areas.append(area)
        current_area = area
        return area

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("# "):
            continue

        if stripped.startswith("## "):
            title = stripped[3:].strip() or f"Area {len(areas) + 1}"
            current_area = {"id": "", "title": title, "description": "", "packets": []}
            areas.append(current_area)
            continue

        if stripped.startswith("### "):
            area = ensure_area()
            title = stripped[4:].strip()
            if not title:
                continue
            pkt = {
                "id": title,
                "title": title,
                "scope": f"Implement {title}. Output: define deliverable.",
                "import_confidence": "medium",
                "import_notes": [f"Imported from heading on line {line_no}."],
            }
            area["packets"].append(pkt)
            continue

        bullet_match = re.match(r"^[-*]\s+(\[[ xX]\]\s+)?(.+)$", stripped)
        if not bullet_match:
            continue

        area = ensure_area()
        checkbox = bool(bullet_match.group(1))
        raw_body = bullet_match.group(2).strip()
        if not raw_body:
            continue

        dep_tokens: List[str] = []
        dep_match = re.search(r"(?i)\b(depends on|after)\b(.+)$", raw_body)
        title_body = raw_body
        if dep_match:
            dep_expr = dep_match.group(2).strip(" .:")
            dep_expr = re.split(r"(?i)\boutput\s*:", dep_expr, maxsplit=1)[0].strip(" .:")
            dep_tokens = [token.strip() for token in re.split(r",| and ", dep_expr) if token.strip()]
            title_body = raw_body[: dep_match.start()].strip(" .:-")

        has_output_clause = "output:" in raw_body.lower()
        if has_output_clause:
            title_body = re.split(r"(?i)\boutput\s*:", title_body, maxsplit=1)[0].strip(" .:-")
        if not title_body:
            title_body = raw_body

        confidence = "low"
        notes = [f"Imported from bullet on line {line_no}."]
        requires_review = True
        if checkbox:
            confidence = "medium"
            requires_review = False
            notes.append("Checkbox task marker found.")
        if has_output_clause:
            confidence = "high"
            requires_review = False
            notes.append("Output clause detected in source line.")
        if confidence == "low":
            notes.append("Ambiguous free-form bullet; manual correction recommended.")
            warnings.append(
                f"line {line_no}: low-confidence mapping for '{title_body}'. "
                "Action: refine packet title/scope and dependency links."
            )

        pkt = {
            "id": title_body,
            "title": title_body,
            "scope": raw_body if has_output_clause else f"{title_body}. Output: define deliverable.",
            "import_confidence": confidence,
            "import_notes": notes,
            "import_requires_review": requires_review,
        }
        if dep_tokens:
            pkt["depends_on"] = dep_tokens
        area["packets"].append(pkt)

    if not areas:
        warnings.append(
            "No sections/tasks were parsed from markdown. Action: add '## Area' headings and bullet tasks."
        )
        areas = [
            {
                "id": "1.0",
                "title": "Imported Scope",
                "description": "No parseable task structure detected; manual fill required.",
                "packets": [],
            }
        ]

    return {
        "project_name": project_name,
        "approved_by": os.environ.get("USER", "planner"),
        "work_areas": areas,
        "import_experimental": True,
        "import_source": str(Path(markdown_path)),
        "import_warnings": warnings,
    }


def collect_import_review_warnings(definition: Dict[str, Any]) -> List[str]:
    warnings = [str(item) for item in definition.get("import_warnings", []) if str(item).strip()]
    for pkt in definition.get("packets", []):
        if not isinstance(pkt, dict):
            continue
        pid = str(pkt.get("id") or "<unknown>").strip()
        confidence = str(pkt.get("import_confidence") or "").strip().lower()
        requires_review = bool(pkt.get("import_requires_review"))
        if confidence == "low" or requires_review:
            warnings.append(
                f"{pid}: import confidence '{confidence or 'unknown'}' requires manual review."
            )
    # Preserve order but remove duplicates.
    return list(dict.fromkeys(warnings))


def build_definition(spec: Dict[str, Any]) -> Dict[str, Any]:
    spec = _coerce_to_plan_spec(spec)

    project_name = str(spec.get("project_name") or "Planned Project").strip()
    approved_by = str(spec.get("approved_by") or os.environ.get("USER", "planner")).strip()
    approved_at = str(spec.get("approved_at") or datetime.now().isoformat()).strip()

    used_area_ids = set()
    used_packet_ids = set()
    aliases: Dict[str, str] = {}
    pending_deps: Dict[str, List[str]] = {}

    work_areas: List[Dict[str, Any]] = []
    packets: List[Dict[str, Any]] = []

    area_specs = spec.get("work_areas", [])
    if not isinstance(area_specs, list):
        area_specs = []

    for area_index, area in enumerate(area_specs, start=1):
        if not isinstance(area, dict):
            continue

        area_id = normalize_area_id(area.get("id"), area_index, used_area_ids)
        area_title = str(area.get("title") or f"Area {area_index}").strip()
        area_desc = str(area.get("description") or "").strip()
        area_entry = {"id": area_id, "title": area_title}
        if area_desc:
            area_entry["description"] = area_desc
        work_areas.append(area_entry)

        packet_specs = area.get("packets", [])
        if not isinstance(packet_specs, list):
            packet_specs = []

        for packet_index, pkt in enumerate(packet_specs, start=1):
            if not isinstance(pkt, dict):
                continue

            raw_packet_id = str(pkt.get("id") or "").strip()
            packet_id = normalize_packet_id(raw_packet_id, area_index, packet_index, used_packet_ids)
            _register_alias(aliases, raw_packet_id, packet_id)

            title = str(pkt.get("title") or f"Packet {area_index}.{packet_index}").strip()
            _register_alias(aliases, title, packet_id)
            scope = str(pkt.get("scope") or "").strip()
            if not scope:
                scope = f"Implement {title}. Output: evidence artifact."

            wbs_ref = str(pkt.get("wbs_ref") or f"{area_index}.{packet_index}").strip()
            packet_entry = {
                "id": packet_id,
                "wbs_ref": wbs_ref,
                "area_id": area_id,
                "title": title,
                "scope": scope,
            }
            if isinstance(pkt.get("required_capabilities"), list):
                caps = [str(cap).strip() for cap in pkt.get("required_capabilities", []) if str(cap).strip()]
                if caps:
                    packet_entry["required_capabilities"] = caps
            confidence = str(pkt.get("import_confidence") or "").strip().lower()
            if confidence in {"high", "medium", "low"}:
                packet_entry["import_confidence"] = confidence
            if "import_requires_review" in pkt:
                packet_entry["import_requires_review"] = bool(pkt.get("import_requires_review"))
            if isinstance(pkt.get("import_notes"), list):
                notes = [str(note).strip() for note in pkt.get("import_notes", []) if str(note).strip()]
                if notes:
                    packet_entry["import_notes"] = notes
            packets.append(packet_entry)

            dep_tokens = []
            dep_tokens.extend(_split_list(pkt.get("depends_on")))
            dep_tokens.extend(_split_list(pkt.get("dependencies")))
            pending_deps[packet_id] = dep_tokens

    # Top-level dependencies can reference either raw ids or normalized ids.
    top_level_deps = spec.get("dependencies", {})
    if isinstance(top_level_deps, dict):
        for raw_packet_id, raw_dep_list in top_level_deps.items():
            packet_id = _normalize_dependency_token(str(raw_packet_id or ""), aliases)
            if not packet_id:
                continue
            pending_deps.setdefault(packet_id, [])
            pending_deps[packet_id].extend(_split_list(raw_dep_list))

    dependencies: Dict[str, List[str]] = {}
    for packet_id, dep_tokens in pending_deps.items():
        cleaned: List[str] = []
        for token in dep_tokens:
            dep_id = _normalize_dependency_token(token, aliases)
            if dep_id and dep_id not in cleaned:
                cleaned.append(dep_id)
        if cleaned:
            dependencies[packet_id] = cleaned

    metadata = {
        "project_name": project_name,
        "approved_by": approved_by,
        "approved_at": approved_at,
    }
    planning_source = str(spec.get("planning_source") or "").strip()
    if planning_source:
        metadata["planning_source"] = planning_source
    planning_generated_at = str(spec.get("planning_generated_at") or "").strip()
    if planning_generated_at:
        metadata["planning_generated_at"] = planning_generated_at

    output = {
        "metadata": metadata,
        "work_areas": work_areas,
        "packets": packets,
        "dependencies": dependencies,
    }
    if "import_experimental" in spec:
        output["import_experimental"] = bool(spec.get("import_experimental"))
    if str(spec.get("import_source") or "").strip():
        output["import_source"] = str(spec.get("import_source")).strip()
    if isinstance(spec.get("import_warnings"), list):
        output["import_warnings"] = [
            str(item).strip() for item in spec.get("import_warnings", []) if str(item).strip()
        ]
    return output


def validate_definition(definition: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    metadata = definition.get("metadata", {})
    if not isinstance(metadata, dict):
        errors.append("metadata must be an object")
    else:
        for key in ("project_name", "approved_by", "approved_at"):
            if not str(metadata.get(key) or "").strip():
                errors.append(f"metadata.{key} is required")

    areas = definition.get("work_areas", [])
    if not isinstance(areas, list) or not areas:
        errors.append("work_areas must contain at least one area")

    packets = definition.get("packets", [])
    if not isinstance(packets, list) or not packets:
        errors.append("packets must contain at least one packet")

    area_ids = []
    for i, area in enumerate(areas):
        if not isinstance(area, dict):
            errors.append(f"work_areas[{i}] must be an object")
            continue
        aid = str(area.get("id") or "").strip()
        title = str(area.get("title") or "").strip()
        if not aid:
            errors.append(f"work_areas[{i}].id is required")
        if not title:
            errors.append(f"work_areas[{i}].title is required")
        area_ids.append(aid)

    known_area_ids = {aid for aid in area_ids if aid}

    packet_ids = []
    for i, pkt in enumerate(packets):
        if not isinstance(pkt, dict):
            errors.append(f"packets[{i}] must be an object")
            continue
        required_fields = ("id", "wbs_ref", "area_id", "title", "scope")
        for key in required_fields:
            if not str(pkt.get(key) or "").strip():
                errors.append(f"packets[{i}].{key} is required")
        pid = str(pkt.get("id") or "").strip()
        area_id = str(pkt.get("area_id") or "").strip()
        if pid:
            packet_ids.append(pid)
        if area_id and area_id not in known_area_ids:
            errors.append(f"packet '{pid or f'index {i}'}' references unknown area_id '{area_id}'")
        confidence = str(pkt.get("import_confidence") or "").strip().lower()
        if confidence and confidence not in {"high", "medium", "low"}:
            errors.append(f"packet '{pid or f'index {i}'}' has invalid import_confidence '{confidence}'")

    if len(packet_ids) != len(set(packet_ids)):
        errors.append("packet ids must be unique")

    deps = definition.get("dependencies", {})
    if not isinstance(deps, dict):
        errors.append("dependencies must be an object")
        deps = {}

    known_packets = set(packet_ids)
    normalized_deps: Dict[str, List[str]] = {}
    for packet_id, dep_list in deps.items():
        pid = str(packet_id or "").strip()
        if pid and pid not in known_packets:
            errors.append(
                f"Dependency target '{pid}' is not a known packet id. "
                "Action: use an existing packet id or remove the dependency mapping."
            )
        if not isinstance(dep_list, list):
            errors.append(f"dependencies['{pid}'] must be an array")
            continue
        normalized_deps[pid] = []
        for dep in dep_list:
            dep_id = str(dep or "").strip()
            if not dep_id:
                continue
            if dep_id not in known_packets:
                errors.append(
                    f"Packet '{pid}' depends on unknown packet '{dep_id}'. "
                    "Action: use an existing packet id or remove the dependency."
                )
            if dep_id == pid:
                errors.append(
                    f"Packet '{pid}' depends on itself. Action: remove the self-reference."
                )
            normalized_deps[pid].append(dep_id)

    cycle = detect_cycle(normalized_deps)
    if cycle:
        errors.append(
            "Dependency cycle detected: "
            + " -> ".join(cycle)
            + ". Action: remove at least one dependency edge in this cycle."
        )

    return errors


def load_plan_spec(path: Path) -> Dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict):
        raise ValueError("Planner spec must be a JSON object")
    return payload


def write_definition(definition: Dict[str, Any], output_path: Path) -> Path:
    target = Path(output_path).expanduser()
    if not target.is_absolute():
        target = (Path.cwd() / target).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(definition, indent=2) + "\n")
    return target


def _ask(
    prompt: str,
    input_fn: Callable[[str], str],
    default: str = "",
    required: bool = False,
    print_fn: Callable[[str], None] = print,
) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input_fn(f"{prompt}{suffix}: ").strip()
        if not value:
            value = default
        if required and not value.strip():
            print_fn("Value required.")
            continue
        return value.strip()


def _ask_int(
    prompt: str,
    input_fn: Callable[[str], str],
    default: int,
    min_value: int = 1,
    max_value: int = 999,
    print_fn: Callable[[str], None] = print,
) -> int:
    while True:
        raw = _ask(prompt, input_fn=input_fn, default=str(default), required=True, print_fn=print_fn)
        try:
            value = int(raw)
        except ValueError:
            print_fn("Enter a valid integer.")
            continue
        if value < min_value or value > max_value:
            print_fn(f"Enter an integer between {min_value} and {max_value}.")
            continue
        return value


def prompt_plan_spec(
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
    default_actor: str = "",
) -> Dict[str, Any]:
    print_fn("Guided WBS Planner")
    print_fn("Provide project metadata, work areas, packets, and dependencies.")
    print_fn("")

    actor = (default_actor or os.environ.get("USER", "planner")).strip() or "planner"
    project_name = _ask("Project name", input_fn=input_fn, required=True, print_fn=print_fn)
    approved_by = _ask("Approved by", input_fn=input_fn, default=actor, required=True, print_fn=print_fn)
    area_count = _ask_int("Number of work areas", input_fn=input_fn, default=3, min_value=1, max_value=20, print_fn=print_fn)

    spec: Dict[str, Any] = {
        "project_name": project_name,
        "approved_by": approved_by,
        "work_areas": [],
    }

    for area_index in range(1, area_count + 1):
        print_fn("")
        print_fn(f"Area {area_index}/{area_count}")
        area_id = _ask("Area id", input_fn=input_fn, default=f"{area_index}.0", print_fn=print_fn)
        title = _ask("Area title", input_fn=input_fn, required=True, print_fn=print_fn)
        desc = _ask("Area description (optional)", input_fn=input_fn, default="", print_fn=print_fn)
        packet_count = _ask_int(
            "Number of packets in this area",
            input_fn=input_fn,
            default=3,
            min_value=1,
            max_value=50,
            print_fn=print_fn,
        )

        area_entry: Dict[str, Any] = {"id": area_id, "title": title, "packets": []}
        if desc:
            area_entry["description"] = desc

        for packet_index in range(1, packet_count + 1):
            print_fn("")
            print_fn(f"Packet {packet_index}/{packet_count} in area {area_index}")
            default_pid = f"PKT-{area_index:02d}-{packet_index:02d}"
            pid = _ask("Packet id", input_fn=input_fn, default=default_pid, print_fn=print_fn)
            packet_title = _ask("Packet title", input_fn=input_fn, required=True, print_fn=print_fn)
            packet_scope = _ask("Packet scope", input_fn=input_fn, required=True, print_fn=print_fn)
            dep_raw = _ask(
                "Depends on packet ids (comma-separated, optional)",
                input_fn=input_fn,
                default="",
                print_fn=print_fn,
            )
            pkt = {"id": pid, "title": packet_title, "scope": packet_scope}
            deps = _split_list(dep_raw)
            if deps:
                pkt["depends_on"] = deps
            area_entry["packets"].append(pkt)

        spec["work_areas"].append(area_entry)

    return spec
