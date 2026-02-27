from typing import Protocol, Dict, Any, Tuple


class GovernanceInterface(Protocol):
    def claim(self, packet_id: str, agent: str) -> Tuple[bool, str]:
        ...

    def done(self, packet_id: str, agent: str, notes: str = "") -> Tuple[bool, str]:
        ...

    def note(self, packet_id: str, agent: str, notes: str) -> Tuple[bool, str]:
        ...

    def fail(self, packet_id: str, agent: str, reason: str = "") -> Tuple[bool, str]:
        ...

    def reset(self, packet_id: str) -> Tuple[bool, str]:
        ...

    def handover(
        self,
        packet_id: str,
        agent: str,
        reason: str,
        progress_notes: str = "",
        files_modified: list = None,
        remaining_work: list = None,
        to_agent: str = None,
    ) -> Tuple[bool, str]:
        ...

    def resume(self, packet_id: str, agent: str) -> Tuple[bool, str]:
        ...

    def context_bundle(
        self,
        packet_id: str,
        compact: bool = False,
        max_events: int = 40,
        max_notes_bytes: int = 4000,
        max_handovers: int = 40,
    ) -> Tuple[bool, Dict[str, Any]]:
        ...

    def ready(self) -> Dict[str, Any]:
        ...

    def status(self) -> Dict[str, Any]:
        ...

    def closeout_l2(self, area_id: str, agent: str, assessment_path: str, notes: str = "") -> Tuple[bool, str]:
        ...
