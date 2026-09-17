# Baseline 검증 — #111, base `72ad4f2`

이 문서는 구현 **이전** 상태에서 실제로 실행한 명령과 결과다.
변경 후 회귀 판정의 기준선이며, 기존 실패를 새 실패로 오인하지 않기 위한 근거다.

## 테스트 러너

이 저장소에는 `pytest`, `pytest.ini`, `pyproject.toml`, `tox.ini`, GitHub Actions workflow 가
모두 없다. `python3 -m pytest` 는 `No module named pytest` 로 실패한다.
`python3 -m unittest discover -s tests -t .` 도 `tests/` 에 `__init__.py` 가 없어
`ImportError: Start directory is not importable` 로 실패한다.

실제로 동작하는 방식은 파일 직접 실행이다. 두 테스트 파일 모두
`if __name__ == "__main__": unittest.main()` 로 끝난다
(`tests/test_ai_session.py:745-746`, `tests/test_orchestrator_profiles.py:4770-4771`).

따라서 이 작업의 판정 명령은 다음 형태를 쓴다.

```bash
python3 tests/test_ai_session.py
python3 tests/test_orchestrator_profiles.py
```

`.pre-commit-config.yaml` 에는 `gitleaks` 훅만 있다. 이것이 유일한 lint 계열 게이트다.
type check 와 build 는 이 저장소에 구성돼 있지 않다.

## 기준선 실행 결과 (2026-09-16, base `72ad4f2`, 작업 트리 clean)

| 명령 | 결과 |
|---|---|
| `python3 tests/test_ai_session.py` | `Ran 19 tests` — **OK** (6.940s) |
| `python3 tests/test_orchestrator_profiles.py` | `Ran 78 tests` — **FAILED (failures=3)** (39.558s) |

## 기존 실패 3건 — 변경 이전부터 실패

```
FAIL: test_changed_path_allowlist (OrchestratorProfileContractTests)
FAIL: test_file_ownership          (OrchestratorProfileContractTests)
FAIL: test_portable_cli_contract   (OrchestratorProfileContractTests)
```

원인은 세 건 모두 **#103 작업 범위에 고정된 scaffolding** 이 이후 머지로 낡았기 때문이다.

### `test_changed_path_allowlist` (`tests/test_orchestrator_profiles.py:527`)

`BASE_REVISION = "fcfb47ee2a0514518d150554ee491aae87d26d52"`(`:28`) 기준으로
`git diff --name-only` 결과가 `T15_ALLOWED_FILES`(`:42`)·`T15_ALLOWED_PREFIXES`(`:79`)
안에 있는지 검사한다. 그 base 이후 #105(`f2b3bda`)와 #119(`9eb8d89`)가 머지되면서
`dot_claude/skills/dual-review/**`, `docs/development/2026-09-11-105-*/**` 등이
allowlist 밖 변경으로 잡힌다.

### `test_file_ownership` (`tests/test_orchestrator_profiles.py:470`)

`inspect_only` 집합이
`docs/development/2026-09-15-103-orchestrator-permission-profiles/installed-cli-contract-evidence.md`
의 존재를 요구하지만 실제 머지된 디렉터리는 접미사 `-2` 가 붙은
`2026-09-15-103-orchestrator-permission-profiles-2/` 다. 해당 파일이 없어 실패한다.

### `test_portable_cli_contract` (`tests/test_orchestrator_profiles.py:4419`)

같은 누락 파일을 근거로 삼아
`installed orchestrator CLI help-only contract: [Errno 2] No such file or directory`
로 실패한다.

## 이 작업에 대한 함의

- 세 건은 **이 작업이 만든 회귀가 아니다**. 보고서의 verification evidence 에 기존 실패로 명시한다.
- 그러나 이 작업은 새 파일을 추가하므로 `test_changed_path_allowlist` 와 `test_file_ownership`
  은 **추가로 더 실패한다**. 두 테스트는 소유 파일 집합을 하드코딩하므로 새 산출물을
  반영하지 않으면 통과할 수 없다.
- 따라서 Plan 은 두 가지를 반드시 정한다.
  1. 새로 추가·수정하는 파일을 `T15_ALLOWED_FILES`/`T15_ALLOWED_PREFIXES`/`expected_files` 에
     반영할지, 아니면 이 task-scoped 검사를 이번 작업 범위에 맞게 갱신할지.
  2. `BASE_REVISION` 을 현재 base `72ad4f24e9df5919773cb877de01007f641ae163` 으로 갱신할지.
- 두 테스트 모두 `tests/test_orchestrator_profiles.py` 한 파일 안에 있으므로 #118 소유 파일과
  겹치지 않는다. 다만 #118 도 같은 파일에 검사를 추가할 가능성이 있으므로
  **공유 파일 충돌 후보**로 기록한다.

## 공유 파일 충돌 후보 (#118 머지 후 rebase 대상)

| 파일 | 사유 |
|---|---|
| `tests/test_orchestrator_profiles.py` | 양쪽 다 계약 테스트를 추가할 수 있다 |
| `dot_config/ai-session/accounts.toml` | #118 이 workspace profile 경로 해석에 참조할 수 있다 |
| `.chezmoiignore` | 양쪽 다 배포 제외 규칙을 건드릴 수 있다 |
| `docs/session-account-profiles.md` | account 선택 계약 문서 |

`#118` 이 소유하는 다음 경로는 이 작업에서 읽기만 하고 **수정하지 않는다**.
`dot_agents/skills/create-worktree/**`, `dot_claude/skills/create-worktree/**`,
`docs/development/2026-09-16-118-profile-aware-create-worktree/**`,
create-worktree profile path resolver, workmux 생성 adapter.
