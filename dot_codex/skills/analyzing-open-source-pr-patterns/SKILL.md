---
name: analyzing-open-source-pr-patterns
description: Use when analyzing an already normalized corpus of open-source pull requests to extract evidence-backed, reusable change patterns. Do not use for PR collection, live candidate validation, or personal GitHub work logs.
---

# Analyze Open-Source PR Patterns

Analyze only the supplied local normalized corpus and optional existing local analysis output. Read [the data contract](references/data-contract.md) and [the analysis contract](references/analysis-contract.md) completely before producing results.

1. Resolve `SKILL_DIR` to this skill's absolute directory. Run `python3 "$SKILL_DIR/scripts/validate_corpus.py" --print-revision` and retain the returned `sha256:...` as `ANALYZER_REVISION`. Then run `python3 "$SKILL_DIR/scripts/validate_corpus.py" CURRENT [--existing PREVIOUS_CORPUS]`. `--existing` accepts only a previous normalized corpus. Stop for an explicit versioned migration, corrected input, or preservation-conflict resolution when validation fails; never silently repair or retry it.
2. Construct the exact output envelope in the analysis contract. Preserve every normalized input field and type. Match resolved records by PR node identity and unresolved records by observed PR URL. Add one current `analysis` and append exactly one strict current snapshot to each record's existing history. Preserve every old history item byte-for-data exactly, even when it predates the strict snapshot shape.
3. Separate changed facts, motivation, review judgment, and closure reason into typed evidence claims. When direct closure-rationale evidence is absent and the normalized reason is `unknown`, emit exactly `{"value":null,"basis":"unknown","evidence_links":[]}` for `analysis.closure_reason`. State, chronology, and review judgment are not closure reasons. Grade evidence categories independently; missing or partial required evidence without an adequate alternative cannot produce high confidence.
4. Reuse stable `PAT-*` identities from the optional prior output. Emit every prior pattern, preserve its complete `pattern_history` as an exact prefix, and append one current snapshot. A new pattern starts with one snapshot. Create patterns only for genuinely recurring behavior and state applicability, counterconditions, search clues, tests, and remaining maintainer judgment.
5. Record source licenses as the required per-PR objects. Default provenance to `independent-reimplementation`; unknown licenses do not support copied code. Use `adapted` or `verbatim` only with compatibility and review evidence.
6. Write the result to a new `OUTPUT`; never mutate inputs. Set every current generator/snapshot revision to `ANALYZER_REVISION`, then run `python3 "$SKILL_DIR/scripts/validate_corpus.py" CURRENT --analysis-output OUTPUT [--existing-analysis PREVIOUS_OUTPUT]`. Do not return or use an output that fails. When machine-readable JSON is requested, return only the validated JSON object, without a fence or prose.
7. Emit no `CAN-*` field or record. Do not collect live PRs, browse or clone candidate repositories, or create external state. End candidate requests with the verifier handoff specified by the analysis contract.

Capabilities are local historical analysis and requested local output writing only. Stop on unsupported schema, invalid input/output, unresolved identity needing an ID, preservation conflict, or unavailable required evidence; report the required next action rather than inventing data.
