# Quality Goal Implementation Plan

- Task ID: 118-profile-aware-create-worktree
- Mode: strict
- Status: PLAN_REVIEW
- Created: 2026-09-16
- Updated: 2026-09-16
- Source goal: GitHub issue #118의 create-worktree가 registry 기반 workspace profile별 목적지를 검증·지연 생성하고 provider별 account binding과 독립적인 tmux 배치를 보장한다.

## Spec link

- 확정 정본: [spec.md](/Users/lee-kyu-hwan/code/profile2/dotfiles/118-create-worktree/docs/development/2026-09-16-118-profile-aware-create-worktree/spec.md)
- SHA-256: `212fb5dc0b3f99d81cd36023c279453d31100ffdb8d7010d1257a1669b4615c7`
- 기준 revision: `72ad4f24e9df5919773cb877de01007f641ae163`
- 구현은 정본의 `D1`~`D9`, AC-1~AC-55, CMD-1~CMD-20을 변경 없이 따른다. Plan 전용 중간 gate는 CMD-21~CMD-28이며 최종 판정은 정본의 실행 순서를 사용한다.

## Global constraints

1. 이 저장소는 chezmoi source다. `dot_local/bin/executable_create-worktree`는 배포 시 `~/.local/bin/create-worktree`, `dot_local/bin/ai_session_registry_loader.py`는 `~/.local/bin/ai_session_registry_loader.py`, `dot_local/libexec/ai_session_registry.py`는 `~/.local/libexec/ai_session_registry.py`가 된다. source의 `dot_`와 `executable_` 이름을 배포 이름과 혼동하지 않는다.
2. task-owned 변경 경로는 아래 File map의 15개 exact file과 `docs/development/2026-09-16-118-profile-aware-create-worktree/` prefix뿐이다. 확정 Spec, Spec 개정 이력, 기존 사용자 변경과 task 밖 경로는 byte-identical로 보존한다.
3. Python 구현은 표준 라이브러리만 사용한다. 공용 module은 registry/path 의미론만 소유하고 subprocess, filesystem mutation, CLI entrypoint를 소유하지 않는다. mutation orchestration은 `executable_create-worktree` 한 곳에만 둔다.
4. `select_strict_account`와 `classify_verifier_payload`의 함수 정의는 `dot_local/bin/executable_ai-session`에 각각 정확히 한 번 남긴다. create backend는 후보 destination을 위해 `ai-session select --directory`나 verifier/login/usage/enrollment/AI executable을 호출하지 않는다.
5. `destination_basename`은 Workmux 또는 wrapper dry-run의 구조화된 destination에서 얻는 path component다. `workmux_handle`은 생성 후 또는 재사용 mutation 전에 `workmux list --json`의 normalized exact-path 유일 매칭에서 얻는 registry identity다. 어느 태스크도 두 값을 같다고 가정하거나 `destination_basename`을 handle-keyed Git config, rollback identity, window identity로 사용하지 않는다.
6. plan과 preflight failure는 directory, runtime state, branch, worktree, Git config, tmux window를 만들지 않는다. apply는 public plan을 먼저 출력하고 dry-run 검증 뒤 runtime lock/journal을 만든 다음, 선택된 destination parent의 missing component를 명시적으로 만들고 각 성공을 즉시 journal에 기록한다.
7. 실제 사용자 worktree, 인증 home, 기본 tmux server, network/provider는 자동 검증에서 접근하지 않는다. 단, CMD-12의 세 번째 segment가 설치된 `codex`/`claude`에 `--version`과 `--help`만 실행하는 help-only probe는 명시적 예외다. 이 probe는 인증·network·mutation을 수행하지 않고 `tests/test_create_worktree.py` harness의 sentinel 대상이 아니므로 R9.3/AC-41의 create-worktree sentinel 범위와 겹치지 않는다. real Workmux는 temporary Git repository에서 `--dry-run`만 사용한다. mutation fixture는 temporary Git/root와 isolated tmux socket/shim만 사용한다.
8. public JSON, log, fixture snapshot, Git/tmux metadata와 문서에는 credential, token, email, raw account identity, 인증 파일 위치, raw subprocess payload와 traceback을 남기지 않는다. 비밀 아닌 alias와 검증된 destination만 허용한다.
9. 각 동작 변경 태스크는 실패하는 검증 기록 → 최소 변경 → 통과 검증 기록 순서다. 실패 시 해당 태스크가 만든 source bytes만 pre-task snapshot으로 복원하고 이전 태스크의 통과본과 기존 dirty bytes를 보존한다. 이 source rollback은 runtime transaction rollback과 별개다.
10. 자동화는 git write, commit, push, PR, merge, deploy, `chezmoi apply`, 실제 profile root 선생성을 수행하지 않는다. main merge와 local apply는 모든 gate 후 operator가 별도로 수행한다.
11. 두 `SKILL.md`는 각 frontmatter 종료 뒤 첫 byte부터 EOF까지 동일해야 한다. `openai.yaml`은 같은 named option과 backend 경계를 안내하되 backend 로직을 복제하지 않는다.
12. 구현 전 baseline은 97 tests 중 #103 전용 `test_changed_path_allowlist`, `test_file_ownership`, `test_portable_cli_contract` 세 건 실패다. 이는 clean main에서도 재현되는 선행 gate 결함이다. T3 전에는 CMD-12 또는 CMD-13을 실행하지 않으며 이 red를 #118 product 결함으로 분류하지 않는다.

## File map

### Task-owned create/modify allowlist

아래 exact file 15개와 다음 prefix 하나가 정본 `R10.2`의 task-owned allowlist와 정확히 일치한다: `docs/development/2026-09-16-118-profile-aware-create-worktree/`.

| 작업 | 경로 | 책임 | 영향받는 interface/behavior |
|---|---|---|---|
| 생성 | `dot_local/bin/ai_session_registry_loader.py` | source/deployed bin에서 `parent.parent / "libexec" / "ai_session_registry.py"` exact regular file을 canonical path로 load하는 유일한 bootstrap | `load_ai_session_registry() -> ModuleType`; schema/path/policy/mutation 구현 금지 |
| 생성 | `dot_local/libexec/ai_session_registry.py` | strict/legacy registry parse, exact allowlist, normalization, containment와 provider scope coherence를 제공하는 side-effect-free module | 두 entrypoint가 동일 file/API/corpus를 사용하고 unknown field를 fail closed |
| 수정 | `dot_local/bin/executable_ai-session` | parser/path 구현을 공용 module 호출로 교체하고 launcher 선택·검증 책임을 보존 | 기존 select/launch/move JSON·exit·current-cwd 의미, selector에 남는 두 함수 |
| 생성 | `dot_local/bin/executable_create-worktree` | `plan|apply` CLI, branch/PR/session, adapters, runtime transaction, post-check, optional binding, rollback, public JSON을 단독 소유 | `create-worktree plan|apply <branch-name|pr-ref> [target-session] --registry <path> [--workspace-profile <name>]` |
| 수정 | `dot_config/ai-session/accounts.toml` | 기존 mapping 옆에 `workspace_profiles`와 `repositories`를 선언 | registry-derived profile enum/root/provider bindings와 canonical repository mapping |
| 수정 | `tests/test_ai_session.py` | parser 추출 뒤 기존 legacy/strict launcher와 mixed deployment 회귀를 실행 | CMD-12와 CMD-22의 module 전체 exact-count gate |
| 생성 | `tests/test_create_worktree.py` | 60개 required contract test, 두 inventory meta-test, temp Git/registry/root, fake gh/provider/adapters와 isolated tmux harness | AC-1~AC-55의 named behavior test와 required-test manifest |
| 생성 | `tests/run_unittest_contract.py` | unittest selection과 result counter의 유일한 판정 runner | exact `-k`, direct `--id`, module/discovery N, 실패 counter와 process exit contract |
| 수정 | `tests/test_orchestrator_profiles.py` | #103 stale gate를 current-main/#118 allowlist로 정정하고 shared module ownership을 판정 | CMD-12, CMD-13, CMD-19의 regression/ownership/changed-path gate |
| 수정 | `tests/check_installed_orchestrator_cli_contract.py` | 존재하지 않는 #103 evidence 의존을 제거하고 source constants, role manifest, help-only probe를 직접 판정 | CMD-12/CMD-19의 portable CLI gate; 인증/network mutation 없음 |
| 수정 | `dot_agents/skills/create-worktree/SKILL.md` | named profile, backend plan/apply, result/error와 reviewed recovery를 설명 | agent `$create-worktree` human-language adapter |
| 수정 | `dot_claude/skills/create-worktree/SKILL.md` | Claude frontmatter를 유지하고 본문을 agent 사본과 동일하게 만든다 | Claude `$create-worktree`와 body identity |
| 수정 | `dot_agents/skills/create-worktree/agents/openai.yaml` | named profile, plan-before-apply, no-fallback/no-auto-move를 안내 | OpenAI prompt가 public backend 한 곳으로 수렴 |
| 수정 | `docs/session-account-profiles.md` | workspace profile, canonical repository, provider binding, omission/fail-closed와 login 비의존성을 문서화 | registry 운영·mixed deployment contract |
| 생성 | `docs/create-worktree.md` | unsupported wrapper, incomplete rollback, cross-profile #111 handoff를 문서화 | no-fallback과 operator-reviewed recovery |

prefix 아래 `spec.md`와 `spec-revision-notes.md`는 읽기 전용이고, 이 Plan과 `plan-revision-notes.md`는 계획 산출물이다. terminal workflow가 같은 prefix의 `report.md`를 생성해 AC-48의 operator evidence를 기록한다.

### Read-only implementation evidence

| 경로 | 읽는 이유 | 변경 영향 |
|---|---|---|
| `dot_local/bin/executable_ai-role-session` | launcher가 registry/selector를 호출하는 현재 경계 확인 | 변경하지 않고 CMD-12로 회귀 확인 |
| `dot_config/workmux/config.yaml` | three-pane, auto base, naming/hooks, Nerd Font, `status_format: false` 기준 | invocation override는 `worktree_dir` 한 key만 포함 |
| `tests/fixtures/orchestrator-profiles/**` | temporary HOME, fake CLI, live-action sentinel pattern 참고 | 기존 fixture 의미와 bytes 보존 |
| source root의 `install.sh`, `setup.sh`, `run_once_*`, `run_onchange_*`, `.chezmoiscripts/**`, `*.tmpl` | profile root 선생성 scanner의 완전한 대상 집합 | scanner만 읽고 apply하지 않음 |
| 확정 Spec, 세 evidence 문서와 issue snapshot | P1~P3, Q1/Q2/Q4, baseline, public contract의 근거 | 구현 중 수정 금지 |

## Task dependencies

구현 순서는 `T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9 → T10 → T11 → T12`이며 같은 파일을 여러 태스크가 순차 수정하므로 병렬화하지 않는다.

| 선행 | 후행 | 제공 interface | 소비하는 전제 |
|---|---|---|---|
| T1 | T2 | import 가능한 module 전체와 failing-test OS exit를 판정하는 runner bootstrap | direct ID/exact selection meta-test가 runner process 자체로 실행 가능 |
| T2 | T3~T12 | exact `-k`/`--id`, result-counter guard, 60-ID manifest와 두 inventory direct ID | 이후 어떤 0건·부분·중복 선택도 조용히 통과하지 않음 |
| T3 | T4 | current-main 기준 #118 allowlist와 존재하는 evidence만 쓰는 세 선행 gate | baseline의 97/3 red가 downstream product 결함으로 오인되지 않음 |
| T4 | T5 | 공용 registry/path module, loader와 temporary schema corpus의 launcher regression | `D1`/`D2`의 shared semantic API; shipped registry bytes는 아직 unchanged |
| T5 | T6 | input/profile/repository resolver, mutation-free plan, adapter protocol | `D6`의 omission/provider 분리와 safe repository parent |
| T6 | T7 | shipped schema rows와 one-key Workmux/wrapper dry-run의 authoritative destination | parser/backend가 준비된 뒤 data를 활성화하고 `D3`과 Q1/Q2의 `destination_basename`을 제공; handle은 아직 없음 |
| T7 | T8 | pre-mutation repository lock, durable journal, TOCTOU phase API | `D5`의 pre-state와 apply lifetime 경계 |
| T8 | T9 | happy create/open과 parent-before-apply identity inventory | `D4`, P1/P2의 lazy parent와 successful identity delta |
| T9 | T10 | owner-only reverse rollback, P3 empty-parent cleanup, stale/diagnostic recovery | 모든 integration failure가 exit 6/7로 닫힘 |
| T10 | T11 | 완전한 backend success/failure/public event contract | skill/docs가 안정된 CLI만 설명 |
| T11 | T12 | shipped skill/prompt/docs와 body identity | final manifest, regression, scope와 human diff 판정 |

결정 배치는 `D1`/`D2`를 T4~T6, `D3`을 T6, `D4`를 T8~T9, `D5`를 T7~T9, `D6`을 T5/T10, `D7`을 T1~T2, `D8`을 T3, `D9`을 T9에 둔다.

### Judgement-test authoring ownership

모든 `-k` 이름은 `tests/test_create_worktree.py`의 `CreateWorktreeContractTests`에 아래 태스크가 작성한다. T2가 같은 60개 이름의 fully-qualified ID를 manifest에 정확히 한 번씩 먼저 고정한다.

| 작성 태스크 | method names |
|---|---|
| T4 | `test_workspace_profile_schema`, `test_profile_enum_from_registry`, `test_canonical_repository_mapping`, `test_registry_mixed_deployment`, `test_unknown_fields_rejected`, `test_provider_bindings`, `test_single_codex_binding` |
| T5 | `test_cli_contract`, `test_session_profile_independence`, `test_profile_inference`, `test_realpath_component_containment`, `test_symlink_escape_and_prefix_confusion`, `test_no_chezmoi_profile_root_creation`, `test_single_backend_contract`, `test_shared_registry_path_module_identity`, `test_creation_requires_no_verifier`, `test_verifier_defect_does_not_block_creation` |
| T6 | `test_real_workmux_dry_run_merge` |
| T7 | `test_prestate_ownership_journal`, `test_runtime_lock_journal_contract`, `test_stale_transaction_requires_reviewed_recovery` |
| T8 | `test_lazy_parent_creation`, `test_validation_precedes_mkdir`, `test_branch_profile_destinations`, `test_pr_forms_and_head_oid`, `test_session_selection_and_open_outside_configured_dir`, `test_canonical_linked_worktree_layout`, `test_workmux_global_config_preserved`, `test_no_automatic_ai_or_server`, `test_high_risk_e2e_isolation` |
| T9 | `test_toctou_symlink_swap`, `test_parent_creation_rollback`, `test_worktree_and_branch_rollback`, `test_tmux_failure_rollback`, `test_preexisting_artifacts_never_removed`, `test_rollback_incomplete_reporting`, `test_repository_lock_and_external_race`, `test_adapter_registered_then_failed_before_handle_lookup`, `test_cold_start_missing_profile_and_repository_parent`, `test_wrapper_cold_start_contract` |
| T10 | `test_wrapper_destination_contract`, `test_wrapper_failure_and_permissions`, `test_wrapper_unsupported`, `test_git_crypt_guard`, `test_same_profile_reuse`, `test_cross_profile_existing_worktree_blocked`, `test_binding_adapter_atomic_or_unavailable`, `test_cross_profile_move_is_out_of_scope`, `test_plan_apply_json_contract`, `test_plan_precedes_mutation`, `test_exit_status_contract`, `test_internal_exception_and_signal_contract`, `test_public_output_allowlist`, `test_sensitive_output_and_metadata_hygiene`, `test_post_create_verification` |
| T11 | `test_skill_body_equivalence`, `test_skill_interface_contract`, `test_profile_aware_worktree_documentation` |
| T12 | `test_issue_118_task_owned_path_allowlist`, `test_no_persistent_or_external_mutation` |

Direct `--id` 소유권도 고정한다. T2가 `tests.test_create_worktree.CreateWorktreeInventoryTests.test_required_create_worktree_inventory_is_complete_and_unskipped`와 `tests.test_create_worktree.CreateWorktreeInventoryTests.test_judgement_command_selection_contract`를 작성한다. T3는 이미 존재하는 `tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_changed_path_allowlist`, `test_file_ownership`, `test_portable_cli_contract`의 body와 fixture를 current-main contract으로 수정한다. 따라서 CMD-1~CMD-28의 모든 `-k`/direct `--id`에는 명명 module의 작성 또는 수정 태스크가 있고 CMD-28은 새 `-k` 이름을 추가하지 않는다.

## Tasks

### T1. unittest contract runner bootstrap을 가장 먼저 만든다

대상 AC: AC-55 (CMD-20)

1. 실패 검증: 현재 `tests/run_unittest_contract.py`가 없음을 기록하고 CMD-21을 실행한다. known-good module import는 성공하지만 runner file 부재로 command가 nonzero여야 한다. CMD-20은 runner 부재 자체도 기대한 nonzero로 오인할 수 있으므로 이 단계의 red 증거로 사용하지 않는다.
2. 최소 변경: `tests/run_unittest_contract.py`를 stdlib-only로 만들고 `--module ... --all --min-count`의 load, 수집 N>0/min-count, 같은 suite의 `testsRun=N`, failures/errors/skipped/expectedFailures/unexpectedSuccesses 0, 실패 시 nonzero OS exit를 먼저 구현한다. stdout/stderr는 비민감 summary만 낸다.
3. 통과 검증: CMD-21이 N=1 known-good를 실행해 exit 0이고 CMD-20이 known-bad runner process의 nonzero를 외부 shell에서 확인해 exit 0이어야 한다.
4. 실패 처리/source rollback: 둘 중 하나가 실패하면 runner 한 파일만 제거해 pre-T1 상태로 복구한다. temp module은 trap이 exact temp directory만 제거하며 repository/user state는 건드리지 않는다.

### T2. exact-selection runner와 60-ID manifest를 완성한다

대상 AC: AC-42 (CMD-13 tests.test_create_worktree.CreateWorktreeInventoryTests.test_required_create_worktree_inventory_is_complete_and_unskipped), AC-52 (CMD-18 tests.test_create_worktree.CreateWorktreeInventoryTests.test_judgement_command_selection_contract)

1. 실패 검증: `tests/test_create_worktree.py`에 `CreateWorktreeInventoryTests.test_judgement_command_selection_contract`를 먼저 작성해 empty module, missing name, duplicate name, 일부만 존재하는 복수 `-k`, skipped, expected-failure, unexpected-success와 valid targeted/direct-ID fixture를 만든다. CMD-18은 T1 runner가 아직 `--id`와 exact selection을 지원하지 않아 nonzero여야 한다.
2. 최소 변경—runner: 시작할 때 runner file이 속한 `tests/`의 부모 디렉터리인 repository root(`Path(__file__).resolve().parents[1]`)를 `sys.path` 맨 앞에 삽입해 `--module tests.<name>`과 `--id tests.<name>.<Class>.<method>`를 load한다. 이 규칙은 CMD-1~CMD-27 가운데 runner를 호출하는 모든 test segment와 CMD-28에 적용되고, CMD-20/CMD-21의 temp top-level module은 기존 `PYTHONPATH` entry로 계속 load된다. `--module`과 `--discover-root/--pattern`을 상호 배타적으로 처리하고, `-k`는 substring이 아닌 final method name exact match, `--id`는 fully-qualified ID exact match로 load한다. discovery는 `top_level_dir` 없이 `discover('tests', pattern)`을 사용하고, manifest와 대조할 때만 각 발견 ID 앞에 `tests.`를 결정적으로 붙인다. 모든 `test_*.py`가 `tests/` 바로 아래에 있고 중첩 test module이 없으므로 이 정규화는 모호하지 않다. `tests/__init__.py`는 R10.2 allowlist 밖 신규 파일이라 AC-46/AC-53을 깨뜨리므로 만들지 않는다. targeted N은 unique selector 수 또는 `--expect-count`, module/discovery N은 실행 직전 flatten한 suite와 `--min-count`로 검증한다. N=0, missing, duplicate, partial selection과 다섯 result counter 중 하나라도 nonzero면 process도 nonzero다.
3. 최소 변경—manifest: 같은 file에 정본 Test strategy의 60개 ID를 `tests.test_create_worktree.CreateWorktreeContractTests.<method>` 형식으로 정확히 한 번 열거한다. `test_required_create_worktree_inventory_is_complete_and_unskipped`는 위 `tests.` 정규화를 적용한 discovery ID의 exact multiplicity와 manifest suite의 실행 count/counter를 단언한다. Plan command table의 unique `-k` set과 manifest method set도 동일해야 한다.
4. 통과 검증: CMD-18이 direct ID 한 건으로 위 synthetic selection contract을 모두 확인해 exit 0이고, CMD-20/CMD-21도 계속 통과해야 한다. CMD-13은 T12까지 실행하지 않는다. 아직 60개 contract method가 모두 작성되지 않았기 때문이다.
5. 실패 처리/source rollback: T2가 바꾼 runner와 새 test module만 T1 bytes/부재 상태로 복구한다. CMD-21/CMD-20으로 T1 bootstrap이 다시 통과하는지 확인한다.

### T3. #103 전용 gate를 product 구현 전에 정정한다

대상 AC: AC-43 (CMD-12), AC-44 (CMD-13), AC-53 (CMD-19 tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_changed_path_allowlist tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_file_ownership tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_portable_cli_contract)

1. 실패 검증: CMD-19를 실행해 세 direct ID가 정확히 3건 선택되지만 stale base와 존재하지 않는 #103 evidence 의존 때문에 nonzero임을 기록한다. 구현 전 full discovery의 97/3도 별도 baseline evidence로만 보존한다. 이 시점까지 CMD-12/CMD-13은 실행하지 않는다.
2. 최소 변경: `tests/test_orchestrator_profiles.py`의 `BASE_REVISION`을 `72ad4f24e9df5919773cb877de01007f641ae163`으로 갱신하고 `T15_ALLOWED_FILES`/`T15_ALLOWED_PREFIXES`를 File map의 15 files/한 prefix와 정확히 맞춘다. `PRESERVED_PATHS`에서는 `dot_claude/skills/create-worktree`만 제거하고 `dot_config/workmux`, `dot_tmux.conf.tmpl`, `dot_zshrc.tmpl`은 남긴다. `test_file_ownership`에서 존재하지 않는 #103 evidence 경로를 제거한다.
3. 최소 변경—portable checker: `tests/check_installed_orchestrator_cli_contract.py`가 frozen evidence file을 읽지 않고 checker-owned version/range/required/forbidden constants, role manifest와 help-only probe를 직접 대조하게 한다. 격리 실측과 맞게 Codex `0.154.0`, Claude `2.1.273`을 사용한다. `tests/test_orchestrator_profiles.py`의 `test_portable_cli_contract`는 exit 97 fake 대신 provider별 정상 shim을 설치한다. 각 shim은 `--version`에 해당 기대 version을, `--help`에 checker의 required options를 출력하고 exit 0이며, 호출 때마다 `AI_TEST_CLI_PROBE_LOG`에 `<provider> <argument>`를 append한다. 기존의 `codex --version`, `codex --help`, `claude --version`, `claude --help` 네 줄 순서 단언은 유지해 checker가 두 probe를 실제 실행했음을 검증한다. checker의 실제 installed-CLI 경로는 그대로 help-only이고 변경은 R10.5가 허용한 이 두 `tests/` files뿐이다.
4. 통과 검증: CMD-19가 N=3과 counter 0으로 exit 0이어야 한다. future task paths가 아직 없어도 changed-path allowlist는 current delta를 허용하며 ownership test는 존재하는 source/constants만 검사한다.
5. 실패 처리/source rollback: 두 gate files만 pre-T3 bytes로 복구하고 T4를 시작하지 않는다. 이 경우 baseline red 세 건은 선행 결함으로 보고하며 full-suite 성공을 주장하지 않는다.

### T4. 공용 registry/path module과 strict placement schema를 추출한다

대상 AC: AC-6 (CMD-2 -k test_workspace_profile_schema -k test_profile_enum_from_registry), AC-7 (CMD-2 -k test_canonical_repository_mapping), AC-8 (CMD-2 -k test_registry_mixed_deployment -k test_unknown_fields_rejected)

1. 실패 검증: T4 소유의 일곱 `CreateWorktreeContractTests`와 `tests/test_ai_session.py`의 `test_shared_registry_extraction_preserves_legacy_cli`, `test_shared_registry_extraction_preserves_strict_cli`, `test_new_parser_old_registry_launch_compatibility`를 먼저 작성한다. CMD-2는 새 tables/API 부재로 nonzero여야 하고, 세 회귀 case 작성 전 CMD-28은 현재 N=19가 `--min-count 22`에 못 미쳐 nonzero여야 한다.
2. 최소 변경—현재 존재해 이동하는 심볼: `ContractError`; constants `PROVIDERS`, `AUTH_KINDS`, `ALIAS_PATTERN`, `ACCOUNT_FIELDS`, `SCOPE_BINDING_FIELDS`, `BINDING_FIELDS`, `STRICT_REGISTRY_FIELDS`, `STRICT_ACCOUNT_FIELDS`, `WORKSPACE_MAPPING_FIELDS`, `STORED_BINDING_FIELDS`, `RESERVED_SELECTABLE_ALIASES`; dataclasses `Account`, `Registry`, `SelectionContext`, `Binding`; helpers `require_alias`, `require_string`, `reject_unknown_fields`, `normalize_repository`, `normalize_organization`, `normalized_directory`, `normalized_config_home`, `normalized_declared_config_home`, `parse_scope`, `parse_strict_scope`, `parse_stored_bindings`, `load_strict_registry`, `load_registry`, `directory_contains`, `scope_matches`, `scope_specificity`, `resolve_same_priority`, `matching_allowed_scope`를 `ai_session_registry.py`로 옮긴다. 이름이 이미 존재하는 심볼은 rename하지 않는다.
3. 최소 변경—새로 작성하는 API: `WORKSPACE_PROFILE_FIELDS`, `REPOSITORY_FIELDS`, `WorkspaceProfile`, `RepositoryPlacement`, `resolve_with_missing_tail`, `validate_safe_component`, `validate_workspace_profiles`, `validate_repositories`, `validate_provider_scope_coherence`를 새로 작성하고 `Registry`에 placement collections를 추가한다. 이는 현재 selector에 존재하는 심볼 이동으로 표현하지 않는다.
4. 최소 변경—selector/loader: loader만 exact regular libexec file을 load한다. `select_legacy_account`, `select_workspace_mapping`, `matching_stored_binding`, `select_strict_account`, `select_account`, `classify_verifier_payload`는 launcher policy로 selector에 남고 shared primitives에 위임한다. shipped `accounts.toml`은 이 태스크에서 수정하지 않고 temporary old/new registry corpus만 사용한다.
5. 통과 검증: CMD-2, 정본 regression인 CMD-22와 Plan 전용 수집 하한 gate인 CMD-28이 exit 0이어야 한다. CMD-28의 N≥22가 기존 19건에 T4의 세 회귀 case가 실제로 추가됐음을 구속한다. provider binding methods는 temporary rows의 coherence/single-Codex rule만 판정한다. new parser/old registry는 launcher를 유지하고 create capability만 unavailable이며 old parser/new registry는 unknown field를 거부한다. source scan은 shared semantic 구현의 duplicate 0건과 selector의 두 필수 함수 정의 각 1건을 확인한다.
6. 실패 처리/source rollback: loader/shared module, selector와 T4 tests만 pre-T4 bytes로 복구하고 CMD-19를 재확인한다. gate 정정 bytes와 shipped registry bytes는 보존한다.

### T5. mutation-free CLI, resolver와 single-backend 경계를 만든다

대상 AC: AC-1 (CMD-1 -k test_cli_contract), AC-2 (CMD-1 -k test_session_profile_independence), AC-3 (CMD-1 -k test_profile_inference), AC-10 (CMD-3 -k test_realpath_component_containment -k test_symlink_escape_and_prefix_confusion), AC-13 (CMD-3 -k test_no_chezmoi_profile_root_creation), AC-15 (CMD-8 -k test_single_backend_contract), AC-51 (CMD-8 -k test_shared_registry_path_module_identity)

1. 실패 검증: T5 소유의 열 contract methods를 먼저 작성한다. CMD-1, CMD-23, CMD-24는 backend 부재, invalid resolver 결과 또는 shared-module identity 불일치로 nonzero여야 하며 filesystem/tmux/provider sentinel count는 0이다.
2. 최소 변경—CLI/resolver: exact positional/named option parser, branch/PR normalization, explicit profile 우선과 unique real-cwd omission, canonical repository/common-dir 검증과 safe repository parent 계산을 구현한다. independently computed path는 `<profile.root>/<repository.workspace_subdir>`까지만이며 full destination은 adapter protocol 결과 전에는 만들지 않는다.
3. 최소 변경—plan/backend boundary: `plan`은 shared pure API와 injected dry-run adapter를 사용해 한 줄 JSON만 출력하고 runtime root/destination parent를 만들지 않는다. skill/OpenAI/TUI source scan은 이 command 밖 profile lookup, destination mkdir, `git worktree add`, `workmux add`, rollback orchestration 0건을 요구한다.
4. 최소 변경—R3.3 scanner test: source의 exact script/glob/`.chezmoiscripts`/모든 template set을 nonempty로 단언하고 registry-derived managed target을 합친다. 오케스트레이터 실측의 `chezmoi version v2.70.0`에서 `--override-data-file`, `--config-format`, `--cache`, `--persistent-state`, `--refresh-externals` 다섯 항목은 모두 global flag이고 `--promptChoice`/`--promptString`은 `execute-template` command flag로 실재한다. 다른 버전에서는 flag surface가 달라질 수 있으므로 구현 시작 때 `chezmoi --version` 출력을 기록한다. 설치된 chezmoi가 제공하는 `execute-template --file`, `--source`, `--destination`, `--config /dev/null --config-format none`, `--cache`, `--persistent-state`, `--refresh-externals never`, `--no-tty`, `--override-data-file`을 모두 temp root로 격리해 render key set이 template set과 같음을 단언한다. fixture data는 `machine_type="personal"`, `nvm_auto_use_hook=""`, synthetic profile/repository roots와 temp `.chezmoi.homeDir`/`.chezmoi.sourceDir`를 제공한다. `.chezmoi.toml.tmpl`에는 `--init --promptChoice machine_type=personal --promptString nvm_auto_use_hook=`를 추가한다. 각 shell/helper/managed-target positive fixture와 comment/document/unrelated negative fixture를 판정하며 `apply`는 호출하지 않는다.
5. 최소 변경—ownership gate: 새 loader/shared/backend files가 모두 존재한 뒤 `test_file_ownership`을 확장해 loader의 import-only 경계, shared semantic file, selector에 남는 두 함수와 backend 한 곳의 mutation ownership을 단언한다.
6. 통과 검증: CMD-1, CMD-23, CMD-24와 CMD-19가 exit 0이어야 한다. invalid input/profile/repository/path는 exit 2/3/5와 mutation 0건이고, two entrypoints가 같은 canonical libexec path/API/corpus 결과를 사용하며 creation trace의 verifier 계열 호출은 0회다.
7. 실패 처리/source rollback: backend, T5 test additions와 T5의 ownership assertions만 제거하고 shared schema T4 상태로 되돌린다. CMD-2, CMD-22, CMD-19가 계속 통과해야 한다.

### T6. Workmux와 wrapper의 authoritative dry-run adapter를 구현한다

대상 AC: AC-9 (CMD-2 -k test_provider_bindings -k test_single_codex_binding), AC-19 (CMD-4 -k test_real_workmux_dry_run_merge)

1. 실패 검증—shipped data: T4의 `test_provider_bindings`와 `test_single_codex_binding`을 shipped registry rows까지 검사하도록 먼저 강화한다. CMD-2는 `accounts.toml`에 `workspace_profiles`/`repositories`가 아직 없어 nonzero여야 하고 기존 launcher regression은 계속 통과해야 한다.
2. 최소 변경—shipped data: reviewed `workspace_profiles`/`repositories` rows를 기존 `workspace_directory_mappings` 옆에 추가한다. 모든 shipped profile에 Claude/Codex alias를 선언하고 Codex binding은 모두 `codex-default`로 유지한다. CMD-2를 다시 실행해 exit 0을 기록한다.
3. 실패 검증—adapter: `test_real_workmux_dry_run_merge`를 작성하고 CMD-25를 실행한다. adapter 부재로 nonzero이고 missing parent, branch, worktree, runtime state와 window 생성은 0건이어야 한다.
4. 최소 변경—adapters: mode 0600 temporary regular YAML에 literal `worktree_dir: <repository_parent>` 한 key만 쓰고 real Workmux 0.1.248은 `add --config ... --dry-run`만 호출한다. 출력 dirname의 byte identity와 safe basename을 검증해 `destination_basename`/normalized destination을 채택하고 optional `Handle:`은 버린다. executable wrapper의 `--destination-parent`와 missing-parent `--dry-run`을 같은 structured destination protocol로 정규화한다. capability/permission/dry-run/git-crypt failure는 apply/open이나 fallback 없이 preflight error다.
5. 통과 검증: CMD-2와 CMD-25가 exit 0이어야 한다. shipped provider bindings, P1/Q1 missing-parent no-mutation, one-key override, optional handle 비권위와 temp config cleanup을 함께 증명한다.
6. 실패 처리/source rollback: shipped data, adapter code와 T6 method만 pre-T6 상태로 복구한다. parser/backend T4~T5는 유지하고 runtime mutation은 아직 없으므로 source rollback 외 cleanup 대상은 exact temp config뿐이다.

### T7. durable runtime lock/journal을 apply보다 먼저 구현한다

대상 AC: AC-29 (CMD-7 -k test_prestate_ownership_journal)

1. 실패 검증: T7 소유 세 methods를 먼저 작성한다. CMD-26과 CMD-17은 lock/journal 부재, wrong schema/mode 또는 scan 기반 lookup 때문에 nonzero여야 하고 allowed temp runtime root 밖 access는 0건이어야 한다.
2. 최소 변경: validated `$XDG_RUNTIME_DIR/create-worktree` 또는 `$TMPDIR/create-worktree-<uid>`, mode 0700 directory, common-dir digest lock, UUID journal, mode 0600 no-follow/exclusive create/atomic replace+fsync를 구현한다. lock은 exact five-field JSON이며 UUID/digest가 journal과 교차 일치한다.
3. 최소 변경: dry-run 성공 뒤 첫 mutation 전에 ancestor identity, branch/OID, Git worktree set, exact `(normalized real path, workmux_handle)` pair, window ID와 handle-keyed session value를 durable하게 기록한다. later lookup은 digest lock 한 개와 그 UUID의 journal 한 개만 직접 열고 glob/scan하지 않는다.
4. 통과 검증: CMD-26과 CMD-17이 test-double lifecycle에서 exit 0이어야 한다. crash/missing/mismatched transaction은 raw runtime identity를 공개하지 않고 exit 5와 recovery ID/enum reason만 내며 자동 탈취·삭제하지 않는다.
5. 실패 처리/source rollback: T7 runtime code와 methods만 되돌린다. test fixture는 소유 temp runtime root만 정리하고 identity가 불명확한 journal을 product code로 삭제하지 않는다.

### T8. parent-first happy apply와 isolated tmux E2E를 연결한다

대상 AC: AC-4 (CMD-4 -k test_branch_profile_destinations), AC-5 (CMD-4 -k test_pr_forms_and_head_oid), AC-12 (CMD-3 -k test_lazy_parent_creation -k test_validation_precedes_mkdir), AC-14 (CMD-9 -k test_canonical_linked_worktree_layout), AC-20 (CMD-9 -k test_workmux_global_config_preserved), AC-23 (CMD-4 -k test_session_selection_and_open_outside_configured_dir)

1. 실패 검증: T8 소유 아홉 methods를 먼저 작성한다. CMD-3, CMD-4, CMD-27은 apply/open 부재, parent 생성 순서 또는 isolated post-state 불일치로 nonzero여야 한다. harness에서 `CREATE_WORKTREE_E2E_NETWORK=deny`는 기본 fake network/provider command sentinel에 더해 socket connect/DNS 시도를 즉시 기록하고 실패시키는 강화 mode다. 변수가 없을 때도 같은 E2E/cold-start methods를 skip하지 않고 기본 sentinel과 zero-hit 단언으로 실행하며, 값이 `deny`가 아니어도 test 선택이나 skip 조건으로 사용하지 않는다. 이 계약은 CMD-9/CMD-16/CMD-27의 강화 실행과 변수 없는 CMD-13 manifest/full discovery 모두에 적용된다. real-user/default-tmux/network/provider sentinel hit는 0이다.
2. 최소 변경—create: T7 journal이 durable한 뒤 destination parent의 missing components를 아래에서 필요한 만큼 하나씩 명시 생성하고 즉시 journal/fsync한다. 그 뒤 T6의 same config/destination으로 Workmux apply를 호출해 P2의 Git implicit parent 생성에 의존하지 않는다.
3. 최소 변경—branch/PR/session: 세 PR form은 조회한 head OID를 사용하고 bare number를 추정하지 않는다. session은 explicit, 생성 뒤 얻을 handle의 stored value가 아직 없으므로 mode default 순으로 exact existing name을 선택하며 자동 생성하지 않는다. pane command는 빈 shell이다.
4. 최소 변경—happy post-state: canonical common-dir, top-level, HEAD, pane cwd와 global panes/base/naming/hooks/Nerd Font/status를 검증한다. 생성 뒤 exact path list match로 얻은 `workmux_handle`만 result와 handle-keyed state에 사용한다.
5. 통과 검증: CMD-3, CMD-4, CMD-27이 exit 0이어야 한다. plan/invalid/dry-run failure는 mutation 0건이고 valid cold parent creation은 adapter apply보다 앞선다. mismatch/fault rollback의 완료 판정은 T9에서 닫는다.
6. 실패 처리/source rollback: happy apply 연결과 T8 methods를 T7의 plan/dry-run+journal 상태로 복구한다. runtime fixture에 failure artifact가 있으면 T9 product rollback을 가장하지 않고 test-owned temp cleanup과 trace evidence만 사용한다.

### T9. owner-only transaction rollback과 reviewed recovery를 완성한다

대상 AC: AC-11 (CMD-7 -k test_toctou_symlink_swap), AC-30 (CMD-7 -k test_parent_creation_rollback), AC-31 (CMD-7 -k test_worktree_and_branch_rollback), AC-32 (CMD-7 -k test_tmux_failure_rollback), AC-33 (CMD-7 -k test_preexisting_artifacts_never_removed), AC-34 (CMD-7 -k test_rollback_incomplete_reporting), AC-35 (CMD-7 -k test_repository_lock_and_external_race), AC-49 (CMD-16 -k test_cold_start_missing_profile_and_repository_parent -k test_wrapper_cold_start_contract), AC-50 (CMD-17 -k test_runtime_lock_journal_contract -k test_stale_transaction_requires_reviewed_recovery), AC-54 (CMD-7 -k test_adapter_registered_then_failed_before_handle_lookup)

1. 실패 검증: T9 소유 열 methods를 먼저 작성하고 T7의 runtime tests를 actual success/complete rollback lifetime까지 강화한다. CMD-7, CMD-16, CMD-17은 reverse cleanup, P3 intermediate removal, stale lifetime 또는 diagnostic ownership 분리가 없어 nonzero여야 한다.
2. 최소 변경—runtime rollback: journal-owned exact window ID → successful exact `(path, workmux_handle)`/handle-keyed delta → linked worktree/admin entry → matching-OID invocation-created branch → backend-created empty components 순으로 best-effort rollback한다. P3 intermediate도 journal-owned이며 현재 empty일 때만 제거한다. pre-existing/changed/dirty/concurrent identity는 force하지 않는다.
3. 최소 변경—diagnostic window: adapter registration 직후 normal handle lookup 전 실패하면 destination exact-path list를 진단용으로 정확히 한 번 실행한다. successful registration evidence와 pre-state에 없던 exact unique safe item이 함께 있을 때만 소유한다. 그 외 item은 제거하지 않고 `rollback_remaining`에 `workmux_registry_entry`와 비민감 destination을 기록한다.
4. 최소 변경—TOCTOU/stale: mkdir 직전/직후와 external apply 직후 containment/common-dir를 재검사한다. normal success와 complete rollback은 terminal journal fsync 뒤 owned journal/lock을 제거하고, incomplete/crash는 reviewed recovery pair를 남긴다.
5. 통과 검증: CMD-7, CMD-16, CMD-17이 exit 0이어야 한다. complete rollback은 exit 6, identity drift/non-empty/non-reversible/diagnostic-only remaining은 exit 7이고 pre-existing bytes는 동일해야 한다.
6. 실패 처리/source rollback: product runtime rollback evidence를 먼저 보존한 뒤 T9 source와 tests만 T8 상태로 복구한다. source restore가 runtime artifact를 삭제하는 수단이 아니며 unproven remaining은 operator-reviewed recovery 대상으로 남긴다.

### T10. wrapper/reuse/binding, public schema와 failure taxonomy를 닫는다

대상 AC: AC-16 (CMD-8 -k test_plan_apply_json_contract -k test_plan_precedes_mutation), AC-17 (CMD-8 -k test_exit_status_contract -k test_internal_exception_and_signal_contract), AC-18 (CMD-8 -k test_creation_requires_no_verifier), AC-21 (CMD-5 -k test_wrapper_destination_contract -k test_wrapper_failure_and_permissions), AC-22 (CMD-5 -k test_wrapper_unsupported -k test_git_crypt_guard), AC-24 (CMD-9 -k test_post_create_verification), AC-25 (CMD-6 -k test_same_profile_reuse), AC-26 (CMD-6 -k test_cross_profile_existing_worktree_blocked), AC-27 (CMD-6 -k test_binding_adapter_atomic_or_unavailable), AC-28 (CMD-6 -k test_cross_profile_move_is_out_of_scope), AC-36 (CMD-8 -k test_public_output_allowlist), AC-37 (CMD-8 -k test_sensitive_output_and_metadata_hygiene), AC-38 (CMD-9 -k test_no_automatic_ai_or_server), AC-41 (CMD-9 -k test_high_risk_e2e_isolation), AC-47 (CMD-8 -k test_verifier_defect_does_not_block_creation)

1. 실패 검증: T10 소유 15 methods를 먼저 작성하고 T5의 no-verifier tests를 plan+actual apply trace로 강화한다. CMD-5, CMD-6, CMD-8, CMD-9는 wrapper/reuse/binding, exact handle, exit precedence, allowlist/redaction 또는 post-check mismatch가 미완성이라 nonzero여야 한다.
2. 최소 변경—wrapper/reuse/binding: capable wrapper만 exact dry-run destination으로 apply/open한다. same-profile existing worktree는 어떤 mutation보다 먼저 exact-path unique safe handle을 얻어 재사용하고, cross-profile/main/scope 밖은 exit 4와 mutation 0건이다. optional binding adapter는 positive generation을 atomic 등록하며 unavailable은 persistent state 0건, declared failure는 T9 rollback을 사용한다.
3. 최소 변경—public contract: plan/apply 첫 event를 동일하게 만들고 new-create plan에는 handle이 없으며 created result/reuse plan/result에만 authoritative handle이 있다. event builder 한 곳이 exact key allowlist, one-line JSON, stdout success/stderr error와 redaction을 적용한다.
4. 최소 변경—failure/post-check: exit 1~7과 catchable signal precedence를 고정하고 retry/fallback을 금지한다. Git list/top-level/common-dir/HEAD, exact-path Workmux item과 pane cwd 중 하나라도 틀리면 success를 반환하지 않고 T9 rollback을 실행한다.
5. 통과 검증: CMD-5, CMD-6, CMD-8, CMD-9가 exit 0이어야 한다. wrapper fallback/move/AI/verifier 호출 0회, sensitive marker 0건, created/reused panes의 command 없음과 actual user-state access 0건을 함께 확인한다.
6. 실패 처리/source rollback: T10 integration/event code와 methods만 T9 상태로 복구한다. public disclosure 또는 live-action sentinel hit가 있으면 즉시 중단하고 같은 case를 실제 host state로 재시도하지 않는다.

### T11. skill 사본, OpenAI prompt와 운영 문서를 갱신한다

대상 AC: AC-39 (CMD-10 -k test_skill_body_equivalence -k test_skill_interface_contract), AC-40 (CMD-11 -k test_profile_aware_worktree_documentation)

1. 실패 검증: T11의 세 methods를 먼저 작성한다. CMD-10/CMD-11은 named profile/backend/recovery contract와 required headings가 없어 nonzero여야 한다.
2. 최소 변경—skills/prompt: agent skill은 backend plan 확인 → 승인된 apply → result/error/recovery 표시만 설명하고 독립 lookup/path/mkdir/Git/Workmux/rollback 절차를 제거한다. Claude frontmatter의 argument hint를 갱신한 뒤 본문은 agent body와 byte-identical하게 쓴다. `openai.yaml`도 동일 public interface만 안내한다.
3. 최소 변경—docs: `docs/session-account-profiles.md`에 정본의 여섯 exact headings을 각각 한 번, `docs/create-worktree.md`에 세 exact recovery headings과 no-fallback/reviewed cleanup/no automatic move-rebind 문구를 해당 절 아래 넣는다.
4. 통과 검증: CMD-10/CMD-11이 exit 0이고 frontmatter 이후 body diff 0, caller source의 backend 밖 mutation orchestration 0건이어야 한다.
5. 실패 처리/source rollback: 두 skills, prompt, 두 docs와 T11 methods를 한 묶음으로 pre-T11 bytes로 복구하고 CMD-2/CMD-8의 backend contract가 유지되는지 확인한다.

### T12. scope tests, required inventory와 final gate를 판정한다

대상 AC: AC-45 (CMD-14), AC-46 (CMD-15 -k test_issue_118_task_owned_path_allowlist -k test_no_persistent_or_external_mutation), AC-48 (docs/development/2026-09-16-118-profile-aware-create-worktree/report.md)

1. 실패 검증: 두 scope methods가 없는 상태에서 CMD-15를 먼저 실행해 exact selection failure를 기록한다. 이름이 비슷한 orchestrator test는 이 module의 selection을 충족하지 않아야 한다.
2. 최소 변경: `test_issue_118_task_owned_path_allowlist`는 base revision 대비 tracked/untracked 합집합에서 `tests.test_orchestrator_profiles.INITIAL_DIRTY_PREFIXES`를 유일한 면제 목록으로 사용한다. 이 prefix들은 #118 시작 전에 이미 존재했다고 baseline에 기록됐고 corrected orchestrator gate도 같은 목록을 적용하므로 두 gate의 규칙이 일치한다. 면제 뒤 changed/untracked 경로 중 File map의 15 exact files/한 prefix allowlist 밖 경로가 0건인지와 `.gitignore`가 unchanged인지 판정하며, allowlist의 모든 경로가 반드시 변경됐다는 equality는 요구하지 않는다. `test_no_persistent_or_external_mutation`은 automated trace의 git write/merge/deploy/`chezmoi apply`, actual user root/default tmux/network/provider mutation이 0건인지 판정한다. 두 methods를 `CreateWorktreeContractTests`에 작성하고 T2 manifest의 fully-qualified ID 목록에 넣은 뒤 command-table unique `-k` set과 manifest의 equality를 다시 확인한다.
3. 통과 검증—고정 순서: CMD-20 → CMD-18 → CMD-19 → CMD-28 → CMD-1~CMD-11 → CMD-16 → CMD-17 → CMD-9 재확인 → CMD-12 → CMD-13 → CMD-15 → CMD-14 순으로 실행한다. 모든 test segment는 exact N과 `testsRun=N`, five counters 0이어야 한다. 특히 `CREATE_WORKTREE_E2E_NETWORK` 없이 실행되는 CMD-13의 manifest meta-test와 full discovery도 E2E/cold-start case를 생략하지 않고 `skipped=0`으로 같은 zero-hit 결과를 내야 한다. CMD-14는 reviewer가 intended task-owned targets, profile-root precreation 0, sensitive material 0, task 밖 drift 0을 기록해야 통과한다.
4. operator handoff: terminal quality-goal workflow가 `docs/development/2026-09-16-118-profile-aware-create-worktree/report.md`의 `Deployment handoff` 절에 verified source digest와 operator가 나중에 채울 main merge/local apply/post-apply `chezmoi diff --no-pager` evidence를 둔다. 자동 구현 세션은 그 행위를 수행하지 않고 실제 evidence 전 AC-48 완료를 주장하지 않는다.
5. 실패 처리/source rollback: 실패를 처음 도입한 태스크의 task-owned files만 pre-task snapshot으로 복구하고 그 태스크부터 downstream gates를 재실행한다. T3 gate가 원인이면 두 tests files만 pre-T3 bytes로 복구하고 downstream을 중단한다. 승인 문서와 실제 user state는 source rollback 대상이 아니다.

## Verification commands

모든 command는 repository root에서 실행한다. CMD-12/CMD-13은 T3 전 baseline red이므로 중간 실행하지 않는다. CMD-1~CMD-20의 command string은 확정 Spec과 동일하다.

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_cli_contract -k test_session_profile_independence -k test_profile_inference` | 명명 module에서 세 ID가 각각 정확히 선택되어 N=3, `testsRun=3`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 입력 문법·session/profile case가 통과한다. |
| CMD-2 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_workspace_profile_schema -k test_profile_enum_from_registry -k test_canonical_repository_mapping -k test_registry_mixed_deployment -k test_unknown_fields_rejected -k test_provider_bindings -k test_single_codex_binding` | 명명 module에서 일곱 ID가 각각 정확히 선택되어 N=7, `testsRun=7`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 schema·mapping·binding case가 통과한다. |
| CMD-3 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_realpath_component_containment -k test_symlink_escape_and_prefix_confusion -k test_lazy_parent_creation -k test_validation_precedes_mkdir -k test_no_chezmoi_profile_root_creation` | 명명 module에서 다섯 ID가 각각 정확히 선택되어 N=5, `testsRun=5`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 path·lazy creation·scanner fixture가 통과한다. |
| CMD-4 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_branch_profile_destinations -k test_pr_forms_and_head_oid -k test_real_workmux_dry_run_merge -k test_session_selection_and_open_outside_configured_dir` | 명명 module에서 네 ID가 각각 정확히 선택되어 N=4, `testsRun=4`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 branch/PR/session 및 real Workmux read-only case가 mutation 없이 통과한다. |
| CMD-5 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_wrapper_destination_contract -k test_wrapper_failure_and_permissions -k test_wrapper_unsupported -k test_git_crypt_guard` | 명명 module에서 네 ID가 각각 정확히 선택되어 N=4, `testsRun=4`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 wrapper/git-crypt 분기가 fallback이나 issue/PR 생성 없이 통과한다. |
| CMD-6 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_same_profile_reuse -k test_cross_profile_existing_worktree_blocked -k test_binding_adapter_atomic_or_unavailable -k test_cross_profile_move_is_out_of_scope` | 명명 module에서 네 ID가 각각 정확히 선택되어 N=4, `testsRun=4`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 reuse·binding·no-move case가 통과한다. |
| CMD-7 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_toctou_symlink_swap -k test_prestate_ownership_journal -k test_parent_creation_rollback -k test_worktree_and_branch_rollback -k test_tmux_failure_rollback -k test_preexisting_artifacts_never_removed -k test_rollback_incomplete_reporting -k test_repository_lock_and_external_race -k test_adapter_registered_then_failed_before_handle_lookup` | 명명 module에서 아홉 ID가 각각 정확히 선택되어 N=9, `testsRun=9`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 rollback/TOCTOU 및 adapter 조회 전 실패의 진단·소유권·remaining 보고가 통과한다. |
| CMD-8 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_single_backend_contract -k test_shared_registry_path_module_identity -k test_plan_apply_json_contract -k test_plan_precedes_mutation -k test_exit_status_contract -k test_internal_exception_and_signal_contract -k test_creation_requires_no_verifier -k test_public_output_allowlist -k test_sensitive_output_and_metadata_hygiene -k test_verifier_defect_does_not_block_creation` | 명명 module에서 열 ID가 각각 정확히 선택되어 N=10, `testsRun=10`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 backend/shared parser·public contract·no-verifier case가 통과한다. |
| CMD-9 | `CREATE_WORKTREE_E2E_NETWORK=deny /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_canonical_linked_worktree_layout -k test_workmux_global_config_preserved -k test_post_create_verification -k test_no_automatic_ai_or_server -k test_high_risk_e2e_isolation` | 명명 module에서 다섯 ID가 각각 정확히 선택되어 N=5, `testsRun=5`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 deny 강화 sentinel 아래 high-risk E2E가 actual state/network/provider 접근 없이 통과한다. |
| CMD-10 | `diff -u <(awk 'BEGIN { n=0 } /^---$/ { n++; if (n == 2) { show=1; next } } show' dot_agents/skills/create-worktree/SKILL.md) <(awk 'BEGIN { n=0 } /^---$/ { n++; if (n == 2) { show=1; next } } show' dot_claude/skills/create-worktree/SKILL.md) && /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_skill_body_equivalence -k test_skill_interface_contract` | body diff가 0이고 명명 module의 두 ID가 각각 정확히 선택되어 N=2, `testsRun=2`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이다. |
| CMD-11 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_profile_aware_worktree_documentation` | 명명 module에서 ID 하나가 정확히 선택되어 N=1, `testsRun=1`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 두 운영 문서 계약이 통과한다. |
| CMD-12 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_ai_session --all --min-count 19 && /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_orchestrator_profiles --all --min-count 78 && AI_SESSION_CLI_PROBE_MODE=help-only /opt/homebrew/bin/python3 tests/check_installed_orchestrator_cli_contract.py` | R10.5 정정 뒤 각 명명 module의 수집 N이 각각 19·78 이상이고 `testsRun=N`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이며 help-only checker도 exit 0이다. |
| CMD-13 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree --id tests.test_create_worktree.CreateWorktreeInventoryTests.test_required_create_worktree_inventory_is_complete_and_unskipped --expect-count 1 && /opt/homebrew/bin/python3 tests/run_unittest_contract.py --discover-root tests --pattern 'test_*.py' --min-count 98 && git diff --check` | meta-test direct ID가 N=1, `testsRun=1`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0으로 실행되고 manifest 전체도 같은 조건을 만족한다. 정정 후 full discovery의 수집 N은 98 이상, `testsRun=N`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이며 whitespace 검사도 exit 0이다. |
| CMD-14 | `chezmoi diff --no-pager` | test module은 없음(N=0)이다. command가 exit 0이고 reviewer가 task-owned target의 의도한 diff만 있으며 profile root 선생성, 민감 material과 task 밖 drift가 없음을 기록해야 한다. |
| CMD-15 | `git diff --exit-code 72ad4f24e9df5919773cb877de01007f641ae163 -- .gitignore && /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_issue_118_task_owned_path_allowlist -k test_no_persistent_or_external_mutation` | `.gitignore` diff가 0이고 명명 module의 고유 두 ID가 각각 정확히 선택되어 N=2, `testsRun=2`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이며 R10.2 allowlist 밖 변경과 external mutation이 0건이다. |
| CMD-16 | `CREATE_WORKTREE_E2E_NETWORK=deny /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_cold_start_missing_profile_and_repository_parent -k test_wrapper_cold_start_contract` | 명명 module의 두 ID가 각각 정확히 선택되어 N=2, `testsRun=2`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 deny 강화 sentinel 아래 cold-start Workmux/wrapper lifecycle이 통과한다. |
| CMD-17 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_runtime_lock_journal_contract -k test_stale_transaction_requires_reviewed_recovery` | 명명 module의 두 ID가 각각 정확히 선택되어 N=2, `testsRun=2`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 runtime lock/journal lifecycle과 stale refusal가 통과한다. |
| CMD-18 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree --id tests.test_create_worktree.CreateWorktreeInventoryTests.test_judgement_command_selection_contract --expect-count 1` | `-k`에 의존하지 않는 direct ID가 정확히 존재해 N=1, `testsRun=1`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 empty·partial·duplicate·skip 계열 synthetic runner fixture는 모두 거부된다. |
| CMD-19 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_orchestrator_profiles --id tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_changed_path_allowlist --id tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_file_ownership --id tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_portable_cli_contract --expect-count 3` | R10.5의 tests-only 정정 뒤 세 direct ID가 정확히 존재해 N=3, `testsRun=3`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 stale base·missing evidence·#118 산출물 금지 조건이 제거된다. |
| CMD-20 | `tmpdir="$(mktemp -d)" || exit 1; trap 'rm -rf "$tmpdir"' EXIT; printf '%s\n' 'import unittest' 'class KnownBad(unittest.TestCase):' '    def test_known_bad(self):' '        self.fail("synthetic failure")' > "$tmpdir/test_runner_known_bad.py" || exit 1; PYTHONPATH="$tmpdir" /opt/homebrew/bin/python3 -c 'import test_runner_known_bad' || exit 1; PYTHONPATH="$tmpdir" /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module test_runner_known_bad --all --min-count 1 >/dev/null 2>&1; runner_status=$?; test "$runner_status" -ne 0` | temp known-bad module의 import가 먼저 exit 0이고, runner 출력·counter와 독립적으로 외부 shell이 포착한 runner process 종료 코드가 nonzero이며 unconditional-zero runner에서는 마지막 `test`가 nonzero다. trap cleanup도 실행된다. |
| CMD-21 | `tmpdir="$(mktemp -d)" || exit 1; trap 'rm -rf "$tmpdir"' EXIT; printf '%s\n' 'import unittest' 'class KnownGood(unittest.TestCase):' '    def test_known_good(self):' '        self.assertTrue(True)' > "$tmpdir/test_runner_known_good.py" || exit 1; PYTHONPATH="$tmpdir" /opt/homebrew/bin/python3 -c 'import test_runner_known_good' || exit 1; PYTHONPATH="$tmpdir" /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module test_runner_known_good --all --min-count 1` | runner file이 실제로 존재하고 import 가능한 known-good module에서 N=1, `testsRun=1`, five counters 0, process exit 0이며 temp fixture가 제거된다. |
| CMD-22 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_ai_session --all --min-count 19` | `tests.test_ai_session`의 수집 N≥19, `testsRun=N`, five counters 0으로 parser extraction과 기존 CLI regression이 모두 실행된다. |
| CMD-23 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_realpath_component_containment -k test_symlink_escape_and_prefix_confusion -k test_no_chezmoi_profile_root_creation` | 명명 module의 세 ID가 정확히 선택되어 path containment와 source/render precreation scanner가 통과한다. |
| CMD-24 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_single_backend_contract -k test_shared_registry_path_module_identity -k test_creation_requires_no_verifier -k test_verifier_defect_does_not_block_creation` | 명명 module의 네 ID가 정확히 선택되어 backend/shared module identity와 mutation-free no-verifier plan이 통과한다. |
| CMD-25 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_real_workmux_dry_run_merge` | 명명 module의 한 ID가 정확히 선택되어 isolated real Workmux dry-run merge와 no-mutation이 통과한다. |
| CMD-26 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_prestate_ownership_journal` | 명명 module의 한 ID가 정확히 선택되어 first-mutation 전 durable pre-state journal이 통과한다. |
| CMD-27 | `CREATE_WORKTREE_E2E_NETWORK=deny /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_canonical_linked_worktree_layout -k test_workmux_global_config_preserved -k test_no_automatic_ai_or_server -k test_high_risk_e2e_isolation` | 명명 module의 네 ID가 정확히 선택되어 deny 강화 sentinel 아래 happy-path isolated E2E와 global config/no-auto-run/isolation이 통과한다. |
| CMD-28 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_ai_session --all --min-count 22` | `tests.test_ai_session`의 수집 N≥22, `testsRun=N`, five counters 0으로 기존 19건과 T4가 추가한 세 회귀 case의 존재 및 실행을 함께 구속한다. 정본 CMD-12 문자열은 변경하지 않는다. |

## Rollout and rollback

1. 구현 시작 전에 base revision, task-owned files/prefix, existing dirty/untracked path와 content digest를 read-only로 캡처한다. T1 runner와 T2 guard를 먼저 만들고 T3 CMD-19를 통과시킨 뒤에만 product source를 수정한다.
2. source rollout 순서는 tests-only gate correction → loader/shared semantics와 temporary corpus → mutation-free backend plan → shipped schema data와 dry-run adapters → runtime transaction/apply/rollback → shipped skills/docs다. mixed deployment에서 old parser/new registry는 unknown field로 중단하고 new parser/old registry는 launcher를 유지하되 create만 차단한다.
3. task 실패 시 source rollback은 pre-task byte snapshot을 사용한다. existing file은 그 bytes로 복원하고 해당 task가 새로 만든 file만 제거한다. `git reset`, `git checkout`, `git clean`으로 사용자 변경을 덮지 않는다. 복구 후 CMD-19와 해당 targeted command를 다시 실행한다.
4. runtime transaction rollback은 T9의 journal 소유 identity에만 적용한다. window → Workmux pair/config delta → worktree/admin entry → matching-OID branch → empty directory 역순이며 dirty/non-empty/identity drift/diagnostic-only artifact를 force하지 않는다. source rollback로 이미 성공한 user worktree를 이동·삭제하지 않는다.
5. rollback trigger는 command nonzero, task allowlist 이탈, mixed compatibility regression, public disclosure, live-action sentinel hit, pre-existing bytes drift, profile root 선생성, `destination_basename`/`workmux_handle` 혼동이다. trigger 뒤 새 apply를 중지하고 remaining runtime inventory를 reviewed recovery와 분리해 기록한다.
6. final gates와 CMD-14 human review가 끝난 뒤에도 main merge와 `chezmoi apply`는 자동화 밖의 operator action이다. 적용 실패 시 이전 reviewed source bytes로 source rollback하고 full gates와 diff review를 다시 수행한다. 이미 존재하는 binding/schema row 제거 전 reference 0을 별도로 확인한다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T5 | `CMD-1 -k test_cli_contract` | 허용 input만 수락하고 잘못된 positional/option은 exit 2와 mutation 0건이다. |
| AC-2 | T5 | `CMD-1 -k test_session_profile_independence` | session과 profile 결정이 독립이며 destination/binding 차이가 registry대로다. |
| AC-3 | T5 | `CMD-1 -k test_profile_inference` | unique real-root 안에서만 생략 추론하고 나머지는 명시 요구와 mutation 0건이다. |
| AC-4 | T8 | `CMD-4 -k test_branch_profile_destinations` | arbitrary registry profile root 아래 branch destination을 계획·생성한다. |
| AC-5 | T8 | `CMD-4 -k test_pr_forms_and_head_oid` | 세 PR form이 같은 number/OID/destination을 만들고 HEAD가 head OID와 같다. |
| AC-6 | T4 | `CMD-2 -k test_workspace_profile_schema -k test_profile_enum_from_registry` | profile exact schema, unique/non-overlap와 registry-derived enum이 통과한다. |
| AC-7 | T4 | `CMD-2 -k test_canonical_repository_mapping` | canonical mapping/common-dir/safe subdir가 검증된다. |
| AC-8 | T4 | `CMD-2 -k test_registry_mixed_deployment -k test_unknown_fields_rejected` | mixed deployment가 launch-compatible/fail-closed 결과를 내고 unknown field를 거부한다. |
| AC-9 | T6 | `CMD-2 -k test_provider_bindings -k test_single_codex_binding` | shipped provider/account/scope coherence와 single Codex binding이 통과한다. |
| AC-10 | T5 | `CMD-3 -k test_realpath_component_containment -k test_symlink_escape_and_prefix_confusion` | component containment가 relative/traversal/prefix/symlink/collision을 막는다. |
| AC-11 | T9 | `CMD-7 -k test_toctou_symlink_swap` | validation/mkdir 뒤 symlink swap이 fail closed하고 owned artifact만 rollback된다. |
| AC-12 | T8 | `CMD-3 -k test_lazy_parent_creation -k test_validation_precedes_mkdir` | 모든 검증/dry-run 뒤 exact missing parent만 명시 생성한다. |
| AC-13 | T5 | `CMD-3 -k test_no_chezmoi_profile_root_creation` | complete source/render set의 positive/negative precreation scanner가 정확하다. |
| AC-14 | T8 | `CMD-9 -k test_canonical_linked_worktree_layout` | dry-run basename의 linked worktree만 canonical common-dir를 공유한다. |
| AC-15 | T5 | `CMD-8 -k test_single_backend_contract` | 모든 caller가 public backend로 수렴하고 밖의 mutation orchestration이 0건이다. |
| AC-16 | T10 | `CMD-8 -k test_plan_apply_json_contract -k test_plan_precedes_mutation` | plan/result fields와 identifier 노출 시점, plan-before-first-mutation이 정확하다. |
| AC-17 | T10 | `CMD-8 -k test_exit_status_contract -k test_internal_exception_and_signal_contract` | exit 1~7, signal/rollback precedence와 one-line redaction이 고정된다. |
| AC-18 | T10 | `CMD-8 -k test_creation_requires_no_verifier` | plan과 actual apply의 launcher/verifier/login/usage/enrollment/AI call이 0회다. |
| AC-19 | T6 | `CMD-4 -k test_real_workmux_dry_run_merge` | literal parent dirname이 dry-run parent와 같고 optional Handle은 비권위다. |
| AC-20 | T8 | `CMD-9 -k test_workmux_global_config_preserved` | isolated apply가 global layout/base/naming/hooks/font/status를 보존한다. |
| AC-21 | T10 | `CMD-5 -k test_wrapper_destination_contract -k test_wrapper_failure_and_permissions` | capable wrapper만 exact destination을 만들고 handle은 exact-path lookup에서 얻는다. |
| AC-22 | T10 | `CMD-5 -k test_wrapper_unsupported -k test_git_crypt_guard` | unsupported/non-executable/git-crypt case가 fallback 없이 fail closed한다. |
| AC-23 | T8 | `CMD-4 -k test_session_selection_and_open_outside_configured_dir` | exact session priority와 handle-keyed state/open-outside behavior가 유지된다. |
| AC-24 | T10 | `CMD-9 -k test_post_create_verification` | Git/HEAD/common-dir/pane/exact-path handle mismatch는 success하지 않는다. |
| AC-25 | T10 | `CMD-6 -k test_same_profile_reuse` | same-profile reuse가 pre-mutation handle을 얻고 branch/worktree를 만들지 않는다. |
| AC-26 | T10 | `CMD-6 -k test_cross_profile_existing_worktree_blocked` | 다른 profile/main/scope 밖은 exit 4와 move/duplicate/window mutation 0건이다. |
| AC-27 | T10 | `CMD-6 -k test_binding_adapter_atomic_or_unavailable` | available adapter는 atomic 등록하고 unavailable은 persistent state 0건이다. |
| AC-28 | T10 | `CMD-6 -k test_cross_profile_move_is_out_of_scope` | #111 안내만 하고 move/rebind command는 0회다. |
| AC-29 | T7 | `CMD-7 -k test_prestate_ownership_journal` | lock 직후 exact pre-state와 path/handle pair를 durable journal에 기록한다. |
| AC-30 | T9 | `CMD-7 -k test_parent_creation_rollback` | P3 intermediate를 포함한 owned empty components만 역순 제거한다. |
| AC-31 | T9 | `CMD-7 -k test_worktree_and_branch_rollback` | owned worktree/admin entry와 matching-OID branch만 제거한다. |
| AC-32 | T9 | `CMD-7 -k test_tmux_failure_rollback` | exact new window부터 역순 정리하고 pre-existing window ID를 보존한다. |
| AC-33 | T9 | `CMD-7 -k test_preexisting_artifacts_never_removed` | pre-existing/concurrent artifact identity와 bytes가 동일하다. |
| AC-34 | T9 | `CMD-7 -k test_rollback_incomplete_reporting` | unsafe remaining은 force 없이 exit 7과 stable inventory로 보고된다. |
| AC-35 | T9 | `CMD-7 -k test_repository_lock_and_external_race` | same-repository apply가 직렬화되고 external swap은 fail closed한다. |
| AC-36 | T10 | `CMD-8 -k test_public_output_allowlist` | event별 exact allowlist와 handle/recovery field 노출 시점이 고정된다. |
| AC-37 | T10 | `CMD-8 -k test_sensitive_output_and_metadata_hygiene` | public/fixture/Git/tmux surface의 sensitive marker가 0건이다. |
| AC-38 | T10 | `CMD-9 -k test_no_automatic_ai_or_server` | created/reused pane은 빈 shell이며 provider/agent/server call은 0회다. |
| AC-39 | T11 | `CMD-10` | 두 skill body diff가 0이고 skill/OpenAI contract가 통과한다. |
| AC-40 | T11 | `CMD-11 -k test_profile_aware_worktree_documentation` | 두 운영 문서의 exact heading/phrase와 recovery contract가 통과한다. |
| AC-41 | T10 | `CMD-9 -k test_high_risk_e2e_isolation` | temp roots/isolated socket만 관찰하고 actual user-state access가 0건이다. |
| AC-42 | T2 | `CMD-13 tests.test_create_worktree.CreateWorktreeInventoryTests.test_required_create_worktree_inventory_is_complete_and_unskipped` | 60-ID manifest가 exact discovery와 실제 실행에서 missing/duplicate/skip 없이 통과한다. |
| AC-43 | T3 | `CMD-12` | corrected gate 뒤 ai-session N≥19, orchestrator N≥78과 help-only checker가 통과한다. |
| AC-44 | T3 | `CMD-13` | discovery N≥98, `testsRun=N`, five counters 0과 whitespace gate가 통과한다. |
| AC-45 | T12 | `CMD-14` | reviewer가 intended task-owned diff와 precreation/sensitive/drift 0을 기록한다. |
| AC-46 | T12 | `CMD-15 -k test_issue_118_task_owned_path_allowlist -k test_no_persistent_or_external_mutation` | `.gitignore`와 task 밖 paths가 unchanged이고 automated external mutation이 0건이다. |
| AC-47 | T10 | `CMD-8 -k test_verifier_defect_does_not_block_creation` | verifier defect와 무관하게 plan/apply가 verifier call 없이 통과한다. |
| AC-48 | T12 | `docs/development/2026-09-16-118-profile-aware-create-worktree/report.md` | `Deployment handoff`에 operator merge/apply/post-diff evidence가 기록된다. |
| AC-49 | T9 | `CMD-16 -k test_cold_start_missing_profile_and_repository_parent -k test_wrapper_cold_start_contract` | missing-root dry-run, parent-first apply와 owned empty rollback이 통과한다. |
| AC-50 | T9 | `CMD-17 -k test_runtime_lock_journal_contract -k test_stale_transaction_requires_reviewed_recovery` | runtime path/mode/schema/direct lookup, lifetime, cleanup과 stale refusal가 정확하다. |
| AC-51 | T5 | `CMD-8 -k test_shared_registry_path_module_identity` | 두 entrypoint가 expected libexec path/API/corpus를 공유하고 duplicate semantic 구현이 0건이다. |
| AC-52 | T2 | `CMD-18 tests.test_create_worktree.CreateWorktreeInventoryTests.test_judgement_command_selection_contract` | every `-k`/manifest mapping과 runner negative/positive fixtures가 direct ID 한 건으로 통과한다. |
| AC-53 | T3 | `CMD-19 tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_changed_path_allowlist tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_file_ownership tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_portable_cli_contract` | two-file gate correction과 세 existing direct ID가 N=3/counter 0으로 통과한다. |
| AC-54 | T9 | `CMD-7 -k test_adapter_registered_then_failed_before_handle_lookup` | diagnostic list는 한 번 실행되며 unproven entry는 제거 없이 remaining으로 보고된다. |
| AC-55 | T1 | `CMD-20` | external shell이 known-bad runner process의 nonzero OS exit를 직접 확인한다. |

<!-- strict-only:start -->

### Threat and trust boundaries

- 신뢰 입력은 reviewed registry bytes, canonical Git metadata, backend/shared module code와 validated adapter capability다. 사용자 branch/PR/profile/session, filesystem names/symlinks, gh/Workmux/wrapper/tmux/binding output은 검증 전 untrusted다.
- CMD-2/CMD-3/CMD-4/CMD-5는 unknown field, repository spoofing, traversal/prefix/symlink, forged dry-run parent/basename과 unsupported wrapper가 mutation boundary를 넘지 못함을 증명한다.
- CMD-7/CMD-16/CMD-17은 pre-state→mutation→rollback 경계를 검사한다. successful exact identity delta만 소유권을 부여하고 diagnostic read는 소유로 승격하지 않는다.
- CMD-8은 external command→public JSON 경계에서 raw payload/traceback/sensitive field를 차단하고 `destination_basename`과 `workmux_handle`의 출처를 분리한다.
- CMD-9는 temporary Git/root와 isolated socket에서 resolver→filesystem/backend→tmux 경계를 검사하며 live-action sentinel hit가 0이어야 한다.

### Authorization and tenant isolation

원격 tenant authorization은 해당 없음이다. provider tenant/credential을 조회하지 않는 local linked-worktree 생성이기 때문이다. workspace profile은 policy isolation boundary로 검증한다.

- 허용 case: CMD-4의 branch/PR methods가 두 arbitrary fixture profile의 각 root 아래 destination과 provider binding을 만들고 반대 profile bytes가 섞이지 않음을 확인한다.
- 허용 case: CMD-1의 `test_profile_inference`가 real cwd가 정확히 한 root 안일 때만 profile을 추론한다.
- 거부 case: CMD-2가 unknown/ambiguous/disabled/provider mismatch/scope violation을 exit 3/4와 mutation 0건으로 차단한다.
- 거부 case: CMD-3이 sibling prefix, traversal, symlink escape와 collision을 component containment로 차단한다.
- 거부 case: CMD-6의 `test_cross_profile_existing_worktree_blocked`가 다른 profile/main/scope 밖 worktree에 exit 4와 move/reuse/window mutation 0건을 확인한다.

### Migration, compatibility, and rollback

- rollout은 runner/manifest → #103 tests-only gate → shared module/loader → mutation-free backend plan → shipped schema data/dry-run adapters → runtime apply/rollback → shipped skills/docs 순이다. 각 targeted gate가 통과하기 전 next layer를 active contract으로 취급하지 않는다.
- old parser/new registry는 unknown field를 거부하고 new parser/old registry는 launcher를 유지하되 create만 차단한다. 기존 `workspace_directory_mappings`와 launcher current-cwd 의미는 유지한다.
- source rollback은 실패 태스크의 task-owned bytes만 pre-task snapshot으로 복구한다. runtime rollback은 journal-owned artifact만 역순 처리하며 두 rollback을 혼합하지 않는다.
- 이미 성공해 사용 중인 worktree/process는 source rollback로 이동·삭제·rebind하지 않는다. main merge/local apply는 operator-only다.

### Failure recovery and observability

- one-line JSON의 status, phase, created/reused/rolled_back, `rollback_remaining`, recovery ID/enum reason이 관측 신호다. raw subprocess output, traceback, raw runtime identity는 관측 surface가 아니다.
- exit 1은 redacted internal defect, exit 5는 preflight/stale reviewed recovery, exit 6은 complete rollback을 동반한 operation failure, exit 7은 force하지 않은 remaining inventory다. catchable signal은 complete rollback 때 128+signal, incomplete 때 exit 7이다.
- CMD-7은 parent/worktree/branch/window fault와 diagnostic-before-handle fault를, CMD-17은 lock→journal direct lookup/crash/stale을, CMD-16은 cold-start parent ownership을 증명한다.
- automatic retry/fallback은 없다. exit 7 또는 stale transaction 뒤에는 operator가 stable inventory를 reviewed recovery한 뒤 새 plan부터 실행한다.

### High-risk end-to-end verification

필수 gate는 CMD-9의 exact command다. exit 0 evidence에는 arbitrary two-profile branch/PR creation, canonical common-dir/HEAD, exact path→handle, pane cwd, global config preservation, empty panes와 actual user/default-tmux/network/provider access 0회가 포함돼야 한다. CMD-16은 P1/P2/P3 cold-start, CMD-7은 TOCTOU/owner-only rollback, CMD-17은 runtime stale/corruption을 추가로 검증한다. 어느 case도 skipped/expected failure면 통과하지 않는다.

### No production mutation confirmation

자동 workflow의 production mutation은 0건이다. 모든 Git/worktree/tmux mutation test는 temporary repository와 isolated socket/shim에서만 수행하고 real Workmux는 `--dry-run`만 사용한다. 실제 user worktree, 인증 상태/home, default tmux, network/provider, merge/deploy/`chezmoi apply`는 automated trace에서 접근·실행 0회여야 한다. main merge와 local apply 및 사후 diff 확인은 모든 gate 후 별도 operator action이다.

<!-- strict-only:end -->
