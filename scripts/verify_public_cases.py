"""Audit public-case snapshots and evidence locations; does not grade RAG quality."""

import argparse
import copy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from urllib.request import urlopen


REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dataset_contract", REPO / "skills/rag-dataset-builder/scripts/dataset.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


def source_path(root, value):
    contract.string(value, "source.path")
    relative = Path(value)
    contract.require(not relative.is_absolute(), "source.path", "must be repository-relative")
    path = (root / relative).resolve()
    allowed = (root / "data/public-cases", root / "examples/public-cases")
    contract.require(any(path.is_relative_to(parent) for parent in allowed), "source.path", "must stay inside public-case directories")
    return path


def fetch_source(source, destination):
    raw_url = source.get("raw_url", "")
    contract.string(raw_url, "source.raw_url")
    url = urlsplit(raw_url)
    segments = url.path.strip("/").split("/")
    allowed = {("github", "docs"), ("cloudflare", "cloudflare-docs"), ("kubernetes", "website")}
    valid = (url.scheme == "https" and url.netloc == "raw.githubusercontent.com"
             and not url.query and not url.fragment and len(segments) >= 4
             and tuple(segments[:2]) in allowed
             and re.fullmatch(r"[0-9a-f]{40}", segments[2]) is not None
             and segments[2] == source.get("upstream_commit"))
    contract.require(valid, "source.raw_url", "requires an allowlisted official repository at a pinned commit")
    with urlopen(raw_url, timeout=15) as response:
        contract.require(response.geturl() == raw_url, "source.raw_url", "redirects are not supported")
        payload = response.read(2 * 1024 * 1024 + 1)
    contract.require(len(payload) <= 2 * 1024 * 1024, "source", "snapshot exceeds 2 MiB")
    contract.require(hashlib.sha256(payload).hexdigest() == source["sha256"], "source.sha256", "download mismatch")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(payload)


def audit_dataset(data, root, *, fetch=False):
    root = Path(root).resolve()
    contract.validate_dataset(data)
    sources = {row["id"]: row for row in data["manifest"]["sources"]}
    paths = {}
    for ident, source in sources.items():
        path = source_path(root, source.get("path"))
        if not path.exists() and fetch:
            contract.require(path.is_relative_to(root / "data/public-cases"), "source.path", "only ignored original snapshots can be fetched")
            fetch_source(source, path)
        contract.require(path.is_file(), f"sources[{ident}].path", "snapshot missing; use --fetch for pinned originals")
        payload = path.read_bytes()
        contract.require(hashlib.sha256(payload).hexdigest() == source["sha256"], f"sources[{ident}].sha256", "snapshot mismatch")
        paths[ident] = path
        for upstream in source.get("upstream_source_ids", []):
            contract.require(upstream in sources and upstream != ident, f"sources[{ident}]", "unknown or self-referential upstream source")

    cells_checked = 0
    for evidence in data["evidence"]:
        ident = evidence["id"]
        path = paths[evidence["source_id"]]
        loc = evidence["locator"]
        modality = evidence["modality"]
        if modality in ("text", "code"):
            declared = source_path(root, loc.get("path"))
            contract.require(declared == path, f"evidence[{ident}].locator", "must point to its source file")
            text = path.read_bytes().decode("utf-8")
            if modality == "text":
                start, end = loc["start"], loc["end"]
                contract.require(end <= len(text), f"evidence[{ident}].locator", "offset outside source")
                actual = text[start:end]
            else:
                lines = text.splitlines(keepends=True)
                contract.require(loc["end_line"] <= len(lines), f"evidence[{ident}].locator", "line outside source")
                actual = "".join(lines[loc["start_line"] - 1:loc["end_line"]])
            contract.require(actual == evidence["content"], f"evidence[{ident}].content", "does not match source locator")
        elif modality == "table":
            with path.open(encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)
                fields = reader.fieldnames or []
            contract.require("row_key" in fields and all(key in fields for key in loc["columns"]), f"evidence[{ident}].locator", "unknown table columns")
            matches = [row for row in rows if row["row_key"] == loc["row"]]
            contract.require(len(matches) == 1, f"evidence[{ident}].locator", "row_key must resolve exactly once")
            values = contract.obj(loc.get("values"), f"evidence[{ident}].locator.values")
            contract.require(set(values) == set(loc["columns"]), f"evidence[{ident}].locator.values", "must cover exactly the referenced columns")
            contract.require(all(type(values[key]) is str and values[key] == matches[0][key] for key in loc["columns"]), f"evidence[{ident}].locator.values", "does not match table cells")
            actual = "; ".join(f"{key}={matches[0][key]}" for key in loc["columns"])
            contract.require(evidence["content"] == actual, f"evidence[{ident}].content", "does not match serialized table cells")
            cells_checked += len(values)
        else:
            raise ValueError(f"evidence[{ident}]: this auditor supports text, code, and CSV tables only")
    return {"status": "valid", "dataset_id": data["manifest"]["dataset_id"], "sources_checked": len(sources), "evidence_checked": len(data["evidence"]), "cells_checked": cells_checked, "items": len(data["items"]), "semantic_truth_verified": False}


def exercise_dataset(data, root):
    """Corrupt copies only; no source or dataset file is modified."""
    contract.require(data["manifest"]["status"] == "draft", "exercise", "use a draft so seal failure cannot mask a control")
    rejected = []
    for name in ("source_hash", "evidence_location", "missing_sufficient_evidence", "split_leak", "self_review"):
        mutated = copy.deepcopy(data)
        answer = next((item for item in mutated["items"] if item["expected_action"] == "answer"), None)
        contract.require(answer is not None, "exercise", "requires at least one answer item")
        if name == "source_hash":
            mutated["manifest"]["sources"][0]["sha256"] = "0" * 64
        elif name == "evidence_location":
            evidence = mutated["evidence"][0]
            if evidence["modality"] == "table":
                key = evidence["locator"]["columns"][0]
                evidence["locator"]["values"][key] += " [corrupted]"
            else:
                evidence["content"] += " [corrupted]"
        elif name == "missing_sufficient_evidence":
            answer["evidence_sets"] = []
        elif name == "split_leak":
            duplicate = copy.deepcopy(answer)
            duplicate.update(id=answer["id"] + "-controlled-leak", split="dev" if answer["split"] == "test" else "test")
            mutated["items"].append(duplicate)
        else:
            answer["verification"].update(status="accepted", reviewer=answer["author"], independent=True, notes="Controlled invalid self-review")
        try:
            audit_dataset(mutated, root)
        except ValueError as exc:
            rejected.append({"control": name, "result": "rejected", "reason": str(exc)})
        else:
            raise ValueError(f"exercise: failed to reject {name}")
    return rejected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--root", type=Path, default=REPO)
    parser.add_argument("--fetch", action="store_true", help="Fetch missing ignored snapshots from pinned official GitHub URLs")
    parser.add_argument("--exercise", action="store_true", help="Reject five deliberately corrupted copies without changing inputs")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"), object_pairs_hook=contract.unique_object, parse_constant=contract.reject_constant)
        result = audit_dataset(data, args.root, fetch=args.fetch)
        if args.exercise:
            controls = exercise_dataset(data, args.root)
            result.update(controls_rejected=len(controls), controls=controls)
        serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            with args.out.open("x", encoding="utf-8") as stream:
                stream.write(serialized)
        print(serialized, end="")
        return 0
    except (ValueError, OSError, UnicodeError, RecursionError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
