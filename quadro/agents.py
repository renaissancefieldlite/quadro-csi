from __future__ import annotations

import json

from .hermes_client import hermes_readout_payload
from .local_band import PersistentRoom
from .persistent_memory import QuadroMemory
from .schemas import (
    ConsentState,
    DecisionPacket,
    EvidenceItem,
    EvidenceManifest,
    PolicyRead,
    TaskFrame,
    new_id,
    to_dict,
)
from .stable_state import StatePath


INTAKE = "QuadroIntake"
EVIDENCE = "QuadroEvidence"
POLICY = "QuadroPolicy"
DECISION = "QuadroDecision"
HUMAN = "HumanOwner"


class IntakeAgent:
    name = INTAKE

    def chat_assist(
        self,
        message: str,
        room: PersistentRoom,
        state: StatePath,
    ) -> dict:
        response = {
            "mode": "chat_assist",
            "question": message or "What can Quadro do?",
            "answer": (
                "Quadro can answer workflow questions, tell you what documents are "
                "needed, or run a four-agent customer review. To run a review, paste "
                "or attach the source material and ask the decision question in the "
                "same message."
            ),
            "review_path": [
                "Customer Intake frames the request, consent, and owner.",
                "Evidence Spine retrieves source-backed support and missing items.",
                "Policy/Risk checks consent, policy blockers, and escalation needs.",
                "Decision Packet returns approve, say no, or need more info.",
            ],
        }
        state.checkpoint("task_state", response)
        room.post_message(
            sender=self.name,
            mentions=[HUMAN],
            content=(
                "@HumanOwner I can answer questions or run a source-backed review. "
                "For a review, paste or attach the documents and include the decision "
                "question, like: Can we approve this refund?"
            ),
            payload={"chat_assist": response},
        )
        return response

    def assist_intake(
        self,
        message: str,
        room: PersistentRoom,
        state: StatePath,
    ) -> dict:
        checklist = {
            "mode": "intake_assist",
            "requested_action": message or "Prepare a Quadro customer review intake.",
            "required_fields": [
                "customer or account name",
                "requested decision or escalation outcome",
                "consent owner and approved scope",
                "source documents, links, or ticket IDs",
                "deadline, regulator, contract, or policy pressure",
                "human decision owner for final signoff",
            ],
            "ready_to_run_when": (
                "at least one customer/request, consent scope, and evidence source "
                "are present"
            ),
        }
        state.checkpoint("task_state", checklist)
        room.post_message(
            sender=self.name,
            mentions=[HUMAN],
            content=(
                "@HumanOwner intake assist ready. Send the customer/request, "
                "consent scope, source docs, risk pressure, and decision owner; "
                "then Quadro can run the evidence, policy, and decision agents."
            ),
            payload={"intake_checklist": checklist},
        )
        return checklist

    def frame_request(self, case: dict, room: PersistentRoom, state: StatePath) -> TaskFrame:
        consent = ConsentState(
            status=case["consent"]["status"],
            actor=case["consent"]["actor"],
            scope=list(case["consent"]["scope"]),
            constraints=list(case["consent"].get("constraints", [])),
            reason=case["consent"].get("reason", "initial consent"),
        )
        frame = TaskFrame(
            task_id=new_id("task"),
            title=case["title"],
            requester=case["requester"],
            business_goal=case["business_goal"],
            requested_action=case["requested_action"],
            consent=consent,
            open_questions=list(case.get("open_questions", [])),
        )
        state.checkpoint("task_state", frame)
        state.checkpoint("consent_state", consent)
        room.post_message(
            sender=self.name,
            mentions=[EVIDENCE],
            content=(
                "@QuadroEvidence build the evidence manifest for this request. "
                f"Consent revision {consent.revision}; allowed scope: "
                f"{_plain_list(consent.scope)}."
            ),
            payload={
                "task_frame": to_dict(frame),
                "input_cohesion": case.get("_input_cohesion"),
            },
        )
        return frame

    def handle_consent_revision(
        self,
        frame: TaskFrame,
        new_scope: list[str],
        reason: str,
        room: PersistentRoom,
        state: StatePath,
    ) -> TaskFrame:
        revised = frame.consent.narrowed(new_scope=new_scope, reason=reason)
        frame.consent = revised
        state.revisit_consent(revised, reason=reason)
        room.post_event(
            sender=self.name,
            kind="consent_revision",
            mentions=[EVIDENCE, POLICY, DECISION],
            content=(
                "@QuadroEvidence @QuadroPolicy @QuadroDecision consent changed. "
                f"Re-check revision {revised.revision}: {reason}"
            ),
            payload={"task_frame": to_dict(frame), "consent": to_dict(revised)},
        )
        return frame


class EvidenceAgent:
    name = EVIDENCE

    def build_manifest(
        self,
        frame: TaskFrame,
        case: dict,
        room: PersistentRoom,
        state: StatePath,
        memory: QuadroMemory,
    ) -> EvidenceManifest:
        valid_items: list[EvidenceItem] = []
        for query_spec in case["evidence_queries"]:
            tags = list(query_spec["scope_tags"])
            if not any(tag in frame.consent.scope for tag in tags):
                continue
            for result in memory.search(
                query_spec["query"],
                limit=query_spec.get("limit", 3),
                required_tags=tags,
            ):
                valid_items.append(
                    EvidenceItem(
                        item_id=new_id("ev"),
                        title=result["title"],
                        source=result["source"],
                        summary=result["snippet"],
                        scope_tags=tags,
                        support_status="real_source_packet",
                    )
                )

        manifest = EvidenceManifest(
            manifest_id=new_id("manifest"),
            task_id=frame.task_id,
            items=valid_items,
            missing_items=_missing_items(frame, valid_items),
            valid_scope=list(frame.consent.scope),
        )
        payload = {"evidence_manifest": to_dict(manifest)}
        model_readout = hermes_readout_payload(
            "evidence",
            _evidence_prompt(frame, manifest),
        )
        if model_readout:
            payload["model_readout"] = model_readout
        state.checkpoint("evidence_state", manifest)
        room.post_message(
            sender=self.name,
            mentions=[POLICY],
            content=(
                "@QuadroPolicy evidence manifest ready. "
                f"{len(valid_items)} items in scope; "
                f"{len(manifest.missing_items)} missing items flagged."
            ),
            payload=payload,
        )
        return manifest


class PolicyAgent:
    name = POLICY

    def review(
        self,
        frame: TaskFrame,
        manifest: EvidenceManifest,
        room: PersistentRoom,
        state: StatePath,
    ) -> PolicyRead:
        blockers: list[str] = []
        evidence_text = " ".join(item.summary.lower() for item in manifest.items)
        revocation_signal = any(
            phrase in evidence_text
            for phrase in [
                "withdrew authorization",
                "authorization is withdrawn",
                "consent revoked",
                "revokedconsent2026",
            ]
        )
        policy_prohibition_signal = any(
            phrase in evidence_text
            for phrase in [
                "quadrodeny2026",
                "must not proceed",
                "do not award",
                "prohibited vendor",
                "barred vendor",
                "sanctions match",
            ]
        )
        if frame.consent.status == "revoked" or revocation_signal:
            blockers.append("consent revoked")
        if frame.consent.status == "needs_review":
            blockers.append("consent needs review")
        if policy_prohibition_signal:
            blockers.append("policy prohibition")
        if manifest.missing_items:
            blockers.extend([f"missing evidence: {item}" for item in manifest.missing_items])
        if "financial_terms" in frame.consent.scope and not _has_scope(
            manifest, "approval_policy"
        ):
            blockers.append("approval policy needed for financial terms")

        risk_level = "high" if blockers else "medium"
        recommendation = "hold_for_review" if blockers else "approve_with_audit"
        read = PolicyRead(
            policy_id=new_id("policy"),
            task_id=frame.task_id,
            consent_revision=frame.consent.revision,
            risk_level=risk_level,
            blockers=blockers,
            escalation_required=bool(blockers),
            recommendation=recommendation,
        )
        payload = {"policy_read": to_dict(read)}
        model_readout = hermes_readout_payload(
            "policy",
            _policy_prompt(frame, manifest, read),
        )
        if model_readout:
            payload["model_readout"] = model_readout
        state.checkpoint("policy_state", read)
        room.post_message(
            sender=self.name,
            mentions=[DECISION],
            content=(
                "@QuadroDecision policy read ready. "
                f"Recommendation: {_plain_label(recommendation)}; "
                f"risk: {_plain_label(risk_level)}."
            ),
            payload=payload,
        )
        return read


class DecisionAgent:
    name = DECISION

    def decide(
        self,
        frame: TaskFrame,
        manifest: EvidenceManifest,
        policy: PolicyRead,
        room: PersistentRoom,
        state: StatePath,
    ) -> DecisionPacket:
        if any(blocker == "consent revoked" for blocker in policy.blockers):
            outcome = "SAY_NO"
            recommendation = "do_not_proceed_without_new_consent"
            current_gate = "stopped_consent_revoked"
        elif any(blocker == "policy prohibition" for blocker in policy.blockers):
            outcome = "SAY_NO"
            recommendation = "do_not_proceed_policy_block"
            current_gate = "stopped_policy_prohibition"
        elif policy.blockers:
            outcome = "NEED_MORE_INFO"
            recommendation = "collect_missing_evidence_or_update_consent"
            current_gate = "blocked_until_evidence_or_consent_updated"
        else:
            outcome = "APPROVE"
            recommendation = "approved_for_scoped_next_step"
            current_gate = "ready_for_human_signoff"

        packet = DecisionPacket(
            packet_id=new_id("packet"),
            task_id=frame.task_id,
            consent_revision=frame.consent.revision,
            outcome=outcome,
            recommendation=recommendation,
            rationale=[
                f"Consent revision {frame.consent.revision} is current.",
                f"{len(manifest.items)} in-scope evidence items were reviewed.",
                f"Policy recommendation: {policy.recommendation}.",
            ],
            required_approvals=_required_approvals(policy),
            revision_history=[
                f"revision {item['revision']}: {item['reason']}"
                for item in state.revision_state
                if item.get("kind") == "consent_revision"
            ],
            current_gate=current_gate,
        )
        payload = {"decision_packet": to_dict(packet)}
        model_readout = hermes_readout_payload(
            "decision",
            _decision_prompt(frame, manifest, policy, packet),
        )
        if model_readout:
            payload["model_readout"] = model_readout
        state.checkpoint("decision_state", packet)
        room.post_message(
            sender=self.name,
            mentions=[HUMAN],
            content=(
                "@HumanOwner decision packet ready. "
                f"Outcome: {_plain_label(outcome)}; gate: {_plain_label(current_gate)}; "
                f"recommendation: {_plain_label(recommendation)}."
            ),
            payload=payload,
        )
        return packet


def _missing_items(frame: TaskFrame, items: list[EvidenceItem]) -> list[str]:
    missing: list[str] = []
    if not items:
        missing.append("source documents for requested decision")
    if "financial_terms" in frame.consent.scope and not _items_have_scope(
        items, "financial_terms"
    ):
        missing.append("financial terms evidence")
    if "approval_policy" in frame.consent.scope and not _items_have_scope(
        items, "approval_policy"
    ):
        missing.append("approval policy")
    return missing


def _items_have_scope(items: list[EvidenceItem], scope: str) -> bool:
    return any(scope in item.scope_tags for item in items)


def _has_scope(manifest: EvidenceManifest, scope: str) -> bool:
    return _items_have_scope(manifest.items, scope)


def _required_approvals(policy: PolicyRead) -> list[str]:
    approvals = ["workflow owner"]
    if policy.escalation_required:
        approvals.append("risk manager")
    return approvals


def _evidence_prompt(frame: TaskFrame, manifest: EvidenceManifest) -> str:
    facts = [
        {
            "title": item.title,
            "summary": item.summary,
            "scope_tags": item.scope_tags,
            "source": item.source,
        }
        for item in manifest.items[:8]
    ]
    return (
        "You are Quadro Evidence Spine in a regulated customer escalation review. "
        "Read only these retrieved facts. Explain in plain English what evidence is "
        "present, what is missing, and what should be handed to Policy/Risk. "
        "Do not change the decision gate.\n\n"
        f"Task: {frame.requested_action}\n"
        f"Consent scope: {_plain_list(frame.consent.scope)}\n"
        f"Missing evidence: {_plain_list(manifest.missing_items) if manifest.missing_items else 'none'}\n"
        f"Evidence facts:\n{json.dumps(facts, indent=2)[:5000]}"
    )


def _policy_prompt(
    frame: TaskFrame,
    manifest: EvidenceManifest,
    policy: PolicyRead,
) -> str:
    return (
        "You are Quadro Policy/Risk in a regulated customer escalation review. "
        "Summarize the policy result in plain English for an audit trail. "
        "Use the deterministic blockers as the source of truth and do not override them.\n\n"
        f"Task: {frame.requested_action}\n"
        f"Consent status: {_plain_label(frame.consent.status)}; revision {frame.consent.revision}\n"
        f"Evidence count: {len(manifest.items)}\n"
        f"Missing evidence: {_plain_list(manifest.missing_items) if manifest.missing_items else 'none'}\n"
        f"Risk level: {_plain_label(policy.risk_level)}\n"
        f"Blockers: {_plain_list(policy.blockers) if policy.blockers else 'none'}\n"
        f"Recommendation: {_plain_label(policy.recommendation)}"
    )


def _decision_prompt(
    frame: TaskFrame,
    manifest: EvidenceManifest,
    policy: PolicyRead,
    packet: DecisionPacket,
) -> str:
    return (
        "You are Quadro Decision Packet in a regulated customer escalation review. "
        "Write a concise human-readable explanation of the final packet. "
        "Use the packet outcome as final and do not invent approvals or evidence.\n\n"
        f"Task: {frame.requested_action}\n"
        f"Consent revision: {packet.consent_revision}\n"
        f"Evidence count: {len(manifest.items)}\n"
        f"Policy blockers: {_plain_list(policy.blockers) if policy.blockers else 'none'}\n"
        f"Outcome: {_plain_label(packet.outcome)}\n"
        f"Gate: {_plain_label(packet.current_gate)}\n"
        f"Recommendation: {_plain_label(packet.recommendation)}\n"
        f"Approvals: {_plain_list(packet.required_approvals)}"
    )


def _plain_list(values: list[str]) -> str:
    return ", ".join(_plain_label(value) for value in values)


def _plain_label(value: str) -> str:
    labels = {
        "APPROVE": "approve",
        "SAY_NO": "say no",
        "NEED_MORE_INFO": "need more info",
        "NEED_INTAKE": "need intake",
        "ANSWERED": "answered",
        "customer_document": "customer documents",
        "consent_record": "consent records",
        "financial_terms": "financial terms",
        "approval_policy": "approval policy",
        "uploaded_source": "uploaded source",
        "policy_or_ticket": "policy or ticket",
        "approve_with_audit": "approve with audit",
        "hold_for_review": "hold for review",
        "do_not_proceed_without_new_consent": "do not proceed without new consent",
        "do_not_proceed_policy_block": "do not proceed because policy blocks it",
        "collect_missing_evidence_or_update_consent": "collect missing evidence or update consent",
        "approved_for_scoped_next_step": "approved for scoped next step",
        "ready_for_human_signoff": "ready for human signoff",
        "stopped_consent_revoked": "stopped because consent was revoked",
        "stopped_policy_prohibition": "stopped by policy prohibition",
        "blocked_until_evidence_or_consent_updated": "blocked until evidence or consent is updated",
        "intake_fields_needed": "intake fields needed",
        "chat_answered_no_review_run": "chat answered; no review run",
        "workflow owner": "workflow owner",
        "risk manager": "risk manager",
    }
    if value in labels:
        return labels[value]
    return value.replace("_", " ").replace("/", " / ")
