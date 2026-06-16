from __future__ import annotations

from typing import Any


DEFAULT_REQUEST = (
    "Review the attached source material and decide whether the requested action "
    "can proceed."
)


def build_input_cohesion(
    case: dict[str, Any],
    operator_message: str,
    uploaded_docs: list[dict[str, str]],
    task_mode: str,
) -> dict[str, Any]:
    """Create a public-safe stabilization packet before agent handoff.

    This is Quadro-owned input cohesion. It does not inspect model internals; it
    stabilizes the review surface by extracting durable task, evidence, consent,
    correction, and next-gate signals before the agent chain runs.
    """

    review_request = str(case.get("requested_action") or DEFAULT_REQUEST).strip()
    combined = _combined_text(review_request, operator_message, uploaded_docs)
    signals = _signals(combined)
    source_count = len(uploaded_docs)
    required_scopes = _required_scopes(signals)
    open_questions = _open_questions(signals)
    correction_markers = _matched(
        combined,
        [
            "correction:",
            "actually",
            "instead",
            "revised",
            "updated",
            "withdrawn",
            "revoked",
            "narrowed",
            "do not proceed",
        ],
    )
    next_gate = _next_gate(source_count, signals, task_mode)
    confidence = _confidence(source_count, signals, review_request)
    return {
        "status": "stabilized",
        "mode": "input_cohesion",
        "review_request": review_request,
        "task_mode_requested": task_mode,
        "source_count": source_count,
        "source_titles": [document["title"] for document in uploaded_docs],
        "signals": signals,
        "required_scopes": required_scopes,
        "open_questions": open_questions,
        "correction_markers": correction_markers,
        "stabilized_query": _stabilized_query(review_request, uploaded_docs, signals),
        "next_gate": next_gate,
        "confidence": confidence,
        "notes": [
            "Review request, source presence, consent signals, evidence needs, and next gate were stabilized before agent handoff.",
            "This packet is recorded in the state path and can be audited without exposing private implementation details.",
        ],
    }


def apply_input_cohesion(case: dict[str, Any], cohesion: dict[str, Any]) -> None:
    case["_input_cohesion"] = cohesion
    case["requested_action"] = cohesion["review_request"]
    _append_unique(case.setdefault("open_questions", []), cohesion["open_questions"])
    consent = case.setdefault("consent", {})
    scope = consent.setdefault("scope", [])
    _append_unique(scope, cohesion["required_scopes"])
    if cohesion["signals"].get("consent_revoked"):
        consent["status"] = "revoked"
        consent["reason"] = "input cohesion detected withdrawn or revoked consent"
    if cohesion["source_count"]:
        queries = case.setdefault("evidence_queries", [])
        query = {
            "query": cohesion["stabilized_query"],
            "scope_tags": ["customer_document"],
            "limit": 8,
        }
        if query not in queries:
            queries.insert(0, query)


def _combined_text(
    review_request: str,
    operator_message: str,
    uploaded_docs: list[dict[str, str]],
) -> str:
    parts = [
        review_request,
        operator_message,
        *(
            f"{document.get('title', '')}\n{document.get('body', '')}"
            for document in uploaded_docs
        ),
    ]
    return "\n".join(parts).lower()


def _signals(text: str) -> dict[str, bool]:
    return {
        "consent_revoked": _has_any(
            text,
            [
                "withdrew authorization",
                "authorization is withdrawn",
                "authority is withdrawn",
                "consent revoked",
                "revoked consent",
                "withdrawn consent",
                "do not proceed without new consent",
                "no export after withdrawal",
                "client authority is withdrawn",
                "revokedconsent2026",
            ],
        ),
        "consent_present": _has_any(
            text,
            ["consent", "authorization", "authorized", "authority"],
        ),
        "financial_action": _has_any(
            text,
            [
                "invoice",
                "refund",
                "payout",
                "credit",
                "wire",
                "payment",
                "claim amount",
                "loss estimate",
                "usd",
                "$",
                "financial",
            ],
        ),
        "approval_missing": _has_any(
            text,
            [
                "approval not attached",
                "approval missing",
                "no approval",
                "no approval matrix",
                "submitted_approval_policy,false",
                "legal/compliance approval not attached",
                "approver evidence missing",
                "approval evidence missing",
            ],
        ),
        "approval_present": _has_any(
            text,
            [
                "approved by",
                "approval granted",
                "approved for",
                "manager approval",
                "legal approval",
                "compliance approval",
                "approval policy",
                "approval rule",
            ],
        ),
        "policy_prohibition": _has_any(
            text,
            [
                "quadrodeny2026",
                "must not proceed",
                "do not award",
                "prohibited vendor",
                "barred vendor",
                "sanctions match",
            ],
        ),
        "external_disclosure": _has_any(
            text,
            ["external notice", "disclosure notice", "external disclosure"],
        ),
    }


def _required_scopes(signals: dict[str, bool]) -> list[str]:
    scopes = ["customer_document"]
    if signals["consent_present"] or signals["consent_revoked"]:
        scopes.append("consent_record")
    if signals["financial_action"]:
        scopes.append("financial_terms")
    if (
        signals["approval_missing"]
        or signals["approval_present"]
        or signals["policy_prohibition"]
        or signals["external_disclosure"]
    ):
        scopes.append("approval_policy")
    return scopes


def _open_questions(signals: dict[str, bool]) -> list[str]:
    questions: list[str] = []
    if signals["consent_revoked"]:
        questions.append("Has the customer or authorized owner provided new written authorization?")
    if signals["approval_missing"]:
        questions.append("Where is the required approval policy or approval record?")
    if signals["external_disclosure"]:
        questions.append("Where is the legal/compliance approval for external disclosure?")
    return questions


def _next_gate(source_count: int, signals: dict[str, bool], task_mode: str) -> str:
    if task_mode in {"chat_assist", "intake_assist"}:
        return task_mode
    if not source_count:
        return "collect_source_documents"
    if signals["consent_revoked"] or signals["policy_prohibition"]:
        return "run_review_with_blocker_focus"
    if signals["approval_missing"]:
        return "run_review_with_missing_evidence_focus"
    return "run_agent_review"


def _confidence(
    source_count: int,
    signals: dict[str, bool],
    review_request: str,
) -> str:
    if source_count and review_request and any(signals.values()):
        return "high"
    if source_count or review_request != DEFAULT_REQUEST:
        return "medium"
    return "low"


def _stabilized_query(
    review_request: str,
    uploaded_docs: list[dict[str, str]],
    signals: dict[str, bool],
) -> str:
    titles = " ".join(document["title"] for document in uploaded_docs)
    signal_terms = " ".join(
        name.replace("_", " ")
        for name, active in signals.items()
        if active
    )
    return (
        f"{review_request} {titles} {signal_terms} customer request consent "
        "authorization approval policy evidence blocker decision"
    ).strip()


def _matched(text: str, phrases: list[str]) -> list[str]:
    return [phrase for phrase in phrases if phrase in text]


def _has_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _append_unique(values: list[str], new_values: list[str]) -> None:
    for value in new_values:
        if value not in values:
            values.append(value)
