import json
import os
import unittest
from unittest.mock import patch

from quadro.featherless_client import featherless_status, featherless_summary_result


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(
            {
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "choices": [
                    {
                        "message": {
                            "content": "Quadro verifier lane is live.",
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 6,
                    "total_tokens": 16,
                },
            }
        ).encode("utf-8")


class FeatherlessClientTest(unittest.TestCase):
    def test_missing_key_is_not_configured(self) -> None:
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("FEATHERLESS")
        }
        with patch.dict(os.environ, env, clear=True):
            status = featherless_status()
        self.assertFalse(status.configured)
        self.assertIn("missing FEATHERLESS_API_KEY", status.reason)

    def test_summary_result_uses_openai_compatible_endpoint(self) -> None:
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["headers"] = dict(request.header_items())
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return _Response()

        with patch.dict(
            os.environ,
            {
                "FEATHERLESS_API_KEY": "test-key",
                "FEATHERLESS_MODEL": "Qwen/Qwen2.5-7B-Instruct",
                "FEATHERLESS_MAX_TOKENS": "33",
            },
            clear=False,
        ), patch("urllib.request.urlopen", fake_urlopen):
            result = featherless_summary_result("Summarize packet", timeout=12)

        self.assertEqual(
            captured["url"],
            "https://api.featherless.ai/v1/chat/completions",
        )
        self.assertEqual(captured["timeout"], 12)
        self.assertEqual(captured["payload"]["max_tokens"], 33)
        self.assertEqual(captured["payload"]["model"], "Qwen/Qwen2.5-7B-Instruct")
        self.assertIn("Bearer test-key", captured["headers"]["Authorization"])
        self.assertEqual(result.content, "Quadro verifier lane is live.")
        self.assertEqual(result.usage["total_tokens"], 16)


if __name__ == "__main__":
    unittest.main()
