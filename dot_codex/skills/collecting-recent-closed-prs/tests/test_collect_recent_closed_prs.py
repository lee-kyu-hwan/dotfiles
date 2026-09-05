"""Deterministic tests for recent-closed pull request collector primitives."""

from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
