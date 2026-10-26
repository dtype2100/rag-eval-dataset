import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "skills/rag-dataset-builder/scripts/dataset.py"


def example():
    return {
        "manifest": {
            "schema_version": "1.0", "dataset_id": "toy", "version": "1",
            "status": "draft", "corpus_snapshot": "toy-v1", "task": "rag",
            "split_policy": "query-disjoint", "coverage": ["synthetic text"],
            "limitations": ["Not a production benchmark"],
            "judging": {"criteria": "Direct evidence for delivery timing is grade 2; partial policy context is grade 1.", "coverage": "exhaustive", "candidate_scope": "all sources in toy-v1"},
            "provenance": {"method": "synthetic fixture", "generator": "test author", "prompt_version": "fixture-v1", "settings": "literal test data; no model sampling", "created_at": "2026-10-27T00:00:00Z"},
            "intake": {
                "data_description": "Synthetic delivery policy",
                "user_task": "Find delivery times", "query_language": "en",
                "scope": "toy-v1 only", "access_policy": "public synthetic data",
                "external_processing": "not needed", "target_size": 1,
            },
            "sources": [{
                "id": "s1", "sha256": "a" * 64, "modality": "text",
                "representation": "native", "transformation": "none",
                "losses": [], "split_group": "policy-v1",
            }],
            "review": {"policy": "independent", "approved_by": "reviewer",
                       "approved_at": "2026-10-27T00:00:00Z"},
        },
        "evidence": [{
            "id": "e1", "source_id": "s1", "modality": "text",
            "locator": {"path": "policy.txt", "start": 0, "end": 29},
            "content": "Delivery takes three days.",
        }],
        "items": [{
            "id": "q1", "query": "How long does delivery take?", "split": "test",
            "leakage_group": "delivery-time", "query_type": "fact",
            "origin": "synthetic", "author": "author",
            "expected_action": "answer", "reference_answer": "Three days.",
            "evidence_sets": [["e1"]], "relevance_judgments": {"e1": 2},
            "rubric": ["Says three days."],
            "verification": {"status": "accepted", "reviewer": "reviewer",
                             "method": "llm", "independent": True,
                             "notes": "Compared with the synthetic source."},
        }],
    }


class DatasetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)

    def run_cli(self, data, command="validate", out=None):
        path = self.folder / "input.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        args = [sys.executable, str(CLI), command, str(path)]
        if out is not None:
            args += ["--out", str(out)]
        return subprocess.run(args, text=True, capture_output=True)

    def invalid(self, data, fragment, command="validate"):
        result = self.run_cli(data, command, self.folder / "frozen.json" if command == "freeze" else None)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(fragment, result.stderr)

    def test_valid_rag(self):
        result = self.run_cli(example())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["items"], 1)

    def test_retrieval_does_not_require_answer_or_evidence_sets(self):
        data = example()
        data["manifest"]["task"] = "retrieval"
        data["items"][0].update(expected_action="retrieve", reference_answer="", evidence_sets=[], rubric=[])
        self.assertEqual(self.run_cli(data).returncode, 0)

    def test_retrieval_requires_positive_judgment(self):
        data = example()
        data["manifest"]["task"] = "retrieval"
        data["items"][0].update(expected_action="retrieve", evidence_sets=[], relevance_judgments={"e1": 0})
        self.invalid(data, "relevance_judgments")

    def test_answer_requires_sufficient_evidence(self):
        data = example()
        data["items"][0]["evidence_sets"] = []
        self.invalid(data, "evidence_sets")

    def test_unknown_evidence_and_source(self):
        for field in ("source", "evidence"):
            with self.subTest(field=field):
                data = example()
                if field == "source":
                    data["evidence"][0]["source_id"] = "missing"
                    message = "source_id"
                else:
                    data["items"][0]["evidence_sets"] = [["missing"]]
                    message = "evidence_sets"
                self.invalid(data, message)

    def test_duplicate_ids(self):
        for field in ("evidence", "items"):
            with self.subTest(field=field):
                data = example()
                data[field].append(copy.deepcopy(data[field][0]))
                self.invalid(data, "duplicate")

    def test_bool_is_not_a_grade_or_target_size(self):
        data = example()
        data["items"][0]["relevance_judgments"]["e1"] = True
        self.invalid(data, "relevance_judgments")
        data = example()
        data["manifest"]["intake"]["target_size"] = True
        self.invalid(data, "target_size")

    def test_answer_evidence_must_have_positive_qrels(self):
        data = example()
        data["items"][0]["relevance_judgments"] = {"e1": 0}
        self.invalid(data, "evidence_sets")

    def test_and_or_groups_survive_freeze(self):
        data = example()
        for ident in ("e2", "e3"):
            row = copy.deepcopy(data["evidence"][0])
            row["id"] = ident
            data["evidence"].append(row)
        data["items"][0]["evidence_sets"] = [["e1", "e3"], ["e2", "e3"]]
        data["items"][0]["relevance_judgments"] = {"e1": 2, "e2": 2, "e3": 1}
        out = self.folder / "frozen.json"
        result = self.run_cli(data, "freeze", out)
        self.assertEqual(result.returncode, 0, result.stderr)
        frozen = json.loads(out.read_text())
        self.assertEqual(frozen["items"][0]["evidence_sets"], [["e1", "e3"], ["e2", "e3"]])

    def test_invalid_shapes_fail_cleanly(self):
        for value in ([], None, {"manifest": []}, {"manifest": {}}):
            with self.subTest(value=value):
                self.invalid(value, "error")

    def test_modalities_validate_locators(self):
        locators = {
            "table": {"sheet": "products", "row": "sku-1", "columns": ["price"]},
            "image": {"page": 1, "bbox": [0, 0.1, 1, 0.8]},
            "audio": {"start_seconds": 0, "end_seconds": 3.5},
            "video": {"start_seconds": 1, "end_seconds": 2},
            "code": {"path": "main.py", "start_line": 1, "end_line": 1},
        }
        for modality, locator in locators.items():
            with self.subTest(modality=modality):
                data = example()
                data["manifest"]["sources"][0]["modality"] = modality
                data["evidence"][0].update(modality=modality, locator=locator)
                self.assertEqual(self.run_cli(data).returncode, 0)
                data["evidence"][0]["locator"] = {}
                self.invalid(data, "locator")

    def test_invalid_bbox_and_nonfinite_time(self):
        for locator in ({"page": 1, "bbox": [1, 0, 0, 1]}, {"page": True, "bbox": [0, 0, 1, 1]}):
            data = example()
            data["manifest"]["sources"][0]["modality"] = "image"
            data["evidence"][0].update(modality="image", locator=locator)
            self.invalid(data, "locator")
        data = example()
        data["manifest"]["sources"][0]["modality"] = "audio"
        data["evidence"][0].update(modality="audio", locator={"start_seconds": 0, "end_seconds": float("inf")})
        self.invalid(data, "error")

    def test_pending_items_validate_but_cannot_freeze(self):
        data = example()
        data["items"][0]["verification"].update(status="pending", reviewer="", independent=False, notes="")
        self.assertEqual(self.run_cli(data).returncode, 0)
        self.invalid(data, "verification", "freeze")

    def test_self_review_and_missing_notes_are_not_accepted(self):
        for changes in ({"reviewer": "author"}, {"independent": False}, {"notes": " "}):
            data = example()
            data["items"][0]["verification"].update(changes)
            self.invalid(data, "verification")

    def test_human_required_policy_rejects_llm_only(self):
        data = example()
        data["manifest"]["review"]["policy"] = "human-required"
        self.invalid(data, "method", "freeze")

    def test_freeze_requires_complete_intake_and_approval(self):
        data = example()
        data["manifest"]["intake"]["scope"] = ""
        self.assertEqual(self.run_cli(data).returncode, 0)
        self.invalid(data, "scope", "freeze")
        data = example()
        data["manifest"]["review"]["approved_at"] = "yesterday"
        self.invalid(data, "approved_at", "freeze")

    def test_query_groups_do_not_cross_splits(self):
        for mode in ("group", "query"):
            data = example()
            second = copy.deepcopy(data["items"][0])
            second.update(id="q2", split="dev")
            if mode == "group":
                second["query"] = "Delivery duration?"
            else:
                second.update(leakage_group="different", query=" HOW  LONG does delivery take? ")
            data["items"].append(second)
            self.invalid(data, "split")

    def test_source_disjoint_and_query_disjoint_differ(self):
        data = example()
        second = copy.deepcopy(data["items"][0])
        second.update(id="q2", split="dev", query="What is the shipping duration?", leakage_group="another")
        data["items"].append(second)
        self.assertEqual(self.run_cli(data).returncode, 0)
        data["manifest"]["split_policy"] = "source-disjoint"
        self.invalid(data, "split_group")

    def test_abstention_needs_rationale(self):
        data = example()
        data["items"][0].update(expected_action="abstain", evidence_sets=[], reference_answer="")
        self.invalid(data, "rationale")
        data["items"][0]["rationale"] = "Toy snapshot has no international delivery policy; checked both sources."
        data["items"][0]["answerability_check"] = {"method": "exhaustive", "source_ids": ["s1"], "notes": "Read the entire toy source."}
        self.assertEqual(self.run_cli(data).returncode, 0)

    def test_freeze_requires_task_specific_judging_criteria(self):
        data = example()
        data["manifest"]["judging"]["criteria"] = ""
        self.invalid(data, "judging", "freeze")

    def test_abstention_exhaustive_check_requires_all_sources(self):
        data = example()
        data["manifest"]["sources"].append({**data["manifest"]["sources"][0], "id": "s2"})
        data["items"][0].update(expected_action="abstain", evidence_sets=[], rationale="No evidence found", answerability_check={"method": "exhaustive", "source_ids": ["s1"], "notes": "Read one source."})
        self.invalid(data, "answerability_check")

    def test_bounded_abstention_must_disclose_limitations(self):
        data = example()
        data["manifest"]["limitations"] = []
        data["items"][0].update(expected_action="abstain", evidence_sets=[], rationale="Not found within the checked sample", answerability_check={"method": "bounded", "source_ids": ["s1"], "notes": "Only a limited search; not proof of absence."})
        self.invalid(data, "limitations", "freeze")

    def test_freeze_requires_generation_provenance(self):
        data = example()
        data["manifest"]["provenance"]["generator"] = ""
        self.invalid(data, "provenance", "freeze")

    def test_unicode_equivalent_queries_cannot_cross_splits(self):
        data = example()
        data["items"][0]["query"] = "배송 기간은?"
        second = copy.deepcopy(data["items"][0])
        second.update(id="q2", split="dev", leakage_group="different", query=unicodedata.normalize("NFD", "배송 기간은?"))
        data["items"].append(second)
        self.invalid(data, "split")

    def test_same_source_hash_cannot_evade_source_disjoint_policy(self):
        data = example()
        data["manifest"]["split_policy"] = "source-disjoint"
        data["manifest"]["sources"].append({**data["manifest"]["sources"][0], "id": "s2", "split_group": "mislabelled-as-different"})
        data["evidence"].append({**data["evidence"][0], "id": "e2", "source_id": "s2"})
        second = copy.deepcopy(data["items"][0])
        second.update(id="q2", split="dev", leakage_group="different", query="Shipping duration?", evidence_sets=[["e2"]], relevance_judgments={"e2": 2})
        data["items"].append(second)
        self.invalid(data, "split")

    def test_freeze_roundtrip_detects_tampering(self):
        out = self.folder / "frozen.json"
        result = self.run_cli(example(), "freeze", out)
        self.assertEqual(result.returncode, 0, result.stderr)
        frozen = json.loads(out.read_text())
        self.assertEqual(frozen["manifest"]["status"], "frozen")
        self.assertEqual(self.run_cli(frozen).returncode, 0)
        frozen["items"][0]["reference_answer"] = "Ten days."
        self.invalid(frozen, "payload_sha256")

    def test_existing_output_survives(self):
        out = self.folder / "frozen.json"
        out.write_text("keep me", encoding="utf-8")
        result = self.run_cli(example(), "freeze", out)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(out.read_text(), "keep me")

    def test_bad_json_and_duplicate_keys_fail(self):
        path = self.folder / "broken.json"
        for content in ('{"manifest":', '{"manifest": 1, "manifest": 2}'):
            path.write_text(content)
            result = subprocess.run([sys.executable, str(CLI), "validate", str(path)], text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
