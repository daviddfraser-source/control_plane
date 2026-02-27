from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from governed_platform.governance.file_lock import atomic_write_json


RISK_REGISTER_VERSION = "1.0"

LIKELIHOOD_VALUES = {"low", "medium", "high"}
IMPACT_VALUES = {"low", "medium", "high", "critical"}
CONFIDENCE_VALUES = {"low", "medium", "high"}
RISK_STATUS_VALUES = {"open", "mitigated", "accepted", "transferred"}


def default_register() -> Dict[str, Any]:
    now = datetime.now().isoformat()
    return {
        "version": RISK_REGISTER_VERSION,
        "created_at": now,
        "updated_at": now,
        "risks": [],
    }


def load_register(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return default_register()
    with open(path) as f:
        payload = json.load(f)
    payload.setdefault("version", RISK_REGISTER_VERSION)
    payload.setdefault("created_at", datetime.now().isoformat())
    payload.setdefault("updated_at", datetime.now().isoformat())
    payload.setdefault("risks", [])
    if not isinstance(payload.get("risks"), list):
        payload["risks"] = []
    return payload


def save_register(path: Path, payload: Dict[str, Any]) -> None:
    payload["version"] = payload.get("version", RISK_REGISTER_VERSION)
    payload["updated_at"] = datetime.now().isoformat()
    atomic_write_json(path, payload)


def _next_risk_id(payload: Dict[str, Any]) -> str:
    max_num = 0
    for entry in payload.get("risks", []):
        rid = str(entry.get("risk_id") or "")
        if rid.startswith("RR-"):
            tail = rid[3:]
            if tail.isdigit():
                max_num = max(max_num, int(tail))
    return f"RR-{max_num + 1:04d}"


def _normalize_token(value: str) -> str:
    return str(value or "").strip().lower()


def normalize_likelihood(value: str) -> str:
    token = _normalize_token(value)
    if token not in LIKELIHOOD_VALUES:
        raise ValueError(f"Invalid likelihood: {value!r} (use low|medium|high)")
    return token


def normalize_impact(value: str) -> str:
    token = _normalize_token(value)
    if token not in IMPACT_VALUES:
        raise ValueError(f"Invalid impact: {value!r} (use low|medium|high|critical)")
    return token


def normalize_confidence(value: str) -> str:
    token = _normalize_token(value)
    if token not in CONFIDENCE_VALUES:
        raise ValueError(f"Invalid confidence: {value!r} (use low|medium|high)")
    return token


def normalize_risk_status(value: str) -> str:
    token = _normalize_token(value)
    if token not in RISK_STATUS_VALUES:
        raise ValueError(f"Invalid risk status: {value!r} (use open|mitigated|accepted|transferred)")
    return token


def normalize_risk_input(entry: Dict[str, Any], packet_id: str, actor: str) -> Dict[str, Any]:
    if not isinstance(entry, dict):
        raise ValueError("Risk entry must be an object")
    description = str(entry.get("description") or "").strip()
    if not description:
        raise ValueError("Risk entry missing required field: description")

    item_packet = str(entry.get("packet_id") or packet_id or "").strip()
    if not item_packet:
        raise ValueError("Risk entry missing packet_id")

    declared_by = str(entry.get("declared_by") or actor or "").strip()
    if not declared_by:
        raise ValueError("Risk entry missing declared_by")

    return {
        "packet_id": item_packet,
        "description": description,
        "likelihood": normalize_likelihood(entry.get("likelihood", "medium")),
        "impact": normalize_impact(entry.get("impact", "medium")),
        "confidence": normalize_confidence(entry.get("confidence", "medium")),
        "status": normalize_risk_status(entry.get("status", "open")),
        "declared_by": declared_by,
        "declared_at": datetime.now().isoformat(),
        "notes": str(entry.get("notes") or "").strip() or None,
    }


def add_risks(path: Path, packet_id: str, actor: str, entries: List[Dict[str, Any]]) -> List[str]:
    payload = load_register(path)
    risk_ids: List[str] = []
    for raw in entries:
        item = normalize_risk_input(raw, packet_id=packet_id, actor=actor)
        item["risk_id"] = _next_risk_id(payload)
        payload.setdefault("risks", []).append(item)
        risk_ids.append(item["risk_id"])
    save_register(path, payload)
    return risk_ids


def list_risks(path: Path, packet_id: str = "", status: str = "", limit: int = 0) -> List[Dict[str, Any]]:
    payload = load_register(path)
    out = []
    packet_filter = str(packet_id or "").strip()
    status_filter = _normalize_token(status)
    for risk in payload.get("risks", []):
        if packet_filter and str(risk.get("packet_id") or "").strip() != packet_filter:
            continue
        if status_filter and _normalize_token(risk.get("status")) != status_filter:
            continue
        out.append(risk)
    if limit > 0:
        out = out[-limit:]
    return out


def get_risk(path: Path, risk_id: str) -> Dict[str, Any]:
    token = str(risk_id or "").strip()
    for risk in load_register(path).get("risks", []):
        if str(risk.get("risk_id") or "").strip() == token:
            return risk
    return {}


def update_risk_status(path: Path, risk_id: str, status: str, actor: str, notes: str = "") -> Tuple[bool, str]:
    token = str(risk_id or "").strip()
    normalized_status = normalize_risk_status(status)
    payload = load_register(path)
    for risk in payload.get("risks", []):
        if str(risk.get("risk_id") or "").strip() != token:
            continue
        risk["status"] = normalized_status
        risk["updated_at"] = datetime.now().isoformat()
        risk["updated_by"] = str(actor or "").strip() or None
        if notes:
            risk["resolution_notes"] = notes
        save_register(path, payload)
        return True, f"{token} updated to {normalized_status}"
    return False, f"Risk {token} not found"


def risk_summary(path: Path) -> Dict[str, Any]:
    payload = load_register(path)
    counts: Dict[str, int] = {}
    for risk in payload.get("risks", []):
        status = _normalize_token(risk.get("status") or "open")
        counts[status] = counts.get(status, 0) + 1
    open_count = counts.get("open", 0)
    return {
        "version": payload.get("version", RISK_REGISTER_VERSION),
        "total": len(payload.get("risks", [])),
        "open": open_count,
        "counts": counts,
    }
