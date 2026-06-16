import unittest

from scripts.compare_input_cohesion import compare_document_sets


class InputCohesionComparisonTest(unittest.TestCase):
    def test_input_cohesion_preserves_outcomes_and_adds_state(self) -> None:
        comparison = compare_document_sets()
        summary = comparison["summary"]
        self.assertGreaterEqual(summary["datasets"], 4)
        self.assertEqual(summary["baseline_passed"], summary["datasets"])
        self.assertEqual(summary["stabilized_passed"], summary["datasets"])
        self.assertEqual(summary["outcome_changes"], 0)
        self.assertEqual(summary["cohesion_packets_added"], summary["datasets"])
        self.assertGreater(summary["total_evidence_delta"], 0)


if __name__ == "__main__":
    unittest.main()
