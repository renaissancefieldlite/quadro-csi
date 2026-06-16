import os
import unittest
from unittest.mock import patch

from quadro.hermes_client import hermes_readout_payload, hermes_status, should_run_hermes_role


class HermesClientTest(unittest.TestCase):
    def test_disabled_status_does_not_claim_live_model(self) -> None:
        with patch.dict(os.environ, {"QUADRO_USE_HERMES": "0"}, clear=False):
            status = hermes_status()
        self.assertFalse(status.enabled)
        self.assertFalse(status.live)
        self.assertIn("disabled", status.reason)

    def test_role_gate_requires_enabled_local_lane(self) -> None:
        with patch.dict(
            os.environ,
            {
                "QUADRO_USE_HERMES": "1",
                "QUADRO_HERMES_AGENT_ROLES": "policy,decision",
            },
            clear=False,
        ):
            self.assertFalse(should_run_hermes_role("evidence"))
            self.assertTrue(should_run_hermes_role("policy"))

    def test_disabled_payload_is_silent(self) -> None:
        with patch.dict(os.environ, {"QUADRO_USE_HERMES": "0"}, clear=False):
            payload = hermes_readout_payload("decision", "test prompt")
        self.assertIsNone(payload)


if __name__ == "__main__":
    unittest.main()
