from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from validate_review import (  # noqa: E402
    ARTIFACTS,
    EVIDENCE_FIELDS,
    FINDING_FIELDS,
    REQUIRED_FIELDS,
    SEVERITIES,
    VERDICTS,
    evaluate_gate,
    main,
    validate_review,
)


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def valid_review(artifact="plan", score=87, verdict="PASS"):
    return {
        "artifact": artifact,
        "round": 1,
        "score": score,
        "verdict": verdict,
        "blockers": [],
        "findings": [],
        "evidence": [
            {
                "claim": "The reviewed artifact is traceable to its acceptance criteria.",
                "location": "plan.md#Traceability",
                "verified": True,
            }
        ],
        "required_next_action": None,
    }


def high_finding(finding_id):
    return {
        "id": finding_id,
        "severity": "High",
        "description": "A required traceability link is missing.",
        "evidence_location": "plan.md#Traceability",
        "rubric_item": "Traceability completeness",
        "required_resolution": "Map the affected acceptance criterion to a task and verification command.",
        "new_blocker_evidence": None,
    }


def valid_plan_checks():
    return {
        "required_sections": True,
        "traceability_complete": True,
        "placeholders_absent": True,
    }


def valid_code_checks():
    return {
        "required_commands_passed": True,
        "acceptance_criteria_met": True,
        "unrelated_changes_absent": True,
        "documentation_current": True,
    }


def valid_spec_checks():
    return {
        "required_sections": True,
        "material_decisions_resolved": True,
        "acceptance_criteria_objective": True,
    }


def load_fixture(name):
    with (FIXTURES_DIR / name).open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(directory, name, value):
    path = Path(directory) / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def carried_over_high_review(finding_id="PLAN-CARRIED-001"):
    review = valid_review(verdict="PASS")
    review["round"] = 2
    review["findings"] = [high_finding(finding_id)]
    review["blockers"] = [finding_id]
    return review


class ValidateReviewTests(unittest.TestCase):
    def test_valid_plan_review_has_no_errors(self):
        review = valid_review(artifact="plan", score=87, verdict="PASS")

        self.assertEqual([], validate_review(review, "plan"))

    def test_unknown_top_level_key_is_rejected(self):
        review = valid_review()
        review["unexpected"] = True

        self.assertIn("unknown top-level field: 'unexpected'", validate_review(review, "plan"))

    def test_unknown_finding_level_key_is_rejected(self):
        finding = high_finding("PLAN-001")
        finding["unexpected"] = True
        review = valid_review()
        review["findings"] = [finding]

        self.assertIn("findings[0] has unknown field: 'unexpected'", validate_review(review, "plan"))

    def test_wrong_artifact_is_rejected_against_expected_artifact(self):
        review = valid_review(artifact="spec")

        self.assertIn(
            "artifact 'spec' does not match expected artifact 'plan'",
            validate_review(review, expected_artifact="plan"),
        )

    def test_score_must_be_an_integer_between_zero_and_one_hundred(self):
        for score, expected_error in (
            (101, "score must be between 0 and 100"),
            (-1, "score must be between 0 and 100"),
            (87.5, "score must be an integer"),
        ):
            with self.subTest(score=score):
                self.assertIn(expected_error, validate_review(valid_review(score=score), "plan"))

    def test_duplicate_finding_ids_are_rejected(self):
        review = valid_review()
        review["findings"] = [
            high_finding("PLAN-001"),
            high_finding("PLAN-001"),
        ]

        self.assertIn("duplicate finding ID: 'PLAN-001'", validate_review(review, "plan"))

    def test_blocker_id_must_resolve_to_a_finding(self):
        review = valid_review(verdict="REVISE")
        review["blockers"] = ["PLAN-001"]

        self.assertIn(
            "blockers[0] does not resolve to a finding: 'PLAN-001'",
            validate_review(review, "plan"),
        )

    def test_medium_finding_cannot_be_listed_as_a_blocker(self):
        finding = high_finding("PLAN-001")
        finding["severity"] = "Medium"
        review = valid_review(verdict="REVISE")
        review["findings"] = [finding]
        review["blockers"] = ["PLAN-001"]

        self.assertIn(
            "blocker 'PLAN-001' must resolve to a Critical or High finding",
            validate_review(review, "plan"),
        )

    def test_pass_with_required_next_action_is_rejected(self):
        review = valid_review()
        review["required_next_action"] = "Revise the traceability table."

        self.assertIn("PASS reviews must have no required_next_action", validate_review(review, "plan"))

    def test_pass_verdict_with_blockers_is_valid_but_fails_the_gate(self):
        review = valid_review(verdict="PASS")
        review["findings"] = [high_finding("PLAN-001")]
        review["blockers"] = ["PLAN-001"]

        self.assertEqual([], validate_review(review, "plan"))

        decision = evaluate_gate(review, valid_plan_checks())
        self.assertFalse(decision["passed"])
        self.assertIn("blockers_present", decision["reasons"])
        self.assertIn("critical_or_high_finding", decision["reasons"])

    def test_new_round_two_blocker_requires_evidence_unless_prior_open(self):
        review = valid_review(verdict="REVISE")
        review["round"] = 2
        review["findings"] = [high_finding("PLAN-NEW")]
        review["blockers"] = ["PLAN-NEW"]
        prior = {"open_finding_ids": ["PLAN-OLD"]}

        self.assertIn(
            "new blocker 'PLAN-NEW' at blockers[0] requires non-empty new_blocker_evidence",
            validate_review(review, "plan", prior),
        )

        review["findings"][0]["new_blocker_evidence"] = (
            "The revised plan introduced a new unmapped acceptance criterion."
        )
        self.assertEqual([], validate_review(review, "plan", prior))

    def test_missing_required_top_level_field_is_rejected(self):
        review = valid_review()
        review.pop("evidence")

        self.assertIn("missing required field: evidence", validate_review(review, "plan"))

    def test_blockers_must_contain_strings(self):
        review = valid_review(verdict="REVISE")
        review["blockers"] = [123]

        self.assertIn("blockers[0] must be a string", validate_review(review, "plan"))

    def test_duplicate_blocker_ids_are_rejected(self):
        review = valid_review(verdict="REVISE")
        review["findings"] = [high_finding("PLAN-001")]
        review["blockers"] = ["PLAN-001", "PLAN-001"]

        self.assertTrue(
            any("duplicate blocker ID" in error for error in validate_review(review, "plan"))
        )

    def test_duplicate_evidence_entries_are_rejected(self):
        review = valid_review()
        review["evidence"] = [review["evidence"][0].copy(), review["evidence"][0].copy()]

        self.assertTrue(
            any("duplicate evidence entry" in error for error in validate_review(review, "plan"))
        )

    def test_non_dict_payload_returns_specific_error(self):
        self.assertEqual(["payload must be a dict"], validate_review([]))

    def test_round_two_requires_prior(self):
        review = valid_review()
        review["round"] = 2

        self.assertIn(
            "prior is required for round >= 2",
            validate_review(review, "plan"),
        )

    def test_round_two_accepts_explicitly_empty_prior(self):
        review = valid_review()
        review["round"] = 2

        self.assertEqual([], validate_review(review, "plan", {"open_finding_ids": []}))


class PriorPayloadTests(unittest.TestCase):
    def prior(self):
        return {
            "open_finding_ids": ["PLAN-001"],
            "open_findings": [{
                "id": "PLAN-001", "severity": "High", "description": "description",
                "evidence_location": "plan.md:1", "required_resolution": "fix it",
                "resolution_claim": None, "resolution_evidence": None,
            }],
            "resolved_finding_ids": ["PLAN-000"],
        }

    def test_structured_prior_accepts_an_open_finding_superset(self):
        prior = self.prior()
        prior["open_findings"].append({
            "id": "PLAN-002", "severity": "Low", "description": "advisory",
            "evidence_location": "plan.md:2", "required_resolution": "consider it",
            "resolution_claim": "noted", "resolution_evidence": "plan.md:3",
        })
        review = valid_review(verdict="REVISE")
        review["round"] = 2
        self.assertEqual(validate_review(review, prior=prior), [])

    def test_structured_prior_rejects_malformed_and_inconsistent_fields(self):
        cases = []
        for field in ("id", "severity", "description", "evidence_location", "required_resolution", "resolution_claim", "resolution_evidence"):
            prior = self.prior()
            del prior["open_findings"][0][field]
            cases.append((f"missing {field}", prior, f"missing required field: {field}"))
        prior = self.prior(); prior["open_findings"][0]["extra"] = True; cases.append(("unknown", prior, "has unknown field: 'extra'"))
        prior = self.prior(); prior["open_findings"].append(dict(prior["open_findings"][0])); cases.append(("duplicate", prior, "duplicate prior open finding ID"))
        prior = self.prior(); prior["open_finding_ids"] = ["PLAN-404"]; cases.append(("coverage", prior, "entry missing from open_findings"))
        prior = self.prior(); prior["resolved_finding_ids"] = ["PLAN-001"]; cases.append(("overlap", prior, "overlaps open finding"))
        prior = self.prior(); prior["resolved_finding_ids"] = ["PLAN-000", "PLAN-000"]; cases.append(("duplicate resolved", prior, "duplicate prior.resolved_finding_ids entry"))
        prior = self.prior(); prior["resolved_finding_ids"] = [1]; cases.append(("nonstring resolved", prior, "prior.resolved_finding_ids[0] must be a string"))
        prior = self.prior(); prior["open_finding"] = []; cases.append(("unknown prior", prior, "prior has unknown field: 'open_finding'"))
        for label, prior, expected_error in cases:
            with self.subTest(label=label):
                review = valid_review(verdict="REVISE")
                review["round"] = 2
                self.assertTrue(
                    any(expected_error in error for error in validate_review(review, prior=prior)),
                    expected_error,
                )

    def test_structured_prior_rejects_invalid_open_finding_severity(self):
        prior = self.prior()
        prior["open_findings"][0]["severity"] = "Trivial"
        review = valid_review(verdict="REVISE")
        review["round"] = 2

        self.assertTrue(any(
            "severity must be one of" in error
            for error in validate_review(review, prior=prior)
        ))

    def test_structured_prior_rejects_empty_and_whitespace_string_fields(self):
        for field in (
            "id", "severity", "description", "evidence_location", "required_resolution",
        ):
            for value in ("", "   "):
                with self.subTest(field=field, value=repr(value)):
                    prior = self.prior()
                    prior["open_findings"][0][field] = value
                    review = valid_review(verdict="REVISE")
                    review["round"] = 2
                    self.assertTrue(any(
                        f"prior.open_findings[0].{field} must be a non-empty string" in error
                        for error in validate_review(review, prior=prior)
                    ))

    def test_structured_prior_allows_null_and_rejects_integer_resolution_fields(self):
        for field in ("resolution_claim", "resolution_evidence"):
            with self.subTest(field=field, value="null"):
                prior = self.prior()
                prior["open_findings"][0][field] = None
                review = valid_review(verdict="REVISE")
                review["round"] = 2
                self.assertEqual([], validate_review(review, prior=prior))
            with self.subTest(field=field, value="integer"):
                prior = self.prior()
                prior["open_findings"][0][field] = 1
                review = valid_review(verdict="REVISE")
                review["round"] = 2
                self.assertTrue(any(
                    f"prior.open_findings[0].{field} must be a string or null" in error
                    for error in validate_review(review, prior=prior)
                ))


class EvaluateGateTests(unittest.TestCase):
    def test_plan_score_below_threshold_fails_the_gate(self):
        review = valid_review(artifact="plan", score=84, verdict="PASS")

        decision = evaluate_gate(review, valid_plan_checks())

        self.assertFalse(decision["passed"])
        self.assertIn("score_below_85", decision["reasons"])

    def test_high_finding_overrides_a_high_plan_score(self):
        review = valid_review(artifact="plan", score=93, verdict="PASS")
        review["findings"] = [high_finding("PLAN-TRACE-001")]
        review["blockers"] = ["PLAN-TRACE-001"]

        decision = evaluate_gate(review, valid_plan_checks())

        self.assertFalse(decision["passed"])
        self.assertIn("critical_or_high_finding", decision["reasons"])

    def test_code_score_is_advisory(self):
        review = valid_review(artifact="code", score=72, verdict="PASS")

        decision = evaluate_gate(review, valid_code_checks())

        self.assertTrue(decision["passed"])

    def test_failed_required_command_blocks_the_code_gate(self):
        review = valid_review(artifact="code", score=99, verdict="PASS")
        checks = valid_code_checks()
        checks["required_commands_passed"] = False

        decision = evaluate_gate(review, checks)

        self.assertFalse(decision["passed"])
        self.assertIn("required_commands_failed", decision["reasons"])

    def test_missing_spec_check_fails_closed(self):
        review = valid_review(artifact="spec", score=91, verdict="PASS")
        checks = valid_spec_checks()
        checks.pop("required_sections")

        decision = evaluate_gate(review, checks)

        self.assertFalse(decision["passed"])
        self.assertIn("missing_check:required_sections", decision["reasons"])

    def test_failed_plan_check_blocks_the_gate(self):
        review = valid_review(artifact="plan", score=91, verdict="PASS")
        checks = valid_plan_checks()
        checks["placeholders_absent"] = False

        decision = evaluate_gate(review, checks)

        self.assertFalse(decision["passed"])
        self.assertIn("check_failed:placeholders_absent", decision["reasons"])

    def test_non_pass_verdict_blocks_a_clean_gate(self):
        review = valid_review(artifact="plan", score=91, verdict="REVISE")

        decision = evaluate_gate(review, valid_plan_checks())

        self.assertFalse(decision["passed"])
        self.assertIn("verdict_not_pass", decision["reasons"])

    def test_evaluate_gate_rejects_an_invalid_payload(self):
        review = valid_review()
        review.pop("evidence")

        with self.assertRaises(ValueError):
            evaluate_gate(review, valid_plan_checks())

    def test_evaluate_gate_rejects_non_dict_checks(self):
        with self.assertRaises(ValueError):
            evaluate_gate(valid_review(), [])

    def test_evaluate_gate_rejects_non_boolean_check_values(self):
        checks = valid_plan_checks()
        checks["required_sections"] = 1

        with self.assertRaises(ValueError):
            evaluate_gate(valid_review(), checks)

    def test_evaluate_gate_rejects_mismatched_expected_artifact(self):
        review = valid_review(artifact="code", score=40)

        with self.assertRaises(ValueError):
            evaluate_gate(review, valid_code_checks(), expected_artifact="plan")

    def test_round_two_carried_over_high_blocker_fails_gate(self):
        review = carried_over_high_review()
        prior = {"open_finding_ids": ["PLAN-CARRIED-001"]}

        decision = evaluate_gate(
            review,
            valid_plan_checks(),
            expected_artifact="plan",
            prior=prior,
        )

        self.assertFalse(decision["passed"])
        self.assertIn("blockers_present", decision["reasons"])
        self.assertIn("critical_or_high_finding", decision["reasons"])


class EvidenceVerificationTests(unittest.TestCase):
    def test_verified_is_required_boolean_and_blocks_pass_when_false(self):
        missing = valid_review()
        del missing["evidence"][0]["verified"]
        self.assertTrue(any(
            "evidence[0] missing required field: verified" in error
            for error in validate_review(missing)
        ))
        string_value = valid_review()
        string_value["evidence"][0]["verified"] = "false"
        self.assertTrue(any(
            "evidence[0].verified must be a boolean" in error
            for error in validate_review(string_value)
        ))
        integer_value = valid_review()
        integer_value["evidence"][0]["verified"] = 0
        self.assertTrue(any(
            "evidence[0].verified must be a boolean" in error
            for error in validate_review(integer_value)
        ))
        false_pass = valid_review()
        false_pass["evidence"][0]["verified"] = False
        self.assertTrue(any(
            "PASS reviews must not contain unverified evidence" in error
            for error in validate_review(false_pass)
        ))
        revise = valid_review(verdict="REVISE")
        revise["evidence"][0]["verified"] = False
        self.assertEqual(validate_review(revise), [])

    def test_verified_evidence_still_requires_a_non_empty_claim(self):
        review = valid_review()
        review["evidence"][0]["claim"] = ""

        self.assertTrue(any(
            "evidence[0].claim must be a non-empty string" in error
            for error in validate_review(review)
        ))


class SchemaDriftTests(unittest.TestCase):
    def test_schema_required_fields_and_enums_match_python_constants(self):
        import json

        schema_path = Path(__file__).resolve().parents[1] / "schemas" / "review.schema.json"
        with schema_path.open(encoding="utf-8") as stream:
            schema = json.load(stream)

        self.assertEqual(set(schema["required"]), set(REQUIRED_FIELDS))
        self.assertEqual(
            set(schema["properties"]["artifact"]["enum"]),
            set(ARTIFACTS),
        )
        self.assertEqual(
            set(schema["properties"]["verdict"]["enum"]),
            set(VERDICTS),
        )
        self.assertEqual(
            set(schema["$defs"]["finding"]["properties"]["severity"]["enum"]),
            set(SEVERITIES),
        )

        finding_schema = schema["$defs"]["finding"]
        evidence_schema = schema["properties"]["evidence"]["items"]
        self.assertEqual(set(finding_schema["required"]), set(FINDING_FIELDS))
        self.assertEqual(set(evidence_schema["required"]), set(EVIDENCE_FIELDS))
        self.assertIs(schema["additionalProperties"], False)
        self.assertIs(finding_schema["additionalProperties"], False)
        self.assertIs(evidence_schema["additionalProperties"], False)
        self.assertEqual("boolean", evidence_schema["properties"]["verified"]["type"])
        self.assertIs(schema["properties"]["blockers"]["uniqueItems"], True)
        self.assertIs(schema["properties"]["evidence"]["uniqueItems"], True)
        self.assertEqual(0, schema["properties"]["score"]["minimum"])
        self.assertEqual(100, schema["properties"]["score"]["maximum"])
        self.assertEqual(1, schema["properties"]["round"]["minimum"])

        for field in (
            "id",
            "description",
            "evidence_location",
            "rubric_item",
            "required_resolution",
        ):
            self.assertEqual(1, finding_schema["properties"][field]["minLength"])
        for field in ("claim", "location"):
            self.assertEqual(1, evidence_schema["properties"][field]["minLength"])


class FixtureTests(unittest.TestCase):
    def test_valid_plan_fixture_passes_validation(self):
        review = load_fixture("review-valid-plan.json")

        self.assertEqual([], validate_review(review, "plan"))

    def test_high_finding_fixture_passes_validation_but_fails_plan_gate(self):
        review = load_fixture("review-high-finding.json")

        self.assertEqual([], validate_review(review, "plan"))
        decision = evaluate_gate(review, valid_plan_checks())
        self.assertFalse(decision["passed"])
        self.assertIn("critical_or_high_finding", decision["reasons"])

    def test_verification_pass_fixture_allows_valid_plan_to_pass(self):
        review = load_fixture("review-valid-plan.json")
        checks = load_fixture("verification-pass.json")

        self.assertEqual(9, len(checks))
        self.assertTrue(all(checks.values()))
        decision = evaluate_gate(review, checks)
        self.assertTrue(decision["passed"])


class CLITests(unittest.TestCase):
    def invoke_main(self, args, output=None):
        if output is None:
            output = io.StringIO()
        with redirect_stdout(output):
            result = main(args)
        return result, output

    def test_gate_cli_returns_zero_for_valid_plan_and_verification(self):
        with TemporaryDirectory() as directory:
            review_path = write_json(
                directory,
                "review.json",
                load_fixture("review-valid-plan.json"),
            )
            checks_path = write_json(
                directory,
                "checks.json",
                load_fixture("verification-pass.json"),
            )

            result, _ = self.invoke_main([
                "gate",
                "--input",
                str(review_path),
                "--checks",
                str(checks_path),
            ])

        self.assertEqual(0, result)

    def test_gate_cli_returns_two_for_malformed_input_file(self):
        with TemporaryDirectory() as directory:
            review_path = Path(directory) / "review.json"
            review_path.write_text("{", encoding="utf-8")
            checks_path = write_json(
                directory,
                "checks.json",
                load_fixture("verification-pass.json"),
            )

            result, _ = self.invoke_main([
                "gate",
                "--input",
                str(review_path),
                "--checks",
                str(checks_path),
            ])

        self.assertEqual(2, result)

    def test_gate_cli_returns_three_for_high_finding_fixture(self):
        with TemporaryDirectory() as directory:
            review_path = write_json(
                directory,
                "review.json",
                load_fixture("review-high-finding.json"),
            )
            checks_path = write_json(
                directory,
                "checks.json",
                load_fixture("verification-pass.json"),
            )

            result, _ = self.invoke_main([
                "gate",
                "--input",
                str(review_path),
                "--checks",
                str(checks_path),
            ])

        self.assertEqual(3, result)

    def test_gate_cli_returns_three_for_round_two_carried_over_blocker(self):
        review = carried_over_high_review()
        prior = {"open_finding_ids": ["PLAN-CARRIED-001"]}
        with TemporaryDirectory() as directory:
            review_path = write_json(directory, "review.json", review)
            checks_path = write_json(
                directory,
                "checks.json",
                load_fixture("verification-pass.json"),
            )
            prior_path = write_json(directory, "prior.json", prior)

            result, _ = self.invoke_main([
                "gate",
                "--input",
                str(review_path),
                "--checks",
                str(checks_path),
                "--artifact",
                "plan",
                "--prior",
                str(prior_path),
            ])

        self.assertEqual(3, result)

    def test_gate_cli_value_error_uses_errors_key(self):
        review = valid_review(artifact="code", score=40)
        checks = valid_code_checks()
        with TemporaryDirectory() as directory:
            review_path = write_json(directory, "review.json", review)
            checks_path = write_json(directory, "checks.json", checks)

            output = io.StringIO()
            result, _ = self.invoke_main([
                "gate",
                "--input",
                str(review_path),
                "--checks",
                str(checks_path),
                "--artifact",
                "plan",
            ], output)

        self.assertEqual(2, result)
        response = json.loads(output.getvalue())
        self.assertEqual(False, response["passed"])
        self.assertIn("errors", response)
        self.assertNotIn("reasons", response)


if __name__ == "__main__":
    unittest.main()
