from typing import Protocol, Dict, Any, Tuple


class GovernanceInterface(Protocol):
    def claim(self, packet_id: str, agent: str, context_attestation: list = None) -> Tuple[bool, str]:
        ...

    def done(self, packet_id: str, agent: str, notes: str = "") -> Tuple[bool, str]:
        ...

    def preflight(self, packet_id: str, agent: str, assessment: Dict[str, Any]) -> Tuple[bool, str]:
        ...

    def preflight_approve(self, packet_id: str, supervisor: str) -> Tuple[bool, str]:
        ...

    def preflight_return(self, packet_id: str, supervisor: str, notes: str) -> Tuple[bool, str]:
        ...

    def heartbeat(
        self,
        packet_id: str,
        agent: str,
        status: str,
        decisions: str = "",
        obstacles: str = "",
        completion_estimate: str = "",
    ) -> Tuple[bool, str]:
        ...

    def check_stalled(self, packet_id: str = "") -> Tuple[bool, str]:
        ...

    def review_claim(self, packet_id: str, reviewer: str) -> Tuple[bool, str]:
        ...

    def review_submit(
        self,
        packet_id: str,
        reviewer: str,
        verdict: str,
        assessment: Dict[str, Any],
    ) -> Tuple[bool, str]:
        ...

    def review_escalate(self, packet_id: str, reviewer: str, reason: str) -> Tuple[bool, str]:
        ...

    def promote_template(
        self,
        packet_id: str,
        supervisor: str,
        template_id: str,
        tags: list = None,
        summary: str = "",
    ) -> Tuple[bool, str]:
        ...

    def templates_list(self) -> Dict[str, Any]:
        ...

    def templates_show(self, template_id: str) -> Tuple[bool, Dict[str, Any]]:
        ...

    def templates_deprecate(
        self,
        template_id: str,
        supervisor: str,
        reason: str,
        replacement: str = "",
    ) -> Tuple[bool, str]:
        ...

    def ontology_validate(self, packet_id: str) -> Tuple[bool, Dict[str, Any]]:
        ...

    def ontology_check_drift(self) -> Dict[str, Any]:
        ...

    def ontology_propose(self, actor: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        ...

    def ontology_approve(self, proposal_id: str, supervisor: str) -> Tuple[bool, str]:
        ...

    def ontology_reject(self, proposal_id: str, supervisor: str, reason: str) -> Tuple[bool, str]:
        ...

    def ontology_history(self) -> Dict[str, Any]:
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
