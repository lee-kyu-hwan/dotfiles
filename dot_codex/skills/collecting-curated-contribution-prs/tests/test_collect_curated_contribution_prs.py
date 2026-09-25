"""Contract tests for the synthetic curated contribution collector."""

from __future__ import annotations

import ast
import contextlib
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "collect_curated_contribution_prs.py"
FIXTURES = SKILL_DIR / "tests" / "fixtures"
SPEC = (
    Path(__file__).resolve().parents[4]
    / "docs"
    / "development"
    / "2026-09-10-80-collecting-curated-contribution-prs"
    / "spec.md"
)
HARDENING_SPEC = (
    Path(__file__).resolve().parents[4]
    / "docs"
    / "development"
    / "2026-09-15-80-post-review-hardening"
    / "spec.md"
)
EVAL = SKILL_DIR / "evals" / "behavioral-eval.md"
# AC-17 의 portable oracle. 이전에는 변경 전 사본을 gitignore 대상인
# .claude/quality-state/<task-id>/baseline-snapshot 에서 읽어, 새 클론이나 배포본에서는
# 이 검증을 아예 실행할 수 없었다(리뷰 CODE-002). 정규화된 문서 전체를 digest 로 고정해
# 우발적 변경 탐지력을 유지하면서 머신 의존 경로를 제거한다.
# 의도적으로 문서를 고쳤다면: shasum -a 256 evals/behavioral-eval.md 로 재생성하고 사유를 보고서에 남긴다.
PORTABLE_EVAL_SHA256 = "42d7cbf280c4999b5a2506463cd25ee5c05f96ea5e7933b64ca65aff2f4763fc"


def assert_portable_eval(case):
    """eval 문서가 placeholder 로 정규화되어 있고 바이트가 고정돼 있는지 확인한다."""
    actual = EVAL.read_bytes()
    case.assertEqual(2, actual.count(b"<worktree>"))
    case.assertNotIn(b"/Users/", actual)
    case.assertEqual(
        PORTABLE_EVAL_SHA256,
        hashlib.sha256(actual).hexdigest(),
        "evals/behavioral-eval.md 가 바뀌었다. 의도한 변경이면 PORTABLE_EVAL_SHA256 을 "
        "갱신하고 사유를 보고서에 기록하라",
    )


def packaged_files():
    """스킬 디렉터리의 패키징 대상 파일 집합.

    PYTHONDONTWRITEBYTECODE 없이 테스트를 한 번 돌리면 unittest 가 test module 을,
    load_collector 가 script 를 import 하며 __pycache__ 를 남긴다. 이는 .gitignore 대상인
    인터프리터 부산물이지 스킬 파일이 아니므로 제외해야 두 번째 실행이 깨지지 않는다.
    """
    return {
        path.relative_to(SKILL_DIR).as_posix()
        for path in SKILL_DIR.rglob("*")
        if path.is_file() and "__pycache__" not in path.relative_to(SKILL_DIR).parts
    }


def load_collector():
    if not SCRIPT.is_file():
        raise AssertionError("curated collector script has not been implemented")
    spec = importlib.util.spec_from_file_location("collect_curated_contribution_prs", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("curated collector module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FakeBudget:
    def __init__(self, limit, consumed=0, error_type=RuntimeError):
        self.limit = limit
        self.consumed = consumed
        self.error_type = error_type

    def consume(self):
        if self.consumed >= self.limit:
            raise self.error_type("request budget exhausted")
        self.consumed += 1


class FakeClient:
    def __init__(
        self,
        routes,
        *,
        limit=100,
        consumed=0,
        preflight_error=None,
        budget_error_type=RuntimeError,
    ):
        self.routes = routes
        self.budget = FakeBudget(limit, consumed, budget_error_type)
        self.request_events = []
        self.calls = []
        self.preflight_error = preflight_error
        self.api_version = "2026-03-10"

    def get_json(self, endpoint, params=None):
        self.budget.consume()
        page = 1 if params is None else params.get("page", 1)
        self.calls.append((endpoint, deepcopy(params)))
        self.request_events.append({"endpoint": endpoint, "attempt": 1, "status": 200})
        value = self.routes[(endpoint, page)]
        if isinstance(value, BaseException):
            raise value
        payload, headers = value
        return SimpleNamespace(status=200, payload=deepcopy(payload), headers=deepcopy(headers))

    def global_preflight(self):
        if self.preflight_error is not None:
            raise self.preflight_error
        self.get_json("/user")
        self.get_json("/versions")
        return {
            "login": "synthetic-runner",
            "client_version": "gh version synthetic",
            "api_version": self.api_version,
        }


def tracker_routes(thread=None, *, link_override=None, comments_override=None):
    thread = fixture("tracker-thread.json") if thread is None else thread
    repository = "synthetic-lab/tracker"
    issue = 7
    issue_endpoint = f"/repos/{repository}/issues/{issue}"
    comments_endpoint = issue_endpoint + "/comments"
    pages = thread["comment_pages"]
    first_link = pages[0]["link"] if link_override is None else link_override
    first_comments = pages[0]["comments"] if comments_override is None else comments_override
    return {
        ("/user", 1): ({"login": "synthetic-runner"}, {}),
        ("/versions", 1): (["2026-03-10"], {}),
        (issue_endpoint, 1): (thread["issue"], {}),
        (comments_endpoint, 1): (first_comments, {"link": first_link} if first_link else {}),
        (comments_endpoint, 2): (pages[1]["comments"], {}),
    }


def hydrated_record(repository, number, role="unknown"):
    association = {
        "upstream-maintainer": "OWNER",
        "contributor": "CONTRIBUTOR",
        "unknown": "NONE",
    }[role]
    return {
        "identity_status": "resolved",
        "record_key": f"github-pr:PR_SYNTHETIC_{repository.replace('/', '_')}_{number}",
        "pr_id": None,
        "pull_request_node_id": f"PR_SYNTHETIC_{repository.replace('/', '_')}_{number}",
        "repository": {
            "full_name": repository,
            "node_id": f"R_SYNTHETIC_{repository.replace('/', '_')}",
            "repository_aliases": [],
        },
        "pull_request": {
            "number": number,
            "url": f"https://github.com/{repository}/pull/{number}",
            "title": "Synthetic pull request",
            "normalized_state": "open",
            "created_at": "2030-01-01T00:00:00Z",
            "closed_at": None,
            "merged_at": None,
            "updated_at": "2030-01-05T00:00:00Z",
        },
        "author": {
            "login": "synthetic-upstream-author",
            "node_id": "U_SYNTHETIC_AUTHOR",
            "association": association,
            "normalized_role": role,
        },
        "sources": [],
        "state_history": [{
            "state": "open",
            "observed_at": "2030-01-05T00:00:00Z",
            "authority": "GitHub pull request",
            "evidence_url": f"https://github.com/{repository}/pull/{number}",
        }],
        "hydration_status": "complete",
        "evidence_snapshot": {"partial_categories": [], "completeness": {}},
    }


def fake_hydrator(client, repository, number, captured_at):
    del client, captured_at
    return hydrated_record(repository, number)


SYNTHETIC_TOKEN = "synthetic_offline_token"


def fake_cli_routes():
    issue = fixture("tracker-thread.json")["issue"]
    pull = {
        "number": 11,
        "node_id": "PR_SYNTHETIC_WIDGET_11",
        "html_url": "https://github.com/synthetic-lab/widget/pull/11",
        "title": "Synthetic pull request",
        "body": "Synthetic pull request body",
        "state": "open",
        "merged_at": None,
        "created_at": "2030-01-01T00:00:00Z",
        "updated_at": "2030-01-05T00:00:00Z",
        "closed_at": None,
        "changed_files": 0,
        "commits": 0,
        "merge_commit_sha": None,
        "labels": [],
        "author_association": "NONE",
        "user": {"login": "synthetic-author", "node_id": "U_SYNTHETIC_AUTHOR"},
        "base": {"sha": "synthetic-base", "repo": {"node_id": "R_SYNTHETIC_WIDGET"}},
        "head": {"sha": "synthetic-head"},
    }
    return {
        "/user": {"login": "synthetic-runner"},
        "/versions": ["2026-03-10"],
        "/repos/synthetic-lab/tracker/issues/7": issue,
        "/repos/synthetic-lab/tracker/issues/7/comments": [],
        "/repos/synthetic-lab/widget": {"full_name": "synthetic-lab/widget", "node_id": "R_SYNTHETIC_WIDGET"},
        "/repos/synthetic-lab/widget/pulls/11": pull,
        "/repos/synthetic-lab/widget/pulls/11/files": [],
        "/repos/synthetic-lab/widget/pulls/11/commits": [],
        "/repos/synthetic-lab/widget/issues/11/comments": [],
        "/repos/synthetic-lab/widget/pulls/11/reviews": [],
        "/repos/synthetic-lab/widget/pulls/11/comments": [],
        "/repos/synthetic-lab/widget/issues/11/timeline": [],
        "/repos/synthetic-lab/widget/license": {
            "html_url": "https://github.com/synthetic-lab/widget/blob/main/LICENSE",
            "license": {"spdx_id": "MIT", "name": "Synthetic permissive license"},
        },
    }


def write_gh_guard(directory, log_path):
    """PATH 상의 gh 를 호출 기록 후 실패하는 guard 로 가린다.

    #192 이후 운영 전송은 urllib 이므로 CLI 자식이 gh 를 부르면 회귀다.
    """
    executable = Path(directory) / "gh"
    executable.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$*\" >> '{os.fspath(log_path)}'\n"
        "exit 97\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


def write_fake_urllib_bootstrap(directory):
    """CLI 자식에서 운영 urllib 경로를 그대로 타되 opener 만 합성 응답으로 바꾸는 bootstrap.

    GhApiClient 는 runner 가 없으면 ``urllib.request.build_opener(_NoRedirect)`` 로
    opener 를 만든다. bootstrap 은 그 함수만 교체하고 스크립트를 ``__main__`` 으로
    실행하므로 argparse, main(), SystemExit 종료코드, http_request, 읽기 전용 검사,
    토큰 부착, _open_api_request 는 모두 운영 코드 그대로 실행된다. 소켓 호출은
    실패시키되 시도 자체를 별도 로그에 남겨, 부모 테스트가 실통신 시도를 잡아낸다.
    """
    bootstrap = Path(directory) / "fake_urllib_bootstrap.py"
    program = """import json
import os
import runpy
import socket
import sys
import urllib.parse
import urllib.request

ROUTES = json.loads({routes!r})
HTTP_LOG = os.environ["SYNTHETIC_HTTP_LOG"]
SOCKET_LOG = os.environ["SYNTHETIC_SOCKET_LOG"]


def _append(path, entry):
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\\n")


def _blocked(name):
    def blocked(*args, **kwargs):
        _append(SOCKET_LOG, {{"call": name, "args": [repr(value) for value in args]}})
        raise OSError("synthetic test forbids socket use: " + name)
    return blocked


socket.socket.connect = _blocked("socket.connect")
socket.socket.connect_ex = _blocked("socket.connect_ex")
socket.create_connection = _blocked("socket.create_connection")
socket.getaddrinfo = _blocked("socket.getaddrinfo")


class SyntheticResponse:
    def __init__(self, url, status, payload):
        self._url = url
        self.status = status
        self.headers = {{"Content-Type": "application/json"}}
        self._body = json.dumps(payload).encode("utf-8")

    def geturl(self):
        return self._url

    def read(self):
        return self._body

    def close(self):
        pass


class SyntheticOpener:
    def __init__(self, handlers):
        self.handlers = handlers

    def open(self, request, timeout=None):
        parts = urllib.parse.urlsplit(request.full_url)
        _append(HTTP_LOG, {{
            "method": request.get_method(),
            "scheme": parts.scheme,
            "host": parts.netloc,
            "path": parts.path,
            "query": urllib.parse.parse_qs(parts.query),
            "headers": {{name.lower(): value for name, value in request.header_items()}},
            "has_body": request.data is not None,
            "timeout": timeout,
            "handlers": self.handlers,
        }})
        if parts.path in ROUTES:
            return SyntheticResponse(request.full_url, 200, ROUTES[parts.path])
        return SyntheticResponse(request.full_url, 404, {{"message": "synthetic missing route"}})


def build_opener(*handlers):
    return SyntheticOpener(sorted(
        getattr(handler, "__name__", type(handler).__name__) for handler in handlers
    ))


urllib.request.build_opener = build_opener
script = sys.argv[1]
sys.argv = [script, *sys.argv[2:]]
runpy.run_path(script, run_name="__main__")
""".format(routes=json.dumps(fake_cli_routes()))
    bootstrap.write_text(program, encoding="utf-8")
    return bootstrap


class FakeGhRunner:
    """Inert in-process stand-in for the real ``gh`` executable."""

    def __init__(self):
        self.calls = []
        self.thread = fixture("tracker-thread.json")

    @staticmethod
    def _pull(repository, number):
        merged = repository.endswith("gadget")
        return {
            "number": number,
            "node_id": f"PR_SYNTHETIC_{repository.replace('/', '_')}_{number}",
            "html_url": f"https://github.com/{repository}/pull/{number}",
            "title": "Synthetic authoritative pull request",
            "body": "Synthetic inert pull request body",
            "state": "closed" if merged else "open",
            "merged_at": "2030-01-08T00:00:00Z" if merged else None,
            "created_at": "2030-01-01T00:00:00Z",
            "updated_at": "2030-01-08T00:00:00Z" if merged else "2030-01-05T00:00:00Z",
            "closed_at": "2030-01-08T00:00:00Z" if merged else None,
            "changed_files": 0,
            "commits": 0,
            "merge_commit_sha": "synthetic-merge-sha" if merged else None,
            "labels": [],
            "author_association": "CONTRIBUTOR" if merged else "NONE",
            "user": {
                "login": "synthetic-upstream-author",
                "node_id": f"U_SYNTHETIC_{number}",
            },
            "base": {
                "sha": f"synthetic-base-{number}",
                "repo": {"node_id": f"R_SYNTHETIC_{repository.replace('/', '_')}"},
            },
            "head": {"sha": f"synthetic-head-{number}"},
        }

    @staticmethod
    def _page(argv):
        for index, value in enumerate(argv[:-1]):
            if value == "-f" and argv[index + 1].startswith("page="):
                return int(argv[index + 1].split("=", 1)[1])
        return 1

    def _response(self, endpoint, page):
        if endpoint == "/user":
            return {"login": "synthetic-runner"}, {}
        if endpoint == "/versions":
            return ["2026-03-10"], {}
        if endpoint == "/repos/synthetic-lab/tracker/issues/7":
            return self.thread["issue"], {}
        if endpoint == "/repos/synthetic-lab/tracker/issues/7/comments":
            entry = self.thread["comment_pages"][page - 1]
            headers = {"Link": entry["link"]} if entry["link"] else {}
            return entry["comments"], headers
        repository_match = re.fullmatch(r"/repos/(synthetic-lab/(?:widget|gadget))", endpoint)
        if repository_match:
            repository = repository_match.group(1)
            return {
                "full_name": repository,
                "node_id": f"R_SYNTHETIC_{repository.replace('/', '_')}",
            }, {}
        pull_match = re.fullmatch(
            r"/repos/(synthetic-lab/(?:widget|gadget))/pulls/(11|22)", endpoint
        )
        if pull_match:
            return self._pull(pull_match.group(1), int(pull_match.group(2))), {}
        if endpoint.endswith("/license"):
            return {
                "html_url": "https://github.com/synthetic-lab/synthetic/blob/main/LICENSE",
                "license": {"spdx_id": "MIT", "name": "Synthetic permissive license"},
            }, {}
        if any(endpoint.endswith(suffix) for suffix in (
            "/files", "/commits", "/comments", "/reviews", "/timeline"
        )):
            return [], {}
        raise AssertionError("unexpected synthetic endpoint: " + endpoint)

    def __call__(self, argv, **kwargs):
        self.calls.append({"argv": list(argv), **deepcopy(kwargs)})
        if argv == ["gh", "--version"]:
            return SimpleNamespace(returncode=0, stdout="gh version synthetic\n", stderr="")
        if argv[:4] != ["gh", "api", "--method", "GET"]:
            return SimpleNamespace(returncode=2, stdout="", stderr="synthetic non-GET rejected")
        endpoint = next((value for value in argv if isinstance(value, str) and value.startswith("/")), None)
        payload, headers = self._response(endpoint, self._page(argv))
        header_text = "".join(f"{name}: {value}\r\n" for name, value in headers.items())
        stdout = "HTTP/1.1 200 OK\r\n" + header_text + "\r\n" + json.dumps(payload)
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


class PartialHydrationGhRunner(FakeGhRunner):
    """Synthetic CLI runner whose repository resolves but PR core is inaccessible."""

    def __init__(self):
        super().__init__()
        self.thread = fixture("partial-hydration-thread.json")

    def _response(self, endpoint, page):
        if endpoint == "/repos/synthetic-lab/sample-lib":
            return {
                "full_name": "synthetic-lab/sample-lib",
                "node_id": "R_SYNTHETIC_SAMPLE_LIB",
            }, {}
        if endpoint == "/repos/synthetic-lab/sample-lib/license":
            return {
                "html_url": "https://github.com/synthetic-lab/sample-lib/blob/main/LICENSE",
                "license": {"spdx_id": "MIT", "name": "Synthetic permissive license"},
            }, {}
        if endpoint.startswith("/repos/synthetic-lab/sample-lib/"):
            return [], {}
        return super()._response(endpoint, page)

    def __call__(self, argv, **kwargs):
        endpoint = next(
            (value for value in argv if isinstance(value, str) and value.startswith("/")),
            None,
        )
        if endpoint == "/repos/synthetic-lab/sample-lib/pulls/9999":
            self.calls.append({"argv": list(argv), **deepcopy(kwargs)})
            return SimpleNamespace(
                returncode=1,
                stdout='HTTP/1.1 404 Not Found\r\n\r\n{"message":"synthetic inaccessible"}',
                stderr="",
            )
        return super().__call__(argv, **kwargs)


def run_end_to_end(root, *, skill_revision=None):
    collector = load_collector()
    runner = FakeGhRunner()
    corpus_path = Path(root) / "synthetic-corpus.json"
    manifest_path = Path(root) / "synthetic-manifest.json"
    sibling = collector.load_sibling()

    def client_factory(**kwargs):
        return sibling.GhApiClient(
            budget=kwargs["budget"],
            runner=runner,
            sleeper=lambda delay: None,
            clock=lambda: 0.0,
        )

    argv = [
        "collect", "--tracker-repo", "synthetic-lab/tracker", "--issue", "7",
        "--max-prs", "2", "--request-budget", "60",
        "--output", os.fspath(corpus_path), "--manifest", os.fspath(manifest_path),
    ]
    with contextlib.ExitStack() as stack:
        stack.enter_context(mock.patch.object(
            collector, "_timestamp", return_value="2030-01-10T00:00:00Z"
        ))
        if skill_revision is not None:
            stack.enter_context(mock.patch.object(
                collector, "compute_skill_revision", return_value=skill_revision
            ))
        exit_code = collector.main(argv, client_factory=client_factory)
    corpus_bytes = corpus_path.read_bytes() if corpus_path.exists() else None
    manifest_bytes = manifest_path.read_bytes() if manifest_path.exists() else None
    return SimpleNamespace(
        collector=collector,
        runner=runner,
        exit_code=exit_code,
        corpus_path=corpus_path,
        manifest_path=manifest_path,
        corpus_bytes=corpus_bytes,
        manifest_bytes=manifest_bytes,
        corpus=json.loads(corpus_bytes) if corpus_bytes is not None else None,
        manifest=json.loads(manifest_bytes) if manifest_bytes is not None else None,
    )


def run_partial_hydration_end_to_end(
    root,
    *,
    existing=False,
    timestamp="2030-03-10T00:00:00Z",
):
    collector = load_collector()
    runner = PartialHydrationGhRunner()
    corpus_path = Path(root) / "synthetic-partial-corpus.json"
    manifest_path = Path(root) / "synthetic-partial-manifest.json"
    sibling = collector.load_sibling()

    def client_factory(**kwargs):
        return sibling.GhApiClient(
            budget=kwargs["budget"],
            runner=runner,
            sleeper=lambda delay: None,
            clock=lambda: 0.0,
        )

    argv = [
        "collect", "--tracker-repo", "synthetic-lab/tracker", "--issue", "7",
        "--max-prs", "1", "--request-budget", "60",
        "--output", os.fspath(corpus_path), "--manifest", os.fspath(manifest_path),
    ]
    if existing:
        argv.extend([
            "--existing-corpus", os.fspath(corpus_path),
            "--existing-manifest", os.fspath(manifest_path),
        ])
    with mock.patch.object(collector, "_timestamp", return_value=timestamp):
        exit_code = collector.main(argv, client_factory=client_factory)
    return SimpleNamespace(
        collector=collector,
        runner=runner,
        exit_code=exit_code,
        corpus_path=corpus_path,
        manifest_path=manifest_path,
        corpus=json.loads(corpus_path.read_text(encoding="utf-8")) if corpus_path.exists() else None,
        manifest=json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None,
    )


class ContractTests(unittest.TestCase):
    def test_ac_01_contract_routing(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: collecting-curated-contribution-prs", skill)
        self.assertIn("tracker Issue", skill)
        self.assertIn("collecting-recent-closed-prs", skill)
        self.assertIn("analyzing-open-source-pr-patterns", skill)
        self.assertIn("verifying-open-source-contribution-candidates", skill)
        self.assertIn("GitHub writes", skill)
        self.assertIn("references/collection-contract.md", skill)
        self.assertIn("references/github-rest-contract.md", skill)

    def test_ac_02_contract_cli_validation(self):
        collector = load_collector()
        valid = [
            "collect",
            "--tracker-repo", "synthetic-lab/tracker",
            "--issue", "7",
            "--max-prs", "3",
            "--request-budget", "40",
            "--output", "corpus.json",
            "--manifest", "manifest.json",
        ]
        args = collector.build_parser().parse_args(valid)
        collector.validate_cli_args(args)

        invalid_variants = (
            ("--tracker-repo", "not-a-repository"),
            ("--issue", "0"),
            ("--max-prs", "0"),
            ("--request-budget", "0"),
            ("--manifest", "corpus.json"),
        )
        for option, replacement in invalid_variants:
            candidate = list(valid)
            candidate[candidate.index(option) + 1] = replacement
            parsed = collector.build_parser().parse_args(candidate)
            with self.subTest(option=option, replacement=replacement):
                with self.assertRaises(ValueError):
                    collector.validate_cli_args(parsed)

        incomplete = collector.build_parser().parse_args(valid + ["--resume-run-id", "run-synthetic"])
        with self.assertRaises(ValueError):
            collector.validate_cli_args(incomplete)

        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                ["/opt/homebrew/bin/python3", os.fspath(SCRIPT), "--print-revision"],
                cwd=temporary,
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertRegex(completed.stdout, r"\Asha256:[0-9a-f]{64}\n\Z")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            binary = root / "bin"
            binary.mkdir()
            gh_log = root / "gh-invocations.log"
            http_log = root / "http-requests.jsonl"
            socket_log = root / "socket-attempts.jsonl"
            write_gh_guard(binary, gh_log)
            bootstrap = write_fake_urllib_bootstrap(root)
            corpus_path = root / "synthetic-corpus.json"
            manifest_path = root / "synthetic-manifest.json"
            completed = subprocess.run(
                [
                    "/opt/homebrew/bin/python3", os.fspath(bootstrap), os.fspath(SCRIPT),
                    "collect", "--tracker-repo", "synthetic-lab/tracker",
                    "--issue", "7", "--max-prs", "1", "--request-budget", "40",
                    "--output", os.fspath(corpus_path),
                    "--manifest", os.fspath(manifest_path),
                ],
                cwd=temporary,
                capture_output=True,
                text=True,
                check=False,
                env={
                    **os.environ,
                    "PATH": os.fspath(binary) + os.pathsep + os.environ.get("PATH", ""),
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "GH_TOKEN": SYNTHETIC_TOKEN,
                    "GITHUB_TOKEN": SYNTHETIC_TOKEN,
                    "SYNTHETIC_HTTP_LOG": os.fspath(http_log),
                    "SYNTHETIC_SOCKET_LOG": os.fspath(socket_log),
                },
            )
            socket_attempts = socket_log.read_text(encoding="utf-8") if socket_log.exists() else ""
            self.assertEqual("", socket_attempts, "CLI child attempted a real socket")
            self.assertFalse(gh_log.exists(), "CLI child invoked gh instead of urllib")
            self.assertEqual(0, completed.returncode, completed.stderr)
            manifest_record = json.loads(manifest_path.read_text(encoding="utf-8"))["records"][-1]
            self.assertEqual("complete", manifest_record["collection_status"])
            self.assertEqual("python-urllib", manifest_record["client_version"])
            self.assertEqual(1, len(json.loads(corpus_path.read_text(encoding="utf-8"))["records"]))

            requests = [
                json.loads(line)
                for line in http_log.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(["/user", "/versions"], [entry["path"] for entry in requests[:2]])
            self.assertTrue({
                "/repos/synthetic-lab/tracker/issues/7",
                "/repos/synthetic-lab/tracker/issues/7/comments",
                "/repos/synthetic-lab/widget/pulls/11",
            } <= {entry["path"] for entry in requests})
            self.assertEqual(manifest_record["request_count"], len(requests))
            routes = fake_cli_routes()
            for entry in requests:
                with self.subTest(path=entry["path"]):
                    self.assertIn(entry["path"], routes)
                    self.assertEqual("GET", entry["method"])
                    self.assertFalse(entry["has_body"])
                    self.assertEqual(("https", "api.github.com"), (entry["scheme"], entry["host"]))
                    self.assertEqual(["100"], entry["query"]["per_page"])
                    self.assertEqual("application/vnd.github+json", entry["headers"]["accept"])
                    self.assertEqual("2026-03-10", entry["headers"]["x-github-api-version"])
                    self.assertEqual("Bearer " + SYNTHETIC_TOKEN, entry["headers"]["authorization"])
                    self.assertEqual(["_NoRedirect"], entry["handlers"])
                    self.assertEqual(30, entry["timeout"])

        calls = []
        missing = Path("/synthetic/missing/collect_recent_closed_prs.py")
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = collector.main(valid, sibling_script=missing, client_factory=lambda **kwargs: calls.append(kwargs))
        self.assertEqual(2, result)
        self.assertEqual([], calls)
        self.assertEqual(
            f"error: collecting-recent-closed-prs sibling script not found: {missing.resolve()}\n",
            stderr.getvalue(),
        )

        with tempfile.TemporaryDirectory() as temporary:
            missing_parent = Path(temporary) / "missing-parent"
            invalid_output = list(valid)
            invalid_output[invalid_output.index("--output") + 1] = os.fspath(missing_parent / "corpus.json")
            invalid_output[invalid_output.index("--manifest") + 1] = os.fspath(missing_parent / "manifest.json")
            calls = []
            with contextlib.redirect_stderr(io.StringIO()):
                result = collector.main(invalid_output, client_factory=lambda **kwargs: calls.append(kwargs))
            self.assertEqual(2, result)
            self.assertEqual([], calls)

    def test_ac_03_contract_packaging(self):
        expected_required = {
            "SKILL.md",
            "agents/openai.yaml",
            "references/collection-contract.md",
            "references/github-rest-contract.md",
            "scripts/collect_curated_contribution_prs.py",
            "tests/test_collect_curated_contribution_prs.py",
        }
        actual = packaged_files()
        self.assertTrue(expected_required.issubset(actual))
        allowed_exact = expected_required | {
            "evals/behavioral-eval.md",
            "tests/fixtures/tracker-thread.json",
            "tests/fixtures/tracker-thread-edited.json",
            "tests/fixtures/tracker-thread-failures.json",
            "tests/fixtures/reference-classification.json",
            "tests/fixtures/partial-hydration-thread.json",
            "tests/fixtures/pr-hydration.json",
            "tests/fixtures/initial-corpus.json",
            "tests/fixtures/expected-corpus.json",
            "tests/fixtures/recollected-corpus.json",
            "tests/fixtures/manifest-cases.json",
        }
        self.assertEqual(set(), actual - allowed_exact)
        metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")
        for key in ("display_name", "short_description", "default_prompt"):
            self.assertRegex(metadata, rf"(?m)^  {key}: \"[^\n]+\"$")
        self.assertIn("$collecting-curated-contribution-prs", metadata)
        all_names = {path.name.lower() for path in SKILL_DIR.rglob("*") if path.is_file()}
        self.assertFalse({"readme.md", "changelog.md", "install.md", "quick-reference.md"} & all_names)

    def test_ac_26_contract_public_fixtures(self):
        public_files = [
            SKILL_DIR / "SKILL.md",
            SKILL_DIR / "references" / "collection-contract.md",
            SKILL_DIR / "references" / "github-rest-contract.md",
            *sorted(FIXTURES.glob("*.json")),
        ]
        self.assertGreaterEqual(len(public_files), 8)
        forbidden = ("PRIVATE ROSTER", "BEGIN PRIVATE KEY", "ghp_", "@example.com")
        for path in public_files:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("synthetic", text.lower())
                self.assertFalse(any(marker in text for marker in forbidden))
        for fixture in FIXTURES.glob("*.json"):
            json.loads(fixture.read_text(encoding="utf-8"))

    def test_ac_40_contract_judgement_mapping(self):
        command_filters = {
            "CMD-2": "contract",
            "CMD-3": "collection",
            "CMD-4": "merge",
            "CMD-12": "end_to_end",
        }
        expected_ac_by_command = {
            "CMD-2": {1, 2, 3, 26, 40},
            "CMD-3": {4, 6, 7, 9, 13, 21, 22, 23, 24, 25, 39},
            "CMD-4": {14, 16, 17, 19, 38},
            "CMD-12": {5, 8, 10, 12, 20, 27, 31, 32, 37},
        }
        acceptance_line = re.compile(
            r"^- \*\*AC-(?P<ac>[1-9][0-9]*)\*\*.*\[실행\]\s+\((?P<judgement>[^)]*)\)\s*$"
        )
        exact_token = re.compile(
            r"\btest_ac_(?P<ac>[0-9]{2})_"
            r"(?P<filter>contract|collection|merge|end_to_end)_"
            r"[a-z0-9_]+\b"
        )
        parsed_by_command = {command: set() for command in command_filters}
        spec_tokens = {}
        for line in SPEC.read_text(encoding="utf-8").splitlines():
            match = acceptance_line.fullmatch(line)
            if match is None:
                continue
            ac_number = int(match.group("ac"))
            judgement = match.group("judgement")
            filtered_commands = [
                command for command in command_filters if command in judgement.split()
            ]
            if not filtered_commands:
                continue
            self.assertEqual(1, len(filtered_commands), line)
            command = filtered_commands[0]
            tokens = list(exact_token.finditer(judgement))
            self.assertEqual(1, len(tokens), line)
            token = tokens[0]
            self.assertEqual(f"{ac_number:02d}", token.group("ac"), line)
            self.assertEqual(command_filters[command], token.group("filter"), line)
            method_name = token.group(0)
            self.assertNotIn(method_name, spec_tokens, line)
            spec_tokens[method_name] = (ac_number, command)
            parsed_by_command[command].add(ac_number)

        self.assertEqual(expected_ac_by_command, parsed_by_command)

        hardening_tokens = {}
        for line in HARDENING_SPEC.read_text(encoding="utf-8").splitlines():
            match = acceptance_line.fullmatch(line)
            if match is None:
                continue
            ac_number = int(match.group("ac"))
            for token in exact_token.finditer(match.group("judgement")):
                self.assertEqual(f"{ac_number:02d}", token.group("ac"), line)
                method_name = token.group(0)
                self.assertNotIn(method_name, hardening_tokens, line)
                hardening_tokens[method_name] = ac_number
        self.assertEqual(
            {"test_ac_22_contract_stdlib_synthetic_packaging": 22},
            hardening_tokens,
        )

        discovered_suite = unittest.TestLoader().discover(
            start_dir=os.fspath(SKILL_DIR / "tests"),
            pattern="test_*.py",
            top_level_dir=os.fspath(SKILL_DIR / "tests"),
        )

        def iter_tests(suite):
            for item in suite:
                if isinstance(item, unittest.TestSuite):
                    yield from iter_tests(item)
                else:
                    yield item

        discovered_tokens = [
            test._testMethodName
            for test in iter_tests(discovered_suite)
            if exact_token.fullmatch(test._testMethodName)
        ]
        self.assertEqual(len(discovered_tokens), len(set(discovered_tokens)))
        hardening_method_names = set(hardening_tokens)
        self.assertTrue(hardening_method_names <= set(discovered_tokens))
        legacy_discovered_tokens = set(discovered_tokens) - hardening_method_names
        self.assertEqual(set(spec_tokens), legacy_discovered_tokens)
        self.assertIn(self._testMethodName, discovered_tokens)


class RevisionTests(unittest.TestCase):
    def test_ac_28_revision_six_file_byte_mutations(self):
        collector = load_collector()
        canonical_paths = (
            "SKILL.md",
            "agents/openai.yaml",
            "references/collection-contract.md",
            "references/github-rest-contract.md",
            "scripts/collect_curated_contribution_prs.py",
            "tests/test_collect_curated_contribution_prs.py",
        )
        self.assertEqual(canonical_paths, tuple(sorted(collector.SKILL_REVISION_PATHS)))

        expected = hashlib.sha256()
        for relative in canonical_paths:
            path_bytes = relative.encode("utf-8")
            content = (SKILL_DIR / relative).read_bytes()
            expected.update(len(path_bytes).to_bytes(8, byteorder="big"))
            expected.update(path_bytes)
            expected.update(len(content).to_bytes(8, byteorder="big"))
            expected.update(content)
        original_revision = "sha256:" + expected.hexdigest()
        self.assertEqual(original_revision, collector.compute_skill_revision())

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, relative in enumerate(canonical_paths):
                copied_skill = root / str(index)
                shutil.copytree(SKILL_DIR, copied_skill)
                target = copied_skill / relative
                content = target.read_bytes()
                self.assertTrue(content, relative)
                target.write_bytes(bytes((content[0] ^ 1,)) + content[1:])
                with self.subTest(relative=relative):
                    self.assertNotEqual(
                        original_revision,
                        collector.compute_skill_revision(copied_skill),
                    )


class CollectionTests(unittest.TestCase):
    def test_ac_01_post_review_remote_repository_validation(self):
        collector = load_collector()
        thread = deepcopy(fixture("tracker-thread.json"))
        thread["issue"]["body"] = "https://github.com/../../pull/1"
        thread["comment_pages"][0]["link"] = None
        thread["comment_pages"][0]["comments"] = []
        client = FakeClient(tracker_routes(thread))

        run = collector.collect(
            client,
            "synthetic-lab/tracker",
            7,
            max_prs=1,
            request_budget=20,
            hydrator=fake_hydrator,
            timestamp="2030-03-01T00:00:00Z",
        )

        record = run.manifest["records"][-1]
        self.assertEqual(4, run.exit_code)
        self.assertEqual("failed", record["collection_status"])
        self.assertEqual("excluded-invalid-repository", record["reference_exclusions"][0]["classification"])
        self.assertTrue(any(scope["kind"] == "reference-identity" for scope in record["failed_scopes"]))
        self.assertTrue(any("invalid repository identity" in warning for warning in record["warnings"]))
        self.assertFalse(any(".." in endpoint.split("/") for endpoint, _ in client.calls))

    def test_ac_02_post_review_terminal_link_without_next(self):
        collector = load_collector()
        comments_endpoint = "/repos/synthetic-lab/tracker/issues/7/comments"
        terminal_routes = tracker_routes()
        comments = terminal_routes[(comments_endpoint, 1)][0]
        terminal_routes[(comments_endpoint, 1)] = (
            comments,
            {
                "Link": (
                    '<https://api.github.com/repos/synthetic-lab/tracker/issues/7/comments?page=1>; rel="prev", '
                    '<https://api.github.com/repos/synthetic-lab/tracker/issues/7/comments?page=1>; rel="first"'
                )
            },
        )
        terminal_client = FakeClient(terminal_routes)
        terminal = collector.collect_issue_thread(
            terminal_client, "synthetic-lab/tracker", 7
        )

        absent_routes = tracker_routes()
        absent_routes[(comments_endpoint, 1)] = (comments, {})
        absent = collector.collect_issue_thread(
            FakeClient(absent_routes), "synthetic-lab/tracker", 7
        )

        self.assertEqual([], terminal["failed_scopes"])
        self.assertEqual("present-terminal", terminal["pages"][0]["link_state"])
        self.assertEqual("absent", absent["pages"][0]["link_state"])
        self.assertEqual(1, len([
            call for call in terminal_client.calls if call[0] == comments_endpoint
        ]))

    def test_ac_03_post_review_unsupported_header_shape(self):
        collector = load_collector()
        comments_endpoint = "/repos/synthetic-lab/tracker/issues/7/comments"
        unsupported_routes = tracker_routes()
        comments = unsupported_routes[(comments_endpoint, 1)][0]
        unsupported_routes[(comments_endpoint, 1)] = (comments, ["synthetic-header"])

        unsupported = collector.collect(
            FakeClient(unsupported_routes),
            "synthetic-lab/tracker",
            7,
            max_prs=1,
            request_budget=20,
            hydrator=fake_hydrator,
            timestamp="2030-03-02T00:00:00Z",
        )
        record = unsupported.manifest["records"][-1]

        absent_routes = tracker_routes()
        absent_routes[(comments_endpoint, 1)] = (comments, {})
        absent = collector.collect_issue_thread(
            FakeClient(absent_routes), "synthetic-lab/tracker", 7
        )

        self.assertEqual(3, unsupported.exit_code)
        self.assertEqual("unsupported-container", record["comment_pages"][0]["link_state"])
        self.assertTrue(any(scope["kind"] == "header-container" for scope in record["failed_scopes"]))
        self.assertTrue(any("header-container" in warning for warning in record["warnings"]))
        self.assertEqual([], absent["failed_scopes"])
        self.assertEqual("absent", absent["pages"][0]["link_state"])

    def test_ac_04_post_review_korean_label_boundary(self):
        collector = load_collector()
        issue = deepcopy(fixture("tracker-thread.json")["issue"])
        labels = [
            keyword + delimiter
            for keyword in ("예시", "공지")
            for delimiter in ("", ":", "：", "-", "–", "—")
        ]
        issue["body"] = "\n".join(
            [
                "리뷰 예시 스크린샷을 첨부합니다",
                "https://github.com/synthetic-lab/korean-real/pull/1",
            ]
            + [
                line
                for number, label in enumerate(labels, start=2)
                for line in (
                    label,
                    f"https://github.com/synthetic-lab/korean-{number}/pull/{number}",
                )
            ]
        )

        inventory = collector.select_references(
            collector.extract_references(issue, [], run_id="run-korean-boundary"),
            max_prs=20,
        )

        self.assertEqual(
            [("synthetic-lab/korean-real", 1)],
            [item["identity"] for item in inventory["selected"]],
        )
        self.assertEqual(12, len(inventory["reference_exclusions"]))
        self.assertEqual(
            {"예시", "공지"},
            {
                item["classification_basis"]["matched_keyword"]
                for item in inventory["reference_exclusions"]
            },
        )

    def test_ac_05_post_review_examples_plural(self):
        collector = load_collector()
        issue = deepcopy(fixture("tracker-thread.json")["issue"])
        issue["body"] = "\n".join([
            "Examples:",
            "https://github.com/synthetic-lab/examples-heading/pull/1",
            "Format example (do NOT count this one)",
            "https://github.com/synthetic-lab/example-description/pull/2",
            "preexamplespost is ordinary prose",
            "https://github.com/synthetic-lab/example-real/pull/3",
        ])

        inventory = collector.select_references(
            collector.extract_references(issue, [], run_id="run-examples-plural"),
            max_prs=10,
        )

        self.assertEqual(
            [("synthetic-lab/example-real", 3)],
            [item["identity"] for item in inventory["selected"]],
        )
        self.assertEqual(
            {"example", "examples"},
            {
                item["classification_basis"]["matched_keyword"]
                for item in inventory["reference_exclusions"]
            },
        )

    def test_ac_06_post_review_notices_plural(self):
        collector = load_collector()
        issue = deepcopy(fixture("tracker-thread.json")["issue"])
        issue["body"] = "\n".join([
            "Notices:",
            "https://github.com/synthetic-lab/notices-heading/pull/1",
            "Notice:",
            "https://github.com/synthetic-lab/notice-heading/pull/2",
            "Announcement:",
            "https://github.com/synthetic-lab/announcement-heading/pull/3",
            "prenoticespost is ordinary prose",
            "https://github.com/synthetic-lab/notice-real/pull/4",
            "preannouncementpost is ordinary prose",
            "https://github.com/synthetic-lab/announcement-real/pull/5",
        ])

        inventory = collector.select_references(
            collector.extract_references(issue, [], run_id="run-notices-plural"),
            max_prs=10,
        )

        self.assertEqual(
            [
                ("synthetic-lab/notice-real", 4),
                ("synthetic-lab/announcement-real", 5),
            ],
            [item["identity"] for item in inventory["selected"]],
        )
        self.assertEqual(
            {"notice", "notices", "announcement"},
            {
                item["classification_basis"]["matched_keyword"]
                for item in inventory["reference_exclusions"]
            },
        )

    def test_ac_07_post_review_non_pr_url_label(self):
        collector = load_collector()
        issue = deepcopy(fixture("tracker-thread.json")["issue"])
        issue["body"] = (
            "Review https://synthetic.invalid/issues/example-notice "
            "https://github.com/synthetic-lab/example-project/pull/7"
        )

        inventory = collector.select_references(
            collector.extract_references(issue, [], run_id="run-url-label"),
            max_prs=10,
        )

        self.assertEqual(
            [("synthetic-lab/example-project", 7)],
            [item["identity"] for item in inventory["selected"]],
        )
        self.assertEqual([], inventory["reference_exclusions"])

        contract = (SKILL_DIR / "references" / "collection-contract.md").read_text(
            encoding="utf-8"
        )
        normalized_contract = " ".join(contract.split())
        self.assertIn(
            "The same-line prefix is checked first, followed by the immediately preceding line.",
            normalized_contract,
        )
        self.assertIn(
            "`example`, `examples`, `notice`, `notices`, and `announcement`",
            normalized_contract,
        )
        self.assertIn("ASCII letter boundaries", normalized_contract)
        self.assertIn("normalized label's first token", normalized_contract)
        self.assertIn("`예시` or `공지`", normalized_contract)
        self.assertIn("`:`, `：`, `-`, `–`, or `—`", normalized_contract)
        self.assertIn(
            "manifest exclusion records the matched keyword, evaluated label, and whether it came from the same-line prefix or previous line",
            normalized_contract,
        )

    def test_ac_08_post_review_processing_handler_append_only(self):
        collector = load_collector()
        prior_records = [
            {
                "run_id": f"run-prior-{number}",
                "collection_method": collector.COLLECTION_METHOD,
                "tracker": {"repository": "synthetic-lab/tracker", "issue_number": 7},
                "collection_status": "complete",
                "synthetic_marker": {"number": number},
            }
            for number in (1, 2)
        ]
        existing_manifest = {
            "schema_version": "2.0.0",
            "generated_by": {"name": collector.SKILL_NAME, "revision": "synthetic"},
            "records": deepcopy(prior_records),
        }
        existing_corpus = {
            "schema_version": "1.0.0",
            "generated_by": {"name": collector.SKILL_NAME, "revision": "synthetic"},
            "records": [],
        }

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus_path = root / "corpus.json"
            manifest_path = root / "manifest.json"
            corpus_path.write_text(json.dumps(existing_corpus) + "\n", encoding="utf-8")
            manifest_path.write_text(json.dumps(existing_manifest) + "\n", encoding="utf-8")
            client = FakeClient(tracker_routes())
            argv = [
                "collect", "--tracker-repo", "synthetic-lab/tracker", "--issue", "7",
                "--max-prs", "9", "--request-budget", "20",
                "--output", os.fspath(corpus_path), "--manifest", os.fspath(manifest_path),
                "--existing-corpus", os.fspath(corpus_path),
                "--existing-manifest", os.fspath(manifest_path),
            ]

            def fail_after_request(*args, **kwargs):
                del args, kwargs
                client.get_json("/user")
                raise ValueError("synthetic post-request processing failure")

            with mock.patch.object(collector, "collect", side_effect=fail_after_request):
                with contextlib.redirect_stderr(io.StringIO()):
                    exit_code = collector.main(argv, client_factory=lambda **kwargs: client)

            actual = json.loads(manifest_path.read_text(encoding="utf-8"))["records"]
        self.assertEqual(4, exit_code)
        self.assertEqual(prior_records, actual[:2])
        self.assertEqual(3, len(actual))
        self.assertEqual("failed", actual[-1]["collection_status"])
        self.assertEqual("processing", actual[-1]["failed_scopes"][0]["kind"])

    def test_ac_09_post_review_failed_record_field_parity(self):
        collector = load_collector()
        max_prs = 9
        common_keys = {
            "run_id", "request_fingerprint", "collection_method", "tracker",
            "collection_status", "started_at", "completed_at", "checkpoint",
            "api_version", "client_version", "skill", "max_prs",
            "request_budget", "request_count", "request_events", "comment_pages",
            "reference_counts", "cap_exclusions", "reference_exclusions",
            "hydration_outcomes", "warnings", "failed_scopes", "preflight",
        }
        normal = collector.collect(
            FakeClient(tracker_routes()),
            "synthetic-lab/tracker",
            7,
            max_prs=max_prs,
            request_budget=20,
            hydrator=fake_hydrator,
            timestamp="2030-03-09T00:00:00Z",
        ).manifest["records"][-1]
        preflight = collector.collect(
            FakeClient({}, preflight_error=RuntimeError("synthetic preflight failed")),
            "synthetic-lab/tracker",
            7,
            max_prs=max_prs,
            request_budget=20,
            hydrator=fake_hydrator,
            timestamp="2030-03-09T00:00:00Z",
        ).manifest["records"][-1]

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            client = FakeClient(tracker_routes())
            manifest_path = root / "manifest.json"
            argv = [
                "collect", "--tracker-repo", "synthetic-lab/tracker", "--issue", "7",
                "--max-prs", str(max_prs), "--request-budget", "20",
                "--output", os.fspath(root / "corpus.json"),
                "--manifest", os.fspath(manifest_path),
            ]

            def fail_after_request(*args, **kwargs):
                del args, kwargs
                client.get_json("/user")
                raise ValueError("synthetic post-request processing failure")

            with mock.patch.object(collector, "collect", side_effect=fail_after_request):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(
                        4,
                        collector.main(argv, client_factory=lambda **kwargs: client),
                    )
            processing = json.loads(manifest_path.read_text(encoding="utf-8"))["records"][-1]

        for label, record in (
            ("normal", normal),
            ("preflight", preflight),
            ("processing", processing),
        ):
            with self.subTest(path=label):
                self.assertEqual(common_keys, set(record))
                self.assertEqual(max_prs, record["max_prs"])

    def test_ac_10_post_review_resume_corpus_reconciliation(self):
        collector = load_collector()
        initial = collector.collect(
            FakeClient(tracker_routes()),
            "synthetic-lab/tracker",
            7,
            max_prs=2,
            request_budget=20,
            hydrator=fake_hydrator,
            timestamp="2030-03-10T00:00:00Z",
        )
        self.assertEqual(0, initial.exit_code)
        run_id = initial.manifest["records"][-1]["run_id"]

        missing = deepcopy(initial.corpus)
        missing["records"] = missing["records"][1:]
        conflicting = deepcopy(initial.corpus)
        duplicate = deepcopy(conflicting["records"][0])
        duplicate["pull_request_node_id"] = "PR_SYNTHETIC_CONFLICT"
        conflicting["records"].append(duplicate)

        def resume(corpus):
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                corpus_path = root / "corpus.json"
                manifest_path = root / "manifest.json"
                corpus_path.write_bytes(collector._json_bytes(corpus))
                manifest_path.write_bytes(collector._json_bytes(initial.manifest))
                before = (corpus_path.read_bytes(), manifest_path.read_bytes())
                client = FakeClient(tracker_routes())
                argv = [
                    "collect", "--tracker-repo", "synthetic-lab/tracker", "--issue", "7",
                    "--max-prs", "2", "--request-budget", "20",
                    "--output", os.fspath(corpus_path), "--manifest", os.fspath(manifest_path),
                    "--existing-corpus", os.fspath(corpus_path),
                    "--existing-manifest", os.fspath(manifest_path),
                    "--resume-run-id", run_id,
                ]
                with contextlib.redirect_stderr(io.StringIO()):
                    exit_code = collector.main(argv, client_factory=lambda **kwargs: client)
                return SimpleNamespace(
                    exit_code=exit_code,
                    calls=deepcopy(client.calls),
                    before=before,
                    after=(corpus_path.read_bytes(), manifest_path.read_bytes()),
                    manifest=json.loads(manifest_path.read_text(encoding="utf-8")),
                )

        for label, corpus in (("missing", missing), ("conflicting", conflicting)):
            with self.subTest(case=label):
                result = resume(corpus)
                self.assertEqual(2, result.exit_code)
                self.assertEqual([], result.calls)
                self.assertEqual(result.before, result.after)
                self.assertFalse(any(
                    record.get("checkpoint_reused")
                    for record in result.manifest["records"]
                ))

        matched = resume(initial.corpus)
        self.assertEqual(0, matched.exit_code)
        self.assertEqual([], matched.calls)
        self.assertTrue(matched.manifest["records"][-1]["checkpoint_reused"])

    def test_ac_11_post_review_manifest_warnings(self):
        collector = load_collector()

        def run_with(thread=None, hydrator=fake_hydrator):
            return collector.collect(
                FakeClient(tracker_routes(thread)),
                "synthetic-lab/tracker",
                7,
                max_prs=2,
                request_budget=20,
                hydrator=hydrator,
                timestamp="2030-03-11T00:00:00Z",
            ).manifest["records"][-1]

        invalid_thread = deepcopy(fixture("tracker-thread.json"))
        invalid_thread["issue"]["body"] = "https://github.com/../../pull/1"
        invalid_thread["comment_pages"][0]["comments"] = []
        invalid_thread["comment_pages"][0]["link"] = None

        unsupported_routes = tracker_routes()
        comments_endpoint = "/repos/synthetic-lab/tracker/issues/7/comments"
        unsupported_routes[(comments_endpoint, 1)] = (
            unsupported_routes[(comments_endpoint, 1)][0],
            ["synthetic-header"],
        )
        unsupported = collector.collect(
            FakeClient(unsupported_routes),
            "synthetic-lab/tracker",
            7,
            max_prs=2,
            request_budget=20,
            hydrator=fake_hydrator,
            timestamp="2030-03-11T00:00:00Z",
        ).manifest["records"][-1]

        pagination_thread = deepcopy(fixture("tracker-thread.json"))
        pagination_thread["comment_pages"][0]["link"] = (
            '<https://api.github.com/repos/synthetic-lab/tracker/issues/7/comments?page=9>; rel="next"'
        )

        def fail_hydration(*args, **kwargs):
            del args, kwargs
            raise RuntimeError("synthetic hydration gap")

        def exhaust_budget(*args, **kwargs):
            del args, kwargs
            raise collector.load_sibling().BudgetExhausted("synthetic budget gap")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_path = root / "manifest.json"
            processing_client = FakeClient(tracker_routes())
            argv = [
                "collect", "--tracker-repo", "synthetic-lab/tracker", "--issue", "7",
                "--max-prs", "2", "--request-budget", "20",
                "--output", os.fspath(root / "corpus.json"),
                "--manifest", os.fspath(manifest_path),
            ]

            def processing_failure(*args, **kwargs):
                del args, kwargs
                processing_client.get_json("/user")
                raise ValueError("secret-token raw processing detail")

            with mock.patch.object(collector, "collect", side_effect=processing_failure):
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(
                        4,
                        collector.main(
                            argv, client_factory=lambda **kwargs: processing_client
                        ),
                    )
            processing = json.loads(manifest_path.read_text(encoding="utf-8"))["records"][-1]

        gap_records = {
            "invalid identity": run_with(invalid_thread),
            "unsupported headers": unsupported,
            "pagination": run_with(pagination_thread),
            "hydration": run_with(hydrator=fail_hydration),
            "budget": run_with(hydrator=exhaust_budget),
            "processing": processing,
        }
        for label, record in gap_records.items():
            with self.subTest(case=label):
                self.assertTrue(record["failed_scopes"])
                self.assertTrue(record["warnings"])
                self.assertTrue(all(
                    any(scope["kind"] in warning for warning in record["warnings"])
                    for scope in record["failed_scopes"]
                ))
                self.assertNotIn("secret-token", " ".join(record["warnings"]))

        complete = run_with()
        self.assertEqual("complete", complete["collection_status"])
        self.assertEqual([], complete["warnings"])

    def test_ac_12_post_review_run_scoped_hydration_caches(self):
        collector = load_collector()
        sibling = collector.load_sibling()
        thread = deepcopy(fixture("tracker-thread.json"))
        thread["issue"]["body"] = "\n".join([
            "https://github.com/synthetic-lab/shared/pull/1",
            "https://github.com/synthetic-lab/shared/pull/2",
        ])
        thread["comment_pages"][0]["comments"] = []
        thread["comment_pages"][0]["link"] = None

        def client_for_run():
            routes = tracker_routes(thread)
            routes[("/repos/synthetic-lab/shared", 1)] = (
                {"full_name": "synthetic-lab/shared", "node_id": "R_SHARED"},
                {},
            )
            return FakeClient(routes)

        license_caches = []

        def observe_hydration(**kwargs):
            license_caches.append(kwargs["license_cache"])
            return hydrated_record(
                kwargs["repository"], kwargs["search_hit"]["number"]
            )

        clients = [client_for_run(), client_for_run()]
        with mock.patch.object(sibling, "hydrate_pull_request", side_effect=observe_hydration):
            for index, client in enumerate(clients, start=1):
                result = collector.collect(
                    client,
                    "synthetic-lab/tracker",
                    7,
                    max_prs=2,
                    request_budget=20,
                    timestamp=f"2030-03-12T00:00:0{index}Z",
                )
                self.assertEqual(0, result.exit_code)

        for client in clients:
            metadata_calls = [
                call for call in client.calls if call[0] == "/repos/synthetic-lab/shared"
            ]
            self.assertEqual(1, len(metadata_calls))
        self.assertIs(license_caches[0], license_caches[1])
        self.assertIs(license_caches[2], license_caches[3])
        self.assertIsNot(license_caches[0], license_caches[2])

    def test_ac_13_post_review_second_temporary_write_cleanup(self):
        collector = load_collector()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus_path = root / "corpus.json"
            manifest_path = root / "manifest.json"
            corpus_path.write_bytes(b"old synthetic corpus\n")
            manifest_path.write_bytes(b"old synthetic manifest\n")
            before_entries = sorted(path.name for path in root.iterdir())
            before_bytes = (corpus_path.read_bytes(), manifest_path.read_bytes())
            original_write = collector._write_temporary
            calls = []

            def fail_second_write(destination, content):
                calls.append(Path(destination))
                if len(calls) == 2:
                    raise OSError("synthetic second staging failure")
                return original_write(destination, content)

            with mock.patch.object(
                collector, "_write_temporary", side_effect=fail_second_write
            ):
                with self.assertRaisesRegex(OSError, "second staging failure"):
                    collector.persist_outputs(
                        corpus_path,
                        {"synthetic": "new corpus"},
                        manifest_path,
                        {"synthetic": "new manifest"},
                    )

            self.assertEqual(before_bytes, (corpus_path.read_bytes(), manifest_path.read_bytes()))
            self.assertEqual(before_entries, sorted(path.name for path in root.iterdir()))

    def test_ac_14_post_review_current_run_usable_records(self):
        collector = load_collector()
        existing_corpus = {
            "schema_version": "1.0.0",
            "generated_by": {"name": collector.SKILL_NAME, "revision": "synthetic"},
            "records": [hydrated_record("synthetic-lab/existing", 99)],
        }

        def fail_all(*args, **kwargs):
            del args, kwargs
            raise RuntimeError("synthetic hydration failure")

        failed = collector.collect(
            FakeClient(tracker_routes()),
            "synthetic-lab/tracker",
            7,
            max_prs=2,
            request_budget=20,
            existing_corpus=existing_corpus,
            hydrator=fail_all,
            timestamp="2030-03-14T00:00:00Z",
        )

        def one_usable(client, repository, number, captured_at):
            del client, captured_at
            if number == 22:
                raise RuntimeError("synthetic second hydration failure")
            return hydrated_record(repository, number)

        partial = collector.collect(
            FakeClient(tracker_routes()),
            "synthetic-lab/tracker",
            7,
            max_prs=2,
            request_budget=20,
            existing_corpus=existing_corpus,
            hydrator=one_usable,
            timestamp="2030-03-14T00:00:01Z",
        )

        self.assertEqual(existing_corpus, failed.corpus)
        self.assertEqual(4, failed.exit_code)
        self.assertEqual("failed", failed.manifest["records"][-1]["collection_status"])
        self.assertEqual(3, partial.exit_code)
        self.assertEqual("partial", partial.manifest["records"][-1]["collection_status"])

    def test_ac_15_post_review_print_revision_help(self):
        def invoke(*arguments):
            return subprocess.run(
                ["/opt/homebrew/bin/python3", os.fspath(SCRIPT), *arguments],
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )

        top_help = invoke("--help")
        self.assertEqual(0, top_help.returncode)
        self.assertIn("--print-revision", top_help.stdout)

        revision = invoke("--print-revision")
        self.assertEqual(0, revision.returncode)
        self.assertRegex(revision.stdout, r"\Asha256:[0-9a-f]{64}\n\Z")
        self.assertEqual("", revision.stderr)

        collect_help = invoke("collect", "--help")
        self.assertEqual(0, collect_help.returncode)
        for option in (
            "--tracker-repo", "--issue", "--max-prs", "--request-budget",
            "--output", "--manifest", "--existing-corpus",
            "--existing-manifest", "--resume-run-id",
        ):
            self.assertIn(option, collect_help.stdout)

        for arguments in (
            ("--print-revision", "collect"),
            ("--print-rev",),
            ("--hel",),
            (),
            ("unknown-command",),
        ):
            with self.subTest(arguments=arguments):
                rejected = invoke(*arguments)
                self.assertEqual(2, rejected.returncode)
                self.assertIn("usage:", rejected.stderr)
                self.assertNotRegex(rejected.stdout, r"sha256:[0-9a-f]{64}")

    def test_ac_16_post_review_shared_api_version(self):
        collector = load_collector()
        sibling = collector.load_sibling()
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(0, source.count('"2026-03-10"'))
        self.assertIn("sibling.API_VERSION", source)

        client = FakeClient(tracker_routes())
        del client.api_version
        client.global_preflight = lambda: {"client_version": "synthetic-no-api-version"}
        result = collector.collect(
            client,
            "synthetic-lab/tracker",
            7,
            max_prs=2,
            request_budget=20,
            hydrator=fake_hydrator,
            timestamp="2030-03-16T00:00:00Z",
        )
        record = result.manifest["records"][-1]
        self.assertEqual(sibling.API_VERSION, record["api_version"])
        self.assertEqual(
            collector.request_fingerprint(
                "synthetic-lab/tracker", 7, 2, 20, sibling.API_VERSION
            ),
            record["request_fingerprint"],
        )

    def test_ac_17_post_review_portable_eval_paths(self):
        assert_portable_eval(self)

    def test_ac_22_contract_stdlib_synthetic_packaging(self):
        root = Path(__file__).resolve().parents[4]
        test_source = Path(__file__).read_text(encoding="utf-8")
        syntax = ast.parse(test_source)
        import_roots = set()
        for node in ast.walk(syntax):
            if isinstance(node, ast.Import):
                import_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                import_roots.add(node.module.split(".", 1)[0])
        self.assertTrue(import_roots <= set(sys.stdlib_module_names), import_roots)
        self.assertTrue(import_roots.isdisjoint({"requests", "urllib", "http", "socket"}))
        public_payload = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                SKILL_DIR / "SKILL.md",
                SKILL_DIR / "references" / "collection-contract.md",
                *sorted(FIXTURES.glob("*.json")),
            )
        )
        self.assertNotIn("gh" + "p_", public_payload)
        self.assertNotIn("BEGIN " + "PRIVATE KEY", public_payload)
        self.assertTrue(all(
            "synthetic" in path.read_text(encoding="utf-8").lower()
            for path in FIXTURES.glob("*.json")
        ))

        focused = {
            f"test_ac_{number:02d}_post_review_{suffix}"
            for number, suffix in (
                (1, "remote_repository_validation"),
                (2, "terminal_link_without_next"),
                (3, "unsupported_header_shape"),
                (4, "korean_label_boundary"),
                (5, "examples_plural"),
                (6, "notices_plural"),
                (7, "non_pr_url_label"),
                (8, "processing_handler_append_only"),
                (9, "failed_record_field_parity"),
                (10, "resume_corpus_reconciliation"),
                (11, "manifest_warnings"),
                (12, "run_scoped_hydration_caches"),
                (13, "second_temporary_write_cleanup"),
                (14, "current_run_usable_records"),
                (15, "print_revision_help"),
                (16, "shared_api_version"),
                (17, "portable_eval_paths"),
            )
        }
        self.assertTrue(focused <= set(dir(CollectionTests)))

        allowed_exact = {
            "SKILL.md", "agents/openai.yaml", "evals/behavioral-eval.md",
            "references/collection-contract.md", "references/github-rest-contract.md",
            "scripts/collect_curated_contribution_prs.py",
            "tests/test_collect_curated_contribution_prs.py",
            *{
                "tests/fixtures/" + path.name
                for path in FIXTURES.glob("*.json")
            },
        }
        packaged = packaged_files()
        self.assertEqual(set(), packaged - allowed_exact)

        plan = (
            root / "docs/development/2026-09-15-80-post-review-hardening/plan.md"
        ).read_text(encoding="utf-8")
        python_commands = re.findall(r"`([^`\n]*/opt/homebrew/bin/python3[^`\n]*)`", plan)
        self.assertTrue(python_commands)
        self.assertTrue(all(
            "PYTHONDONTWRITEBYTECODE=1" in command for command in python_commands
        ))

        assert_portable_eval(self)

    def test_ac_04_collection_link_page_validation(self):
        collector = load_collector()
        client = FakeClient(tracker_routes())
        result = collector.collect_issue_thread(client, "synthetic-lab/tracker", 7)
        self.assertEqual([7101, 7102, 7103], [item["id"] for item in result["comments"]])
        self.assertEqual([], result["failed_scopes"])
        self.assertEqual(2, len(result["pages"]))
        first = result["pages"][0]
        self.assertIn("per_page=100&page=2", first["next_url"])
        self.assertEqual(2, first["parsed_next_page"])
        self.assertEqual("valid", first["link_validation"])
        comment_calls = [call for call in client.calls if call[0].endswith("/comments")]
        self.assertEqual(
            [
                ("/repos/synthetic-lab/tracker/issues/7/comments", {"page": 1}),
                ("/repos/synthetic-lab/tracker/issues/7/comments", {"page": 2}),
            ],
            comment_calls,
        )
        self.assertTrue(all("per_page" not in params for _, params in comment_calls))

        failures = fixture("tracker-thread-failures.json")
        for label in ("malformed", "cursor", "before", "page_mismatch", "foreign_host"):
            bad_client = FakeClient(tracker_routes(link_override=failures["links"][label]))
            bad = collector.collect_issue_thread(bad_client, "synthetic-lab/tracker", 7)
            with self.subTest(label=label):
                self.assertEqual("invalid", bad["pages"][0]["link_validation"])
                self.assertEqual(1, len([call for call in bad_client.calls if call[0].endswith("/comments")]))
                self.assertTrue(bad["failed_scopes"])

        numeric = collector.validate_next_link(
            '<https://api.github.com/repositories/7001/issues/7/comments?page=2&per_page=100>; rel="next"',
            "/repos/synthetic-lab/tracker/issues/7/comments",
            1,
        )
        self.assertEqual("invalid", numeric["link_validation"])
        self.assertEqual("next URL comments endpoint mismatch", numeric["link_failure_reason"])

    def test_ac_06_collection_cap_counts(self):
        collector = load_collector()
        issue = deepcopy(fixture("tracker-thread.json")["issue"])
        issue["body"] = "\n".join(
            f"Synthetic submission: https://github.com/synthetic-lab/project-{number}/pull/{number}"
            for number in (11, 22, 33, 44)
        )
        comments = [{
            "id": 7999,
            "node_id": "IC_SYNTHETIC_DUPLICATE",
            "url": "https://api.github.com/repos/synthetic-lab/tracker/issues/comments/7999",
            "html_url": "https://github.com/synthetic-lab/tracker/issues/7#issuecomment-7999",
            "user": {"login": "synthetic-user"},
            "author_association": "NONE",
            "created_at": "2030-01-06T00:00:00Z",
            "updated_at": "2030-01-06T00:00:00Z",
            "body": "Synthetic duplicate: https://github.com/synthetic-lab/project-11/pull/11",
        }]
        references = collector.extract_references(issue, comments, run_id="run-synthetic")
        inventory = collector.select_references(references, max_prs=2)
        self.assertEqual(4, inventory["matched_count"])
        self.assertEqual(2, inventory["selected_count"])
        self.assertEqual(2, inventory["excluded_by_cap"])
        self.assertEqual(
            [("synthetic-lab/project-11", 11), ("synthetic-lab/project-22", 22)],
            [item["identity"] for item in inventory["selected"]],
        )
        self.assertEqual(2, len(inventory["selected"][0]["references"]))

        classification = fixture("reference-classification.json")
        classified = collector.select_references(
            collector.extract_references(
                classification["issue"], [], run_id="run-classification"
            ),
            max_prs=10,
        )
        self.assertEqual(
            [tuple(item) for item in classification["expected_selected"]],
            [item["identity"] for item in classified["selected"]],
        )
        self.assertEqual(
            [tuple(item) for item in classification["expected_excluded"]],
            [item["identity"] for item in classified["reference_exclusions"]],
        )
        for exclusion in classified["reference_exclusions"]:
            self.assertEqual("excluded-example-or-notice", exclusion["classification"])
            basis = exclusion["classification_basis"]
            self.assertIn(basis["matched_keyword"], {"example", "공지"})
            self.assertIn(basis["label_scope"], {"same-line-prefix", "previous-line"})
            self.assertNotIn(exclusion["url"].lower(), basis["evaluated_label"].lower())

        classification_thread = {
            "issue": classification["issue"],
            "comment_pages": [
                {"page": 1, "link": None, "comments": []},
                {"page": 2, "link": None, "comments": []},
            ],
        }
        classified_run = collector.collect(
            FakeClient(tracker_routes(classification_thread)),
            "synthetic-lab/tracker",
            7,
            max_prs=10,
            request_budget=20,
            hydrator=fake_hydrator,
            skill_revision="sha256:" + "c" * 64,
            timestamp="2030-02-10T00:00:00Z",
        )
        manifest_exclusions = classified_run.manifest["records"][-1]["reference_exclusions"]
        self.assertEqual(2, len(manifest_exclusions))
        self.assertTrue(all("classification_basis" in item for item in manifest_exclusions))

    def test_collection_neighbor_url_is_not_a_classification_label(self):
        collector = load_collector()
        classification = fixture("reference-classification.json")
        issue = deepcopy(classification["issue"])
        neighbor_case = classification["neighbor_url_case"]
        issue["body"] = neighbor_case["body"]

        references = collector.extract_references(issue, [], run_id="run-neighbor-url")
        inventory = collector.select_references(references, max_prs=10)

        self.assertEqual(
            [tuple(item) for item in neighbor_case["expected_selected"]],
            [item["identity"] for item in inventory["selected"]],
        )
        self.assertEqual(
            [tuple(item) for item in neighbor_case["expected_excluded"]],
            [item["identity"] for item in inventory["reference_exclusions"]],
        )

    def test_ac_07_collection_shared_budget(self):
        collector = load_collector()
        thread = deepcopy(fixture("tracker-thread.json"))
        thread["issue"]["body"] += (
            "\nSynthetic submission: "
            "https://github.com/synthetic-lab/third-project/pull/33"
        )
        client = FakeClient(
            tracker_routes(thread),
            limit=5,
            budget_error_type=collector.load_sibling().BudgetExhausted,
        )
        hydrate_calls = []

        def budget_hydrator(fake_client, repository, number, captured_at):
            hydrate_calls.append((repository, number))
            if len(hydrate_calls) == 2:
                fake_client.get_json("/synthetic/hydration")
            return hydrated_record(repository, number)

        run = collector.collect(
            client,
            "synthetic-lab/tracker",
            7,
            max_prs=3,
            request_budget=5,
            hydrator=budget_hydrator,
            timestamp="2030-01-10T00:00:00Z",
        )
        self.assertEqual(3, run.exit_code)
        self.assertEqual(5, run.manifest["records"][-1]["request_count"])
        self.assertLessEqual(client.budget.consumed, client.budget.limit)
        self.assertTrue(any(scope["kind"] == "budget" for scope in run.manifest["records"][-1]["failed_scopes"]))
        self.assertEqual(
            ["collected", "failed", "not-attempted"],
            [outcome["status"] for outcome in run.manifest["records"][-1]["hydration_outcomes"]],
        )
        self.assertEqual(
            {"repository": "synthetic-lab/gadget", "number": 22, "status": "not-attempted"},
            run.manifest["records"][-1]["hydration_outcomes"][2],
        )

        bad_link = fixture("tracker-thread-failures.json")["links"]["page_mismatch"]
        bad_client = FakeClient(tracker_routes(link_override=bad_link), limit=20)
        collector.collect(
            bad_client,
            "synthetic-lab/tracker",
            7,
            max_prs=1,
            request_budget=20,
            hydrator=fake_hydrator,
            timestamp="2030-01-10T00:00:00Z",
        )
        self.assertEqual(1, len([call for call in bad_client.calls if call[0].endswith("/comments")]))

    def test_collection_api_failure_budget_text_does_not_exhaust_budget(self):
        collector = load_collector()
        sibling = collector.load_sibling()
        attempted = []

        def hydrator(client, repository, number, captured_at):
            del client, captured_at
            attempted.append((repository, number))
            if len(attempted) == 1:
                raise sibling.ApiFailure(
                    "synthetic remote response says budget exhausted",
                    status=500,
                    endpoint="/synthetic/hydration",
                )
            return hydrated_record(repository, number)

        run = collector.collect(
            FakeClient(tracker_routes()),
            "synthetic-lab/tracker",
            7,
            max_prs=2,
            request_budget=20,
            hydrator=hydrator,
            timestamp="2030-01-10T00:00:00Z",
        )

        self.assertEqual(
            [("synthetic-lab/widget", 11), ("synthetic-lab/gadget", 22)],
            attempted,
        )
        self.assertEqual(
            ["failed", "collected"],
            [outcome["status"] for outcome in run.manifest["records"][-1]["hydration_outcomes"]],
        )
        self.assertEqual(
            "hydration",
            run.manifest["records"][-1]["failed_scopes"][-1]["kind"],
        )

    def test_ac_09_collection_role_separation(self):
        collector = load_collector()
        comment = fixture("tracker-thread.json")["comment_pages"][1]["comments"][0]
        observation = collector.comment_observation(comment, "run-synthetic")
        self.assertEqual("MEMBER", observation["tracker_author_association"])
        for role in ("upstream-maintainer", "contributor", "unknown"):
            record = hydrated_record("synthetic-lab/widget", 11, role)
            attached = collector.attach_tracker_source(
                record,
                fixture("tracker-thread.json")["issue"],
                [observation],
                skill_revision="sha256:" + "a" * 64,
            )
            with self.subTest(role=role):
                self.assertEqual(role, attached["author"]["normalized_role"])
                self.assertEqual("MEMBER", attached["sources"][0]["observations"][0]["tracker_author_association"])

    def test_ac_13_collection_observation_provenance(self):
        collector = load_collector()
        thread = fixture("tracker-thread.json")
        original = thread["comment_pages"][0]["comments"][0]
        edited = fixture("tracker-thread-edited.json")["comment"]
        first = collector.comment_observation(original, "run-one")
        second = collector.comment_observation(edited, "run-two")
        required = {
            "run_id", "origin_kind", "comment_id", "comment_node_id",
            "comment_url", "comment_html_url", "commenter_login", "tracker_author_association",
            "created_at", "updated_at", "body_sha256",
        }
        self.assertEqual(required, set(first))
        self.assertNotEqual(first["body_sha256"], second["body_sha256"])
        issue = collector.issue_observation(thread["issue"], "run-one")
        self.assertEqual("issue-body", issue["origin_kind"])
        self.assertEqual("I_SYNTHETIC_TRACKER_7", issue["issue_node_id"])
        self.assertNotIn("comment_database_id", issue)

    def test_ac_21_collection_resume_append(self):
        collector = load_collector()
        fingerprint = collector.request_fingerprint(
            "synthetic-lab/tracker", 7, 2, 20, "2026-03-10"
        )
        complete_run = {
            "run_id": "run-synthetic-complete",
            "request_fingerprint": fingerprint,
            "collection_method": "tracker-issue-comments",
            "tracker": {"repository": "synthetic-lab/tracker", "issue_number": 7},
            "collection_status": "complete",
            "request_count": 8,
            "completed_at": "2030-01-09T00:00:00Z",
        }
        existing_manifest = {
            "schema_version": "2.0.0",
            "generated_by": {"name": "collecting-curated-contribution-prs", "revision": "sha256:" + "a" * 64},
            "records": [complete_run],
        }
        existing_corpus = {
            "schema_version": "1.0.0",
            "generated_by": {"name": "collecting-curated-contribution-prs", "revision": "sha256:" + "a" * 64},
            "records": [hydrated_record("synthetic-lab/widget", 11)],
        }
        client = FakeClient({}, limit=20)
        resumed = collector.collect(
            client,
            "synthetic-lab/tracker",
            7,
            max_prs=2,
            request_budget=20,
            existing_corpus=existing_corpus,
            existing_manifest=existing_manifest,
            resume_run_id="run-synthetic-complete",
            hydrator=fake_hydrator,
            timestamp="2030-01-10T00:00:00Z",
        )
        self.assertEqual(0, resumed.exit_code)
        self.assertEqual([], client.calls)
        self.assertEqual(1, len(resumed.manifest["records"]))
        self.assertEqual("run-synthetic-complete", resumed.manifest["records"][0]["run_id"])
        self.assertEqual(8, resumed.manifest["records"][0]["request_count"])

        append_client = FakeClient(tracker_routes(), limit=20)
        appended = collector.collect(
            append_client,
            "synthetic-lab/tracker",
            7,
            max_prs=2,
            request_budget=20,
            existing_corpus=existing_corpus,
            existing_manifest=existing_manifest,
            hydrator=fake_hydrator,
            timestamp="2030-01-10T00:00:00Z",
        )
        self.assertEqual(2, len(appended.manifest["records"]))
        self.assertEqual(complete_run, appended.manifest["records"][0])

    def test_ac_22_collection_fingerprint_mismatch(self):
        collector = load_collector()
        old_fingerprint = collector.request_fingerprint(
            "synthetic-lab/tracker", 7, 2, 20, "2026-03-10"
        )
        manifest = {
            "schema_version": "2.0.0",
            "generated_by": {"name": "collecting-curated-contribution-prs", "revision": "sha256:" + "a" * 64},
            "records": [{
                "run_id": "run-synthetic",
                "request_fingerprint": old_fingerprint,
                "collection_method": "tracker-issue-comments",
                "tracker": {"repository": "synthetic-lab/tracker", "issue_number": 7},
                "collection_status": "partial",
                "request_count": 4,
            }],
        }
        corpus = {"schema_version": "1.0.0", "generated_by": {"name": "synthetic", "revision": "synthetic"}, "records": []}
        client = FakeClient(tracker_routes(), limit=20)
        with self.assertRaises(ValueError):
            collector.collect(
                client,
                "synthetic-lab/tracker",
                7,
                max_prs=3,
                request_budget=20,
                existing_corpus=corpus,
                existing_manifest=manifest,
                resume_run_id="run-synthetic",
                hydrator=fake_hydrator,
                timestamp="2030-01-10T00:00:00Z",
            )
        self.assertEqual([], client.calls)

    def test_ac_23_collection_partial_gaps(self):
        collector = load_collector()
        failure_fixture = fixture("tracker-thread-failures.json")
        for label in ("malformed", "cursor", "page_mismatch"):
            client = FakeClient(tracker_routes(link_override=failure_fixture["links"][label]))
            run = collector.collect(
                client,
                "synthetic-lab/tracker",
                7,
                max_prs=1,
                request_budget=20,
                hydrator=fake_hydrator,
                timestamp="2030-01-10T00:00:00Z",
            )
            with self.subTest(label=label):
                self.assertEqual(3, run.exit_code)
                self.assertEqual("partial", run.manifest["records"][-1]["collection_status"])
                self.assertTrue(run.manifest["records"][-1]["failed_scopes"])

        duplicate_comments = deepcopy(fixture("tracker-thread.json")["comment_pages"][0]["comments"])
        duplicate_comments.append(deepcopy(duplicate_comments[0]))
        duplicate_client = FakeClient(tracker_routes(comments_override=duplicate_comments))
        duplicate = collector.collect(
            duplicate_client,
            "synthetic-lab/tracker",
            7,
            max_prs=1,
            request_budget=20,
            hydrator=fake_hydrator,
            timestamp="2030-01-10T00:00:00Z",
        )
        self.assertEqual(3, duplicate.exit_code)
        self.assertTrue(any(scope["kind"] == "comment-order" for scope in duplicate.manifest["records"][-1]["failed_scopes"]))

        hydration_calls = []

        def failing_hydrator(client, repository, number, captured_at):
            del client, captured_at
            hydration_calls.append((repository, number))
            if len(hydration_calls) == 2:
                raise RuntimeError("synthetic inaccessible pull request")
            return hydrated_record(repository, number)

        hydration_client = FakeClient(tracker_routes())
        hydration = collector.collect(
            hydration_client,
            "synthetic-lab/tracker",
            7,
            max_prs=2,
            request_budget=20,
            hydrator=failing_hydrator,
            timestamp="2030-01-10T00:00:00Z",
        )
        self.assertEqual(3, hydration.exit_code)
        self.assertTrue(any(scope["kind"] == "hydration" for scope in hydration.manifest["records"][-1]["failed_scopes"]))

    def test_ac_24_collection_exit_matrix(self):
        collector = load_collector()
        calls = []
        stderr = io.StringIO()
        invalid = [
            "collect", "--tracker-repo", "invalid", "--issue", "7",
            "--max-prs", "1", "--request-budget", "20",
            "--output", "corpus.json", "--manifest", "manifest.json",
        ]
        with contextlib.redirect_stderr(stderr):
            code = collector.main(invalid, client_factory=lambda **kwargs: calls.append(kwargs))
        self.assertEqual(2, code)
        self.assertEqual([], calls)
        self.assertNotIn("Traceback", stderr.getvalue())

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus_path = root / "corpus.json"
            manifest_path = root / "manifest.json"
            corpus_path.write_text('{"schema_version":"synthetic-invalid","records":[]}\n', encoding="utf-8")
            manifest_path.write_text(json.dumps({
                "schema_version": "2.0.0",
                "generated_by": {"name": "collecting-curated-contribution-prs", "revision": "synthetic"},
                "records": [],
            }) + "\n", encoding="utf-8")
            original_corpus = corpus_path.read_bytes()
            original_manifest = manifest_path.read_bytes()
            schema_client = FakeClient(tracker_routes())
            schema_argv = [
                "collect", "--tracker-repo", "synthetic-lab/tracker", "--issue", "7",
                "--max-prs", "1", "--request-budget", "20",
                "--output", os.fspath(corpus_path), "--manifest", os.fspath(manifest_path),
                "--existing-corpus", os.fspath(corpus_path),
                "--existing-manifest", os.fspath(manifest_path),
            ]
            with contextlib.redirect_stderr(io.StringIO()):
                schema_code = collector.main(schema_argv, client_factory=lambda **kwargs: schema_client)
            self.assertEqual(2, schema_code)
            self.assertEqual([], schema_client.calls)
            self.assertEqual(original_corpus, corpus_path.read_bytes())
            self.assertEqual(original_manifest, manifest_path.read_bytes())

        failed_client = FakeClient({}, preflight_error=RuntimeError("synthetic preflight failed"))
        failed = collector.collect(
            failed_client,
            "synthetic-lab/tracker",
            7,
            max_prs=1,
            request_budget=20,
            hydrator=fake_hydrator,
            timestamp="2030-01-10T00:00:00Z",
        )
        self.assertEqual(4, failed.exit_code)
        self.assertEqual("failed", failed.manifest["records"][-1]["collection_status"])

        complete_client = FakeClient(tracker_routes())
        complete = collector.collect(
            complete_client,
            "synthetic-lab/tracker",
            7,
            max_prs=2,
            request_budget=20,
            hydrator=fake_hydrator,
            timestamp="2030-01-10T00:00:00Z",
        )
        self.assertEqual(0, complete.exit_code)
        self.assertEqual("complete", complete.manifest["records"][-1]["collection_status"])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus_path = root / "corpus.json"
            manifest_path = root / "manifest.json"
            processing_client = FakeClient(tracker_routes())
            processing_argv = [
                "collect", "--tracker-repo", "synthetic-lab/tracker", "--issue", "7",
                "--max-prs", "1", "--request-budget", "20",
                "--output", os.fspath(corpus_path), "--manifest", os.fspath(manifest_path),
            ]

            def post_request_failure(*args, **kwargs):
                del args, kwargs
                processing_client.get_json("/user")
                raise ValueError("synthetic post-request processing failure")

            with mock.patch.object(collector, "collect", side_effect=post_request_failure):
                with contextlib.redirect_stderr(io.StringIO()):
                    processing_code = collector.main(
                        processing_argv,
                        client_factory=lambda **kwargs: processing_client,
                    )
            self.assertEqual(4, processing_code)
            processing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual("failed", processing_manifest["records"][-1]["collection_status"])
            self.assertEqual("processing", processing_manifest["records"][-1]["failed_scopes"][0]["kind"])

    def test_ac_25_collection_atomic_output(self):
        collector = load_collector()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus_path = root / "corpus.json"
            manifest_path = root / "manifest.json"
            corpus_path.write_bytes(b"old synthetic corpus\n")
            manifest_path.write_bytes(b"old synthetic manifest\n")
            before = sorted(path.name for path in root.iterdir())

            def fail_replace(source, destination):
                del source, destination
                raise OSError("synthetic replace failure")

            with self.assertRaises(OSError):
                collector.persist_outputs(
                    corpus_path,
                    {"synthetic": "corpus"},
                    manifest_path,
                    {"synthetic": "manifest"},
                    replacer=fail_replace,
                )
            self.assertEqual(b"old synthetic corpus\n", corpus_path.read_bytes())
            self.assertEqual(b"old synthetic manifest\n", manifest_path.read_bytes())
            self.assertEqual(before, sorted(path.name for path in root.iterdir()))

            replace_calls = []

            def replace_then_fail_second(source, destination):
                os.replace(source, destination)
                replace_calls.append(os.fspath(destination))
                if len(replace_calls) == 2:
                    raise OSError("synthetic failure after second replacement")

            with self.assertRaises(OSError):
                collector.persist_outputs(
                    corpus_path,
                    {"synthetic": "new corpus"},
                    manifest_path,
                    {"synthetic": "new manifest"},
                    replacer=replace_then_fail_second,
                )
            self.assertEqual(b"old synthetic corpus\n", corpus_path.read_bytes())
            self.assertEqual(b"old synthetic manifest\n", manifest_path.read_bytes())
            self.assertEqual(before, sorted(path.name for path in root.iterdir()))

            with self.assertRaises(TypeError):
                collector.persist_outputs(
                    corpus_path,
                    {"synthetic": object()},
                    manifest_path,
                    {"synthetic": "manifest"},
                )
            self.assertEqual(b"old synthetic corpus\n", corpus_path.read_bytes())
            self.assertEqual(b"old synthetic manifest\n", manifest_path.read_bytes())
            self.assertEqual(before, sorted(path.name for path in root.iterdir()))

            collector.persist_outputs(
                corpus_path,
                {"synthetic": "corpus"},
                manifest_path,
                {"synthetic": "manifest"},
            )
            self.assertTrue(corpus_path.read_bytes().endswith(b"\n"))
            self.assertTrue(manifest_path.read_bytes().endswith(b"\n"))
            self.assertEqual({"synthetic": "corpus"}, json.loads(corpus_path.read_text(encoding="utf-8")))

    def test_ac_39_collection_rejects_foreign_manifest(self):
        collector = load_collector()
        base_run = {
            "run_id": "run-synthetic",
            "request_fingerprint": "sha256:" + "b" * 64,
            "collection_method": "tracker-issue-comments",
            "tracker": {"repository": "synthetic-lab/tracker", "issue_number": 7},
            "collection_status": "complete",
            "request_count": 8,
        }
        valid = {
            "schema_version": "2.0.0",
            "generated_by": {"name": "collecting-curated-contribution-prs", "revision": "sha256:" + "a" * 64},
            "records": [base_run],
        }
        collector.validate_existing_manifest(valid, "synthetic-lab/tracker", 7)

        variants = []
        date_range = deepcopy(valid)
        date_range["generated_by"]["name"] = "collecting-recent-closed-prs"
        variants.append(date_range)
        method = deepcopy(valid)
        method["records"][0]["collection_method"] = "synthetic-other-method"
        variants.append(method)
        repository = deepcopy(valid)
        repository["records"][0]["tracker"]["repository"] = "synthetic-lab/other-tracker"
        variants.append(repository)
        issue = deepcopy(valid)
        issue["records"][0]["tracker"]["issue_number"] = 8
        variants.append(issue)

        for index, manifest in enumerate(variants):
            client = FakeClient(tracker_routes())
            with tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                corpus_path = root / "corpus.json"
                manifest_path = root / "manifest.json"
                corpus_path.write_text(json.dumps({"schema_version": "1.0.0", "generated_by": {"name": "synthetic", "revision": "synthetic"}, "records": []}) + "\n", encoding="utf-8")
                manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
                before_corpus = corpus_path.read_bytes()
                before_manifest = manifest_path.read_bytes()
                argv = [
                    "collect", "--tracker-repo", "synthetic-lab/tracker", "--issue", "7",
                    "--max-prs", "2", "--request-budget", "20",
                    "--output", os.fspath(corpus_path), "--manifest", os.fspath(manifest_path),
                    "--existing-corpus", os.fspath(corpus_path),
                    "--existing-manifest", os.fspath(manifest_path),
                ]
                with contextlib.redirect_stderr(io.StringIO()):
                    code = collector.main(argv, client_factory=lambda **kwargs: client)
                with self.subTest(index=index):
                    self.assertEqual(2, code)
                    self.assertEqual([], client.calls)
                    self.assertEqual(before_corpus, corpus_path.read_bytes())
                    self.assertEqual(before_manifest, manifest_path.read_bytes())


class MergeTests(unittest.TestCase):
    @staticmethod
    def _recent_corpus(record):
        recent = deepcopy(record)
        recent["pr_id"] = "PR-041"
        recent["sources"] = [{
            "source_key": "recent-closed",
            "kind": "search-api",
            "observations": [{
                "run_id": "recent-run-synthetic",
                "updated_at": recent["pull_request"]["updated_at"],
                "body_sha256": "1" * 64,
                "pull_request_url": recent["pull_request"]["url"],
            }],
        }]
        recent["synthetic_unknown"] = {"preserve": [1, {"typed": True}]}
        return {
            "schema_version": "1.0.0",
            "generated_by": {
                "name": "collecting-recent-closed-prs",
                "revision": "sha256:" + "1" * 64,
            },
            "records": [recent],
            "synthetic_envelope_unknown": {"preserve": [False, 7]},
        }

    @staticmethod
    def _collect(collector, *, thread=None, existing_corpus=None, existing_manifest=None,
                 timestamp="2030-01-10T00:00:00Z", hydrator=fake_hydrator):
        return collector.collect(
            FakeClient(tracker_routes(thread=thread)),
            "synthetic-lab/tracker",
            7,
            max_prs=1,
            request_budget=20,
            existing_corpus=existing_corpus,
            existing_manifest=existing_manifest,
            hydrator=hydrator,
            skill_revision="sha256:" + "c" * 64,
            timestamp=timestamp,
        )

    def test_ac_14_merge_global_identity(self):
        collector = load_collector()
        recent = self._recent_corpus(hydrated_record("synthetic-lab/widget", 11))
        merged = self._collect(collector, existing_corpus=recent).corpus
        self.assertEqual(1, len(merged["records"]))
        self.assertEqual("PR-041", merged["records"][0]["pr_id"])
        self.assertEqual(
            ["recent-closed", collector._tracker_source_key("I_SYNTHETIC_TRACKER_7")],
            [source["source_key"] for source in merged["records"][0]["sources"]],
        )

        curated = self._collect(collector).corpus
        sibling = collector.load_sibling()
        incoming_recent = self._recent_corpus(hydrated_record("synthetic-lab/widget", 11))
        reverse = sibling.merge_corpus(curated, incoming_recent)
        self.assertEqual(1, len(reverse["records"]))
        self.assertEqual(
            [collector._tracker_source_key("I_SYNTHETIC_TRACKER_7"), "recent-closed"],
            [source["source_key"] for source in reverse["records"][0]["sources"]],
        )

    def test_ac_16_merge_explicit_only_sources(self):
        collector = load_collector()
        corpus = self._collect(collector).corpus
        self.assertEqual(1, len(corpus["records"]))
        source_keys = [source["source_key"] for source in corpus["records"][0]["sources"]]
        self.assertEqual([collector._tracker_source_key("I_SYNTHETIC_TRACKER_7")], source_keys)
        self.assertNotIn(b'"source_key": "recent-closed"', collector._json_bytes(corpus))

    def test_ac_17_merge_recollection_idempotency(self):
        collector = load_collector()
        recent = self._recent_corpus(hydrated_record("synthetic-lab/widget", 11))
        first = self._collect(
            collector,
            existing_corpus=recent,
            timestamp="2030-01-10T00:00:00Z",
        )
        self.assertEqual(fixture("initial-corpus.json"), first.corpus)
        first_record = first.corpus["records"][0]
        source_key = collector._tracker_source_key("I_SYNTHETIC_TRACKER_7")
        first_source = next(source for source in first_record["sources"] if source["source_key"] == source_key)
        first_observations = deepcopy(first_source["observations"])
        first_states = deepcopy(first_record["state_history"])

        unchanged = self._collect(
            collector,
            existing_corpus=first.corpus,
            existing_manifest=first.manifest,
            timestamp="2030-01-11T00:00:00Z",
        )
        unchanged_record = unchanged.corpus["records"][0]
        unchanged_source = next(
            source for source in unchanged_record["sources"] if source["source_key"] == source_key
        )
        with self.subTest("unchanged source observations do not grow"):
            self.assertEqual(
                0,
                len(unchanged_source["observations"]) - len(first_observations),
            )
        with self.subTest("unchanged state history does not grow"):
            self.assertEqual(
                0,
                len(unchanged_record["state_history"]) - len(first_states),
            )

        edited_thread = deepcopy(fixture("tracker-thread.json"))
        edited_thread["comment_pages"][0]["comments"][0] = fixture(
            "tracker-thread-edited.json"
        )["comment"]

        def edited_hydrator(client, repository, number, captured_at):
            del client, captured_at
            record = hydrated_record(repository, number)
            record["pull_request"]["normalized_state"] = "merged"
            record["pull_request"]["closed_at"] = "2030-01-12T00:00:00Z"
            record["pull_request"]["merged_at"] = "2030-01-12T00:00:00Z"
            record["pull_request"]["updated_at"] = "2030-01-12T00:00:00Z"
            record["state_history"] = [{
                "state": "merged",
                "observed_at": "2030-01-12T00:00:00Z",
                "authority": "GitHub pull request",
                "evidence_url": record["pull_request"]["url"],
            }]
            return record

        edited = self._collect(
            collector,
            thread=edited_thread,
            existing_corpus=unchanged.corpus,
            existing_manifest=unchanged.manifest,
            timestamp="2030-01-12T00:00:00Z",
            hydrator=edited_hydrator,
        )
        edited_record = edited.corpus["records"][0]
        edited_source = next(source for source in edited_record["sources"] if source["source_key"] == source_key)
        self.assertEqual(first_observations, edited_source["observations"][:len(first_observations)])
        self.assertEqual(len(first_observations) + 1, len(edited_source["observations"]))
        self.assertEqual(first_states, edited_record["state_history"][:len(first_states)])
        self.assertEqual(len(first_states) + 1, len(edited_record["state_history"]))
        self.assertEqual("merged", edited_record["state_history"][-1]["state"])
        self.assertEqual(fixture("recollected-corpus.json"), edited.corpus)

    def test_merge_unresolved_recollection_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            first = run_partial_hydration_end_to_end(temporary)
            first_record = first.corpus["records"][0]
            source_key = first.collector._tracker_source_key(
                "I_SYNTHETIC_PARTIAL_HYDRATION"
            )
            first_source = next(
                source for source in first_record["sources"]
                if source["source_key"] == source_key
            )

            unchanged = run_partial_hydration_end_to_end(
                temporary,
                existing=True,
                timestamp="2030-03-11T00:00:00Z",
            )
            unchanged_record = unchanged.corpus["records"][0]
            unchanged_source = next(
                source for source in unchanged_record["sources"]
                if source["source_key"] == source_key
            )

            with self.subTest("unchanged unresolved state history does not grow"):
                self.assertEqual(
                    0,
                    len(unchanged_record["state_history"])
                    - len(first_record["state_history"]),
                )
            with self.subTest("unchanged unresolved tracker observations do not grow"):
                self.assertEqual(
                    0,
                    len(unchanged_source["observations"])
                    - len(first_source["observations"]),
                )

            accessible_thread = fixture("partial-hydration-thread.json")
            accessible_routes = tracker_routes()
            accessible_routes[("/repos/synthetic-lab/tracker/issues/7", 1)] = (
                accessible_thread["issue"],
                {},
            )
            accessible_routes[("/repos/synthetic-lab/tracker/issues/7/comments", 1)] = (
                [],
                {},
            )

            def accessible_hydrator(client, repository, number, captured_at):
                del client
                record = hydrated_record(repository, number)
                record["repository"]["node_id"] = "R_SYNTHETIC_SAMPLE_LIB"
                record["pull_request"]["updated_at"] = captured_at
                record["state_history"][0]["observed_at"] = captured_at
                return record

            accessible = unchanged.collector.collect(
                FakeClient(accessible_routes),
                "synthetic-lab/tracker",
                7,
                max_prs=1,
                request_budget=60,
                existing_corpus=unchanged.corpus,
                existing_manifest=unchanged.manifest,
                hydrator=accessible_hydrator,
                skill_revision="sha256:" + "c" * 64,
                timestamp="2030-03-12T00:00:00Z",
            )
            accessible_record = accessible.corpus["records"][0]
            self.assertEqual("resolved", accessible_record["identity_status"])
            self.assertEqual(
                first_record["state_history"],
                accessible_record["state_history"][:len(first_record["state_history"])],
            )
            self.assertEqual(
                len(first_record["state_history"]) + 1,
                len(accessible_record["state_history"]),
            )
            self.assertEqual("open", accessible_record["state_history"][-1]["state"])

    def test_ac_19_merge_projection_history(self):
        collector = load_collector()
        current_record = hydrated_record("synthetic-lab/widget", 11)
        current_record["pull_request"]["title"] = "Synthetic authoritative latest title"
        current_record["pull_request"]["updated_at"] = "2030-01-20T00:00:00Z"
        current_record["state_history"] = [{
            "state": "open",
            "observed_at": "2030-01-20T00:00:00Z",
            "authority": "GitHub pull request",
            "evidence_url": current_record["pull_request"]["url"],
        }]
        existing = self._recent_corpus(current_record)
        existing_record = deepcopy(existing["records"][0])

        older = self._collect(
            collector,
            existing_corpus=existing,
            timestamp="2030-01-21T00:00:00Z",
        )
        record = older.corpus["records"][0]
        self.assertEqual("Synthetic authoritative latest title", record["pull_request"]["title"])
        self.assertEqual(existing_record["state_history"], record["state_history"][:1])
        self.assertEqual(existing_record["synthetic_unknown"], record["synthetic_unknown"])

        def inaccessible(client, repository, number, captured_at):
            del client, repository, number, captured_at
            raise RuntimeError("synthetic inaccessible pull request")

        failed = self._collect(
            collector,
            existing_corpus=older.corpus,
            timestamp="2030-01-22T00:00:00Z",
            hydrator=inaccessible,
        )
        self.assertEqual(4, failed.exit_code)
        self.assertEqual(older.corpus, failed.corpus)
        self.assertFalse(any(
            state.get("state") in {"closed-unmerged", "merged"}
            for state in failed.corpus["records"][0]["state_history"]
        ))

    def test_ac_38_merge_preserves_generated_by(self):
        collector = load_collector()
        existing = self._recent_corpus(hydrated_record("synthetic-lab/widget", 11))
        generated_by = deepcopy(existing["generated_by"])
        sibling = collector.load_sibling()
        with mock.patch.object(sibling, "merge_corpus", wraps=sibling.merge_corpus) as merge:
            merged = self._collect(collector, existing_corpus=existing).corpus
        for call in merge.call_args_list:
            incoming = call.args[1]
            self.assertIsInstance(incoming, dict)
            self.assertEqual("1.0.0", incoming["schema_version"])
            self.assertEqual(
                {"name": "collecting-curated-contribution-prs", "revision": "sha256:" + "c" * 64},
                incoming["generated_by"],
            )
        self.assertEqual(generated_by, merged["generated_by"])
        self.assertEqual(
            existing["synthetic_envelope_unknown"],
            merged["synthetic_envelope_unknown"],
        )
        tracker_source = merged["records"][0]["sources"][-1]
        self.assertEqual(
            {"name": "collecting-curated-contribution-prs", "revision": "sha256:" + "c" * 64},
            tracker_source["generated_by"],
        )


class EndToEndTests(unittest.TestCase):
    def test_ac_05_end_to_end_reference_normalization(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_end_to_end(temporary)
            self.assertEqual(0, result.exit_code)
            self.assertEqual(2, len(result.corpus["records"]))
            widget = next(
                record for record in result.corpus["records"]
                if record["pull_request"]["number"] == 11
            )
            tracker_source = widget["sources"][0]
            self.assertEqual(2, len(tracker_source["observations"]))
            self.assertEqual(
                {"issue-body", "comment"},
                {observation["origin_kind"] for observation in tracker_source["observations"]},
            )
            counts = result.manifest["records"][-1]["reference_counts"]
            self.assertEqual(
                {"matched": 2, "selected": 2, "excluded_by_cap": 0, "excluded_examples_or_notices": 1},
                counts,
            )

    def test_ac_08_end_to_end_authoritative_hydration(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_end_to_end(temporary)
            by_number = {record["pull_request"]["number"]: record for record in result.corpus["records"]}
            self.assertEqual("open", by_number[11]["pull_request"]["normalized_state"])
            self.assertEqual("merged", by_number[22]["pull_request"]["normalized_state"])
            self.assertEqual("unknown", by_number[11]["author"]["normalized_role"])
            self.assertEqual("contributor", by_number[22]["author"]["normalized_role"])
            self.assertEqual("complete", by_number[11]["hydration_status"])
            self.assertEqual("complete", by_number[22]["hydration_status"])

        with tempfile.TemporaryDirectory() as temporary:
            failed = run_partial_hydration_end_to_end(temporary)
            self.assertEqual(3, failed.exit_code)
            run = failed.manifest["records"][-1]
            self.assertEqual("partial", run["collection_status"])
            self.assertEqual("partial", run["hydration_outcomes"][0]["status"])
            self.assertEqual("synthetic-lab/sample-lib", run["hydration_outcomes"][0]["repository"])
            self.assertEqual(9999, run["hydration_outcomes"][0]["number"])
            scope = next(scope for scope in run["failed_scopes"] if scope["kind"] == "hydration")
            self.assertEqual("synthetic-lab/sample-lib", scope["repository"])
            self.assertEqual(9999, scope["number"])
            self.assertIn("pull_request_body", scope["endpoint_categories"])

            self.assertEqual(1, len(failed.corpus["records"]))
            record = failed.corpus["records"][0]
            self.assertEqual("unresolved", record["identity_status"])
            self.assertEqual("partial", record["hydration_status"])
            self.assertEqual("unknown", record["pull_request"]["normalized_state"])
            self.assertEqual(["unknown"], [event["state"] for event in record["state_history"]])
            self.assertEqual(
                "https://github.com/synthetic-lab/sample-lib/pull/9999",
                record["state_history"][0]["evidence_url"],
            )
            self.assertIn("pull_request_body", record["state_history"][0]["failure_basis"]["endpoint_categories"])

            analyzer = (
                SKILL_DIR.parent
                / "analyzing-open-source-pr-patterns"
                / "scripts"
                / "validate_corpus.py"
            )
            validated = subprocess.run(
                ["/opt/homebrew/bin/python3", os.fspath(analyzer), os.fspath(failed.corpus_path)],
                capture_output=True,
                text=True,
                check=False,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            self.assertEqual(0, validated.returncode, validated.stderr)

    def test_ac_10_end_to_end_injection_is_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_end_to_end(temporary)
            self.assertEqual(0, result.exit_code)
            flattened_argv = "\n".join(
                value
                for call in result.runner.calls
                for value in call["argv"]
            )
            self.assertNotIn("run shell", flattened_argv)
            self.assertNotIn("not-authorized", flattened_argv)
            self.assertEqual(
                "complete",
                result.manifest["records"][-1]["collection_status"],
            )
            self.assertEqual(
                {"synthetic-corpus.json", "synthetic-manifest.json"},
                {path.name for path in Path(temporary).iterdir()},
            )

    def test_ac_12_end_to_end_corpus_invariants(self):
        with tempfile.TemporaryDirectory() as temporary:
            expected = fixture("expected-corpus.json")
            result = run_end_to_end(
                temporary, skill_revision=expected["generated_by"]["revision"]
            )
            self.assertEqual("1.0.0", result.corpus["schema_version"])
            self.assertEqual(len(result.corpus["records"]), len({
                record["pull_request_node_id"] for record in result.corpus["records"]
            }))
            for record in result.corpus["records"]:
                self.assertEqual(
                    "github-pr:" + record["pull_request_node_id"],
                    record["record_key"],
                )
                self.assertTrue(record["repository"]["node_id"])
                self.assertTrue(record["sources"])
                self.assertTrue(record["state_history"])
                self.assertTrue(record["pull_request"]["url"])
            self.assertEqual(expected, result.corpus)
            self.assertEqual(
                (json.dumps(expected, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
                result.corpus_bytes,
            )

    def test_ac_20_end_to_end_manifest_provenance(self):
        with tempfile.TemporaryDirectory() as first_directory, tempfile.TemporaryDirectory() as second_directory:
            first = run_end_to_end(first_directory)
            second = run_end_to_end(second_directory)
            run = first.manifest["records"][-1]
            required = {
                "run_id", "request_fingerprint", "collection_method", "tracker",
                "collection_status", "started_at", "completed_at", "request_budget",
                "request_count", "request_events", "comment_pages", "reference_counts",
                "hydration_outcomes", "warnings", "failed_scopes", "skill",
            }
            self.assertTrue(required.issubset(run))
            self.assertEqual("tracker-issue-comments", run["collection_method"])
            self.assertEqual("complete", run["collection_status"])
            self.assertEqual(2, len(run["comment_pages"]))
            self.assertEqual("valid", run["comment_pages"][0]["link_validation"])
            self.assertEqual(2, run["comment_pages"][0]["parsed_next_page"])
            self.assertEqual(first.manifest_bytes, second.manifest_bytes)

    def test_ac_27_end_to_end_read_only_runner(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_end_to_end(temporary)
            api_calls = [call for call in result.runner.calls if call["argv"][:2] == ["gh", "api"]]
            self.assertTrue(api_calls)
            for call in api_calls:
                self.assertEqual(["gh", "api", "--method", "GET"], call["argv"][:4])
                self.assertIs(False, call["shell"])
                self.assertEqual(1, call["argv"].count("per_page=100"))
                self.assertFalse(any(
                    token.upper() in {"POST", "PATCH", "PUT", "DELETE", "CLONE", "INSTALL"}
                    for token in call["argv"]
                ))

    def test_ac_31_end_to_end_red_to_green(self):
        with tempfile.TemporaryDirectory() as first_directory, tempfile.TemporaryDirectory() as second_directory:
            expected = fixture("expected-corpus.json")
            expected_revision = expected["generated_by"]["revision"]
            first = run_end_to_end(first_directory, skill_revision=expected_revision)
            second = run_end_to_end(second_directory, skill_revision=expected_revision)
            record = next(record for record in first.corpus["records"] if record["pull_request"]["number"] == 11)
            observations = record["sources"][0]["observations"]
            self.assertTrue(all(observation.get("body_sha256") for observation in observations))
            self.assertTrue(all("tracker_author_association" in observation for observation in observations if observation["origin_kind"] == "comment"))
            self.assertEqual("unknown", record["author"]["normalized_role"])
            self.assertEqual(first.corpus_bytes, second.corpus_bytes)
            self.assertEqual(first.manifest_bytes, second.manifest_bytes)
            self.assertEqual(expected, first.corpus)
            self.assertEqual(0, first.exit_code)

    def test_ac_32_end_to_end_safety_regression(self):
        collector = load_collector()
        existing = fixture("initial-corpus.json")

        def inaccessible(client, repository, number, captured_at):
            del client, repository, number, captured_at
            raise RuntimeError("synthetic 404 inaccessible pull request")

        run = collector.collect(
            FakeClient(tracker_routes()),
            "synthetic-lab/tracker",
            7,
            max_prs=1,
            request_budget=20,
            existing_corpus=existing,
            hydrator=inaccessible,
            timestamp="2030-01-20T00:00:00Z",
        )
        self.assertEqual(4, run.exit_code)
        self.assertEqual("failed", run.manifest["records"][-1]["collection_status"])
        self.assertEqual(existing, run.corpus)
        self.assertEqual("open", run.corpus["records"][0]["pull_request"]["normalized_state"])
        self.assertEqual(1, run.manifest["records"][-1]["reference_counts"]["excluded_examples_or_notices"])
        self.assertNotIn("private roster", json.dumps(run.corpus).lower())

    def test_ac_37_end_to_end_fresh_generated_by(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = run_end_to_end(temporary)
            expected = {
                "name": "collecting-curated-contribution-prs",
                "revision": result.collector.compute_skill_revision(),
            }
            self.assertEqual(expected, result.corpus["generated_by"])
            self.assertEqual(expected, result.manifest["generated_by"])
            self.assertEqual(expected, result.manifest["records"][-1]["skill"])
            self.assertTrue(all(
                source["generated_by"] == expected
                for record in result.corpus["records"]
                for source in record["sources"]
            ))


def sibling_names(path):
    """Return the sibling names ``path`` reads and the uses this scan cannot follow.

    The sibling module lives only in names called ``sibling`` or is read straight
    off ``load_sibling()``. It is read as ``sibling.X``, by string through
    ``getattr``-style calls and ``mock.patch.object``, or passed to a local
    function's parameter that is also named ``sibling``. Any other use is
    untraced, so a new sibling name cannot hide behind an alias.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    functions = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    used, untraced = set(), []
    for node in ast.walk(tree):
        loads = isinstance(node, ast.Call) and "load_sibling" in {
            getattr(node.func, "id", None), getattr(node.func, "attr", None)
        }
        holds = isinstance(node, ast.Name) and node.id == "sibling" and isinstance(node.ctx, ast.Load)
        if not (loads or holds):
            continue
        parent = parents[node]
        if isinstance(parent, ast.Attribute):
            used.add(parent.attr)
            continue
        if loads and isinstance(parent, ast.Assign) and all(
            isinstance(target, ast.Name) and target.id == "sibling" for target in parent.targets
        ):
            continue
        if holds and isinstance(parent, ast.Compare):
            continue
        if holds and isinstance(parent, ast.keyword) and parent.arg == "sibling":
            if getattr(parents[parent].func, "id", None) in functions:
                continue
        if holds and isinstance(parent, ast.Call) and node in parent.args:
            callee = getattr(parent.func, "id", None) or getattr(parent.func, "attr", None)
            named = parent.args[1] if len(parent.args) > 1 and parent.args[0] is node else None
            if callee in {"getattr", "hasattr", "setattr", "delattr", "object"} and isinstance(
                getattr(named, "value", None), str
            ):
                used.add(named.value)
                continue
            if isinstance(parent.func, ast.Name) and callee in functions:
                parameters = functions[callee].args.posonlyargs + functions[callee].args.args
                index = parent.args.index(node)
                if index < len(parameters) and parameters[index].arg == "sibling":
                    continue
        untraced.append(f"{path.name}:{node.lineno}")
    return used, untraced


class SiblingDependencyTests(unittest.TestCase):
    """The closed-PR collector is used only through the names it registers for this skill."""

    def test_uses_exactly_the_names_the_sibling_registers_as_shared(self):
        """The sibling's tests only protect names listed in its SHARED_WITH_SIBLINGS.

        ApiFailure is raised only by these tests, so the tests count as a user too.
        """
        collector = load_collector()
        used, untraced = set(), []
        for path in (SCRIPT, Path(__file__).resolve()):
            names, unfollowed = sibling_names(path)
            used |= names
            untraced += unfollowed
        self.assertEqual([], untraced, "hold the sibling only as `sibling` so its names stay countable")
        # Reading the registry is how this test checks the contract, not a use of it.
        used.discard("SHARED_WITH_SIBLINGS")
        registered = collector.load_sibling().SHARED_WITH_SIBLINGS[collector.SKILL_NAME]
        self.assertEqual(sorted(registered), sorted(used))


if __name__ == "__main__":
    unittest.main()
