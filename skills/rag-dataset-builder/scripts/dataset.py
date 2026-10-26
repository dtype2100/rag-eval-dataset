"""Validate declared evidence contracts; never infer semantic truth from structure."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import unicodedata


def require(condition, path, message):
    if not condition:
        raise ValueError(f"{path}: {message}")


def obj(value, path):
    require(isinstance(value, dict), path, "expected object")
    return value


def array(value, path, nonempty=False):
    require(isinstance(value, list), path, "expected array")
    require(not nonempty or bool(value), path, "must not be empty")
    return value


def string(value, path, nonempty=True):
    require(isinstance(value, str), path, "expected string")
    require(not nonempty or bool(value.strip()), path, "must not be blank")
    return value


def strings(value, path, nonempty=False, unique=False):
    array(value, path, nonempty)
    for index, entry in enumerate(value):
        string(entry, f"{path}[{index}]")
    require(not unique or len(set(value)) == len(value), path, "duplicate values")
    return value


def choice(value, choices, path):
    require(isinstance(value, str) and value in choices, path, f"expected one of {choices}")
    return value


def integer(value, minimum, path):
    require(type(value) is int and value >= minimum, path, f"expected integer >= {minimum}")
    return value


def timestamp(value, path):
    string(value, path)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"{path}: expected ISO 8601 timestamp") from None
    require(parsed.tzinfo is not None and "T" in value, path, "timezone is required")


def records(value, path):
    result = {}
    for index, row in enumerate(array(value, path, nonempty=True)):
        where = f"{path}[{index}]"
        obj(row, where)
        ident = string(row.get("id"), f"{where}.id")
        require(ident not in result, where, f"duplicate id {ident}")
        result[ident] = row
    return result


def finite_number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def validate_locator(modality, value, path):
    loc = obj(value, path)
    if modality == "text":
        string(loc.get("path"), path + ".path")
        start = integer(loc.get("start"), 0, path + ".start")
        integer(loc.get("end"), start + 1, path + ".end")
    elif modality == "table":
        for key in ("sheet", "row"):
            string(loc.get(key), f"{path}.{key}")
        strings(loc.get("columns"), path + ".columns", nonempty=True, unique=True)
    elif modality == "image":
        integer(loc.get("page"), 1, path + ".page")
        box = array(loc.get("bbox"), path + ".bbox")
        require(len(box) == 4, path + ".bbox", "expected four coordinates")
        require(all(finite_number(n) and 0 <= n <= 1 for n in box), path + ".bbox", "expected finite normalized coordinates")
        require(box[0] < box[2] and box[1] < box[3], path + ".bbox", "rectangle must have positive area")
    elif modality in ("audio", "video"):
        start, end = loc.get("start_seconds"), loc.get("end_seconds")
        require(all(finite_number(n) for n in (start, end)), path, "expected finite time offsets")
        require(0 <= start < end, path, "expected 0 <= start_seconds < end_seconds")
    elif modality == "code":
        string(loc.get("path"), path + ".path")
        start = integer(loc.get("start_line"), 1, path + ".start_line")
        integer(loc.get("end_line"), start, path + ".end_line")


def json_bytes(data):
    try:
        return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, UnicodeError) as exc:
        raise ValueError(f"JSON: {exc}") from None


def payload_hash(data):
    manifest = {k: v for k, v in data["manifest"].items() if k not in ("payload_sha256", "frozen_at")}
    payload = {**data, "manifest": manifest}
    return hashlib.sha256(json_bytes(payload)).hexdigest()


def validate_dataset(data, *, for_freeze=False):
    obj(data, "dataset")
    # Include extension fields: a valid draft must also be serializable when frozen.
    json_bytes(data)
    manifest = obj(data.get("manifest"), "manifest")
    choice(manifest.get("schema_version"), ("1.0",), "manifest.schema_version")
    for key in ("dataset_id", "version", "corpus_snapshot"):
        string(manifest.get(key), f"manifest.{key}")
    status = choice(manifest.get("status"), ("draft", "frozen"), "manifest.status")
    strict = for_freeze or status == "frozen"
    task = choice(manifest.get("task"), ("retrieval", "rag"), "manifest.task")
    split_policy = choice(manifest.get("split_policy"), ("query-disjoint", "source-disjoint"), "manifest.split_policy")
    strings(manifest.get("coverage"), "manifest.coverage", nonempty=strict)
    strings(manifest.get("limitations"), "manifest.limitations")
    judging = obj(manifest.get("judging"), "manifest.judging")
    for key in ("criteria", "candidate_scope"):
        string(judging.get(key), f"manifest.judging.{key}", nonempty=strict)
    choice(judging.get("coverage"), ("exhaustive", "pooled", "sampled"), "manifest.judging.coverage")
    provenance = obj(manifest.get("provenance"), "manifest.provenance")
    for key in ("method", "generator", "prompt_version", "settings"):
        string(provenance.get(key), f"manifest.provenance.{key}", nonempty=strict)
    if strict:
        timestamp(provenance.get("created_at"), "manifest.provenance.created_at")
    intake = obj(manifest.get("intake"), "manifest.intake")
    for key in ("data_description", "user_task", "query_language", "scope", "access_policy", "external_processing"):
        string(intake.get(key), f"manifest.intake.{key}", nonempty=strict or key in ("data_description", "user_task"))
    integer(intake.get("target_size"), 1, "manifest.intake.target_size")
    review = obj(manifest.get("review"), "manifest.review")
    policy = choice(review.get("policy"), ("independent", "human-required"), "manifest.review.policy")
    if strict:
        string(review.get("approved_by"), "manifest.review.approved_by")
        timestamp(review.get("approved_at"), "manifest.review.approved_at")
        for key in ("calibration", "disagreements"):
            string(review.get(key), f"manifest.review.{key}")

    modalities = ("text", "table", "image", "audio", "video", "code")
    sources = records(manifest.get("sources"), "manifest.sources")
    for ident, source in sources.items():
        path = f"manifest.sources[{ident}]"
        digest = source.get("sha256")
        require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest) is not None, path + ".sha256", "expected lowercase SHA-256")
        choice(source.get("modality"), modalities, path + ".modality")
        choice(source.get("representation"), ("native", "derived"), path + ".representation")
        string(source.get("transformation"), path + ".transformation")
        strings(source.get("losses"), path + ".losses")
        string(source.get("split_group"), path + ".split_group")

    evidence = records(data.get("evidence"), "evidence")
    for ident, row in evidence.items():
        path = f"evidence[{ident}]"
        source_id = string(row.get("source_id"), path + ".source_id")
        require(source_id in sources, path + ".source_id", "unknown source")
        modality = choice(row.get("modality"), modalities, path + ".modality")
        require(modality == sources[source_id]["modality"], path + ".modality", "must match source modality")
        string(row.get("content"), path + ".content")
        validate_locator(modality, row.get("locator"), path + ".locator")

    items = records(data.get("items"), "items")
    splits = {}

    def bind_split(key, split, path):
        require(key not in splits or splits[key] == split, path, "group crosses dev/test split")
        splits[key] = split

    for ident, item in items.items():
        path = f"items[{ident}]"
        query = string(item.get("query"), path + ".query")
        split = choice(item.get("split"), ("dev", "test"), path + ".split")
        group = string(item.get("leakage_group"), path + ".leakage_group")
        bind_split(("query", " ".join(unicodedata.normalize("NFC", query).casefold().split())), split, path + ".split")
        bind_split(("query_group", group), split, path + ".split")
        for key in ("query_type", "author"):
            string(item.get(key), f"{path}.{key}")
        choice(item.get("origin"), ("real", "synthetic"), path + ".origin")
        action = choice(item.get("expected_action"), ("retrieve", "answer", "abstain", "clarify"), path + ".expected_action")
        require(action != "answer" or task == "rag", path + ".expected_action", "answer requires rag task")
        require(action != "retrieve" or task == "retrieval", path + ".expected_action", "retrieve requires retrieval task")
        string(item.get("reference_answer"), path + ".reference_answer", nonempty=action == "answer")
        strings(item.get("rubric"), path + ".rubric", nonempty=action != "retrieve")
        if action in ("abstain", "clarify"):
            string(item.get("rationale"), path + ".rationale")
        if action == "abstain":
            check_path = path + ".answerability_check"
            check = obj(item.get("answerability_check"), check_path)
            method = choice(check.get("method"), ("exhaustive", "bounded"), check_path + ".method")
            checked = strings(check.get("source_ids"), check_path + ".source_ids", nonempty=True, unique=True)
            require(all(s in sources for s in checked), check_path + ".source_ids", "unknown source")
            string(check.get("notes"), check_path + ".notes")
            if method == "exhaustive":
                require(set(checked) == set(sources), check_path, "exhaustive check must cover all snapshot sources")
            elif strict:
                require(bool(manifest["limitations"]), "manifest.limitations", "bounded answerability requires disclosed limitations")

        query_ids = strings(item.get("query_evidence_ids", []), path + ".query_evidence_ids", unique=True)
        require(all(e in evidence for e in query_ids), path + ".query_evidence_ids", "unknown evidence")
        judgments = obj(item.get("relevance_judgments"), path + ".relevance_judgments")
        for evidence_id, grade in judgments.items():
            require(evidence_id in evidence, path + ".relevance_judgments", "unknown evidence")
            require(type(grade) is int and grade in (0, 1, 2), path + ".relevance_judgments", "expected grade 0, 1, or 2")
        if action == "retrieve":
            require(any(g > 0 for g in judgments.values()), path + ".relevance_judgments", "retrieve requires a positive judgment")
        sets = array(item.get("evidence_sets"), path + ".evidence_sets", nonempty=action == "answer")
        require(action not in ("abstain", "clarify") or not sets, path + ".evidence_sets", "non-answer action cannot assert sufficient answer evidence")
        seen_sets = set()
        for index, group_ids in enumerate(sets):
            group_path = f"{path}.evidence_sets[{index}]"
            strings(group_ids, group_path, nonempty=True, unique=True)
            require(all(e in evidence and judgments.get(e, 0) > 0 for e in group_ids), group_path, "unknown evidence or missing positive judgment")
            key = frozenset(group_ids)
            require(key not in seen_sets, group_path, "duplicate sufficient evidence set")
            seen_sets.add(key)
        if split_policy == "source-disjoint":
            for evidence_id, grade in judgments.items():
                if grade > 0:
                    source = sources[evidence[evidence_id]["source_id"]]
                    bind_split(("source", source["split_group"]), split, path + ".split_group")
                    bind_split(("source_hash", source["sha256"]), split, path + ".split_group")

        verification = obj(item.get("verification"), path + ".verification")
        verified = choice(verification.get("status"), ("pending", "accepted", "rejected"), path + ".verification.status")
        method = choice(verification.get("method"), ("human", "llm", "hybrid"), path + ".verification.method")
        string(verification.get("reviewer"), path + ".verification.reviewer", nonempty=verified == "accepted")
        string(verification.get("notes"), path + ".verification.notes", nonempty=verified == "accepted")
        require(type(verification.get("independent")) is bool, path + ".verification.independent", "expected boolean")
        if verified == "accepted":
            require(verification["independent"] and verification["reviewer"] != item["author"], path + ".verification", "accepted item needs an independent reviewer")
            require(policy != "human-required" or method in ("human", "hybrid"), path + ".verification.method", "policy requires human review")
        require(not strict or verified == "accepted", path + ".verification", "freeze requires accepted items")

    if status == "frozen":
        timestamp(manifest.get("frozen_at"), "manifest.frozen_at")
        require(manifest.get("payload_sha256") == payload_hash(data), "manifest.payload_sha256", "integrity mismatch")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "JSON", f"duplicate key {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"JSON: nonfinite number {value}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "freeze"):
        sub = commands.add_parser(command)
        sub.add_argument("input", type=Path)
        if command == "freeze":
            sub.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.input.open(encoding="utf-8") as stream:
            data = json.load(stream, object_pairs_hook=unique_object, parse_constant=reject_constant)
        validate_dataset(data, for_freeze=args.command == "freeze")
        if args.command == "freeze":
            require(data["manifest"]["status"] == "draft", "manifest.status", "create a new draft version before freezing again")
            data["manifest"]["status"] = "frozen"
            data["manifest"]["frozen_at"] = datetime.now(timezone.utc).isoformat()
            data["manifest"]["payload_sha256"] = payload_hash(data)
            serialized = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
            fd = os.open(args.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(serialized)
        print(json.dumps({"status": "valid", "items": len(data["items"]), "task": data["manifest"]["task"], "frozen": data["manifest"]["status"] == "frozen"}))
        return 0
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
