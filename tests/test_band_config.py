from pathlib import Path
import tempfile
import unittest

from quadro.band_config import load_agent_config, missing_agent_configs


class BandConfigTest(unittest.TestCase):
    def test_example_config_maps_four_roles(self) -> None:
        configs = load_agent_config(Path("agent_config.example.yaml"))
        self.assertEqual(
            set(configs),
            {
                "quadro_intake",
                "quadro_evidence",
                "quadro_policy",
                "quadro_decision",
            },
        )
        self.assertEqual(configs["quadro_intake"].name, "Quadro Customer Intake")
        self.assertEqual(configs["quadro_policy"].role, "policy_risk")
        self.assertEqual(
            missing_agent_configs(configs),
            [
                "quadro_intake",
                "quadro_evidence",
                "quadro_policy",
                "quadro_decision",
            ],
        )

    def test_complete_config_has_no_missing_roles(self) -> None:
        text = """
quadro_intake:
  name: "Quadro Customer Intake"
  role: "customer_intake"
  agent_id: "agent-111111"
  api_key: "key-111111"
quadro_evidence:
  name: "Quadro Evidence Spine"
  role: "evidence_spine"
  agent_id: "agent-222222"
  api_key: "key-222222"
quadro_policy:
  name: "Quadro Policy Risk"
  role: "policy_risk"
  agent_id: "agent-333333"
  api_key: "key-333333"
quadro_decision:
  name: "Quadro Decision Packet"
  role: "decision_packet"
  agent_id: "agent-444444"
  api_key: "key-444444"
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "agent_config.yaml"
            path.write_text(text, encoding="utf-8")
            configs = load_agent_config(path)
        self.assertEqual(missing_agent_configs(configs), [])


if __name__ == "__main__":
    unittest.main()

