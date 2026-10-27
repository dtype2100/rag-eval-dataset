import copy
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_dataset import example


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/verify_public_cases.py"


class PublicCaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.relative = "data/public-cases/test/source.txt"
        source = self.root / self.relative
        source.parent.mkdir(parents=True)
        source.write_text("Delivery takes three days.", encoding="utf-8")
        self.data = example()
        self.data["manifest"]["sources"][0].update(
            path=self.relative,
            sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            url="https://example.org/policy",
            raw_url="https://raw.githubusercontent.com/github/docs/" + "a" * 40 + "/policy.md",
            upstream_commit="a" * 40,
            license="CC-BY-4.0",
        )
        self.data["evidence"][0]["locator"].update(path=self.relative, end=26)

    def run_cli(self, data=None, fetch=False, exercise=False):
        path = self.root / "dataset.json"
        path.write_text(json.dumps(self.data if data is None else data), encoding="utf-8")
        args = [sys.executable, str(CLI), str(path), "--root", str(self.root)]
        if fetch:
            args.append("--fetch")
        if exercise:
            args.append("--exercise")
        return subprocess.run(args, text=True, capture_output=True)

    def test_exercise_rejects_five_controlled_corruptions(self):
        result = self.run_cli(exercise=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["controls_rejected"], 5)

    def test_exercise_keeps_pending_input_and_source_unchanged(self):
        self.data["items"][0]["verification"].update(status="pending", reviewer="", independent=False, notes="")
        before = (self.root / self.relative).read_bytes()
        result = self.run_cli(exercise=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = json.loads((self.root / "dataset.json").read_text())
        self.assertEqual(saved["items"][0]["verification"]["status"], "pending")
        self.assertEqual((self.root / self.relative).read_bytes(), before)

    def test_real_source_hash_and_text_locator_match(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["evidence_checked"], 1)

    def test_changed_source_is_rejected(self):
        (self.root / self.relative).write_text("Delivery takes ten days.")
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("sha256", result.stderr)

    def test_contract_valid_wrong_quote_is_rejected(self):
        self.data["evidence"][0]["content"] = "Delivery takes ten days."
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("content", result.stderr)

    def test_out_of_bounds_offset_is_rejected(self):
        self.data["evidence"][0]["locator"]["end"] = 1000
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("locator", result.stderr)

    def test_path_traversal_and_symlink_escape_are_rejected(self):
        for path in ("../outside.txt", "/etc/passwd", "README.md"):
            with self.subTest(path=path):
                data = copy.deepcopy(self.data)
                data["manifest"]["sources"][0]["path"] = path
                result = self.run_cli(data)
                self.assertEqual(result.returncode, 1)
                self.assertIn("path", result.stderr)
        link = self.root / "data/public-cases/test/link"
        link.symlink_to(Path(self.tmp.name).parent, target_is_directory=True)
        self.data["manifest"]["sources"][0]["path"] = "data/public-cases/test/link/outside.txt"
        self.assertEqual(self.run_cli().returncode, 1)

    def test_text_locator_cannot_point_to_different_source_file(self):
        other = self.root / "data/public-cases/test/other.txt"
        other.write_text("Delivery takes three days.")
        self.data["evidence"][0]["locator"]["path"] = str(other.relative_to(self.root))
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("locator", result.stderr)

    def test_table_cells_are_checked(self):
        relative = "examples/public-cases/test/pricing.csv"
        path = self.root / relative
        path.parent.mkdir(parents=True)
        with path.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["row_key", "included", "period"])
            writer.writeheader()
            writer.writerow({"row_key": "free", "included": "100000", "period": "day"})
        self.data["manifest"]["sources"][0].update(
            path=relative, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), modality="table",
            representation="derived", transformation="reviewed CSV extraction", upstream_source_ids=[],
        )
        self.data["evidence"][0].update(modality="table", content="included=100000; period=day",
            locator={"sheet": "pricing", "row": "free", "columns": ["included", "period"], "values": {"included": "100000", "period": "day"}})
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.data["evidence"][0]["locator"]["values"]["period"] = "month"
        result = self.run_cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("values", result.stderr)

    def test_unpinned_or_untrusted_fetch_url_is_rejected_before_request(self):
        (self.root / self.relative).unlink()
        for url in ("http://127.0.0.1/private", "https://raw.githubusercontent.com/github/docs/main/policy.md", "https://raw.githubusercontent.com/unknown/repo/" + "a" * 40 + "/x"):
            with self.subTest(url=url):
                self.data["manifest"]["sources"][0]["raw_url"] = url
                result = self.run_cli(fetch=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn("raw_url", result.stderr)


if __name__ == "__main__":
    unittest.main()
