import math
import unittest
from datetime import datetime, timezone

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from governed_platform.governance.canonical_json import canonical_json_dumps, CanonicalJsonError


class CanonicalJsonTests(unittest.TestCase):
    def test_key_order_and_spacing(self) -> None:
        payload = {"b": 1, "a": {"z": 1, "y": 2}}
        out = canonical_json_dumps(payload)
        self.assertEqual(out, '{"a":{"y":2,"z":1},"b":1}')

    def test_datetime_utc_normalization(self) -> None:
        payload = {"ts": datetime(2026, 2, 28, 13, 0, 0, tzinfo=timezone.utc)}
        out = canonical_json_dumps(payload)
        self.assertIn('"2026-02-28T13:00:00Z"', out)

    def test_float_and_int_distinct(self) -> None:
        self.assertNotEqual(canonical_json_dumps({"v": 1}), canonical_json_dumps({"v": 1.0}))

    def test_nan_rejected(self) -> None:
        with self.assertRaises(CanonicalJsonError):
            canonical_json_dumps({"v": math.nan})


if __name__ == "__main__":
    unittest.main()

