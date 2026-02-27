import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any


@dataclass
class SchemaRecord:
    name: str
    version: str
    path: Path


class SchemaRegistry:
    """Central registry for governance schema authority."""

    def __init__(self):
        self._schemas: Dict[str, SchemaRecord] = {}

    def register(self, name: str, version: str, path: Path) -> None:
        self._schemas[name] = SchemaRecord(name=name, version=version, path=path)

    def get(self, name: str) -> SchemaRecord:
        if name not in self._schemas:
            raise KeyError(f"Schema not registered: {name}")
        return self._schemas[name]

    def validate_version(self, name: str, expected_version: str) -> bool:
        rec = self.get(name)
        return rec.version == expected_version

    def load_schema(self, name: str) -> Dict[str, Any]:
        rec = self.get(name)
        return json.loads(rec.path.read_text())

    def enforce_registered_path(self, name: str, target: Path) -> bool:
        rec = self.get(name)
        return rec.path.resolve() == target.resolve()

    @classmethod
    def from_registry_file(cls, registry_path: Path, root: Path = None) -> "SchemaRegistry":
        root = root or registry_path.parent.parent
        data = json.loads(registry_path.read_text())
        reg = cls()
        for entry in data.get("schemas", []):
            rel = Path(entry["path"])
            reg.register(
                name=entry["name"],
                version=entry["version"],
                path=(root / rel).resolve(),
            )
        return reg
