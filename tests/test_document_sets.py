from pathlib import Path
import tempfile
import unittest

from quadro.document_sets import load_document_sets, run_document_set


class DocumentSetTest(unittest.TestCase):
    def test_acceptance_document_sets_match_expected_gates(self) -> None:
        packs = load_document_sets()
        self.assertGreaterEqual(len(packs), 4)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            for pack in packs:
                with self.subTest(pack=pack["id"]):
                    result = run_document_set(
                        pack,
                        audit_path=temp / f"{pack['id']}.jsonl",
                        db_path=temp / f"{pack['id']}.sqlite3",
                    )
                    self.assertEqual(result["document_set"]["failures"], [])


if __name__ == "__main__":
    unittest.main()
