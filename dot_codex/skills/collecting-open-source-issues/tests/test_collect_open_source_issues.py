"""Contract tests for the general Issue collector."""

from __future__ import annotations

import contextlib
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import shutil
import tempfile
from types import SimpleNamespace
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "collect_open_source_issues.py"
FIXTURES = SKILL_DIR / "tests" / "fixtures"
REPO = "synthetic-lab/widget"
JANUARY = ("--start-at", "2030-01-01T00:00:00Z", "--end-at", "2030-02-01T00:00:00Z")
CAPTURED_AT = "2030-02-02T00:00:00Z"


def load_collector():
    if not SCRIPT.is_file():
        raise AssertionError("general Issue collector script has not been implemented")
    spec = importlib.util.spec_from_file_location("collect_open_source_issues", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("general Issue collector module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _http(status, payload, headers=None):
    reason = {200: "OK", 404: "Not Found", 403: "Forbidden", 502: "Bad Gateway"}.get(status, "Status")
    header_text = "".join(f"{name}: {value}\r\n" for name, value in (headers or {}).items())
    stdout = f"HTTP/2.0 {status} {reason}\r\n{header_text}\r\n{json.dumps(payload)}"
    return SimpleNamespace(returncode=0 if status < 400 else 1, stdout=stdout, stderr="")


class SyntheticGh:
    """In-process stand-in for ``gh`` that serves a synthetic public world.

    REST calls must be ``gh api --method GET``. GraphQL calls must be
    ``gh api graphql`` with a query document; anything else is rejected so a
    write-capable command can never succeed against this fake.
    """

    def __init__(self, world=None):
        self.world = deepcopy(world) if world is not None else fixture("synthetic-issues.json")
        self.calls = []
        self.split_above_seconds = None
        self.search_slack_seconds = 0
        self.graphql_overrides = {}
        self.core_overrides = {}
        self.search_failures = {}
        self.rest_overrides = {}

    def issue(self, number, repository=REPO):
        return next(
            item for item in self.world["issues"]
            if item["repository"] == repository and item["number"] == number
        )

    def __call__(self, argv, **kwargs):
        self.calls.append(list(argv))
        if kwargs.get("shell"):
            raise AssertionError("gh must be invoked without a shell")
        if argv == ["gh", "--version"]:
            return SimpleNamespace(returncode=0, stdout="gh version 9.9.9 (synthetic)\n", stderr="")
        if argv[:3] == ["gh", "api", "graphql"]:
            return self._graphql(argv)
        if argv[:4] != ["gh", "api", "--method", "GET"]:
            return SimpleNamespace(returncode=2, stdout="", stderr="synthetic runner rejects non-GET REST")
        endpoint = next(value for value in argv if value.startswith("/"))
        fields = self._fields(argv, "-f")
        return self._rest(endpoint, fields)

    @staticmethod
    def _fields(argv, flag):
        values = {}
        for index, value in enumerate(argv[:-1]):
            if value == flag:
                name, _, field_value = argv[index + 1].partition("=")
                values[name] = field_value
        return values

    def _rest(self, endpoint, fields):
        if endpoint in self.rest_overrides:
            return self.rest_overrides[endpoint]
        if endpoint == "/user":
            return _http(200, {"login": "synthetic-runner"})
        if endpoint == "/versions":
            return _http(200, ["2026-03-10"])
        if endpoint == "/search/issues":
            return self._search(fields["q"], int(fields.get("page", "1")))
        parts = endpoint.strip("/").split("/")
        repository = "/".join(parts[1:3])
        if len(parts) == 3:
            metadata = self.world["repositories"].get(repository)
            return _http(200, metadata) if metadata else _http(404, {"message": "Not Found"})
        number = int(parts[4])
        override = self.core_overrides.get(number)
        if len(parts) == 5 and override is not None:
            return override
        try:
            issue = self.issue(number, repository)
        except StopIteration:
            return _http(404, {"message": "Not Found"})
        if issue.get("inaccessible"):
            return _http(404, {"message": "Not Found"})
        if len(parts) == 5:
            return _http(200, self._core(issue))
        if parts[5] == "comments":
            return _http(200, self._comments(issue))
        if parts[5] == "timeline":
            return _http(200, deepcopy(issue["timeline"]))
        raise AssertionError("unexpected synthetic endpoint: " + endpoint)

    def _search(self, query, page):
        failure = self.search_failures.get(query)
        if failure is not None:
            return failure
        tokens = shlex.split(query)
        repository = next(token[5:] for token in tokens if token.startswith("repo:"))
        field, start, end = next(
            (name, *value.split(".."))
            for token in tokens
            for name, _, value in [token.partition(":")]
            if name in {"created", "updated", "closed"}
        )
        labels = [token[6:] for token in tokens if token.startswith("label:")]
        start_time, end_time = _timestamp(start), _timestamp(end)
        slack = timedelta(seconds=self.search_slack_seconds)
        matches = []
        for issue in self.world["issues"]:
            if issue["repository"] != repository:
                continue
            if "is:open" in tokens and issue["state"] != "open":
                continue
            if "is:closed" in tokens and issue["state"] != "closed":
                continue
            if not all(label in issue["labels"] for label in labels):
                continue
            value = issue[field + "_at"]
            if value is None or not start_time <= _timestamp(value) <= end_time + slack:
                continue
            matches.append(self._search_item(issue))
        if self.split_above_seconds is not None and (end_time - start_time).total_seconds() > self.split_above_seconds:
            return _http(200, {"total_count": 1000, "incomplete_results": False, "items": matches[:100]})
        items = matches[(page - 1) * 100:page * 100]
        return _http(200, {"total_count": len(matches), "incomplete_results": False, "items": items})

    @staticmethod
    def _search_item(issue):
        item = {
            "number": issue["number"],
            "node_id": issue["node_id"],
            "title": issue["title"],
            "state": issue["state"],
            "state_reason": issue["state_reason"],
            "created_at": issue["created_at"],
            "updated_at": issue["updated_at"],
            "closed_at": issue["closed_at"],
            "labels": [{"name": name} for name in issue["labels"]],
            "url": f"https://api.github.com/repos/{issue['repository']}/issues/{issue['number']}",
            "html_url": f"https://github.com/{issue['repository']}/issues/{issue['number']}",
        }
        if issue.get("is_pull_request"):
            item["pull_request"] = {"html_url": f"https://github.com/{issue['repository']}/pull/{issue['number']}"}
        return item

    def _core(self, issue):
        payload = self._search_item(issue)
        payload.update({
            "body": issue["body"],
            "user": deepcopy(issue["user"]),
            "author_association": issue["author_association"],
            "locked": False,
            "active_lock_reason": None,
            "closed_by": {"login": "synthetic-maintainer"} if issue["state"] == "closed" else None,
            "type": None,
            "comments": len(issue["comments"]),
        })
        return payload

    @staticmethod
    def _comments(issue):
        comments = []
        for comment in issue["comments"]:
            value = deepcopy(comment)
            value["url"] = f"https://api.github.com/repos/{issue['repository']}/issues/comments/{comment['id']}"
            value["html_url"] = f"https://github.com/{issue['repository']}/issues/{issue['number']}#issuecomment-{comment['id']}"
            comments.append(value)
        return comments

    def _graphql(self, argv):
        strings = self._fields(argv, "-f")
        typed = self._fields(argv, "-F")
        document = strings.get("query", "")
        if not document.lstrip().startswith("query") or "mutation" in document:
            return SimpleNamespace(returncode=2, stdout="", stderr="synthetic runner accepts query documents only")
        number = int(typed["number"])
        if number in self.graphql_overrides:
            return self.graphql_overrides[number]
        repository = strings["owner"] + "/" + strings["name"]
        try:
            issue = self.issue(number, repository)
        except StopIteration:
            issue = None
        if issue is None or issue.get("inaccessible"):
            return _http(200, {
                "data": {"repository": None},
                "errors": [{"type": "NOT_FOUND", "path": ["repository"], "message": "Could not resolve"}],
            })
        return _http(200, {"data": {"repository": {"issue": self._graphql_issue(issue)}}})

    @staticmethod
    def _connection(nodes, has_next=False):
        return {"totalCount": len(nodes), "pageInfo": {"hasNextPage": has_next}, "nodes": deepcopy(nodes)}

    def _graphql_issue(self, issue):
        graph = issue.get("graphql", {})
        comment_edits = graph.get("comment_edits", {})
        comments = []
        for comment in issue["comments"]:
            edits = comment_edits.get(str(comment["id"]), {})
            comments.append({
                "databaseId": comment["id"],
                "lastEditedAt": edits.get("last_edited_at"),
                "userContentEdits": self._connection(edits.get("edits", [])),
            })
        return {
            "id": issue["node_id"],
            "lastEditedAt": graph.get("last_edited_at"),
            "userContentEdits": self._connection(graph.get("body_edits", []), graph.get("body_edits_has_next", False)),
            "duplicateOf": deepcopy(graph.get("duplicate_of")),
            "closedByPullRequestsReferences": self._connection(graph.get("closing_references", [])),
            "timelineItems": self._connection(graph.get("closed_events", [])),
            "comments": self._connection(comments),
        }


class Workspace:
    def __init__(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.output = root / "issues.json"
        self.manifest = root / "manifest.json"

    def close(self):
        self.directory.cleanup()


def run_main(collector, workspace, *arguments, runner=None, repos=(REPO,)):
    runner = runner if runner is not None else SyntheticGh()
    argv = ["collect"]
    for repository in repos:
        argv += ["--repo", repository]
    argv += ["--output", str(workspace.output), "--manifest", str(workspace.manifest)]
    argv += list(arguments)
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        code = collector.main(argv, runner=runner, sleeper=lambda _seconds: None)
    return code, runner, stderr.getvalue()


class InputValidationTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()
        self.workspace = Workspace()
        self.addCleanup(self.workspace.close)

    def assert_rejected_before_network(self, *arguments, repos=(REPO,)):
        code, runner, stderr = run_main(self.collector, self.workspace, *arguments, repos=repos)
        self.assertEqual(2, code, stderr)
        self.assertEqual([], runner.calls)
        self.assertFalse(self.workspace.manifest.exists())
        self.assertTrue(stderr.strip())
        return stderr

    def test_closed_date_field_with_open_state_exits_2_before_any_request(self):
        self.assert_rejected_before_network("--date-field", "closed", "--state", "open", *JANUARY)
        self.assertFalse(self.workspace.output.exists())

    def test_missing_date_field_exits_2(self):
        self.assert_rejected_before_network(*JANUARY)

    def test_two_interval_modes_exit_2(self):
        self.assert_rejected_before_network(
            "--date-field", "created", *JANUARY, "--start-date", "2030-01-01", "--end-date", "2030-01-31",
        )

    def test_invalid_repository_exits_2(self):
        self.assert_rejected_before_network("--date-field", "created", *JANUARY, repos=("not-a-repository",))

    def test_duplicate_repository_exits_2(self):
        self.assert_rejected_before_network(
            "--date-field", "created", *JANUARY, repos=(REPO, "Synthetic-Lab/Widget"),
        )

    def test_label_with_double_quote_exits_2(self):
        self.assert_rejected_before_network("--date-field", "created", *JANUARY, "--label", 'say "hi"')

    def test_non_positive_cap_exits_2(self):
        self.assert_rejected_before_network("--date-field", "created", *JANUARY, "--max-per-repo", "0")

    def test_out_of_range_interval_exits_2(self):
        self.assert_rejected_before_network("--date-field", "created", "--recent-days", "800000")
        self.assert_rejected_before_network("--date-field", "created", "--start-date", "2030-01-01",
                                            "--end-date", "9999-12-31")

    def test_missing_output_directory_exits_2(self):
        self.workspace.output = Path(self.workspace.directory.name) / "absent" / "issues.json"
        self.assert_rejected_before_network("--date-field", "created", *JANUARY)

    def test_existing_corpus_with_malformed_records_exits_2(self):
        broken = {"schema_version": "1.0.0", "corpus_kind": "github-issue", "generated_by": {"name": "x"},
                  "records": [{"record_key": "github-issue:I_X", "issue": None}]}
        self.workspace.output.write_text(json.dumps(broken), encoding="utf-8")
        self.assert_rejected_before_network("--date-field", "created", *JANUARY)

    def test_same_output_and_manifest_exits_2(self):
        self.workspace.manifest = self.workspace.output
        self.assert_rejected_before_network("--date-field", "created", *JANUARY)

    def test_foreign_manifest_at_manifest_path_exits_2(self):
        foreign = {"schema_version": "2.0.0", "generated_by": {"name": "collecting-recent-closed-prs"}, "records": []}
        self.workspace.manifest.write_text(json.dumps(foreign), encoding="utf-8")
        code, runner, stderr = run_main(self.collector, self.workspace, "--date-field", "created", *JANUARY)
        self.assertEqual(2, code, stderr)
        self.assertEqual([], runner.calls)
        self.assertEqual(foreign, json.loads(self.workspace.manifest.read_text(encoding="utf-8")))

    def test_existing_pull_request_corpus_at_output_exits_2(self):
        pull_request_corpus = {"schema_version": "1.0.0", "generated_by": {"name": "x"}, "records": []}
        self.workspace.output.write_text(json.dumps(pull_request_corpus), encoding="utf-8")
        self.assert_rejected_before_network("--date-field", "created", *JANUARY)
        self.assertEqual(pull_request_corpus, json.loads(self.workspace.output.read_text(encoding="utf-8")))


class SearchQueryTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()
        self.january = self.collector.resolve_interval(
            start_at="2030-01-01T00:00:00Z", end_at="2030-02-01T00:00:00Z",
            start_date=None, end_date=None, recent_days=None, timezone_name="UTC", as_of=None,
        )

    def test_query_has_one_date_qualifier_state_and_every_label(self):
        self.assertEqual(
            'repo:synthetic-lab/widget is:issue is:closed '
            'closed:2030-01-01T00:00:00Z..2030-01-31T23:59:59Z label:"bug" label:"good first issue"',
            self.collector.build_issue_query(REPO, self.january, "closed", "closed", ["bug", "good first issue"]),
        )

    def test_query_for_all_states_has_no_state_qualifier(self):
        self.assertEqual(
            "repo:synthetic-lab/widget is:issue created:2030-01-01T00:00:00Z..2030-01-31T23:59:59Z",
            self.collector.build_issue_query(REPO, self.january, "created", "all", []),
        )


TEST_REVISION = "sha256:" + "0" * 64


def collect_run(
    collector,
    runner=None,
    *,
    date_field="created",
    state="all",
    labels=(),
    start_at="2030-01-01T00:00:00Z",
    end_at="2030-02-01T00:00:00Z",
    cap=25,
    budget=1000,
    repos=(REPO,),
    existing_corpus=None,
    existing_manifest=None,
    captured_at=CAPTURED_AT,
):
    runner = runner if runner is not None else SyntheticGh()
    rest, graphql = collector.build_clients(
        api_version="2026-03-10", request_budget=budget, runner=runner, sleeper=lambda _seconds: None,
    )
    interval = collector.resolve_interval(
        start_at=start_at, end_at=end_at, start_date=None, end_date=None,
        recent_days=None, timezone_name="UTC", as_of=None,
    )
    run = collector.collect(
        rest,
        graphql,
        repositories=list(repos),
        date_field=date_field,
        state=state,
        labels=list(labels),
        interval=interval,
        max_per_repository=cap,
        existing_corpus=existing_corpus,
        existing_manifest=existing_manifest,
        captured_at=captured_at,
        skill_revision=TEST_REVISION,
    )
    return run, runner


def record_for(run, number):
    return next(record for record in run.corpus["records"] if record["issue"]["number"] == number)


def latest_run(run):
    return run.manifest["records"][-1]


def repository_entry(run, repository=REPO):
    return next(item for item in latest_run(run)["repositories"] if item["repository"] == repository)


class SearchSelectionTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()

    def test_pull_request_search_hits_are_counted_not_collected(self):
        run, _ = collect_run(self.collector)
        numbers = sorted(record["issue"]["number"] for record in run.corpus["records"])
        self.assertEqual([1, 2, 3, 4, 5, 6], numbers)
        self.assertEqual({"is-pull-request": 1}, repository_entry(run)["excluded"])

    def test_hydrated_payload_with_pull_request_key_is_excluded(self):
        runner = SyntheticGh()
        disguised = runner._core(runner.issue(1))
        disguised["pull_request"] = {"html_url": "https://github.com/synthetic-lab/widget/pull/1"}
        runner.core_overrides[1] = _http(200, disguised)
        run, _ = collect_run(self.collector, runner, state="open")
        self.assertNotIn(1, [record["issue"]["number"] for record in run.corpus["records"]])
        self.assertEqual({"is-pull-request": 2}, repository_entry(run)["excluded"])

    def test_issue_whose_state_changed_after_search_is_excluded_and_counted(self):
        runner = SyntheticGh()
        closed_since = runner._core(runner.issue(1))
        closed_since.update(state="closed", state_reason="completed", closed_at="2030-01-30T00:00:00Z")
        runner.core_overrides[1] = _http(200, closed_since)
        run, _ = collect_run(self.collector, runner, state="open", end_at="2030-01-26T00:00:00Z")
        self.assertEqual([6, 5], [record["issue"]["number"] for record in run.corpus["records"]])
        self.assertEqual({"is-pull-request": 1, "state-changed-after-search": 1}, repository_entry(run)["excluded"])
        self.assertEqual(0, run.exit_code)

    def test_date_field_is_post_filtered_to_the_half_open_interval(self):
        runner = SyntheticGh()
        runner.issue(2)["created_at"] = "2030-01-12T00:00:00Z"
        runner.issue(1)["created_at"] = "2030-01-10T00:00:00Z"
        runner.search_slack_seconds = 1
        run, _ = collect_run(
            self.collector, runner, start_at="2030-01-10T00:00:00Z", end_at="2030-01-12T00:00:00Z",
        )
        self.assertEqual([1], [record["issue"]["number"] for record in run.corpus["records"]])

    def test_unsafe_search_is_split_and_the_parent_is_recorded(self):
        runner = SyntheticGh()
        runner.split_above_seconds = 16 * 24 * 3600
        run, _ = collect_run(self.collector, runner, state="closed")
        entry = repository_entry(run)
        self.assertEqual(1, len(entry["split_observations"]))
        observation = entry["split_observations"][0]
        self.assertEqual(["2030-01-01T00:00:00Z", "2030-02-01T00:00:00Z"], observation["interval"])
        self.assertEqual(["search-result-limit"], observation["split_reasons"])
        self.assertEqual(
            [["2030-01-01T00:00:00Z", "2030-01-16T12:00:00Z"], ["2030-01-16T12:00:00Z", "2030-02-01T00:00:00Z"]],
            observation["children"],
        )
        self.assertEqual(["complete", "complete"], [leaf["completion_state"] for leaf in entry["partitions"]])
        self.assertEqual([2, 3, 4], sorted(record["issue"]["number"] for record in run.corpus["records"]))

    def test_budget_cutoff_records_every_unsearched_partition(self):
        runner = SyntheticGh()
        runner.split_above_seconds = 16 * 24 * 3600
        run, _ = collect_run(self.collector, runner, state="closed", budget=4)
        partitions = repository_entry(run)["partitions"]
        self.assertEqual(
            [(["2030-01-01T00:00:00Z", "2030-01-16T12:00:00Z"], "failed"),
             (["2030-01-16T12:00:00Z", "2030-02-01T00:00:00Z"], "failed")],
            [(item["interval"], item["completion_state"]) for item in partitions],
        )
        self.assertEqual(2, len([scope for scope in latest_run(run)["failed_scopes"]
                                 if scope["scope"] == "search-partition"]))

    def test_malformed_search_hit_makes_the_repository_partial(self):
        runner = SyntheticGh()
        runner.issue(2)["node_id"] = None
        run, _ = collect_run(self.collector, runner, state="closed")
        self.assertEqual("partial", repository_entry(run)["collection_status"])
        self.assertEqual(3, run.exit_code)

    def test_cap_keeps_the_newest_issues_and_does_not_count_failures_as_cap_exclusions(self):
        run, _ = collect_run(self.collector, state="open", cap=2)
        self.assertEqual([6, 5], [record["issue"]["number"] for record in run.corpus["records"]])
        entry = repository_entry(run)
        self.assertEqual(4, entry["matched_count"])
        self.assertEqual(2, entry["selected_count"])
        self.assertEqual(1, entry["excluded_by_cap"])


class IssueRecordTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()
        self.run, _ = collect_run(self.collector)

    def test_corpus_envelope_is_a_versioned_issue_corpus(self):
        self.assertEqual("1.0.0", self.run.corpus["schema_version"])
        self.assertEqual("github-issue", self.run.corpus["corpus_kind"])
        self.assertEqual({"name": "collecting-open-source-issues", "revision": TEST_REVISION},
                         self.run.corpus["generated_by"])

    def test_record_identity_type_and_raw_state(self):
        record = record_for(self.run, 3)
        self.assertEqual("resolved", record["identity_status"])
        self.assertEqual("github-issue:I_SYNTHETIC_3", record["record_key"])
        self.assertEqual("ISS-4", record["issue_id"])
        self.assertEqual("issue", record["item_type"])
        self.assertEqual("general-issue", record["input_path"])
        self.assertEqual(
            {"full_name": "synthetic-lab/widget", "node_id": "R_SYNTHETIC_WIDGET", "repository_aliases": []},
            record["repository"],
        )
        self.assertEqual("closed", record["issue"]["state"])
        self.assertEqual("not_planned", record["issue"]["state_reason_raw"])
        self.assertEqual(["wontfix"], record["issue"]["labels_raw"])
        self.assertEqual({"state_reason_raw": "not_planned", "normalized_cause": "unknown"}, record["closure"])

    def test_cause_is_never_inferred_from_state_labels_or_a_merged_closer(self):
        causes = {record["issue"]["number"]: record["closure"]["normalized_cause"] for record in self.run.corpus["records"]}
        self.assertEqual({1: "unknown", 2: "unknown", 3: "unknown", 4: "unknown", 5: "unknown", 6: "unknown"}, causes)

    def test_author_association_is_mapped_without_inventing_roles(self):
        self.assertEqual("contributor", record_for(self.run, 2)["author"]["normalized_role"])
        self.assertEqual("unknown", record_for(self.run, 1)["author"]["normalized_role"])
        self.assertEqual("NONE", record_for(self.run, 1)["author"]["association"])

    def test_comments_timeline_and_body_are_preserved_with_capture_time(self):
        record = record_for(self.run, 1)
        evidence = record["evidence_snapshot"]
        self.assertEqual("Steps: run the synthetic command twice.", evidence["body_excerpt"])
        self.assertEqual(["Confirmed on the synthetic main branch."], [item["excerpt"] for item in evidence["comments"]])
        self.assertEqual(["commented"], [item["kind"] for item in evidence["timeline_events"]])
        self.assertEqual(CAPTURED_AT, evidence["completeness"]["comments"]["captured_at"])
        self.assertEqual("complete", record["hydration_status"])

    def test_observations_identify_body_and_comment_content(self):
        source = record_for(self.run, 1)["sources"][0]
        self.assertEqual("general-issue", source["source_key"])
        body, comment = source["observations"]
        self.assertEqual("issue-body", body["origin_kind"])
        self.assertEqual("2030-01-11T00:00:00Z", body["updated_at"])
        self.assertEqual(sha256_text("Steps: run the synthetic command twice."), body["body_sha256"])
        self.assertEqual("comment", comment["origin_kind"])
        self.assertEqual(101, comment["comment_id"])
        self.assertEqual("MEMBER", comment["author_association"])
        self.assertEqual(sha256_text("Confirmed on the synthetic main branch."), comment["body_sha256"])


class RelatedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()
        self.run, self.runner = collect_run(self.collector)

    def test_closer_closing_reference_and_cross_reference_are_distinct_relations(self):
        related = record_for(self.run, 2)["evidence_snapshot"]["related_pull_requests"]
        expected_common = {
            "url": "https://github.com/synthetic-lab/widget/pull/20",
            "node_id": "PR_SYNTHETIC_20",
            "number": 20,
            "repository_full_name": "synthetic-lab/widget",
        }
        self.assertEqual([
            dict(expected_common, relation="closer", relation_method="graphql-closed-event",
                 event_at="2030-01-14T00:00:00Z", state_raw="MERGED", merged_raw=True),
            dict(expected_common, relation="closing-reference", relation_method="graphql-closing-references",
                 event_at=None, state_raw="MERGED", merged_raw=True),
            dict(expected_common, relation="cross-reference", relation_method="rest-timeline",
                 event_at="2030-01-13T00:00:00Z", state_raw=None, merged_raw=None),
        ], related)

    def test_unmerged_closing_reference_on_a_not_planned_issue_is_kept_as_observed(self):
        related = record_for(self.run, 3)["evidence_snapshot"]["related_pull_requests"]
        self.assertEqual([("closing-reference", 30, "CLOSED", False)],
                         [(item["relation"], item["number"], item["state_raw"], item["merged_raw"]) for item in related])

    def test_closed_events_keep_the_raw_reason_and_closer(self):
        self.assertEqual(
            [{"created_at": "2030-01-14T00:00:00Z", "state_reason_raw": "COMPLETED",
              "closer_type": "PullRequest", "closer_url": "https://github.com/synthetic-lab/widget/pull/20"}],
            record_for(self.run, 2)["evidence_snapshot"]["closed_events"],
        )

    def test_duplicate_of_comes_from_graphql(self):
        self.assertEqual(
            {"url": "https://github.com/synthetic-lab/widget/issues/1", "number": 1, "node_id": "I_SYNTHETIC_1",
             "repository_full_name": "synthetic-lab/widget", "method": "graphql-duplicate-of"},
            record_for(self.run, 4)["evidence_snapshot"]["duplicate_of"],
        )
        self.assertIsNone(record_for(self.run, 3)["evidence_snapshot"]["duplicate_of"])

    def test_unreadable_cross_reference_is_not_evidence_of_no_pull_request(self):
        evidence = record_for(self.run, 6)["evidence_snapshot"]
        self.assertEqual([], evidence["related_pull_requests"])
        self.assertEqual(
            [{"event": "cross-referenced", "event_at": "2030-01-24T00:00:00Z",
              "reason": "cross-reference source is not readable"}],
            evidence["unresolvable_references"],
        )

    def test_issue_without_pull_request_has_complete_empty_relations(self):
        record = record_for(self.run, 1)
        evidence = record["evidence_snapshot"]
        self.assertEqual([], evidence["related_pull_requests"])
        self.assertEqual([], evidence["unresolvable_references"])
        self.assertIsNone(evidence["duplicate_of"])
        self.assertTrue(all(item["pages_complete"] for item in evidence["completeness"].values()))

    def test_edit_history_keeps_metadata_and_hashes_but_never_diff_text(self):
        history = record_for(self.run, 5)["evidence_snapshot"]["edit_history"]
        self.assertEqual({
            "total_count": 2,
            "last_edited_at": "2030-01-22T00:00:00Z",
            "edits": [
                {"edited_at": "2030-01-22T00:00:00Z", "editor_login": "synthetic-reporter", "deleted_at": None,
                 "diff_sha256": sha256_text("SYNTHETIC-DIFF-BODY-SECOND")},
                {"edited_at": "2030-01-21T00:00:00Z", "editor_login": "synthetic-reporter", "deleted_at": None,
                 "diff_sha256": sha256_text("SYNTHETIC-DIFF-BODY-FIRST")},
            ],
        }, history["body"])
        self.assertEqual([{
            "comment_id": 501,
            "total_count": 1,
            "last_edited_at": "2030-01-22T00:00:00Z",
            "edits": [{"edited_at": "2030-01-22T00:00:00Z", "editor_login": None,
                       "deleted_at": "2030-01-23T00:00:00Z",
                       "diff_sha256": sha256_text("SYNTHETIC-DIFF-COMMENT-REMOVED-TEXT")}],
        }], history["comments"])
        serialized = json.dumps(self.run.corpus) + json.dumps(self.run.manifest)
        self.assertNotIn("SYNTHETIC-DIFF", serialized)

    def test_truncated_graphql_connection_makes_the_record_partial(self):
        runner = SyntheticGh()
        runner.issue(5)["graphql"]["body_edits_has_next"] = True
        run, _ = collect_run(self.collector, runner, state="open", end_at="2030-01-26T00:00:00Z")
        record = record_for(run, 5)
        self.assertFalse(record["evidence_snapshot"]["completeness"]["graphql"]["pages_complete"])
        self.assertEqual("partial", record["hydration_status"])
        self.assertEqual(3, run.exit_code)

    def test_graphql_failure_leaves_graphql_facts_unknown_and_partial(self):
        runner = SyntheticGh()
        runner.graphql_overrides[2] = _http(200, {
            "data": {"repository": None},
            "errors": [{"type": "NOT_FOUND", "message": "Could not resolve"}],
        })
        run, _ = collect_run(self.collector, runner, state="closed")
        evidence = record_for(run, 2)["evidence_snapshot"]
        self.assertFalse(evidence["completeness"]["graphql"]["pages_complete"])
        self.assertIsNone(evidence["edit_history"])
        self.assertEqual([], evidence["closed_events"])
        self.assertEqual(["cross-reference"], [item["relation"] for item in evidence["related_pull_requests"]])
        self.assertEqual("partial", record_for(run, 2)["hydration_status"])
        self.assertEqual(3, run.exit_code)


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()

    def test_every_request_is_rest_get_or_a_graphql_query(self):
        _, runner = collect_run(self.collector)
        graphql_calls = [call for call in runner.calls if call[:3] == ["gh", "api", "graphql"]]
        rest_calls = [call for call in runner.calls if call[:4] == ["gh", "api", "--method", "GET"]]
        self.assertEqual(len(runner.calls), len(graphql_calls) + len(rest_calls) + 1)
        self.assertEqual(6, len(graphql_calls))
        for call in graphql_calls:
            self.assertTrue(call[call.index("-f") + 1].startswith("query=query IssueEvidence("))
            self.assertNotIn("mutation", " ".join(call))
            self.assertIn("-F", call)

    def test_graphql_client_refuses_a_mutation_before_running_gh(self):
        runner = SyntheticGh()
        _, graphql = self.collector.build_clients(
            api_version="2026-03-10", request_budget=10, runner=runner, sleeper=lambda _seconds: None,
        )
        with self.assertRaises(ValueError):
            graphql.query("mutation { addComment(input: {}) { clientMutationId } }", {})
        self.assertEqual([], runner.calls)

    def test_rest_and_graphql_share_one_request_budget(self):
        run, runner = collect_run(self.collector, state="closed")
        api_calls = [call for call in runner.calls if call[:2] == ["gh", "api"]]
        self.assertEqual(len(api_calls), latest_run(run)["request_count"])


class FailureTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()

    def test_inaccessible_issue_is_not_found_or_inaccessible_and_not_deleted(self):
        run, _ = collect_run(self.collector)
        entry = repository_entry(run)
        self.assertEqual([(8, "I_SYNTHETIC_8", "not-found-or-inaccessible")],
                         [(item["number"], item["node_id"], item["outcome"]) for item in entry["partial_records"]])
        self.assertIn({"repository": REPO, "scope": "issue", "number": 8, "outcome": "not-found-or-inaccessible"},
                      latest_run(run)["failed_scopes"])
        self.assertNotIn("I_SYNTHETIC_8", [record["issue_node_id"] for record in run.corpus["records"]])
        self.assertNotIn("delet", json.dumps(run.manifest).lower())
        self.assertEqual("partial", latest_run(run)["collection_status"])
        self.assertEqual(3, run.exit_code)

    def test_only_an_inaccessible_repository_fails_with_exit_4(self):
        run, _ = collect_run(self.collector, repos=("synthetic-lab/missing",))
        self.assertEqual(4, run.exit_code)
        self.assertEqual("failed", latest_run(run)["collection_status"])
        self.assertEqual("not-found-or-inaccessible", repository_entry(run, "synthetic-lab/missing")["collection_status"])
        self.assertEqual([], run.corpus["records"])

    def test_inaccessible_repository_beside_a_usable_one_is_partial(self):
        run, _ = collect_run(self.collector, state="closed", repos=(REPO, "synthetic-lab/missing"))
        self.assertEqual(3, run.exit_code)
        self.assertEqual("collected", repository_entry(run)["collection_status"])

    def test_fully_collected_scope_exits_0(self):
        run, _ = collect_run(self.collector, state="closed")
        self.assertEqual(0, run.exit_code)
        self.assertEqual("complete", latest_run(run)["collection_status"])
        self.assertEqual([], latest_run(run)["failed_scopes"])

    def test_global_preflight_failure_exits_4(self):
        runner = SyntheticGh()
        runner.rest_overrides["/user"] = _http(401, {"message": "Requires authentication"})
        run, _ = collect_run(self.collector, runner)
        self.assertEqual(4, run.exit_code)
        self.assertEqual("failed", latest_run(run)["collection_status"])
        self.assertEqual(["preflight"], [scope["scope"] for scope in latest_run(run)["failed_scopes"]])

    def test_budget_exhaustion_is_partial_and_stops_new_requests(self):
        run, runner = collect_run(self.collector, budget=12)
        self.assertEqual(3, run.exit_code)
        self.assertEqual(12, latest_run(run)["request_count"])
        self.assertEqual(12, len([call for call in runner.calls if call[:2] == ["gh", "api"]]))
        self.assertEqual("complete", record_for(run, 6)["hydration_status"])
        entry = repository_entry(run)
        self.assertEqual("partial", entry["collection_status"])
        self.assertEqual(4, entry["not_attempted"])
        self.assertIn({"repository": REPO, "scope": "issue", "number": 4, "outcome": "budget-exhausted"},
                      latest_run(run)["failed_scopes"])

    def test_method_limitations_record_the_unverified_items(self):
        run, _ = collect_run(self.collector, date_field="updated")
        prefixes = [item.split(":", 2)[0] + ":" + item.split(":", 2)[1] if item.startswith("unverified:")
                    else item.split(":", 1)[0] for item in latest_run(run)["method_limitations"]]
        self.assertIn("unverified:private-cross-reference-visibility", prefixes)
        self.assertIn("unverified:linked-pr-qualifier", prefixes)
        self.assertIn("volatile-updated-at", prefixes)
        created_run, _ = collect_run(self.collector)
        self.assertFalse(any(item.startswith("volatile-updated-at") for item in latest_run(created_run)["method_limitations"]))

    def test_manifest_records_filters_and_interval(self):
        run, _ = collect_run(self.collector, labels=("bug",))
        record = latest_run(run)
        self.assertEqual("general-issue-search", record["collection_method"])
        self.assertEqual({"repositories": [REPO], "date_field": "created", "state": "all", "labels": ["bug"],
                          "label_semantics": "all-of"}, record["filters"])
        self.assertEqual(("2030-01-01T00:00:00Z", "2030-02-01T00:00:00Z"),
                         (record["interval"]["start_at"], record["interval"]["end_at"]))
        self.assertEqual([1, 2], sorted(item["issue"]["number"] for item in run.corpus["records"]))


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()

    def rerun(self, first, runner, **options):
        return collect_run(self.collector, runner, existing_corpus=first.corpus, existing_manifest=first.manifest,
                           captured_at="2030-02-03T00:00:00Z", **options)

    def test_unchanged_recollection_adds_no_observations_and_keeps_ids(self):
        runner = SyntheticGh()
        first, _ = collect_run(self.collector, runner)
        second, _ = self.rerun(first, runner)
        self.assertEqual(
            [(record["issue_id"], len(record["sources"][0]["observations"])) for record in first.corpus["records"]],
            [(record["issue_id"], len(record["sources"][0]["observations"])) for record in second.corpus["records"]],
        )
        self.assertEqual(2, len(second.manifest["records"]))

    def test_edited_body_appends_an_observation_and_keeps_the_old_one(self):
        runner = SyntheticGh()
        first, _ = collect_run(self.collector, runner)
        runner.issue(1)["body"] = "Steps: run the synthetic command three times."
        runner.issue(1)["updated_at"] = "2030-01-25T00:00:00Z"
        second, _ = self.rerun(first, runner)
        record = record_for(second, 1)
        bodies = [item["body_sha256"] for item in record["sources"][0]["observations"] if item["origin_kind"] == "issue-body"]
        self.assertEqual([sha256_text("Steps: run the synthetic command twice."),
                          sha256_text("Steps: run the synthetic command three times.")], bodies)
        self.assertEqual("Steps: run the synthetic command three times.", record["evidence_snapshot"]["body_excerpt"])

    def test_activity_without_a_body_edit_adds_no_body_observation(self):
        runner = SyntheticGh()
        first, _ = collect_run(self.collector, runner)
        runner.issue(1)["labels"] = ["bug", "triaged"]
        runner.issue(1)["updated_at"] = "2030-01-27T00:00:00Z"
        second, _ = self.rerun(first, runner)
        bodies = [item for item in record_for(second, 1)["sources"][0]["observations"]
                  if item["origin_kind"] == "issue-body"]
        self.assertEqual(1, len(bodies))
        self.assertEqual(["bug", "triaged"], record_for(second, 1)["issue"]["labels_raw"])

    def test_partial_recollection_keeps_complete_earlier_evidence(self):
        runner = SyntheticGh()
        first, _ = collect_run(self.collector, runner, state="closed")
        before = record_for(first, 2)["evidence_snapshot"]
        runner.graphql_overrides[2] = _http(502, {"message": "Bad Gateway"})
        runner.rest_overrides["/repos/synthetic-lab/widget/issues/2/timeline"] = _http(502, {"message": "Bad Gateway"})
        second, _ = self.rerun(first, runner, state="closed")
        after = record_for(second, 2)["evidence_snapshot"]
        self.assertEqual(3, second.exit_code)
        self.assertEqual(before["related_pull_requests"], after["related_pull_requests"])
        self.assertEqual(before["closed_events"], after["closed_events"])
        self.assertEqual(before["timeline_events"], after["timeline_events"])
        self.assertEqual(CAPTURED_AT, after["completeness"]["graphql"]["captured_at"])
        self.assertEqual("complete", record_for(second, 2)["hydration_status"])

    def test_state_change_appends_to_state_history(self):
        runner = SyntheticGh()
        first, _ = collect_run(self.collector, runner)
        runner.issue(1).update(state="closed", state_reason="completed",
                               closed_at="2030-01-28T00:00:00Z", updated_at="2030-01-28T00:00:00Z")
        second, _ = self.rerun(first, runner)
        self.assertEqual([("open", None), ("closed", "completed")],
                         [(item["state"], item["state_reason_raw"]) for item in record_for(second, 1)["state_history"]])

    def test_new_issues_get_the_next_issue_ids(self):
        runner = SyntheticGh()
        first, _ = collect_run(self.collector, runner, state="closed")
        self.assertEqual({4: "ISS-1", 3: "ISS-2", 2: "ISS-3"},
                         {record["issue"]["number"]: record["issue_id"] for record in first.corpus["records"]})
        second, _ = self.rerun(first, runner)
        self.assertEqual({4: "ISS-1", 3: "ISS-2", 2: "ISS-3", 6: "ISS-4", 5: "ISS-5", 1: "ISS-6"},
                         {record["issue"]["number"]: record["issue_id"] for record in second.corpus["records"]})


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()
        self.workspace = Workspace()
        self.addCleanup(self.workspace.close)

    def test_collect_writes_the_issue_corpus_and_manifest(self):
        code, _, stderr = run_main(self.collector, self.workspace, "--date-field", "created", *JANUARY)
        self.assertEqual(3, code, stderr)
        corpus = json.loads(self.workspace.output.read_text(encoding="utf-8"))
        manifest = json.loads(self.workspace.manifest.read_text(encoding="utf-8"))
        self.assertEqual(("1.0.0", "github-issue"), (corpus["schema_version"], corpus["corpus_kind"]))
        self.assertEqual(6, len(corpus["records"]))
        self.assertEqual("2.0.0", manifest["schema_version"])
        self.assertEqual(self.collector.compute_skill_revision(), manifest["generated_by"]["revision"])
        self.assertTrue(self.workspace.output.read_text(encoding="utf-8").endswith("\n"))

    def test_second_collect_merges_into_the_existing_outputs(self):
        run_main(self.collector, self.workspace, "--date-field", "created", *JANUARY)
        code, _, stderr = run_main(self.collector, self.workspace, "--date-field", "created", *JANUARY)
        self.assertEqual(3, code, stderr)
        manifest = json.loads(self.workspace.manifest.read_text(encoding="utf-8"))
        self.assertEqual(2, len(manifest["records"]))
        self.assertEqual(6, len(json.loads(self.workspace.output.read_text(encoding="utf-8"))["records"]))

    def test_failed_collection_writes_the_manifest_but_keeps_an_existing_corpus(self):
        run_main(self.collector, self.workspace, "--date-field", "created", *JANUARY)
        before = self.workspace.output.read_bytes()
        runner = SyntheticGh()
        runner.rest_overrides["/user"] = _http(401, {"message": "Requires authentication"})
        code, _, _ = run_main(self.collector, self.workspace, "--date-field", "created", *JANUARY, runner=runner)
        self.assertEqual(4, code)
        self.assertEqual(before, self.workspace.output.read_bytes())
        self.assertEqual("failed", json.loads(self.workspace.manifest.read_text(encoding="utf-8"))["records"][-1]["collection_status"])


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.collector = load_collector()

    def test_print_revision_prints_the_packaged_revision(self):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = self.collector.main(["--print-revision"])
        self.assertEqual(0, code)
        self.assertRegex(stdout.getvalue().strip(), r"\Asha256:[0-9a-f]{64}\Z")
        self.assertEqual(self.collector.compute_skill_revision(), stdout.getvalue().strip())

    def test_revision_changes_when_any_revision_file_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / "skill"
            shutil.copytree(SKILL_DIR, copy, ignore=shutil.ignore_patterns("__pycache__"))
            baseline = self.collector.compute_skill_revision(copy)
            for relative in self.collector.SKILL_REVISION_PATHS:
                target = copy / relative
                original = target.read_bytes()
                target.write_bytes(original + b"\n")
                self.assertNotEqual(baseline, self.collector.compute_skill_revision(copy), relative)
                target.write_bytes(original)
            self.assertEqual(baseline, self.collector.compute_skill_revision(copy))


if __name__ == "__main__":
    unittest.main()
