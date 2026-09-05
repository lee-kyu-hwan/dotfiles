"""Deterministic tests for recent-closed pull request collector primitives."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from importlib import util
from pathlib import Path
import sys
import unittest


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "collect_recent_closed_prs.py"
)


def load_collector():
    """Load the production collector module by its source-file path."""
    spec = util.spec_from_file_location("collect_recent_closed_prs", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("could not create a loader for the collector script")

    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass
class FakeCompletedProcess:
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


class FakeRunner:
    """A deterministic replacement for subprocess.run."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if not self.responses:
            raise AssertionError("runner received more calls than expected")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class FakeSleep:
    def __init__(self):
        self.delays = []

    def __call__(self, delay):
        self.delays.append(delay)


class FakeSearchClient:
    """A deterministic injected GitHub client for repository-search tests."""

    def __init__(self, collector, handler):
        self.collector = collector
        self.handler = handler
        self.calls = []

    def get_json(self, endpoint, params=None):
        copied_params = dict(params or {})
        self.calls.append((endpoint, copied_params))
        payload = self.handler(endpoint, copied_params)
        if isinstance(payload, BaseException):
            raise payload
        return self.collector.ApiResponse(status=200, headers={}, payload=payload)


def included_response(status, headers=None, payload="{}"):
    header_lines = "\n".join(
        f"{name}: {value}" for name, value in (headers or {}).items()
    )
    return "HTTP/2 {status} status\n{headers}\n\n{payload}".format(
        status=status,
        headers=header_lines,
        payload=payload,
    )


class ResolveIntervalTests(unittest.TestCase):
    def test_recent_days_includes_current_partial_local_day(self):
        collector = load_collector()

        interval = collector.resolve_interval(
            start_at=None,
            end_at=None,
            start_date=None,
            end_date=None,
            recent_days=7,
            timezone_name="Asia/Seoul",
            as_of="2026-09-05T12:34:56+09:00",
        )

        self.assertEqual(interval.start_at, "2026-08-29T15:00:00Z")
        self.assertEqual(interval.end_at, "2026-09-05T03:34:56Z")
        self.assertEqual(interval.timezone, "Asia/Seoul")
        self.assertEqual(interval.input_mode, {"recent_days": 7})
        self.assertEqual(interval.as_of, "2026-09-05T03:34:56Z")
        self.assertTrue(interval.last_day_partial)

    def test_exact_timestamps_become_utc_half_open_interval(self):
        collector = load_collector()

        interval = collector.resolve_interval(
            start_at="2026-09-01T00:00:00+09:00",
            end_at="2026-09-01T01:02:03.987654+09:00",
            start_date=None,
            end_date=None,
            recent_days=None,
            timezone_name="Asia/Seoul",
            as_of=None,
        )

        self.assertEqual(interval.start_at, "2026-08-31T15:00:00Z")
        self.assertEqual(interval.end_at, "2026-08-31T16:02:03Z")
        self.assertEqual(
            interval.input_mode,
            {
                "start_at": "2026-09-01T00:00:00+09:00",
                "end_at": "2026-09-01T01:02:03.987654+09:00",
            },
        )
        self.assertFalse(interval.last_day_partial)

    def test_local_dates_cover_inclusive_dates_across_daylight_saving_change(self):
        collector = load_collector()

        interval = collector.resolve_interval(
            start_at=None,
            end_at=None,
            start_date="2026-03-07",
            end_date="2026-03-09",
            recent_days=None,
            timezone_name="America/New_York",
            as_of=None,
        )

        self.assertEqual(interval.start_at, "2026-03-07T05:00:00Z")
        self.assertEqual(interval.end_at, "2026-03-10T04:00:00Z")
        self.assertEqual(
            interval.input_mode,
            {"start_date": "2026-03-07", "end_date": "2026-03-09"},
        )

    def test_rejects_conflicting_interval_modes(self):
        collector = load_collector()

        with self.assertRaises(ValueError):
            collector.resolve_interval(
                start_at="2026-09-01T00:00:00Z",
                end_at="2026-09-02T00:00:00Z",
                start_date=None,
                end_date=None,
                recent_days=7,
                timezone_name="UTC",
                as_of=None,
            )

    def test_rejects_invalid_timezone(self):
        collector = load_collector()

        with self.assertRaises(ValueError):
            collector.resolve_interval(
                start_at=None,
                end_at=None,
                start_date="2026-09-01",
                end_date="2026-09-01",
                recent_days=None,
                timezone_name="Mars/Olympus_Mons",
                as_of=None,
            )

    def test_rejects_non_positive_recent_days(self):
        collector = load_collector()

        with self.assertRaises(ValueError):
            collector.resolve_interval(
                start_at=None,
                end_at=None,
                start_date=None,
                end_date=None,
                recent_days=0,
                timezone_name="UTC",
                as_of=None,
            )

    def test_rejects_recent_days_that_are_not_positive_integers(self):
        collector = load_collector()

        for recent_days in (7.0, True, "7", "not-a-number"):
            with self.subTest(recent_days=recent_days):
                with self.assertRaises(ValueError):
                    collector.resolve_interval(
                        start_at=None,
                        end_at=None,
                        start_date=None,
                        end_date=None,
                        recent_days=recent_days,
                        timezone_name="UTC",
                        as_of=None,
                    )

    def test_rejects_empty_or_reversed_timestamp_interval(self):
        collector = load_collector()

        with self.assertRaises(ValueError):
            collector.resolve_interval(
                start_at="2026-09-01T00:00:00Z",
                end_at="2026-09-01T00:00:00Z",
                start_date=None,
                end_date=None,
                recent_days=None,
                timezone_name="UTC",
                as_of=None,
            )

    def test_rejects_non_rfc3339_timestamp_grammar(self):
        collector = load_collector()

        for timestamp in (
            "2026-09-01 00:00:00+09:00",
            "2026-09-01T00:00:00+0900",
            "2026-09-01T00:00+09:00",
            "2026-09-01T00:00:00Z trailing",
            "2026-09-01T00:00:00+00:60",
            "2026-09-01T00:00:00+24:00",
        ):
            with self.subTest(timestamp=timestamp):
                with self.assertRaises(ValueError):
                    collector.resolve_interval(
                        start_at=timestamp,
                        end_at="2026-09-02T00:00:00Z",
                        start_date=None,
                        end_date=None,
                        recent_days=None,
                        timezone_name="UTC",
                        as_of=None,
                    )


class BuildClosedQueryTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()
        self.interval = self.collector.resolve_interval(
            start_at=None,
            end_at=None,
            start_date=None,
            end_date=None,
            recent_days=7,
            timezone_name="Asia/Seoul",
            as_of="2026-09-05T12:34:56+09:00",
        )

    def test_builds_one_inclusive_closed_qualifier_for_half_open_interval(self):
        query = self.collector.build_closed_query("owner/repo", self.interval, "all")

        self.assertEqual(query.count("closed:"), 1)
        self.assertIn("repo:owner/repo", query)
        self.assertIn("is:pr", query)
        self.assertIn("is:closed", query)
        self.assertIn("closed:2026-08-29T15:00:00Z..2026-09-05T03:34:55Z", query)

    def test_adds_merged_qualifier_only_for_merged_outcome(self):
        query = self.collector.build_closed_query("owner/repo", self.interval, "merged")

        self.assertIn("is:merged", query)
        self.assertNotIn("-is:merged", query)

    def test_adds_not_merged_qualifier_only_for_closed_unmerged_outcome(self):
        query = self.collector.build_closed_query(
            "owner/repo", self.interval, "closed-unmerged"
        )

        self.assertIn("-is:merged", query)

    def test_rejects_unknown_outcome(self):
        with self.assertRaises(ValueError):
            self.collector.build_closed_query("owner/repo", self.interval, "unknown")


class GhApiClientTests(unittest.TestCase):
    API_VERSION = "2026-03-10"

    def setUp(self):
        self.collector = load_collector()

    def make_client(self, responses, *, limit=10, clock=lambda: 1000):
        self.runner = FakeRunner(responses)
        self.sleeper = FakeSleep()
        return self.collector.GhApiClient(
            api_version=self.API_VERSION,
            budget=self.collector.RequestBudget(limit),
            runner=self.runner,
            sleeper=self.sleeper,
            clock=clock,
        )

    def test_get_json_constructs_read_only_command_and_parses_final_included_block(self):
        client = self.make_client(
            [
                FakeCompletedProcess(
                    stdout=(
                        "HTTP/1.1 200 Connection established\nProxy: example\n\n"
                        + included_response(
                            200,
                            {"eTAG": '"cached-v1"', "X-RateLimit-Remaining": "99"},
                            '{"login":"octocat"}',
                        )
                    )
                )
            ]
        )

        response = client.get_json("/user")

        self.assertEqual(response.status, 200)
        self.assertEqual(response.headers["etag"], '"cached-v1"')
        self.assertEqual(response.headers["x-ratelimit-remaining"], "99")
        self.assertEqual(response.payload, {"login": "octocat"})
        self.assertEqual(client.budget.consumed, 1)
        args, kwargs = self.runner.calls[0]
        self.assertEqual(
            args,
            [
                "gh",
                "api",
                "--method",
                "GET",
                "--include",
                "-H",
                "Accept: application/vnd.github+json",
                "-H",
                "X-GitHub-Api-Version: 2026-03-10",
                "/user",
                "-f",
                "per_page=100",
            ],
        )
        self.assertFalse(kwargs.get("shell", False))
        self.assertNotIn("Authorization", " ".join(args))

    def test_conditional_request_does_not_expose_cache_validator_in_response_metadata(self):
        client = self.make_client(
            [FakeCompletedProcess(stdout=included_response(200, {"ETag": '"new"'}, "[]"))]
        )

        response = client.get_json(
            "/repos/owner/repo/pulls/1/files",
            cached_payload=[{"name": "old"}],
            cached_etag='"old"',
        )

        args, _ = self.runner.calls[0]
        self.assertIn("If-None-Match: \"old\"", args)
        self.assertNotIn("if-none-match", response.headers)
        self.assertNotIn("authorization", response.headers)
        self.assertEqual(response.payload, [])

    def test_matching_304_reuses_cached_payload_without_upgrading_completeness(self):
        client = self.make_client(
            [FakeCompletedProcess(stdout=included_response(304, {"ETag": '"old"'}, ""))]
        )
        cached_payload = {"items": [1], "completeness": {"pages_complete": False}}

        response = client.get_json(
            "/repos/owner/repo/pulls/1/files",
            cached_payload=cached_payload,
            cached_etag='"old"',
        )

        self.assertEqual(response.status, 304)
        self.assertIs(response.payload, cached_payload)
        self.assertFalse(response.payload["completeness"]["pages_complete"])

    def test_304_without_matching_cached_payload_fails(self):
        client = self.make_client(
            [FakeCompletedProcess(stdout=included_response(304, {"ETag": '"old"'}, ""))]
        )

        with self.assertRaises(self.collector.ApiFailure) as raised:
            client.get_json("/repos/owner/repo", cached_payload={"old": True}, cached_etag='"other"')

        self.assertEqual(raised.exception.status, 304)

    def test_classifies_non_retryable_repository_failures(self):
        for status, expected in ((401, "unauthorized"), (404, "not-found-or-inaccessible"), (403, "forbidden")):
            with self.subTest(status=status):
                self.assertEqual(
                    self.collector.classify_repository_failure(status=status), expected
                )

    def test_403_with_retry_after_has_precedence_and_retries_at_most_three_times(self):
        retry = FakeCompletedProcess(
            stdout=included_response(403, {"Retry-After": "60", "X-RateLimit-Reset": "3000"}),
            stderr="Authorization: Bearer ghp_secret-token",
        )
        client = self.make_client([retry, retry, retry, retry])

        with self.assertRaises(self.collector.ApiFailure) as raised:
            client.get_json("/user")

        self.assertEqual(len(self.runner.calls), 4)
        self.assertEqual(client.budget.consumed, 4)
        self.assertEqual(self.sleeper.delays, [60, 60, 60])
        self.assertNotIn("ghp_secret-token", raised.exception.diagnostics)
        self.assertNotIn("authorization", raised.exception.diagnostics.lower())

    def test_rate_limit_reset_precedes_capped_exponential_fallback(self):
        client = self.make_client(
            [
                FakeCompletedProcess(
                    stdout=included_response(429, {"x-ratelimit-reset": "1125"})
                ),
                FakeCompletedProcess(stdout=included_response(200, payload="{}")),
            ],
            clock=lambda: 1000,
        )

        client.get_json("/user")

        self.assertEqual(self.sleeper.delays, [125])

    def test_headerless_secondary_limit_uses_capped_exponential_backoff(self):
        client = self.make_client(
            [
                FakeCompletedProcess(stdout=included_response(403, payload='{"message":"secondary rate limit"}')),
                FakeCompletedProcess(stdout=included_response(429, payload='{"message":"rate limit"}')),
                FakeCompletedProcess(stdout=included_response(200, payload="{}")),
            ]
        )

        client.get_json("/user")

        self.assertEqual(self.sleeper.delays, [60, 120])

    def test_retryable_server_and_transport_failures_are_bounded(self):
        client = self.make_client(
            [
                FakeCompletedProcess(stdout=included_response(500, payload='{"message":"oops"}')),
                OSError("network down"),
                FakeCompletedProcess(stdout=included_response(502, payload='{"message":"again"}')),
                OSError("still down"),
            ]
        )

        with self.assertRaises(self.collector.ApiFailure):
            client.get_json("/user")

        self.assertEqual(len(self.runner.calls), 4)
        self.assertEqual(self.sleeper.delays, [1, 2, 4])

    def test_malformed_json_is_not_retried(self):
        client = self.make_client(
            [FakeCompletedProcess(stdout=included_response(200, payload="not json"))]
        )

        with self.assertRaises(self.collector.ApiFailure) as raised:
            client.get_json("/user")

        self.assertEqual(raised.exception.status, 200)
        self.assertEqual(len(self.runner.calls), 1)

    def test_budget_is_consumed_before_every_attempt_and_stops_new_requests(self):
        client = self.make_client(
            [FakeCompletedProcess(stdout=included_response(500, payload="{}"))], limit=1
        )

        with self.assertRaises(self.collector.BudgetExhausted):
            client.get_json("/user")

        self.assertEqual(client.budget.consumed, 1)
        self.assertEqual(len(self.runner.calls), 1)

    def test_rejects_calendar_invalid_api_version_before_runner_call(self):
        runner = FakeRunner([])

        with self.assertRaises(ValueError):
            self.collector.GhApiClient(
                api_version="2026-99-99",
                budget=self.collector.RequestBudget(1),
                runner=runner,
            )

        self.assertEqual(runner.calls, [])

    def test_redacts_conditional_header_values_from_error_messages_and_diagnostics(self):
        failure = self.collector.ApiFailure(
            'If-None-Match: "cached-secret"\nrequest failed',
            diagnostics='retry context\niF-NoNe-MaTcH: "cached-secret"\nkeep this context',
        )

        self.assertNotIn("cached-secret", str(failure))
        self.assertNotIn("cached-secret", failure.diagnostics)
        self.assertNotIn("if-none-match", str(failure).lower())
        self.assertNotIn("if-none-match", failure.diagnostics.lower())
        self.assertIn("request failed", str(failure))
        self.assertIn("retry context", failure.diagnostics)
        self.assertIn("keep this context", failure.diagnostics)

    def test_rejects_caller_per_page_override_before_runner_call(self):
        client = self.make_client([], limit=1)

        with self.assertRaises(ValueError):
            client.get_json("/user", params={"per_page": 1})

        self.assertEqual(self.runner.calls, [])
        self.assertEqual(client.budget.consumed, 0)

    def test_global_preflight_returns_login_and_versions_and_rejects_unsupported_version(self):
        client = self.make_client(
            [
                FakeCompletedProcess(stdout="gh version 2.99.0 (2026-09-01)\n"),
                FakeCompletedProcess(stdout=included_response(200, payload='{"login":"octocat"}')),
                FakeCompletedProcess(stdout=included_response(200, payload='["2026-03-10", "2022-11-28"]')),
            ]
        )

        preflight = client.global_preflight()

        self.assertEqual(preflight, {"login": "octocat", "client_version": "2.99.0", "api_version": self.API_VERSION})
        self.assertEqual(self.runner.calls[0][0], ["gh", "--version"])
        self.assertEqual(client.budget.consumed, 2)

        unsupported = self.make_client(
            [
                FakeCompletedProcess(stdout="gh version 2.99.0\n"),
                FakeCompletedProcess(stdout=included_response(200, payload='{"login":"octocat"}')),
                FakeCompletedProcess(stdout=included_response(200, payload='["2022-11-28"]')),
            ]
        )
        with self.assertRaises(self.collector.ApiFailure):
            unsupported.global_preflight()
        self.assertEqual(unsupported.budget.consumed, 2)


class MigrateManifestV1Tests(unittest.TestCase):
    def test_migrates_known_fields_without_losing_unknown_json_values(self):
        collector = load_collector()
        legacy = {
            "schema_version": "1.0.0",
            "generated_by": {"name": "fixture", "revision": "one"},
            "top_level_unknown": [None, False, {"nested": [1, "two"]}],
            "runs": [
                {
                    "run_key": "fixture-recent-20260903",
                    "kind": "search-api",
                    "captured_at": "2026-09-03T21:45:07Z",
                    "github_api_version": "2022-11-28",
                    "github_cli_version": "2.98.0",
                    "fixture_only": {"flag": False, "items": [None, 3]},
                    "nullable": None,
                }
            ],
        }

        migrated = collector.migrate_manifest_v1(legacy)

        self.assertEqual(migrated["schema_version"], "2.0.0")
        self.assertEqual(migrated["generated_by"], legacy["generated_by"])
        self.assertEqual(migrated["legacy_payload"]["top_level_unknown"], legacy["top_level_unknown"])
        record = migrated["records"][0]
        self.assertEqual(record["run_id"], "fixture-recent-20260903")
        self.assertEqual(record["collection_method"], "search-api")
        self.assertEqual(record["completed_at"], "2026-09-03T21:45:07Z")
        self.assertEqual(record["api_version"], "2022-11-28")
        self.assertEqual(record["client_version"], "2.98.0")
        self.assertIsNone(record["started_at"])
        self.assertEqual(record["collection_status"], "partial")
        self.assertEqual(record["legacy_payload"]["fixture_only"]["flag"], False)
        self.assertIsNone(record["legacy_payload"]["nullable"])
        self.assertTrue(record["migration_warnings"])

        legacy["runs"][0]["fixture_only"]["items"].append("later")
        self.assertEqual(record["legacy_payload"]["fixture_only"]["items"], [None, 3])

    def test_rejects_unsupported_source_schema_versions(self):
        collector = load_collector()

        with self.assertRaises(ValueError):
            collector.migrate_manifest_v1({"schema_version": "2.0.0", "runs": []})


class RepositorySearchTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()
        self.interval = self.collector.resolve_interval(
            start_at="2026-09-01T00:00:00Z",
            end_at="2026-09-01T00:00:04Z",
            start_date=None,
            end_date=None,
            recent_days=None,
            timezone_name="UTC",
            as_of=None,
        )

    def test_collects_one_repository_with_exact_filter_dedupe_order_and_cap(self):
        def handler(endpoint, params):
            if endpoint == "/repos/owner/repo":
                return {"node_id": "R_1", "full_name": "owner/repo", "default_branch": "main"}
            self.assertEqual(endpoint, "/search/issues")
            self.assertEqual(params["page"], 1)
            return {
                "total_count": 6,
                "incomplete_results": False,
                "items": [
                    {"node_id": "P-start", "number": 1, "closed_at": "2026-09-01T00:00:00Z"},
                    {"node_id": "P-last", "number": 2, "closed_at": "2026-09-01T00:00:03Z"},
                    {"node_id": "P-excluded", "number": 3, "closed_at": "2026-09-01T00:00:04Z"},
                    {"node_id": "P-duplicate", "number": 4, "closed_at": "2026-09-01T00:00:02Z"},
                    {"node_id": "P-duplicate", "number": 99, "closed_at": "2026-09-01T00:00:02Z"},
                    {"node_id": "P-outside", "number": 6, "closed_at": "2026-08-31T23:59:59Z"},
                ],
            }

        client = FakeSearchClient(self.collector, handler)
        result = self.collector.collect_repository_hits(
            client=client,
            repository="owner/repo",
            interval=self.interval,
            outcome="merged",
            max_per_repository=2,
        )

        self.assertEqual(result.preflight["node_id"], "R_1")
        self.assertEqual(result.collection_status, "collected")
        self.assertEqual(result.matched_count, 3)
        self.assertEqual(result.selected_count, 2)
        self.assertEqual(result.excluded_by_cap, 1)
        self.assertEqual([hit["node_id"] for hit in result.hits], ["P-last", "P-duplicate", "P-start"])
        self.assertEqual([hit["node_id"] for hit in result.selected_hits], ["P-last", "P-duplicate"])
        self.assertEqual([hit["node_id"] for hit in result.overflow_hits], ["P-start"])
        self.assertEqual(result.partitions[0].interval, ("2026-09-01T00:00:00Z", "2026-09-01T00:00:04Z"))
        self.assertTrue(result.partitions[0].pagination_complete)
        self.assertEqual(result.partitions[0].completion_state, "complete")
        with self.assertRaises(FrozenInstanceError):
            result.partitions[0].failure = "mutated"
        query = client.calls[1][1]["q"]
        self.assertEqual(query.count("closed:"), 1)
        self.assertIn("is:merged", query)

    def test_marks_no_results_after_a_successful_repository_preflight(self):
        def handler(endpoint, params):
            if endpoint == "/repos/owner/empty":
                return {"node_id": "R_empty", "full_name": "owner/empty"}
            return {"total_count": 0, "incomplete_results": False, "items": []}

        result = self.collector.collect_repository_hits(
            client=FakeSearchClient(self.collector, handler),
            repository="owner/empty",
            interval=self.interval,
            outcome="all",
            max_per_repository=2,
        )

        self.assertEqual(result.collection_status, "no-results")
        self.assertEqual(result.matched_count, 0)
        self.assertEqual(result.selected_count, 0)
        self.assertEqual(result.excluded_by_cap, 0)

    def test_recursively_splits_unsafe_partitions_and_keeps_safe_hits(self):
        def item(node_id, number, closed_at):
            return {"node_id": node_id, "number": number, "closed_at": closed_at}

        first_leaf = [item("P-left-{0}".format(index), index, "2026-09-01T00:00:01Z") for index in range(100)]
        second_leaf = [item("P-left-100", 100, "2026-09-01T00:00:01Z")]

        def handler(endpoint, params):
            if endpoint == "/repos/owner/repo":
                return {"node_id": "R_1", "full_name": "owner/repo"}
            query = params["q"]
            page = params["page"]
            if "closed:2026-09-01T00:00:00Z..2026-09-01T00:00:03Z" in query:
                return {"total_count": 1000, "incomplete_results": False, "items": []}
            if "closed:2026-09-01T00:00:00Z..2026-09-01T00:00:01Z" in query:
                return {
                    "total_count": 101,
                    "incomplete_results": False,
                    "items": first_leaf if page == 1 else second_leaf,
                }
            if "closed:2026-09-01T00:00:02Z..2026-09-01T00:00:03Z" in query:
                return {"total_count": 1000, "incomplete_results": True, "items": []}
            if "closed:2026-09-01T00:00:02Z..2026-09-01T00:00:02Z" in query:
                return {"total_count": 1, "incomplete_results": False, "items": [item("P-mid", 101, "2026-09-01T00:00:02Z")]}
            if "closed:2026-09-01T00:00:03Z..2026-09-01T00:00:03Z" in query:
                return {"total_count": 1000, "incomplete_results": True, "items": []}
            raise AssertionError("unexpected search query: {0}".format(query))

        client = FakeSearchClient(self.collector, handler)
        result = self.collector.collect_repository_hits(
            client=client,
            repository="owner/repo",
            interval=self.interval,
            outcome="closed-unmerged",
            max_per_repository=200,
        )

        self.assertEqual(result.collection_status, "partial")
        self.assertEqual(
            [partition.interval for partition in result.partitions],
            [
                ("2026-09-01T00:00:00Z", "2026-09-01T00:00:02Z"),
                ("2026-09-01T00:00:02Z", "2026-09-01T00:00:03Z"),
                ("2026-09-01T00:00:03Z", "2026-09-01T00:00:04Z"),
            ],
        )
        self.assertTrue(result.partitions[0].pagination_complete)
        self.assertEqual(result.partitions[2].completion_state, "failed")
        self.assertTrue(result.partitions[2].failure)
        self.assertEqual(result.matched_count, 102)
        self.assertEqual(result.selected_count, 102)
        self.assertEqual(len({hit["node_id"] for hit in result.hits}), len(result.hits))
        for endpoint, params in client.calls:
            if endpoint == "/search/issues":
                self.assertEqual(params["q"].count("closed:"), 1)
                self.assertIn("-is:merged", params["q"])
                self.assertNotIn("per_page", params)
        leaf_pages = [params["page"] for endpoint, params in client.calls if endpoint == "/search/issues" and "00:00:00Z..2026-09-01T00:00:01Z" in params["q"]]
        self.assertEqual(leaf_pages, [1, 2])

    def test_budget_stop_records_current_partition_without_starting_its_sibling(self):
        def handler(endpoint, params):
            if endpoint == "/repos/owner/repo":
                return {"node_id": "R_1", "full_name": "owner/repo"}
            if "00:00:00Z..2026-09-01T00:00:03Z" in params["q"]:
                return {"total_count": 1000, "incomplete_results": False, "items": []}
            raise self.collector.BudgetExhausted("request budget exhausted")

        client = FakeSearchClient(self.collector, handler)
        result = self.collector.collect_repository_hits(
            client=client,
            repository="owner/repo",
            interval=self.interval,
            outcome="all",
            max_per_repository=2,
        )

        self.assertEqual(result.collection_status, "partial")
        self.assertEqual(len(result.partitions), 1)
        self.assertEqual(result.partitions[0].completion_state, "failed")
        self.assertIn("budget exhausted", result.partitions[0].failure)
        search_calls = [call for call in client.calls if call[0] == "/search/issues"]
        self.assertEqual(len(search_calls), 2)

    def test_repositories_keep_independent_caps(self):
        def handler(endpoint, params):
            if endpoint.startswith("/repos/"):
                return {"node_id": endpoint, "full_name": endpoint.removeprefix("/repos/")}
            repository = "high" if "repo:owner/high" in params["q"] else "low"
            count = 3 if repository == "high" else 2
            return {
                "total_count": count,
                "incomplete_results": False,
                "items": [
                    {"node_id": "P-{0}-{1}".format(repository, number), "number": number, "closed_at": "2026-09-01T00:00:0{0}Z".format(number)}
                    for number in range(count)
                ],
            }

        client = FakeSearchClient(self.collector, handler)
        high = self.collector.collect_repository_hits(client, "owner/high", self.interval, "all", 2)
        low = self.collector.collect_repository_hits(client, "owner/low", self.interval, "all", 2)

        self.assertEqual((high.selected_count, high.excluded_by_cap), (2, 1))
        self.assertEqual((low.selected_count, low.excluded_by_cap), (2, 0))
        queries = [params["q"] for endpoint, params in client.calls if endpoint == "/search/issues"]
        self.assertEqual(sum("repo:owner/high" in query for query in queries), 1)
        self.assertEqual(sum("repo:owner/low" in query for query in queries), 1)


if __name__ == "__main__":
    unittest.main()
