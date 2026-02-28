from dataclasses import dataclass
from typing import Dict, Set


ROLE_OPERATOR = "operator"
ROLE_REVIEWER = "reviewer"
ROLE_SUPERVISOR = "supervisor"
ROLE_ADMIN = "admin"


ROLE_ACTIONS: Dict[str, Set[str]] = {
    ROLE_OPERATOR: {"claim", "done", "fail", "note", "heartbeat", "preflight"},
    ROLE_REVIEWER: {"review_claim", "review_submit", "review_escalate"},
    ROLE_SUPERVISOR: {
        "preflight_approve",
        "preflight_return",
        "review_escalate",
        "reset",
        "ontology_approve",
        "ontology_reject",
        "closeout-l2",
    },
    ROLE_ADMIN: {"*"},
}


@dataclass(frozen=True)
class IdentityContext:
    user_id: str
    role: str
    workspace: str = "default"


def role_allows(role: str, action: str) -> bool:
    allowed = ROLE_ACTIONS.get((role or "").strip().lower(), set())
    return "*" in allowed or action in allowed

