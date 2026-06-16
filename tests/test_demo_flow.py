from pathlib import Path
import tempfile
import unittest

from quadro.demo import HACKATHON_CASE, load_case, run_quadro_workflow


class DemoFlowTest(unittest.TestCase):
    def test_revisit_consent_creates_revision_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_quadro_workflow(
                case=load_case(),
                audit_path=Path(temp_dir) / "audit.jsonl",
                db_path=Path(temp_dir) / "memory.sqlite3",
                revisit=True,
            )
        self.assertEqual(result["final_packet"]["consent_revision"], 1)
        self.assertTrue(result["final_packet"]["revision_history"])
        kinds = [event["kind"] for event in result["transcript"]]
        self.assertIn("consent_revision", kinds)

    def test_initial_flow_has_four_agent_messages(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_quadro_workflow(
                case=load_case(),
                audit_path=None,
                db_path=Path(temp_dir) / "memory.sqlite3",
                revisit=False,
                operator_message=(
                    "Customer request: refund invoice USD 240.\n"
                    "Approval policy: refunds under USD 500 may proceed.\n\n"
                    "Task: Can we approve the refund?"
                ),
            )
        senders = {event["sender"] for event in result["transcript"]}
        self.assertIn("QuadroIntake", senders)
        self.assertIn("QuadroEvidence", senders)
        self.assertIn("QuadroPolicy", senders)
        self.assertIn("QuadroDecision", senders)

    def test_evidence_items_are_real_source_packets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_quadro_workflow(
                case=load_case(HACKATHON_CASE),
                audit_path=Path(temp_dir) / "audit.jsonl",
                db_path=Path(temp_dir) / "memory.sqlite3",
                revisit=False,
                task_mode="full_review",
            )
        evidence_state = result["state_path"]["evidence_state"]
        self.assertGreater(len(evidence_state["items"]), 0)
        statuses = {item["support_status"] for item in evidence_state["items"]}
        self.assertEqual(statuses, {"real_source_packet"})

    def test_product_case_does_not_pull_hackathon_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_quadro_workflow(
                case=load_case(),
                audit_path=Path(temp_dir) / "audit.jsonl",
                db_path=Path(temp_dir) / "memory.sqlite3",
                revisit=False,
                operator_message=(
                    "Customer Account Admin withdrew authorization for the export.\n\n"
                    "Task: Can we send the customer export?"
                ),
            )
        rendered = str(result["transcript"]) + str(result["state_path"])
        for forbidden in [
            "Band Hackathon",
            "lablab",
            "public GitHub",
            "hackathon_submission",
            "portfolio_use",
            "band_integration",
        ]:
            self.assertNotIn(forbidden, rendered)

    def test_review_request_is_extracted_from_task_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_quadro_workflow(
                case=load_case(),
                audit_path=Path(temp_dir) / "audit.jsonl",
                db_path=Path(temp_dir) / "memory.sqlite3",
                revisit=False,
                operator_message=(
                    "Customer request: refund invoice USD 240.\n"
                    "Approval policy: refunds under USD 500 may proceed.\n\n"
                    "Task: Can we approve the refund?"
                ),
            )
        task_state = result["state_path"]["task_state"]
        self.assertEqual(task_state["requested_action"], "Can we approve the refund?")

    def test_input_cohesion_stabilizes_correction_and_next_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_quadro_workflow(
                case=load_case(),
                audit_path=Path(temp_dir) / "audit.jsonl",
                db_path=Path(temp_dir) / "memory.sqlite3",
                revisit=False,
                operator_message=(
                    "Correction: actually the customer withdrew authorization "
                    "for the export and said do not proceed.\n\n"
                    "Task: Can we send the customer export?"
                ),
            )
        cohesion = result["state_path"]["cohesion_state"]
        self.assertEqual(cohesion["status"], "stabilized")
        self.assertTrue(cohesion["signals"]["consent_revoked"])
        self.assertIn("correction:", cohesion["correction_markers"])
        self.assertEqual(cohesion["next_gate"], "run_review_with_blocker_focus")
        self.assertEqual(result["final_packet"]["outcome"], "SAY_NO")

    def test_chat_question_routes_to_chat_assist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_quadro_workflow(
                case=load_case(),
                audit_path=Path(temp_dir) / "audit.jsonl",
                db_path=Path(temp_dir) / "memory.sqlite3",
                revisit=False,
                operator_message="What can you do?",
            )
        self.assertEqual(result["task_mode"], "chat_assist")
        self.assertEqual(result["final_packet"]["outcome"], "ANSWERED")
        self.assertEqual(result["state_path"]["evidence_state"], {})

    def test_intake_assist_does_not_run_full_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_quadro_workflow(
                case=load_case(),
                audit_path=Path(temp_dir) / "audit.jsonl",
                db_path=Path(temp_dir) / "memory.sqlite3",
                revisit=False,
                operator_message="Can you help me start intake?",
            )
        self.assertEqual(result["task_mode"], "intake_assist")
        self.assertEqual(result["final_packet"]["current_gate"], "intake_fields_needed")
        self.assertEqual(result["state_path"]["evidence_state"], {})

    def test_uploaded_document_reaches_evidence_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_quadro_workflow(
                case=load_case(),
                audit_path=Path(temp_dir) / "audit.jsonl",
                db_path=Path(temp_dir) / "memory.sqlite3",
                revisit=False,
                operator_message="Review refund escalation against the uploaded policy.",
                uploaded_docs=[
                    {
                        "title": "Customer Refund Policy",
                        "body": "Customer request: refund escalation. Policy: manager approval required before customer data export.",
                    }
                ],
            )
        items = result["state_path"]["evidence_state"]["items"]
        self.assertTrue(
            any("customer_document" in item["scope_tags"] for item in items)
        )

    def test_manual_upload_revoked_consent_says_no(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_quadro_workflow(
                case=load_case(),
                audit_path=Path(temp_dir) / "audit.jsonl",
                db_path=Path(temp_dir) / "memory.sqlite3",
                revisit=False,
                operator_message="Can we send the customer export?",
                uploaded_docs=[
                    {
                        "title": "Withdrawal Note",
                        "body": (
                            "Customer Account Admin withdrew authorization for the export "
                            "and requested that no further customer files be shared until "
                            "a new approval is signed."
                        ),
                    },
                    {
                        "title": "Export Scope",
                        "body": "The request includes customer files and export scope.",
                    },
                ],
            )
        self.assertEqual(result["final_packet"]["outcome"], "SAY_NO")
        self.assertEqual(result["final_packet"]["current_gate"], "stopped_consent_revoked")

    def test_manual_upload_missing_approval_needs_more_info(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_quadro_workflow(
                case=load_case(),
                audit_path=Path(temp_dir) / "audit.jsonl",
                db_path=Path(temp_dir) / "memory.sqlite3",
                revisit=False,
                operator_message="Can we approve the credit exception?",
                uploaded_docs=[
                    {
                        "title": "Credit Exception",
                        "body": (
                            "Credit request includes invoice and outage references, "
                            "but no approval matrix is attached."
                        ),
                    },
                    {
                        "title": "Customer Authorization",
                        "body": (
                            "Customer Account Admin authorized review of renewal ticket "
                            "for a limited credit exception decision. It does not waive "
                            "the requirement for an approval policy or approval matrix."
                        ),
                    },
                ],
            )
        self.assertEqual(result["final_packet"]["outcome"], "NEED_MORE_INFO")
        self.assertEqual(
            result["final_packet"]["current_gate"],
            "blocked_until_evidence_or_consent_updated",
        )


if __name__ == "__main__":
    unittest.main()
