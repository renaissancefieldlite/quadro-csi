from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
from typing import Any

from .agents import INTAKE, DecisionAgent, EvidenceAgent, IntakeAgent, PolicyAgent
from .aimlapi_client import aimlapi_status, partner_summary_result
from .env import load_dotenv
from .featherless_client import featherless_status, featherless_summary_result
from .hermes_client import hermes_status
from .input_cohesion import apply_input_cohesion, build_input_cohesion
from .local_band import PersistentRoom
from .persistent_memory import QuadroMemory
from .stable_state import StatePath

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE = ROOT / "data" / "real_cases" / "quadro_product_review_case.json"
HACKATHON_CASE = ROOT / "data" / "real_cases" / "quadro_hackathon_readiness_case.json"
DEFAULT_AUDIT = ROOT / "audit" / "quadro_local_room.jsonl"
DEFAULT_DB = ROOT / "audit" / "quadro_memory.sqlite3"


def load_case(path: Path = DEFAULT_CASE) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def run_quadro_workflow(
    case: dict[str, Any] | None = None,
    audit_path: Path | None = DEFAULT_AUDIT,
    db_path: Path | None = DEFAULT_DB,
    revisit: bool = True,
    operator_message: str = "",
    task_mode: str = "auto",
    uploaded_docs: list[dict[str, str]] | None = None,
    use_input_cohesion: bool = True,
) -> dict[str, Any]:
    case = copy.deepcopy(case or load_case())
    uploaded_docs = _clean_uploaded_docs(uploaded_docs or [])
    operator_message = operator_message.strip()
    review_request = _extract_review_request(operator_message)
    if operator_message:
        case["requested_action"] = review_request
    if operator_message and not uploaded_docs and _message_has_source_material(operator_message):
        uploaded_docs = _clean_uploaded_docs(
            [{"title": "Review Packet", "body": operator_message}]
        )
    cohesion = None
    if use_input_cohesion:
        cohesion = build_input_cohesion(
            case=case,
            operator_message=operator_message,
            uploaded_docs=uploaded_docs,
            task_mode=task_mode,
        )
        apply_input_cohesion(case, cohesion)
    if uploaded_docs:
        _attach_customer_doc_scope(case, uploaded_docs)
    if audit_path and audit_path.exists():
        audit_path.unlink()
    if db_path and db_path.exists():
        db_path.unlink()

    room = PersistentRoom(room_name="quadro-real-workflow-room", audit_path=audit_path)
    memory = _prepare_memory(case, db_path or DEFAULT_DB, uploaded_docs=uploaded_docs)
    state = StatePath()
    if cohesion:
        state.checkpoint("cohesion_state", cohesion)
        memory.record_checkpoint("input_cohesion", cohesion)
    intake = IntakeAgent()
    evidence = EvidenceAgent()
    policy = PolicyAgent()
    decision = DecisionAgent()

    if operator_message:
        room.post_message(
            sender="HumanOwner",
            mentions=[INTAKE],
            content=operator_message,
            payload={"operator_message": operator_message},
        )

    resolved_mode = _resolve_task_mode(operator_message, task_mode, revisit, uploaded_docs)
    if resolved_mode == "chat_assist":
        chat = intake.chat_assist(operator_message, room, state)
        memory.record_checkpoint("chat_assist", chat)
        memory.close()
        packet = {
            "packet_id": None,
            "task_id": None,
            "consent_revision": 0,
            "outcome": "ANSWERED",
            "recommendation": "chat_answered_no_review_run",
            "rationale": [
                "Quadro answered a workflow question.",
                "No evidence, policy, or decision review was run.",
            ],
            "required_approvals": [],
            "revision_history": [],
            "current_gate": "chat_answered_no_review_run",
        }
        state.checkpoint("decision_state", packet)
        return _result(
            room=room,
            state=state,
            first_packet=packet,
            final_packet=packet,
            audit_path=audit_path,
            db_path=db_path,
            task_mode=resolved_mode,
            aimlapi=aimlapi_status().to_dict(),
            featherless=featherless_status().to_dict(),
            hermes=hermes_status().to_dict(),
        )

    if resolved_mode == "intake_assist":
        checklist = intake.assist_intake(operator_message, room, state)
        memory.record_checkpoint("intake_assist", checklist)
        memory.close()
        packet = {
            "packet_id": None,
            "task_id": None,
            "consent_revision": 0,
            "outcome": "NEED_INTAKE",
            "recommendation": "collect_required_intake_fields",
            "rationale": [
                "Customer/request details are not complete enough for evidence, policy, and decision review.",
                "No evidence or policy claim was made from this intake-assist turn.",
            ],
            "required_approvals": ["workflow owner"],
            "revision_history": [],
            "current_gate": "intake_fields_needed",
        }
        state.checkpoint("decision_state", packet)
        return _result(
            room=room,
            state=state,
            first_packet=packet,
            final_packet=packet,
            audit_path=audit_path,
            db_path=db_path,
            task_mode=resolved_mode,
            aimlapi=aimlapi_status().to_dict(),
            featherless=featherless_status().to_dict(),
            hermes=hermes_status().to_dict(),
        )

    frame = intake.frame_request(case, room, state)
    manifest = evidence.build_manifest(frame, case, room, state, memory)
    policy_read = policy.review(frame, manifest, room, state)
    first_packet = decision.decide(frame, manifest, policy_read, room, state)

    final_packet = first_packet
    if revisit:
        revision = case["revisit_consent"]
        frame = intake.handle_consent_revision(
            frame=frame,
            new_scope=list(revision["new_scope"]),
            reason=revision["reason"],
            room=room,
            state=state,
        )
        manifest = evidence.build_manifest(frame, case, room, state, memory)
        policy_read = policy.review(frame, manifest, room, state)
        final_packet = decision.decide(frame, manifest, policy_read, room, state)

    memory.record_checkpoint("final_state_path", state.to_dict())
    aimlapi = aimlapi_status().to_dict()
    featherless = featherless_status().to_dict()
    partner_readout = None
    aimlapi_usage = None
    partner_errors: dict[str, str] = {}
    if os.getenv("QUADRO_USE_AIMLAPI") == "1" and aimlapi["configured"]:
        try:
            partner_result = partner_summary_result(_partner_prompt(state.to_dict()))
            partner_readout = partner_result.content
            aimlapi_usage = partner_result.to_dict()
            memory.record_checkpoint("aimlapi_partner_summary", aimlapi_usage)
        except Exception as exc:  # pragma: no cover - provider/network gate
            partner_errors["aimlapi"] = str(exc)
    featherless_readout = None
    featherless_usage = None
    if os.getenv("QUADRO_USE_FEATHERLESS") == "1" and featherless["configured"]:
        try:
            featherless_result = featherless_summary_result(_partner_prompt(state.to_dict()))
            featherless_readout = featherless_result.content
            featherless_usage = featherless_result.to_dict()
            memory.record_checkpoint("featherless_partner_summary", featherless_usage)
        except Exception as exc:  # pragma: no cover - provider/network gate
            partner_errors["featherless"] = str(exc)
    if partner_errors:
        memory.record_checkpoint("partner_provider_errors", partner_errors)
    memory.close()
    return _result(
        room=room,
        state=state,
        first_packet=first_packet.__dict__,
        final_packet=final_packet.__dict__,
        audit_path=audit_path,
        db_path=db_path,
        task_mode=resolved_mode,
        aimlapi=aimlapi,
        featherless=featherless,
        hermes=hermes_status().to_dict(),
        partner_readout=partner_readout,
        aimlapi_usage=aimlapi_usage,
        featherless_readout=featherless_readout,
        featherless_usage=featherless_usage,
        partner_errors=partner_errors,
    )


def _result(
    room: PersistentRoom,
    state: StatePath,
    first_packet: dict[str, Any],
    final_packet: dict[str, Any],
    audit_path: Path | None,
    db_path: Path | None,
    task_mode: str,
    aimlapi: dict[str, Any],
    featherless: dict[str, Any],
    hermes: dict[str, Any],
    partner_readout: str | None = None,
    aimlapi_usage: dict[str, Any] | None = None,
    featherless_readout: str | None = None,
    featherless_usage: dict[str, Any] | None = None,
    partner_errors: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "room": room.room_name,
        "transcript": room.transcript(),
        "state_path": state.to_dict(),
        "first_packet": first_packet,
        "final_packet": final_packet,
        "audit_path": str(audit_path) if audit_path else None,
        "db_path": str(db_path) if db_path else None,
        "task_mode": task_mode,
        "aimlapi": aimlapi,
        "featherless": featherless,
        "hermes": hermes,
        "partner_readout": partner_readout,
        "aimlapi_usage": aimlapi_usage,
        "featherless_readout": featherless_readout,
        "featherless_usage": featherless_usage,
        "partner_errors": partner_errors or {},
    }


def run_demo_case(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return run_quadro_workflow(*args, **kwargs)


def _prepare_memory(
    case: dict[str, Any],
    db_path: Path,
    uploaded_docs: list[dict[str, str]] | None = None,
) -> QuadroMemory:
    memory = QuadroMemory(db_path)
    for source in case.get("source_packets", []):
        path = ROOT / source["path"]
        memory.ingest_source_packet(
            path=path,
            tags=list(source.get("tags", [])),
            source_url=source.get("url"),
        )
    for index, document in enumerate(uploaded_docs or [], start=1):
        memory.ingest_text_document(
            title=document["title"],
            body=document["body"],
            tags=[
                "customer_document",
                "uploaded_source",
                "policy_or_ticket",
                *document.get("scope_tags", []),
            ],
            source_label=document.get("source_label", f"uploaded_document_{index}"),
        )
    return memory


def _clean_uploaded_docs(documents: list[dict[str, str]]) -> list[dict[str, str]]:
    clean: list[dict[str, str]] = []
    for index, document in enumerate(documents, start=1):
        body = str(document.get("body", "")).strip()
        if not body:
            continue
        title = str(document.get("title", "")).strip() or f"Customer Document {index}"
        scope_tags = [
            str(tag).strip()
            for tag in document.get("scope_tags", [])
            if str(tag).strip()
        ]
        source_label = str(document.get("source_label", "")).strip()
        clean.append(
            {
                "title": title[:120],
                "body": body[:20000],
                "scope_tags": scope_tags[:12],
                "source_label": source_label[:240],
            }
        )
    return clean


def _attach_customer_doc_scope(case: dict[str, Any], uploaded_docs: list[dict[str, str]]) -> None:
    analysis = _analyze_uploaded_docs(case, uploaded_docs)
    case["_uploaded_document_analysis"] = analysis

    consent = case.setdefault("consent", {})
    scope = consent.setdefault("scope", [])
    _append_unique(scope, analysis["required_scopes"])
    if analysis["consent_revoked"]:
        consent["status"] = "revoked"
        consent["reason"] = "uploaded documents indicate consent or authority was withdrawn"
        constraints = consent.setdefault("constraints", [])
        _append_unique(
            constraints,
            [
                "do not proceed while consent or authority is revoked",
                "collect new written authorization before release",
            ],
        )

    open_questions = case.setdefault("open_questions", [])
    _append_unique(open_questions, analysis["open_questions"])

    for document in uploaded_docs:
        inferred_tags = _infer_document_tags(document)
        existing_tags = document.setdefault("scope_tags", [])
        _append_unique(existing_tags, inferred_tags)

    queries = case.setdefault("evidence_queries", [])
    queries[0:0] = _manual_review_queries(case, uploaded_docs, analysis)


def _analyze_uploaded_docs(
    case: dict[str, Any],
    uploaded_docs: list[dict[str, str]],
) -> dict[str, Any]:
    combined = _combined_review_text(case, uploaded_docs)
    consent_revoked = _has_any(
        combined,
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
    )
    financial_terms = _has_any(
        combined,
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
    )
    approval_needed = financial_terms or _has_any(
        combined,
        [
            "approval not attached",
            "approval missing",
            "no approval",
            "submitted_approval_policy,false",
            "approval matrix is attached",
            "legal/compliance approval not attached",
            "external notice",
            "disclosure notice",
            "release the refund",
            "approve the payout",
            "proceed with award",
            "policy exception",
        ],
    )
    policy_block = _has_any(
        combined,
        [
            "quadrodeny2026",
            "must not proceed",
            "do not award",
            "prohibited vendor",
            "barred vendor",
            "sanctions match",
        ],
    )

    required_scopes = ["customer_document"]
    if _has_any(combined, ["consent", "authorization", "authorized", "authority"]):
        required_scopes.append("consent_record")
    if financial_terms:
        required_scopes.append("financial_terms")
    if approval_needed or policy_block:
        required_scopes.append("approval_policy")

    open_questions: list[str] = []
    if consent_revoked:
        open_questions.append("Has the customer or authorized owner provided new written authorization?")
    if approval_needed and not _has_present_approval(uploaded_docs):
        open_questions.append("Where is the required approval policy or approval record?")
    if _has_any(combined, ["legal/compliance approval not attached", "external notice", "disclosure notice"]):
        open_questions.append("Where is the legal/compliance approval for external disclosure?")

    return {
        "consent_revoked": consent_revoked,
        "financial_terms": financial_terms,
        "approval_needed": approval_needed,
        "policy_block": policy_block,
        "required_scopes": required_scopes,
        "open_questions": open_questions,
    }


def _manual_review_queries(
    case: dict[str, Any],
    uploaded_docs: list[dict[str, str]],
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    title_text = " ".join(document["title"] for document in uploaded_docs)
    base = (
        f"{case.get('requested_action', '')} {title_text} "
        "customer request consent authorization approval policy escalation "
        "deadline decision refund invoice payout credit wire legal compliance "
        "disclosure vendor procurement incident"
    )
    queries: list[dict[str, Any]] = [
        {"query": base, "scope_tags": ["customer_document"], "limit": 8},
    ]
    if "consent_record" in analysis["required_scopes"]:
        queries.append(
            {
                "query": "consent authorization authorized withdrew revoked withdrawn authority",
                "scope_tags": ["consent_record"],
                "limit": 4,
            }
        )
    if analysis["financial_terms"]:
        queries.append(
            {
                "query": "refund invoice payout credit wire amount usd loss estimate financial terms",
                "scope_tags": ["financial_terms"],
                "limit": 4,
            }
        )
    if analysis["approval_needed"] or analysis["policy_block"]:
        queries.append(
            {
                "query": "approval policy manager approval legal compliance approval record coverage procurement policy",
                "scope_tags": ["approval_policy"],
                "limit": 4,
            }
        )
    if analysis["policy_block"]:
        queries.append(
            {
                "query": "barred vendor prohibited vendor sanctions match must not proceed do not award",
                "scope_tags": ["customer_document"],
                "limit": 4,
            }
        )
    return queries


def _infer_document_tags(document: dict[str, str]) -> list[str]:
    text = f"{document.get('title', '')}\n{document.get('body', '')}".lower()
    tags = ["customer_document", "uploaded_source", "policy_or_ticket"]
    if _has_any(text, ["consent", "authorization", "authorized", "authority", "policyholder consent"]):
        tags.append("consent_record")
    if _has_any(
        text,
        ["invoice", "refund", "payout", "credit", "wire", "payment", "claim amount", "loss estimate", "usd", "$"],
    ):
        tags.append("financial_terms")
    if _looks_like_present_approval(text):
        tags.append("approval_policy")
    return tags


def _has_present_approval(uploaded_docs: list[dict[str, str]]) -> bool:
    return any(
        _looks_like_present_approval(f"{document.get('title', '')}\n{document.get('body', '')}".lower())
        for document in uploaded_docs
    )


def _looks_like_present_approval(text: str) -> bool:
    if _has_any(
        text,
        [
            "approval not attached",
            "approval missing",
            "no approval",
            "no approval matrix",
            "submitted_approval_policy,false",
            "without approval",
            "not approved",
            "not attached",
            "approver evidence missing",
            "approval evidence missing",
            "does not waive the requirement",
            "still requires legal/compliance approval",
            "requires legal/compliance approval",
            "where is the legal/compliance approval",
        ],
    ):
        return False
    policy_label = _has_any(
        text,
        [
            "approval policy",
            "approval rule",
            "coverage policy",
            "eligibility policy",
            "approval record",
            "procurement policy",
            "outside counsel policy",
            "privacy approval policy",
        ],
    )
    policy_rule = _has_any(
        text,
        [
            "may proceed",
            "can proceed",
            "must proceed",
            "must pause",
            "must not proceed",
            "cannot proceed",
            "must be routed",
            "may be released",
            "when the",
        ],
    )
    explicit_approval = _has_any(
        text,
        [
            "approved by",
            "approval granted",
            "approved for",
            "approved public",
            "manager approval",
            "legal approval",
            "compliance approval",
        ],
    )
    return (policy_label and policy_rule) or explicit_approval


def _combined_review_text(
    case: dict[str, Any],
    uploaded_docs: list[dict[str, str]],
) -> str:
    return "\n".join(
        [
            str(case.get("requested_action", "")),
            *(f"{document.get('title', '')}\n{document.get('body', '')}" for document in uploaded_docs),
        ]
    ).lower()


def _has_any(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _append_unique(values: list[str], new_values: list[str]) -> None:
    for value in new_values:
        if value not in values:
            values.append(value)


def _partner_prompt(state_path: dict[str, Any]) -> str:
    return (
        "Summarize this Quadro state path for a hackathon judge. Return exactly "
        "four bullets, each under 16 words: Outcome, Evidence, Consent gate, "
        "Human next step. Do not add a preface or closing.\n\n"
        f"{json.dumps(state_path, indent=2, sort_keys=True)[:8000]}"
    )


def _resolve_task_mode(
    message: str,
    task_mode: str,
    revisit: bool,
    uploaded_docs: list[dict[str, str]] | None = None,
) -> str:
    if task_mode != "auto":
        return task_mode
    lower = message.lower()
    has_documents = bool(uploaded_docs)
    review_terms = [
        "approve",
        "send",
        "release",
        "export",
        "payout",
        "refund",
        "proceed",
        "signoff",
        "disclosure",
        "award",
        "transfer",
        "claim",
        "credit",
        "wire",
    ]
    chat_terms = [
        "what can you do",
        "how does this work",
        "how do you work",
        "explain",
        "walk me through",
        "what is quadro",
        "what should i upload",
        "what documents",
        "where do documents go",
        "how do i test",
    ]
    help_terms = [
        "intake",
        "what do you need",
        "what info",
        "what fields",
        "assist me",
        "how do i",
        "how should i",
        "what can you do",
        "explain",
        "help",
    ]
    has_review_terms = any(term in lower for term in review_terms)
    if not revisit and any(term in lower for term in chat_terms) and not has_documents:
        return "chat_assist"
    if not revisit and any(term in lower for term in help_terms) and not has_review_terms:
        return "intake_assist"
    if not revisit and has_review_terms and not has_documents:
        return "intake_assist"
    if not revisit and not has_documents and not has_review_terms:
        return "chat_assist"
    return "consent_review" if revisit else "full_review"


def _extract_review_request(message: str) -> str:
    cleaned = message.strip()
    if not cleaned:
        return "Review the attached source material and decide whether the requested action can proceed."
    markers = ["Task:", "Review request:", "Request:", "Question:"]
    for marker in markers:
        index = cleaned.lower().rfind(marker.lower())
        if index >= 0:
            extracted = cleaned[index + len(marker) :].strip()
            if extracted:
                return extracted
    question_lines = [
        line.strip()
        for line in cleaned.splitlines()
        if line.strip().endswith("?")
    ]
    if question_lines:
        return question_lines[-1]
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if len(cleaned) > 360 and lines:
        return lines[-1]
    return cleaned


def _message_has_source_material(message: str) -> bool:
    text = message.strip()
    lower = text.lower()
    if len(text) > 320:
        return True
    if "\n" in text and any(
        marker in lower
        for marker in [
            "task:",
            "review request:",
            "customer:",
            "policy:",
            "approval:",
            "authorization",
            "consent",
            "invoice",
            "refund",
            "wire",
            "claim",
            "incident",
            "contract",
        ]
    ):
        return True
    return any(
        marker in lower
        for marker in [
            "withdrew authorization",
            "authorization is withdrawn",
            "consent revoked",
            "approval not attached",
            "no approval matrix",
            "submitted_approval_policy,false",
            "must not proceed",
            "do not award",
            "prohibited vendor",
            "barred vendor",
            "sanctions match",
        ]
    )


def main() -> None:
    load_dotenv(ROOT / ".env")
    parser = argparse.ArgumentParser(description="Run the Quadro local workflow.")
    parser.add_argument("--case", type=Path, default=DEFAULT_CASE)
    parser.add_argument("--no-revisit", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_quadro_workflow(
        case=load_case(args.case),
        audit_path=DEFAULT_AUDIT,
        revisit=not args.no_revisit,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    print("Quadro local workflow complete")
    print(f"Room: {result['room']}")
    print(f"Events: {len(result['transcript'])}")
    print(f"Audit: {result['audit_path']}")
    print(f"SQLite memory: {result['db_path']}")
    print(f"Final gate: {result['final_packet']['current_gate']}")
    print(f"Recommendation: {result['final_packet']['recommendation']}")


if __name__ == "__main__":
    main()
