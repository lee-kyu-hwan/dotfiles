#!/usr/bin/env python3
"""Check worker results against the corpus: verbatim quotes and distinct supporting PRs.

Every object in a result that has both `pr` (a digest key) and `quote` is checked.
The quote must sit inside one source text of that PR in the corpus, compared the
way validate_corpus.py compares final pattern quotes: HTML comments dropped and
whitespace collapsed, nothing else. Stitched (`...`) or reworded quotes fail.

Extraction results report, per pattern, the distinct PRs whose supporting quote
verified; a pattern is grounded with two or more. Verification results report
the PRs whose `holds: true` check verified. `verified_evidence` lists every
verified quote with its PR-* id so the coordinator can synthesize candidates and
write pattern quotes without re-reading the digest.

Prints a JSON report. Exit 0 when every quote verified, 1 when any failed (drop
those quotes; do not repair them), 2 on invalid input.
"""

import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_digest import DigestError, records_by_key  # noqa: E402
from validate_corpus import (  # noqa: E402
    MAX_QUOTE_LENGTH,
    MIN_QUOTE_LENGTH,
    _validate_document,
    clean_text,
    quote_in_record,
)


def _walk(value, path="$"):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from _walk(child, path + "." + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, path + "[" + str(index) + "]")


def _check_quote(records, key, quote):
    if not isinstance(key, str) or key not in records:
        return "unknown-key"
    cleaned = clean_text(quote) if isinstance(quote, str) else ""
    if not cleaned:
        return "empty-quote"
    if not MIN_QUOTE_LENGTH <= len(cleaned) <= MAX_QUOTE_LENGTH:
        return "length"
    if not quote_in_record(records[key], cleaned):
        return "not-verbatim"
    return None


def _grounding(keys, records):
    with_ids = sorted({key for key in keys if records[key].get("pr_id")})
    repositories = {records[key]["repository"].get("full_name") for key in with_ids
                    if isinstance(records[key].get("repository"), dict)}
    return {"prs": with_ids, "repositories": len(repositories), "grounded": len(with_ids) >= 2}


def check_result(path, result, records):
    verified, failures, evidence = {}, [], []
    for location, item in _walk(result):
        if "pr" not in item or "quote" not in item:
            continue
        reason = _check_quote(records, item["pr"], item["quote"])
        if reason:
            failures.append({"path": location, "pr": item["pr"], "reason": reason,
                             "quote": str(item["quote"])[:200]})
            continue
        verified[location] = item["pr"]
        record = records[item["pr"]]
        evidence.append({"file": path, "path": location, "pr": item["pr"], "pr_id": record.get("pr_id"),
                         "quote": clean_text(item["quote"])})
    report = {"file": path, "quotes": {"verified": len(verified), "total": len(verified) + len(failures)},
              "failures": failures}
    patterns = result.get("patterns") if isinstance(result, dict) else None
    if isinstance(patterns, list):
        report["kind"] = "extraction"
        report["patterns"] = []
        for index, pattern in enumerate(patterns):
            if not isinstance(pattern, dict):
                continue
            prefix = "$.patterns[" + str(index) + "].evidence["
            evidence_items = pattern.get("evidence")
            supporting = [
                verified[prefix + str(position) + "]"]
                for position, item in enumerate(evidence_items if isinstance(evidence_items, list) else [])
                if isinstance(item, dict) and item.get("role", "supports") == "supports"
                and prefix + str(position) + "]" in verified
            ]
            report["patterns"].append({"title": pattern.get("title"), **_grounding(supporting, records)})
    if isinstance(result, dict) and isinstance(result.get("evidence_checks"), list):
        report["kind"] = "verification"
        confirmed = [
            verified["$.evidence_checks[" + str(position) + "]"]
            for position, item in enumerate(result["evidence_checks"])
            if isinstance(item, dict) and item.get("holds") is True
            and "$.evidence_checks[" + str(position) + "]" in verified
        ]
        counterexamples = [location for location in verified if location.startswith("$.counterexamples[")]
        report["verification"] = {
            "id": result.get("id"),
            "verdict": result.get("verdict"),
            "actionable": result.get("actionable"),
            "confidence": result.get("confidence"),
            "counterexamples_verified": len(counterexamples),
            **_grounding(confirmed, records),
        }
    report.setdefault("kind", "other")
    return report, evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("current", help="the corpus the digest was built from")
    parser.add_argument("results", nargs="+", help="worker result JSON files (<prompt>.result.json)")
    args = parser.parse_args(argv)
    try:
        corpus = json.loads(Path(args.current).read_text(encoding="utf-8"))
        errors = _validate_document(corpus, "current")
        if errors:
            raise DigestError("; ".join(errors))
        records = records_by_key(corpus)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DigestError) as error:
        print("corpus could not be used: " + str(error), file=sys.stderr)
        return 2

    files, evidence = [], []
    for path in args.results:
        try:
            result = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            print("result could not be read as JSON: " + path + ": " + str(error), file=sys.stderr)
            return 2
        report, verified = check_result(path, result, records)
        files.append(report)
        evidence.extend(verified)
    totals = {
        "verified": sum(report["quotes"]["verified"] for report in files),
        "total": sum(report["quotes"]["total"] for report in files),
    }
    print(json.dumps({"totals": totals, "files": files, "verified_evidence": evidence},
                     ensure_ascii=False, indent=1))
    return 0 if totals["verified"] == totals["total"] else 1


if __name__ == "__main__":
    sys.exit(main())
