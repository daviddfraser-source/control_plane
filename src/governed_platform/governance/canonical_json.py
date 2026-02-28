import json
import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any


class CanonicalJsonError(ValueError):
    """Raised when a value cannot be canonicalized."""


def _normalize_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _normalize(value: Any) -> Any:
    if isinstance(value, datetime):
        return _normalize_datetime(value)
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, tuple):
        return [_normalize(v) for v in value]
    if isinstance(value, Decimal):
        # Preserve Decimal intent via string to avoid binary float drift.
        return str(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise CanonicalJsonError("NaN/Infinity are not allowed in canonical JSON")
        return value
    return value


def canonical_json_dumps(value: Any) -> str:
    """Deterministic JSON serializer for DCL hashing."""
    normalized = _normalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )

