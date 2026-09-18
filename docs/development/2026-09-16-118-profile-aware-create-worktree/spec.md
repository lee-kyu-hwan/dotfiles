# Quality Goal Specification

- Task ID: 118-profile-aware-create-worktree
- Mode: strict
- Status: SPEC_REVIEW
- Created: 2026-09-16
- Updated: 2026-09-16
- Source goal: GitHub issue #118의 create-worktree가 registry 기반 workspace profile별 목적지를 검증·지연 생성하고 provider별 account binding과 독립적인 tmux 배치를 보장한다.

## Problem and context

현재 `create-worktree` 스킬은 브랜치 또는 PR과 선택적 tmux 세션을 받아 Workmux로 linked worktree와 window를 만들지만, workspace profile을 입력받거나 목적지를 profile root 아래로 강제하는 실행 backend가 없다. 두 스킬 사본은 Claude 전용 frontmatter를 제외하면 같은 본문을 유지해야 하고, `dot_agents/skills/create-worktree/agents/openai.yaml`도 같은 사용자 계약을 안내해야 한다.

배포 registry에는 active account 세 개와 provider별 `workspace_directory_mappings` 세 개가 있으나 workspace profile 이름이나 canonical repository를 선언하는 필드는 없다. `dot_local/bin/executable_ai-session:34-54`의 strict field allowlist와 `:192-195`의 unknown-field 거부 때문에 schema를 명시적으로 확장하지 않고는 profile 필드를 추가할 수 없다. 현재 path 포함 판정은 `:591-597`의 `Path.relative_to` 기반이고, strict 선택은 `:733-842`에서 current real directory mapping과 account scope를 재대조한다. 이 component의 안전 성질은 재사용해야 한다.

반면 기존 `ai-session select`는 strict registry에서 `os.getcwd()`를 실제 경로로 확정하고, 전달한 `--directory`가 그 cwd와 다르면 `blocked_binding`으로 끝난다(`dot_local/bin/executable_ai-session:1329-1366`). 아직 존재하지 않는 목적지를 선택하기 위해 그 CLI를 호출하는 것은 불가능하다. worktree 목적지 계산은 current-cwd account selection과 분리된 순수 resolver가 필요하다.

설치된 Workmux 0.1.248의 help에는 `--path`가 없고 `add --config`, `add --dry-run`, `open --config`가 있다. 2026-09-16 read-only probe에서 source global config와 `worktree_dir: ~/code/profile2/{project}`만 든 invocation config를 병합한 `workmux add ... --dry-run`은 `~/code/profile2/dotfiles/118-spec-dry-run-probe`, base `main`, Nerd Font target을 출력했다. 로그는 global config와 invocation config 양쪽을 읽었다고 기록했다. 따라서 `{project}`가 main worktree 디렉터리명으로 치환되고 global `base_branch: auto`와 `nerdfont: true`가 유지됨은 실측됐다. dry-run은 pane 수와 `status_format`을 출력하지 않으므로 그 둘과 hook 보존은 격리 tmux 통합 테스트로 별도 증명해야 한다. source global config의 세 pane, `status_format: false`, `base_branch: auto`, `nerdfont: true`는 `dot_config/workmux/config.yaml:12-34`에 있다.

오케스트레이터의 2026-09-16 격리 실측(`.claude/quality-state/20260916T003638Z-118-create-worktree에서-workspace-profile별-1ea3c575/coldstart-probe-evidence.md`)은 cold-start 순서와 소유권 경계를 추가로 확정한다. P1에서 profile root와 repository parent가 모두 없는 `worktree_dir`을 준 Workmux 0.1.248 dry-run이 정확한 목적지를 출력하고 directory·branch·worktree를 만들지 않았으며 `{project}`는 main worktree 디렉터리명으로 치환됐다. P2에서는 `git worktree add`가 없는 상위 component 전체를 암묵 생성했으므로 backend가 검증·dry-run 뒤 parent를 먼저 명시적으로 만들고 journal에 기록해야 한다. P3에서는 `git worktree remove`가 worktree만 지우고 중간 빈 directory를 남겼으므로 rollback이 journal 소유 component를 역순 제거해야 한다. wrapper의 missing-parent `--dry-run`은 이 실측 대상이 아니며 repository별 구현이 충족해야 하는 capability 계약으로 남긴다.

두 번째 격리 실측(`.claude/quality-state/20260916T003638Z-118-create-worktree에서-workspace-profile별-1ea3c575/handle-probe-evidence.md`)은 식별자와 리터럴 override 계약을 확정한다. Q1에서 `{project}` 없는 리터럴 절대경로 `worktree_dir`의 dry-run 목적지 dirname은 override 값과 byte-identical이었고 아무것도 생성되지 않았다. Q2에서 `--name`을 주면 dry-run에 `Handle:` 줄이 나타났지만 기본 명명에는 없었으므로 이 값은 조건부 참고 값일 뿐이다. Q3의 `worktree_prefix`는 목적지 basename 자체를 바꿨고 `worktree_naming`은 `full` 또는 `basename`이다. Q4의 실제 read-only `workmux list --json` 항목 key는 `agent_statuses`, `branch`, `created_at`, `handle`, `has_uncommitted_changes`, `is_main`, `is_open`, `mode`, `path`, `project`, `project_path`였고 `path`와 `handle`을 함께 제공했으므로 정확한 실제 worktree 경로로 항목을 매칭해 registry handle을 얻을 수 있다. 관측에서는 두 값이 같았지만 이는 불변식이 아니며, 기존 skill의 PR `--target-name` 계약처럼 창 이름도 handle과 구조적으로 갈라질 수 있다.

이 저장소에는 `scripts/create-worktree.sh`가 없고 git-crypt smudge 설정도 비어 있으므로 일반 Workmux 경로가 현재 저장소의 실행 경로다. 다만 스킬은 저장소 중립이므로 wrapper, 실행 권한, git-crypt 보호 계약을 보존해야 한다. 또한 `dot_local/libexec/executable_ai-session-verify-claude:50-78`의 현재 verifier 계약은 설치된 Claude Code 2.1.273의 공식 JSON 이름과 맞지 않고 `usage_unknown`이 launch를 차단한다. 이 결함은 별도 follow-up이며 worktree 생성은 account alias만 해석하고 login/usage verifier나 AI process를 실행하지 않아야 한다.

구현 전 독립 baseline 실측(`.claude/quality-state/20260916T003638Z-118-create-worktree에서-workspace-profile별-1ea3c575/baseline-suite-evidence.md`)에서 base revision `72ad4f24e9df5919773cb877de01007f641ae163`의 suite는 97 tests 중 3 failures였다. 실패는 모두 `tests/test_orchestrator_profiles.py`의 #103 전용 gate인 `test_changed_path_allowlist`, `test_file_ownership`, `test_portable_cli_contract`였다. `BASE_REVISION`이 오래된 revision을 가리키고, file ownership과 installed CLI checker가 main에 존재하지 않는 #103 미커밋 evidence 파일을 요구하기 때문이다.

같은 gate는 #118 산출물도 구조적으로 금지한다. `PRESERVED_PATHS`는 `dot_claude/skills/create-worktree`의 diff 0을 요구해 R9.1의 두 skill 본문 변경과 충돌하고, `T15_ALLOWED_FILES`/`T15_ALLOWED_PREFIXES`에는 신규 backend·공유 module·`tests/test_create_worktree.py`·두 skill 경로·운영 문서·이번 task 문서 디렉터리가 없다. 사용자는 2026-09-16에 이 선행 결함 정정을 #118 범위에 포함하되 gate 정정 자체의 변경은 `tests/test_orchestrator_profiles.py`와 `tests/check_installed_orchestrator_cli_contract.py` 두 `tests/` 경로로 한정하고 다른 저장소 동작은 바꾸지 않기로 결정했다.

## Goals

- `$create-worktree <branch-name|pr-ref> [target-session] --workspace-profile <name>` 호출이 registry의 profile, canonical repository와 provider별 binding을 통해 `~/code/<workspace-profile>/<repo>/<task>`를 계산하게 한다.
- target session과 workspace profile을 독립적으로 결정하고, profile 생략은 current real path가 정확히 한 profile root 아래일 때만 허용한다.
- profile·repository·scope·realpath 검증을 모두 마친 뒤 선택한 task의 정확한 parent만 지연 생성하고, 생성 직전과 직후 symlink escape를 다시 차단한다.
- 스킬, 미래 TUI와 다른 진입점이 동일한 machine-testable backend를 호출하고 자체 목적지 계산이나 `mkdir`를 갖지 않게 한다.
- Workmux global 설정과 기존 branch/PR, wrapper, git-crypt, session/window 재사용 계약을 보존하면서 invocation별 목적지를 지정한다.
- 부분 실패 때 이번 호출이 만든 directory, worktree, branch와 tmux window만 역순으로 정리하고 pre-existing state는 보존한다.
- 실제 사용자 worktree, 인증 상태나 tmux를 건드리지 않는 synthetic unit/integration/E2E로 모든 계약을 검증한다.
- #103 전용 선행 gate를 current-main 기준의 #118 task-owned 경로와 존재하는 증거만 검사하도록 `tests/` 안에서 정정해 전체 suite를 실패 0으로 복구한다.

## Non-goals

- 기존 worktree의 자동 cross-profile 이동은 하지 않는다. 이동은 #111의 별도 shutdown, handoff와 rebind 절차다.
- 실행 중 process의 account hot-swap, 사용량 기반 fallback/rotation, credential 또는 config home의 copy·rename·symlink를 하지 않는다.
- tmux 세션 이름으로 workspace profile이나 account profile을 추측하지 않는다.
- worktree 생성만으로 Claude, Codex 또는 다른 AI를 자동 실행하지 않는다.
- profile별 기준 저장소 clone을 만들지 않고 canonical repository 하나의 linked worktree만 사용한다.
- #94/#95 공통 binding registry가 없을 때 별도 임시 registry나 중복 영구 상태를 만들지 않는다.
- repository별 wrapper 구현 변경 및 그 저장소의 연계 issue/PR 생성은 이 이슈의 범위가 아니다. 이 이슈는 wrapper capability 계약, fail-closed 처리와 synthetic fixture만 제공하며 연계 작업 생성은 별도 operator follow-up이다.
- `.gitignore`를 수정하지 않는다.
- installed Claude Code 2.1.273의 공식 `loggedIn`/`authMethod`/`orgId`와 현재 verifier의 `logged_in`/`auth_kind`/`subject_id`/`tenant_id` 불일치 및 `usage_unknown` launch 차단을 이 이슈에서 고치지 않는다. 이는 별도 follow-up이며 생성 backend가 verifier를 호출하지 않는 것으로 이 이슈의 판정을 독립시킨다.
- 이 Spec 작성 라운드에서 구현, 테스트, 배포, `chezmoi apply`, 실제 tmux/worktree mutation, commit, push, merge를 수행하지 않는다.

## Requirements

### 사용자 입력과 선택

- **R1.1** 사용자 호출은 필수 `<branch-name|pr-ref>`, 선택적 `[target-session]`, 선택적 named option `--workspace-profile <name>`만 받는다. 세 번째 positional은 항상 usage 오류이며 자연어도 기존 branch/PR 및 session 2-tuple 규칙으로 환원한 뒤 profile은 named option으로만 전달한다.
- **R1.2** `target-session`은 window 표시 위치이고 `workspace-profile`은 목적지와 provider별 binding의 선택 단위다. 명시 profile이 우선하며 생략 시 current cwd를 `expanduser`와 `resolve`한 실제 경로가 정확히 한 registry profile root에 포함될 때만 그 profile을 선택한다. canonical repository처럼 모든 profile root 밖이거나 0개·2개 이상과 일치하면 생성 전에 명시를 요구하며 tmux 이름, provider default 또는 account alias로 추측하지 않는다.
- **R1.3** 기존 branch와 PR URL, `owner/repo#N`, 표지가 있는 PR 번호 해석, bare 숫자 비추정, repository 일치, closed/merged 확인, PR head branch/OID 검증, naming, session 정확 일치와 window 재사용 계약을 유지한다.

### registry schema와 canonical source

- **R2.1** strict registry에 top-level `workspace_profiles` table array를 추가하고 각 row의 허용 필드를 `name`, `root`, `provider_bindings`로 고정한다. `name`은 기존 alias 문법의 비밀 아닌 enum key, `root`는 정규화 가능한 절대 또는 home-relative directory, `provider_bindings`는 지원 provider를 key로 하고 active same-provider account alias를 value로 하는 table이다. 이름과 real root는 각각 고유해야 하며 두 root가 같거나 ancestor/descendant로 겹치면 생략 추론이 모호하므로 registry 전체를 거부한다. 허용 profile 집합은 이 table에서만 오고 구현·skill·test control flow에 profile 이름을 하드코딩하지 않는다.
- **R2.2** strict registry에 top-level `repositories` table array를 추가하고 각 row의 허용 필드를 `id`, `canonical_path`, `workspace_subdir`로 고정한다. `id`는 normalized `owner/name`, `canonical_path`는 기준 저장소의 정규화된 실제 경로, `workspace_subdir`은 separator가 없는 단일 안전 path component다. 세 값은 각각 고유하고 `.`·`..`·absolute·empty component를 거부한다. branch current repository와 PR repository는 반드시 이 mapping을 거쳐야 하며 canonical path의 Git common-dir와 현재 repository의 common-dir가 같아야 한다.
- **R2.3** 기존 `workspace_directory_mappings`는 launcher compatibility를 위해 유지하고 새 table을 그 row에 확장하지 않는다. `STRICT_REGISTRY_FIELDS`, 새 row allowlist, dataclass와 parser를 함께 갱신해 모든 unknown field를 계속 거부한다. 새 parser+옛 registry는 AI launch를 기존대로 허용하되 create backend는 `blocked_contract`; 옛 parser+새 registry는 unknown field를 fail closed한다. 새 profile binding은 active account의 provider와 allowed directory scope가 계산 목적지를 포함하는지 검사해 기존 mapping과 모순을 허용하지 않는다.
- **R2.4** shipped profile마다 Claude와 Codex binding을 명시한다. 초기 Codex binding은 모든 profile에서 같은 `codex-default`이고 Claude binding은 각 profile의 registry alias를 따른다. Claude용 다른 profile 선택이 새 Codex account/home이나 인증 복제를 요구해서는 안 되며 provider 누락·불일치·disabled account·scope 위반은 생성 전에 `blocked_contract`다.

### 경로 안전성과 지연 생성

- **R3.1** profile root, canonical path, workspace parent와 destination은 `~`, 상대 component, `..`와 symlink를 해소한 실제 absolute path로 비교하고 `Path.relative_to`와 같은 path-component containment만 사용한다. 문자열 prefix 비교를 금지하며 형제 이름, symlink root escape, canonical repository mismatch와 destination collision을 생성 전에 거부한다. 아직 없는 tail은 가장 가까운 existing ancestor의 realpath와 각 새 component를 결합해 검증한다.
- **R3.2** backend는 모든 입력, registry, repository, account scope, existing worktree, session과 Workmux/wrapper dry-run이 성공한 뒤, adapter가 출력한 destination을 다시 검증하고 나서만 그 destination의 정확한 parent chain을 아래에서 필요한 만큼 명시적으로 만든다. P1에 따라 Workmux dry-run은 profile root와 repository parent가 모두 없어도 성공하고 mutation하지 않으며, wrapper도 같은 missing-parent dry-run capability를 계약으로 제공해야 한다. P2 때문에 Git/Workmux apply가 parent를 암묵 생성하도록 맡기는 것은 금지한다. 각 `mkdir` 성공을 즉시 journal에 기록하며 profile root 전체나 다른 repository parent를 투기적으로 만들지 않는다. 검증 실패와 plan mode는 directory를 0개 만든다.
- **R3.3** chezmoi source가 관리하는 것은 profile/repository mapping 선언과 공용 backend뿐이다. 선생성 검사는 source root의 `install.sh`, `setup.sh`, 모든 `run_once_*`/`run_onchange_*`, `.chezmoiscripts/**`, 모든 `*.tmpl`의 격리 렌더 결과와 registry-derived profile root 아래로 해석되는 managed directory target을 대상으로 한다. 최소 탐지 패턴은 shell `mkdir`, `install -d`, `ensure[_-]?(dir|directory)`·`create[_-]?(dir|directory)` helper 호출, chezmoi directory target 또는 placeholder file로 parent를 만드는 지시다. comment/문서 문자열과 무관한 directory를 negative로 분류하되 각 패턴의 positive fixture를 반드시 검출하며, 어떤 대상도 registry에서 읽은 profile root를 미리 만들지 않는다.
- **R3.4** backend가 독립 계산하는 경로는 정확히 `<profile.root>/<repository.workspace_subdir>` repository parent까지다. `destination_basename`과 전체 `normalized_destination`의 유일한 권위 출처는 선택된 Workmux 또는 wrapper dry-run의 구조화된 destination 출력이다. backend는 destination basename을 branch/PR이나 Workmux naming 설정에서 재구현하지 않고, 출력의 parent가 독립 계산한 repository parent와 byte-identical real path이며 basename이 separator·`.`·`..` 없는 단일 safe component인지 검증한 뒤 `<profile.root>/<repository.workspace_subdir>/<destination_basename>`을 확정한다. `destination_basename`은 경로 component일 뿐 R5.4의 `workmux_handle`과 같은 식별자라는 불변식이 없으며, plan의 이 경로 component를 Git config의 `workmux.worktree.<workmux_handle>.*` handle key로 절대 쓰지 않는다. 마지막 task directory만 linked worktree이고 canonical repository는 하나이며 epic, tmux session/window, provider 또는 account alias는 path component가 아니다.

### 단일 backend 계약

- **R4.1** 공용 실행 진입점은 chezmoi source `dot_local/bin/executable_create-worktree`가 배포하는 `create-worktree` 단 하나다. 스킬 사본, OpenAI prompt와 미래 TUI는 이 command의 `plan|apply` interface를 호출하고 자체 profile lookup, destination 계산, `mkdir`, Git/Workmux 생성 또는 rollback을 구현하지 않는다. strict registry parse, exact field allowlist, path normalization/component containment와 account-scope coherence의 semantic 구현은 side-effect-free import-only module `dot_local/libexec/ai_session_registry.py` 정확히 하나로 추출한다. `dot_local/bin/ai_session_registry_loader.py`는 bin에서 기본 import path 밖의 libexec module을 installed/source layout 모두에서 같은 exact file로 결정·load하기 위한 유일한 import bootstrap이며 schema constant, parser, path validator, policy 또는 mutation을 구현하지 않는다. `ai-session`과 create backend는 이 loader를 통해 같은 module object/API를 import한다. launcher 책임 경계를 나타내는 `def select_strict_account`와 `def classify_verifier_payload`는 `dot_local/bin/executable_ai-session`에 정의된 채 남아 공용 module의 primitive에 위임하며, 그 위임 함수는 별도 parser 또는 path validator의 중복 정의가 아니다. executable backend 계약과 mutation orchestration은 계속 한 곳에만 둔다.
- **R4.2** backend 호출은 `create-worktree plan|apply <branch-name|pr-ref> [target-session] --registry <path> [--workspace-profile <name>]`다. `plan`은 mutation 없이 JSON line 하나를, `apply`는 같은 입력을 재해석해 동일한 `plan` JSON을 먼저 출력한 뒤 mutation하고 마지막 `result` 또는 `error` JSON을 출력한다. plan에는 repository, branch 또는 PR number/head OID, target_session, 각 provider/account_profile, selection_source, worktree_root, independently computed repository_parent, adapter dry-run에서 얻은 `destination_basename`과 `destination_basename_source=adapter_dry_run`, normalized_destination, existing_worktree, binding registration availability가 있다. 새 생성 plan에는 아직 확정할 수 없는 `workmux_handle`을 넣지 않으며, existing worktree 재사용 plan에만 R6.1의 exact-path 조회로 이미 확정한 `workmux_handle`을 넣는다. `created|reused` result에는 R5.4 또는 R6.1에서 확정한 `workmux_handle`을 필수로 넣는다.
- **R4.3** exit/status는 0=`planned|created|reused`, 1=`internal_error`, 2=`invalid_request`, 3=`blocked_contract`, 4=`blocked_binding`, 5=`preflight_failed`, 6=`operation_failed_rolled_back`, 7=`rollback_incomplete`로 고정한다. 예상하지 못한 내부 exception은 traceback이나 exception 원문 없이 단일 redacted `internal_error` JSON을 stderr에 쓰며 mutation 뒤라면 R7 rollback을 먼저 수행하고, 불완전 rollback이면 1보다 7이 우선한다. catch 가능한 `SIGHUP`·`SIGINT`·`SIGTERM`은 같은 redaction/rollback을 적용해 완전 rollback 또는 pre-mutation이면 각각 exit 129·130·143과 `interrupted`, 불완전 rollback이면 exit 7을 낸다. catch 불가능한 `SIGKILL`·`SIGSTOP`은 출력·rollback을 보장하지 않으며 durable runtime journal을 다음 reviewed recovery에 남긴다. stdout은 성공 public JSON이며 backend는 public traceback, silent fallback, retry, 기존 위치 생성 또는 오류 재분류를 하지 않는다.
- **R4.4** `plan`과 `apply`는 registry의 비밀 아닌 alias/scope만 검증하며 `ai-session launch`, provider verifier, login, usage, identity enrollment 또는 AI process를 호출하지 않는다. strict `ai-session select --directory`의 current-cwd 제약을 우회하거나 완화하지 않고 candidate destination용 순수 resolver를 사용한다.

### Workmux, wrapper와 사후 검증

- **R5.1** 일반 경로는 mode 0600 임시 regular YAML에 독립 계산한 repository parent만을 리터럴 절대경로 `worktree_dir`로 기록하고 `workmux add --config <file> --dry-run`을 먼저 실행한다. Q1 실측처럼 `{project}` 없는 repository-parent-only override의 dry-run `Worktree` destination dirname은 그 리터럴 값과 byte-identical이어야 한다. backend는 이 destination을 구조적으로 파싱해 dirname 일치와 safe `destination_basename`을 검증하고, 이 출력에서만 `destination_basename`과 `normalized_destination`을 취득한다. dry-run의 선택적 `Handle:` 줄은 있을 때만 비권위 참고 값이며 `workmux_handle`이나 Git config key로 쓰지 않는다. branch/PR 또는 naming 설정으로 어느 식별자도 재계산하거나 미리 계산한 전체 destination과 순환 비교하지 않는다. apply도 같은 config와 dry-run이 확정한 destination을 사용하고 실제 생성 경로가 다르면 rollback한다. alternate config가 global config와 병합되도록 panes, `base_branch`, naming, hooks, `nerdfont`, `status_format`을 override에 복제하지 않는다. dry-run 실패·parent mismatch는 생성 전에 중단하고 임시 파일은 모든 경로에서 제거한다. mutation 뒤 cleanup까지 실패하면 해당 임시 artifact를 R7 transaction의 remaining inventory로 다룬다.
- **R5.2** executable `scripts/create-worktree.sh`가 있는 저장소는 wrapper를 우선한다. wrapper는 기존 branch positional 계약과 함께 `--destination-parent <absolute-path>`와 `--dry-run` capability를 명시적으로 지원하고, parent가 없어도 mutation 없이 구조화된 전체 destination을 반환해야 한다. backend는 Workmux와 동일하게 반환 parent와 `destination_basename`을 검증해 이를 wrapper dry-run에서만 취득하고 apply에 그 exact destination을 전달한다. wrapper apply 뒤 `workmux open`을 거친 경우도 R5.4의 exact-path list 매칭으로만 `workmux_handle`을 취득한다. capability 없음, 실행 권한 없음, failure 또는 apply destination drift는 기존 위치를 만들지 않고 중단한다. git-crypt filter가 있으면 wrapper 없이 일반 Workmux add를 자동 사용하지 않고 기존 확인/차단 계약을 유지한다. repository별 wrapper 변경과 연계 issue/PR 생성은 별도 operator follow-up이며 backend가 자동 생성하지 않는다.
- **R5.3** target session은 명시값, 유효하고 생존한 stored window session, PR/branch mode default 순서를 유지하고 exact full name으로 검증하며 자동 생성하지 않는다. stored session을 읽거나 쓸 때의 Git config key는 오직 R5.4 또는 R6.1에서 얻은 `workmux.worktree.<workmux_handle>.window-session`이고 `destination_basename`을 그 key에 대입하지 않는다. 새 생성에는 생성 전 `workmux_handle`과 stored-session key가 없으므로 명시값 또는 mode default로 session을 선택·검증하고, 생성 후 handle을 얻은 뒤에만 session-state key를 쓴다. 재사용은 R6.1의 pre-mutation exact-path 매칭 뒤 stored 값을 읽고 최종 값을 쓴다. profile 선택과 session 선택은 서로의 입력이 아니다. 기존 worktree를 여는 `workmux open`은 invocation config를 전달해도 configured worktree directory 밖 linked worktree를 계속 열 수 있어야 한다.
- **R5.4** 새 생성과 wrapper의 `workmux open` 뒤 `git worktree list --porcelain`, worktree의 `git rev-parse --show-toplevel`, absolute `--git-common-dir`, `HEAD`, Workmux registry 항목과 격리 tmux pane cwd를 검증한다. `workmux_handle`의 유일한 권위 출처는 생성된 worktree의 정확한 normalized real path와 `path`가 일치하는 `workmux list --json`의 유일 항목에 든 `handle` 필드다. Q4 실측은 각 항목이 `path`와 `handle`을 함께 제공해 이 매칭이 구현 가능함을 보인다. 0개 또는 2개 이상 매칭, unsafe/empty handle은 추측하거나 basename으로 폴백하지 않고 post-mutation operation failure로 처리해 R7 rollback을 수행하며, complete rollback이면 `operation_failed_rolled_back`/6, incomplete이면 `rollback_incomplete`/7이다. PR은 HEAD가 조회된 head OID와 같아야 하고 branch도 요청 ref와 일치해야 하며 하나라도 다르면 성공으로 보고하지 않는다.

### 재사용과 binding

- **R6.1** 동일 branch의 existing linked worktree가 요청 profile real root와 repository parent 아래에 있으면 directory나 branch를 새로 만들지 않고 재사용한다. 재사용의 `workmux_handle`은 생성 단계가 없으므로 plan 출력과 어떤 window/config mutation보다 먼저 existing worktree의 정확한 normalized real path를 `workmux list --json`의 `path`에 매칭해 유일 항목의 `handle`에서 취득한다. 0개·복수·unsafe handle이면 basename으로 추측하지 않고 `preflight_failed`/5로 mutation 없이 끝낸다. 다른 profile root, canonical main path 또는 허용 root 밖에 있으면 실제 기존 경로와 요청 profile을 redacted public error에 표시하고 `blocked_binding`으로 중단하며 자동 이동·중복 checkout·profile hot-swap을 하지 않는다.
- **R6.2** #94/#95 공통 registry adapter가 제공되면 성공한 생성/재사용의 task ID, repository ID, workspace profile, real worktree path, tmux 위치, provider별 account alias와 positive binding generation을 adapter의 atomic contract로 등록한다. adapter가 없으면 `binding_registration=not_available`을 출력하고 별도 상태를 만들지 않는다. adapter가 있다고 선언됐으나 atomic registration이 실패하면 transaction failure로 처리한다.
- **R6.3** cross-profile move, main worktree와 submodule worktree 이동은 이 backend의 어떤 status에서도 수행하지 않는다. 오류는 #111 handoff/rebind 절차를 안내하되 그 command를 자동 호출하지 않는다.

### transaction, rollback과 TOCTOU

- **R7.1** apply는 dry-run과 destination 검증 뒤 첫 filesystem mutation 전에 R7.5 runtime root에서 canonical Git common-dir digest 단위 lock을 잡고, ancestor 존재 여부와 identity, branch ref/OID set, `git worktree list --porcelain`, `workmux list --json`의 exact `(normalized real path, workmux_handle)` pair set, tmux window ID set과 기존 `workmux.worktree.<workmux_handle>.window-session` 값을 pre-state journal로 durable하게 보존한다. 새 생성 대상의 `workmux_handle`은 이 시점에 존재한다고 가정하지 않고, 생성 뒤 R5.4 exact-path 매칭으로 얻은 pair가 pre-state에 없을 때만 호출 소유 Workmux 항목으로 기록한다. 재사용 대상은 R6.1에서 pre-state pair 자체를 매칭하므로 호출 소유로 만들지 않는다. 다른 호출 소유권도 pre-state에 없고 이 호출의 성공한 syscall/command 결과에 새로 나타난 exact identity만 인정하며 단순히 현재 empty이거나 destination 아래라는 이유로 추정하지 않는다.
- **R7.2** backend가 parent를 명시적으로 생성한 뒤에만 Git/Workmux apply를 호출한다. parent path 생성, worktree 생성, branch 생성, Workmux 항목/session-state key, tmux window 생성 또는 binding registration 단계가 실패하면 exact window ID, 생성 뒤 R5.4에서 확정해 journal에 기록한 `(path, workmux_handle)`과 그 handle key의 호출 소유 변경, worktree identity, branch ref/OID, backend-created empty directory의 역순으로 best-effort rollback한다. adapter apply가 항목을 등록했을 가능성이 있으나 정상 R5.4 조회 전에 실패하면 rollback 진입 전에 destination exact path로 `workmux list --json`을 진단 목적으로 정확히 한 번 다시 조회한다. 이 진단 조회만으로는 소유권을 부여하지 않는다. pre-state에 없고 adapter의 성공한 등록 command 결과와 진단의 exact-path 유일 항목이 함께 확인될 때만 R7.1의 호출 소유 pair로 기록하고, 성공 결과가 없거나 0개·복수·unsafe 항목으로 소유 판정이 불가능하면 제거하지 않은 채 `rollback_remaining`에 artifact type `workmux_registry_entry`와 비민감 destination path를 기록한다. plan의 `destination_basename`은 rollback 대상 선택이나 Git config key에 사용하지 않는다. 재사용 경로는 pre-existing Workmux pair와 worktree를 제거하지 않고 이번 호출이 새로 만든 window 또는 session-state 변경만 pre-state 값으로 되돌린다. P3처럼 `git worktree remove` 뒤 남은 intermediate directory도 journal에 이 호출의 생성으로 기록됐고 현재 비어 있을 때 backend가 직접 역순 제거한다. branch는 이 호출이 만들었고 OID가 journal과 같을 때만 제거하며 pre-existing directory/worktree/branch/Workmux pair/window는 절대 삭제·이름변경·이동하지 않는다.
- **R7.3** rollback 중 identity가 바뀌거나 directory가 non-empty/dirty이고 wrapper/hook 외부 side effect처럼 안전하게 되돌릴 수 없는 항목은 강제 제거하지 않는다. exit 7과 `rollback_remaining`의 public artifact type/비민감 path 또는 stable ID, 마지막 성공 phase와 수동 복구 안내를 출력한다. 모두 되돌린 원래 operation failure는 exit 6이며 rollback 자체를 성공으로 보고하지 않는다.
- **R7.4** destination의 nearest existing ancestor와 각 component를 지연 생성 직전 다시 resolve하고, 각 mkdir 직후와 worktree 생성 직후 root containment와 symlink 여부를 재검사한다. lock을 유지해 같은 backend의 경쟁 호출을 직렬화하되 외부 process가 검증과 생성 사이 path를 교체할 수 있는 TOCTOU를 가정한다. descriptor-relative/no-follow가 가능한 단계는 사용하고, 불가능한 external Git/Workmux 경계는 post-check 실패와 R7.2 rollback으로 닫는다.
- **R7.5** lock/journal은 profile root나 repository tree가 아니라 검증된 per-user runtime root에만 둔다. runtime root는 절대경로·현재 uid 소유·non-symlink인 `$XDG_RUNTIME_DIR/create-worktree`를 우선하고, 조건을 못 채우면 절대경로·현재 uid 소유·non-symlink인 `$TMPDIR/create-worktree-<uid>`를 사용하며 directory mode는 0700이다. lock은 `locks/<sha256(real-git-common-dir)>.lock`, journal은 `journals/<invocation-uuid>.json`, file mode는 0600이고 no-follow/exclusive create와 atomic replace+fsync를 사용한다. lock 파일의 exact JSON object는 정수 `schema_version=1`, 양의 정수 `pid`, 비어 있지 않은 비밀 아닌 현재 boot의 opaque `boot_identity`, 소문자 canonical UUID 문자열 `journal_invocation_uuid`, lock filename과 같은 64자리 lowercase hex `real_git_common_dir_digest`의 다섯 필드만 가진다. journal top-level에는 같은 `schema_version=1`, `invocation_uuid`, `real_git_common_dir_digest`와 R7.1 pre-state/phase/inventory가 있다. 나중 호출은 현재 repository의 real Git common-dir digest로 lock 경로를 단 하나 계산해 no-follow로 읽고, 그 lock의 `journal_invocation_uuid`로 journal 경로를 직접 구성한다. glob·directory scan·basename 추측은 금지하며, 두 파일의 schema/UUID/digest 교차 일치가 실패하거나 journal이 없으면 손상된 transaction으로 `preflight_failed`하고 자동 복구·삭제하지 않는다. lock은 apply 수명, journal은 lock 취득 직후부터 terminal success 또는 complete rollback까지 유지하고 정상 종료 시 backend가 삭제한다. crash 뒤에는 acquire 가능한 repository lock과 recorded PID 부재 또는 boot identity 불일치를 stale로 판정하되 backend가 자동 탈취·삭제하지 않고 `preflight_failed`로 `recovery_journal_id`, `stale_reason`과 public recovery inventory만 제시한다. `stale_reason`은 `pid_absent`, `boot_identity_mismatch`, `transaction_metadata_invalid` 중 하나이고 raw PID와 boot identity는 mode 0600 runtime files 안에만 두며 public JSON에는 내보내지 않는다. 같은 OS user인 operator가 pre-state와 remaining artifact를 reviewed recovery로 확인·정리한 뒤 lock/journal을 삭제하는 유일한 cleanup 주체다. 이 transient recovery state는 binding/task registry가 아니므로 중복 영구 상태를 만들지 않으며, dry-run 성공 전에는 runtime root도 만들지 않아 A1의 profile root 선생성 금지와 양립한다.

### 출력, 비밀과 실행 경계

- **R8.1** public plan/result/error는 R4.2의 allowlist와 status, phase, created/reused/rollback 사실만 포함한다. `destination_basename`은 plan/result에 허용하되, `workmux_handle`은 새 생성 plan에는 없고 R5.4 생성 후 result 또는 R6.1 재사용 plan/result에만 허용한다. stale transaction error에는 `recovery_journal_id`와 enum `stale_reason`만 추가로 허용하고 raw PID·boot identity·lock/journal filesystem path는 금지한다. provider마다 account alias와 selection source를 명시하고 legacy unbound 상태가 생기면 숨기지 않고 `account_profile=unbound`와 이유를 표시한다.
- **R8.2** config home, credential, token, email, raw account identity, 인증 파일 위치와 provider 원시 출력은 stdout/stderr, log, fixture snapshot, Git config, branch description, commit message와 tmux option/window metadata에 기록하지 않는다. destination과 비밀 아닌 alias만 허용하고 test fixture의 synthetic marker도 public surface에서 0건이어야 한다.
- **R8.3** 생성/재사용 호출은 빈 shell pane만 열고 provider launcher, login/usage verifier, dev server나 agent를 자동 실행하지 않는다. 기존 Workmux global pane layout의 command 없는 상태를 보존한다.

### 문서, 사본과 검증 격리

- **R9.1** 두 `SKILL.md`는 각 frontmatter 종료 뒤 첫 byte부터 EOF까지 동일해야 하고 `$create-worktree` named option, backend plan/apply, 실패/복구와 non-goal을 같은 순서로 문서화한다. `openai.yaml` prompt도 named workspace profile을 안내하며 skill prose는 backend logic을 복제하지 않는다.
- **R9.2** 기존 `docs/session-account-profiles.md`는 `Workspace profiles`, `Canonical repositories`, `Provider bindings`, `Profile omission and fail-closed`, `Creation does not verify provider login`, `#94/#95 binding availability` heading을 포함한다. 신규 운영 문서 `docs/create-worktree.md`는 `Unsupported repository wrappers`, `Incomplete rollback recovery`, `Cross-profile recovery (#111)` heading 아래 각각 no-fallback, remaining inventory reviewed cleanup, no automatic move/rebind 문구를 포함한다.
- **R9.3** 모든 automated test는 temporary Git repository, temporary registry/home/destination, fake provider/gh/Workmux 또는 read-only real Workmux dry-run, isolated tmux socket/shim만 사용한다. 실제 사용자 worktree, 인증 home, default tmux socket, network, login/usage/auth 상태와 provider process를 읽거나 변경하지 않는다.

### 완료와 회귀

- **R10.1** issue #118의 필수 branch/profile, PR 세 형태/OID, session 독립성, invalid profile/provider/root/scope, prefix/symlink/relative/`..`/collision, dry-run no-mutation, same/cross-profile reuse, wrapper/git-crypt, post-create Git/tmux, no-verifier, provider binding과 sensitive-output case를 모두 deterministic test로 둔다. A1의 chezmoi root-creation 금지, A2의 lazy parent, A3의 single backend, A4의 enum/repository/realpath/rollback case도 명시적 test name을 가진다. 단일 required-test manifest는 판정 명령 표에 등장하는 모든 `-k` 이름을 `tests.test_create_worktree.CreateWorktreeContractTests.<method>` fully-qualified test ID로 정확히 한 번씩 열거하고, module 밖 동명 method는 일치로 세지 않는다. manifest meta-test는 discovery에서 각 expected ID가 정확히 하나 존재하는지 확인하고 manifest 전체를 실제 실행해 `testsRun`이 manifest 크기와 같으며 failures·errors·skipped·expectedFailures·unexpectedSuccesses가 모두 0인지 단언한다. meta-test 자체의 존재와 1건 실행은 `-k`를 쓰지 않는 direct fully-qualified ID로 판정한다.
- **R10.2** 정정 전 baseline은 base revision `72ad4f24e9df5919773cb877de01007f641ae163`에서 97 tests/3 failures이며, 완료 gate는 R10.5의 #103 전용 gate 정정 뒤 targeted tests, existing selector/orchestrator regression, 두 skill 본문 diff와 validator, high-risk E2E, full unittest discovery, `git diff --check`, task-owned path와 `.gitignore` 보존 확인, `chezmoi diff --no-pager`의 human review 순이다. task-owned file allowlist는 `dot_local/bin/ai_session_registry_loader.py`, `dot_local/libexec/ai_session_registry.py`, `dot_local/bin/executable_ai-session`, `dot_local/bin/executable_create-worktree`, `dot_config/ai-session/accounts.toml`, `tests/test_ai_session.py`, `tests/test_create_worktree.py`, `tests/run_unittest_contract.py`, `tests/test_orchestrator_profiles.py`, `tests/check_installed_orchestrator_cli_contract.py`, `dot_agents/skills/create-worktree/SKILL.md`, `dot_claude/skills/create-worktree/SKILL.md`, `dot_agents/skills/create-worktree/agents/openai.yaml`, `docs/session-account-profiles.md`, `docs/create-worktree.md`이고, task-owned prefix allowlist는 `docs/development/2026-09-16-118-profile-aware-create-worktree/` 하나다. 정정 후 targeted·regression·full discovery는 선택/수집된 기대 건수를 모두 실행하고 failures·errors·skipped·expectedFailures·unexpectedSuccesses 0으로 exit 0이어야 하며 의도한 diff만 확인되기 전에는 merge/apply 준비 완료로 판정하지 않는다.
- **R10.3** automated workflow는 commit, push, PR, merge, `chezmoi apply`, 실제 main 배포나 profile root 선생성을 하지 않는다. automated scope 판정은 R10.2의 명시적 allowlist와 #118 전용 `test_issue_118_task_owned_path_allowlist`를 사용한다. main merge와 local apply는 검증된 diff를 사용한 별도 명시적 operator action이며 실패 시 source rollback 후 새 검증을 요구한다. issue 완료에는 operator가 merge/apply와 그 뒤의 diff 재확인 결과를 Report에 기록해야 한다.
- **R10.4** 모든 판정 명령의 test segment는 `tests/run_unittest_contract.py`를 사용한다. 이 stdlib-only runner는 명명한 module을 직접 load하고 `-k`를 substring이 아닌 exact method name으로 해석해 R10.1 manifest의 fully-qualified ID와 1:1 대응시킨다. targeted 실행의 기대 건수 N은 서로 다른 `-k` 수와 같고, direct ID 실행은 명시한 `--expect-count`와 같아야 한다. module 전체와 discovery 실행은 실행 전에 수집한 N을 기록하고 N이 선언한 `--min-count` 이상인지 확인한 뒤 같은 suite의 `testsRun=N`을 단언한다. 어떤 mode도 N=0, missing·duplicate·부분 선택을 허용하지 않으며 failures·errors·skipped·expectedFailures·unexpectedSuccesses 중 하나라도 0이 아니면 nonzero다. runner 독립 교차 검사는 import 가능한 단일 known-bad synthetic module을 임시 경로에 만들고 runner process의 OS 종료 코드를 외부 shell이 직접 포착해 nonzero임을 단언하며 runner의 출력·counter 보고를 판정 근거로 사용하지 않는다. test module이 없는 판정 단계는 N=0으로 표시하되 그 단계의 명시적 non-test 조건과 exit 0을 모두 만족해야 한다.
- **R10.5** #103 전용 gate 정정은 `tests/test_orchestrator_profiles.py`와 `tests/check_installed_orchestrator_cli_contract.py`만 수정한다. 전자의 `BASE_REVISION`은 `72ad4f24e9df5919773cb877de01007f641ae163`으로 갱신하고 `T15_ALLOWED_FILES`/`T15_ALLOWED_PREFIXES`는 R10.2의 task-owned allowlist와 정확히 일치시킨다. `PRESERVED_PATHS`에서는 R9.1이 수정할 `dot_claude/skills/create-worktree`만 제거하고 `dot_config/workmux`, `dot_tmux.conf.tmpl`, `dot_zshrc.tmpl`은 유지한다. file ownership과 installed CLI checker는 main에 없는 #103 evidence 경로 의존을 제거하고 기존 source constants·role manifest·격리 help-only probe를 직접 판정한다. 이 정정은 product source, runtime behavior와 다른 저장소 계약을 바꾸지 않으며 정정 뒤 선행 세 case와 full suite가 failures·errors·skips 0으로 통과해야 한다.

## Acceptance criteria

- **AC-1** 첫 positional과 선택적 두 번째 positional, named `--workspace-profile`만 허용되고 세 번째 positional, missing option value, 둘 이상의 branch/PR 또는 session 후보는 exit 2로 생성 전에 끝난다. [실행](`CMD-1 -k test_cli_contract`)
- **AC-2** 같은 profile로 target session만 바꾼 두 plan의 destination/provider bindings가 byte-identical이고 같은 session으로 profile만 바꾼 두 plan은 session이 같고 root만 registry대로 달라진다. [실행](`CMD-1 -k test_session_profile_independence`)
- **AC-3** profile 생략은 current real path가 정확히 한 registry root 안인 fixture에서만 추론되고 canonical main, root 밖, 겹침/모호 fixture에서는 `blocked_contract`와 명시 요구로 directory 생성 0건이다. [실행](`CMD-1 -k test_profile_inference`)
- **AC-4** branch mode가 서로 다른 두 registry profile root 아래 정확한 repository/task destination을 계획·생성하고 profile 이름을 바꾼 fixture도 코드 변경 없이 통과한다. [실행](`CMD-4 -k test_branch_profile_destinations`)
- **AC-5** PR URL, `owner/repo#N`, 표지가 있는 번호가 같은 PR number/head OID/profile destination을 만들고 bare 숫자는 PR로 추정되지 않으며 생성 후 HEAD가 head OID와 같다. [실행](`CMD-4 -k test_pr_forms_and_head_oid`)
- **AC-6** `workspace_profiles`의 name/root/provider_bindings unique·non-overlap·unknown-field 규칙이 적용되고 unknown/ambiguous profile과 hardcoded-profile sentinel이 생성 전에 실패한다. [실행](`CMD-2 -k test_workspace_profile_schema -k test_profile_enum_from_registry`)
- **AC-7** `repositories`의 id/canonical_path/workspace_subdir validation과 current/PR repository mapping이 통과하고 unmapped, mismatched common-dir, unsafe subdir는 생성 전에 거부된다. [실행](`CMD-2 -k test_canonical_repository_mapping`)
- **AC-8** 새 parser/옛 registry와 옛 parser/새 registry mixed-deployment fixture가 R2.3의 fail-closed/launch-compatible 결과를 내고 모든 unknown strict field는 무시되지 않는다. [실행](`CMD-2 -k test_registry_mixed_deployment -k test_unknown_fields_rejected`)
- **AC-9** 각 shipped profile의 provider binding이 active same-provider account와 scope에 맞고 Claude profile 변경에도 Codex는 단일 `codex-default`이며 provider 누락·불일치·disabled·scope 위반은 pre-mutation 실패다. [실행](`CMD-2 -k test_provider_bindings -k test_single_codex_binding`)
- **AC-10** home-relative, relative, `..`, symlink와 realpath fixture가 component containment로 판정되고 profile sibling의 유사 prefix, root 밖 symlink와 destination collision은 모두 directory/branch/worktree/window 0건으로 차단된다. [실행](`CMD-3 -k test_realpath_component_containment -k test_symlink_escape_and_prefix_confusion`)
- **AC-11** validation 직후 ancestor symlink를 root 밖으로 교체하는 fixture와 mkdir 직후 component를 교체하는 fixture가 post-check에서 실패하고 호출 소유 artifact만 rollback된다. [실행](`CMD-7 -k test_toctou_symlink_swap`)
- **AC-12** valid apply는 dry-run destination 검증 뒤 정확한 destination parent 중 없던 component만 backend가 명시적으로 지연 생성·journal 기록하고, plan/invalid registry/profile/repository/session/dry-run failure는 directory, branch, worktree, tmux window, runtime state와 Git config를 하나도 만들거나 바꾸지 않는다. [실행](`CMD-3 -k test_lazy_parent_creation -k test_validation_precedes_mkdir`)
- **AC-13** R3.3의 대상 path 집합과 격리 렌더 결과를 검사했을 때 registry-derived profile root를 만드는 지시가 0건이고, `mkdir`, `install -d`, ensure/create-directory helper, managed directory target/placeholder 각각의 positive fixture는 검출되며 comment·문서 문자열과 unrelated-directory negative fixture는 검출되지 않는다. [실행](`CMD-3 -k test_no_chezmoi_profile_root_creation`)
- **AC-14** adapter dry-run이 반환한 safe `destination_basename`을 사용해 temp canonical repository 하나의 Git common-dir를 공유하는 linked worktree만 `<root>/<workspace_subdir>/<destination_basename>`에 생기고, backend의 branch/PR naming 재구현과 profile clone, epic/session/provider/account path component, nested worktree parent는 0건이다. [실행](`CMD-9 -k test_canonical_linked_worktree_layout`)
- **AC-15** skill/OpenAI/TUI fixture의 모든 create call이 `create-worktree` backend로 수렴하고 source scan에 backend 밖 profile lookup, destination `mkdir`, `git worktree add`, `workmux add` orchestration이 0건이며 shared import-only module은 mutation entrypoint를 노출하지 않는다. [실행](`CMD-8 -k test_single_backend_contract`)
- **AC-16** plan과 apply의 첫 JSON이 repository_parent, dry-run-derived `destination_basename`/source, normalized_destination과 provider별 binding을 포함한 required public field set을 가지며 같은 immutable fixture에서는 동일하고 apply는 plan event 이후에만 첫 mutation을 기록한다. 새 생성 plan에는 `workmux_handle`이 없고 created result에는 있으며, 재사용 plan/result에는 pre-mutation exact-path 매칭으로 얻은 `workmux_handle`이 있다. [실행](`CMD-8 -k test_plan_apply_json_contract -k test_plan_precedes_mutation`)
- **AC-17** invalid/preflight/binding/rolled-back/rollback-incomplete fixture가 exact exit 2..7을 내고, 생성 후 Workmux exact-path 매칭 실패는 complete rollback 시 exit 6·incomplete 시 exit 7, 재사용의 매칭 실패는 mutation 없는 exit 5를 낸다. unexpected exception은 redacted exit 1·no-traceback, catch 가능한 signal은 complete rollback 시 128+signal·`interrupted`, incomplete rollback은 exit 7을 낸다. 각 stderr에는 단일 stable error JSON만 있고 fallback, retry, 기존 default destination 생성은 0회다. [실행](`CMD-8 -k test_exit_status_contract -k test_internal_exception_and_signal_contract`)
- **AC-18** plan/apply 생성 경로의 call trace에 `ai-session launch`, provider verifier, login, usage, enrollment와 AI executable이 0회이고 candidate destination은 current-cwd `select --directory`를 호출하지 않고 해석된다. [실행](`CMD-8 -k test_creation_requires_no_verifier`)
- **AC-19** Workmux 0.1.248 read-only dry-run이 source global config와 `{project}` 없는 repository-parent-only 리터럴 regular override를 함께 읽고, 출력 dirname이 그 override 및 독립 계산한 `<root>/<workspace_subdir>`와 byte-identical이며 safe `destination_basename`을 덧붙인다. 기본 명명에서는 없고 `--name`일 때 있을 수 있는 `Handle:` 줄은 참고 값으로만 취급하며 backend는 이를 `workmux_handle`이나 Git config key로 쓰지 않고 실제 directory/branch/worktree/window를 만들지 않는다. [실행](`CMD-4 -k test_real_workmux_dry_run_merge`)
- **AC-20** isolated tmux apply가 global three-pane layout, auto base, naming, hook fixture, Nerd Font와 `status_format: false`를 보존하고 invocation override에는 worktree_dir 외 key가 없다. [실행](`CMD-9 -k test_workmux_global_config_preserved`)
- **AC-21** destination-parent-capable executable wrapper의 missing-parent dry-run/success/failure와 non-executable wrapper fixture가 기존 branch contract를 보존하고, dry-run-derived safe `destination_basename`의 exact destination만 생성한다. `workmux open` 뒤에는 그 exact path로 list 항목을 매칭해 `workmux_handle`을 얻고 failure 때 기존 위치 fallback이나 추측 없이 rollback한다. [실행](`CMD-5 -k test_wrapper_destination_contract -k test_wrapper_failure_and_permissions`)
- **AC-22** `--destination-parent` 또는 missing-parent `--dry-run` capability가 없는 wrapper는 `preflight_failed`, wrapper 없는 git-crypt fixture는 기존 확인/차단 결과가 되고 일반 Workmux가 기존 위치에 생성되는 호출과 연계 issue/PR 자동 생성은 0회다. [실행](`CMD-5 -k test_wrapper_unsupported -k test_git_crypt_guard`)
- **AC-23** exact target session 검증, stored/default 우선순위와 no-auto-create가 유지되고 session 이름을 profile로 해석하지 않으며 outside-worktree-dir의 existing worktree도 `workmux open --config`로 열린다. 새 생성은 explicit/default를 생성 전에 선택하고 handle-key write는 생성 뒤에만 하며, 재사용의 stored read/write는 pre-mutation exact-path list 매칭으로 얻은 `workmux_handle` key만 쓴다. plan의 `destination_basename` key는 0건이다. [실행](`CMD-4 -k test_session_selection_and_open_outside_configured_dir`)
- **AC-24** 생성 뒤 Git worktree list, top-level, absolute common-dir, branch/PR HEAD와 isolated tmux pane cwd가 plan destination에 일치한다. `workmux list --json`에서 exact normalized real path에 일치하는 항목이 정확히 하나이고 result의 `workmux_handle`은 그 항목의 `handle`과 같으며, 0개·복수·unsafe handle 또는 다른 post-check mismatch fixture는 추측 없이 exit 6/7이고 성공을 반환하지 않는다. [실행](`CMD-9 -k test_post_create_verification`)
- **AC-25** 같은 branch가 요청 profile/repository parent 안에 있으면 branch/worktree 생성 없이 같은 path를 재사용하고, 어떤 mutation보다 먼저 `workmux list --json`의 exact-path 유일 항목에서 `workmux_handle`을 얻어 그 handle의 session-state key와 window만 처리한다. 매칭 실패는 basename 폴백 없이 exit 5이고 mutation 0건이다. [실행](`CMD-6 -k test_same_profile_reuse`)
- **AC-26** 같은 branch가 다른 profile, canonical main 또는 scope 밖에 있으면 실제 path와 요청 profile을 포함한 redacted `blocked_binding`으로 끝나고 move, duplicate checkout, branch/window 생성이 0건이다. [실행](`CMD-6 -k test_cross_profile_existing_worktree_blocked`)
- **AC-27** available fake #94/#95 adapter는 provider별 binding과 positive generation을 atomic하게 받고 unavailable case는 `not_available` 외 상태 파일을 만들지 않으며 declared adapter failure는 transaction rollback을 유발한다. [실행](`CMD-6 -k test_binding_adapter_atomic_or_unavailable`)
- **AC-28** cross-profile, main worktree와 submodule move 요청 fixture는 #111 안내를 내지만 move-rebind 또는 `git worktree move`를 한 번도 호출하지 않는다. [실행](`CMD-6 -k test_cross_profile_move_is_out_of_scope`)
- **AC-29** lock 취득 직후 durable pre-state journal이 directory identity, branch/OID, worktree, exact `(normalized real path, workmux_handle)` pair, handle별 session-state 값과 window ID를 캡처한다. 새 생성 후 exact-path 매칭으로 얻은 pair와 pre-state의 set difference만 호출 소유로 부여하고, 재사용 pair는 소유하지 않으며 rollback과 Git config key에 `destination_basename`을 쓰는 경우는 0건이다. [실행](`CMD-7 -k test_prestate_ownership_journal`)
- **AC-30** parent creation과 worktree 제거 직후 fault injection이 P3처럼 Git이 남긴 intermediate를 포함해 이번 호출이 만든 empty component만 journal에 따라 역순 제거하고 pre-existing parent와 그 content를 byte-identical 보존한다. [실행](`CMD-7 -k test_parent_creation_rollback`)
- **AC-31** branch 또는 worktree 생성 직후 fault injection이 새 worktree/admin entry와 이 호출이 만든 matching-OID branch만 제거하고 pre-existing/changed/dirty branch와 worktree를 보존한다. [실행](`CMD-7 -k test_worktree_and_branch_rollback`)
- **AC-32** tmux window 생성 중 또는 직후 fault injection이 이번 호출의 exact new window ID, worktree, branch와 directory만 역순 정리하고 pre-existing window ID는 보존한다. [실행](`CMD-7 -k test_tmux_failure_rollback`)
- **AC-33** 각 rollback fixture에서 호출 전 존재한 directory, worktree, branch, window와 unrelated concurrent artifact의 identity/bytes가 전후 동일하다. [실행](`CMD-7 -k test_preexisting_artifacts_never_removed`)
- **AC-34** dirty/non-empty/identity-changed와 non-reversible hook fixture는 force-delete 없이 exit 7, remaining artifact inventory와 수동 복구 안내를 내고 완전 rollback은 exit 6으로 원래 실패를 보존한다. [실행](`CMD-7 -k test_rollback_incomplete_reporting`)
- **AC-35** 같은 canonical repository의 두 backend apply가 lock으로 직렬화되고 external path swap은 pre/post realpath check 또는 post-create rollback에서 fail closed한다. [실행](`CMD-7 -k test_repository_lock_and_external_race`)
- **AC-36** public plan/result/error가 required allowlist와 explicit/unbound binding 상태만 포함한다. 새 생성 plan의 `workmux_handle`, stale error의 raw PID/boot identity/runtime path, unexpected extra field와 raw subprocess payload는 거부되고, created result와 reuse plan/result의 권위 있는 `workmux_handle` 및 stale error의 `recovery_journal_id`/enum `stale_reason`만 허용된다. [실행](`CMD-8 -k test_public_output_allowlist`)
- **AC-37** stdout/stderr/log/fixture/Git/tmux metadata scan에서 credential, config-home 원문, email, token, raw identity와 synthetic secret marker가 0건이다. [실행](`CMD-8 -k test_sensitive_output_and_metadata_hygiene`)
- **AC-38** created/reused window의 모든 pane이 빈 shell이고 provider, agent와 dev-server fake executable call count가 0이다. [실행](`CMD-9 -k test_no_automatic_ai_or_server`)
- **AC-39** frontmatter를 제거한 두 skill 본문의 diff가 0이고 두 문서와 openai prompt가 named profile/backend/failure 계약을 통과한다. [실행](`CMD-10 -k test_skill_body_equivalence -k test_skill_interface_contract`)
- **AC-40** `docs/session-account-profiles.md`와 신규 `docs/create-worktree.md`가 R9.2에 열거된 heading을 정확히 한 번씩 포함하고, 후자는 no-fallback, remaining inventory reviewed cleanup, no automatic move/rebind phrase를 각 지정 heading 아래 포함한다. [실행](`CMD-11 -k test_profile_aware_worktree_documentation`)
- **AC-41** 전체 create-worktree test harness의 filesystem/tmux/network/provider sentinels가 temp roots와 isolated socket만 관찰하고 actual user-state access count가 0이다. [실행](`CMD-9 -k test_high_risk_e2e_isolation`)
- **AC-42** required-test manifest가 판정 명령 표의 모든 `-k` method를 `tests.test_create_worktree.CreateWorktreeContractTests.<method>` ID로 정확히 한 번 포함하고 discovery 대조의 missing·duplicate가 0이다. manifest 전체 실제 실행은 `testsRun=manifest 크기`이고 failures·errors·skipped·expectedFailures·unexpectedSuccesses가 모두 0이다. meta-test 자체는 direct fully-qualified ID로 정확히 1건 실행된다. [실행](`CMD-13 tests.test_create_worktree.CreateWorktreeInventoryTests.test_required_create_worktree_inventory_is_complete_and_unskipped`)
- **AC-43** 정정 전 baseline이 97 tests/3 failures였음을 고정하고 R10.5 정정 뒤 기존 `test_ai_session.py` 전체는 수집 N≥19, `test_orchestrator_profiles.py` 전체는 수집 N≥78이며 각 module에서 `testsRun=N`, failures·errors·skipped·expectedFailures·unexpectedSuccesses 0으로 통과한다. installed CLI help-only checker도 exit 0이어서 selector, session, PR/OID, git-crypt와 launcher 계약의 무관한 회귀가 없다. [실행](`CMD-12`)
- **AC-44** R10.5 정정과 targeted, skill/doc, high-risk E2E 뒤 repository discovery는 정정 전 97보다 큰 수집 N을 기록하고 `testsRun=N`, failures·errors·skipped·expectedFailures·unexpectedSuccesses 0으로 exit 0이며 whitespace 검사도 exit 0이다. [실행](`CMD-13`)
- **AC-45** `chezmoi diff --no-pager`가 task-owned 배포 target의 의도한 변경만 보이고 profile root 선생성, credential material과 task 밖 drift가 없다고 reviewer가 기록한다. [실행](`CMD-14`)
- **AC-46** base revision 대비 `.gitignore` diff가 0이고 R10.2에 열거한 task-owned file/prefix allowlist 밖 변경이 없다. #118 전용 고유 이름 `test_issue_118_task_owned_path_allowlist`와 persistent/external mutation sentinel은 각각 정확히 1건 실행되고 automated command trace의 git write, merge, deploy와 `chezmoi apply`는 0회다. [실행](`CMD-15 -k test_issue_118_task_owned_path_allowlist -k test_no_persistent_or_external_mutation`)
- **AC-47** installed Claude verifier mismatch와 `usage_unknown` fixture가 남아 있어도 branch/PR plan/apply 테스트는 verifier를 호출하지 않고 독립적으로 통과한다. [실행](`CMD-8 -k test_verifier_defect_does_not_block_creation`)
- **AC-48** 모든 automated gate 뒤 별도 operator action으로 main merge와 local apply가 수행되고, 후속 `chezmoi diff --no-pager` 재확인에서 unintended drift가 없다는 evidence가 issue 완료 Report에 기록된다. [문서] docs/development/2026-09-16-118-profile-aware-create-worktree/report.md 의 "Deployment handoff" 절
- **AC-49** profile root와 repository parent가 모두 없는 temp cold-start에서 real Workmux dry-run은 exact parent 아래 destination을 출력하고 mutation 0건이며, isolated apply는 dry-run 뒤 backend가 parent를 먼저 만들고 최초 linked worktree를 생성한다. 같은 상태의 wrapper fixture도 missing-parent dry-run 계약을 만족하고, apply fault 때 journal-owned 빈 component가 모두 제거된다. [실행](`CMD-16 -k test_cold_start_missing_profile_and_repository_parent -k test_wrapper_cold_start_contract`)
- **AC-50** validated runtime-root fixture에서 lock/journal의 exact path, 0700/0600 mode, no-follow, apply-only lifetime과 정상 cleanup이 일치한다. lock JSON이 R7.5의 다섯 필드만 갖고 exact `schema_version=1`/양의 `pid`/비어 있지 않은 `boot_identity`/canonical `journal_invocation_uuid`/64자리 lowercase hex `real_git_common_dir_digest`를 만족하며 journal의 UUID/digest가 일치함을 단언한다. 나중 호출이 repository digest lock 하나를 읽어 그 UUID로 journal 경로를 직접 구성하고 scan/glob 없이 교차 검증하는 것을 확인한다. crash·missing/mismatched journal fixture는 자동 탈취 없이 exit 5로 fail closed하고 public error에는 raw PID/boot identity/path 없이 `recovery_journal_id`와 `pid_absent|boot_identity_mismatch|transaction_metadata_invalid` 중 하나의 `stale_reason`만 있으며, operator-reviewed cleanup 전 profile/repository tree와 binding registry에 runtime state를 0건 남긴다. [실행](`CMD-17 -k test_runtime_lock_journal_contract -k test_stale_transaction_requires_reviewed_recovery`)
- **AC-51** `ai-session`과 create backend가 `dot_local/bin/ai_session_registry_loader.py`의 import bootstrap을 통해 exact `dot_local/libexec/ai_session_registry.py`의 parser/strict field constants/normalization/containment API를 import하고 동일 registry/path corpus에서 같은 accept/reject 결과를 낸다. loader의 import 경로 결정·load 외 semantic 구현과 mutation은 source scan 0건이고, `def select_strict_account`와 `def classify_verifier_payload`는 `dot_local/bin/executable_ai-session`에 각각 정확히 한 번 정의되어 공용 primitive에 위임하며 별도 parser 또는 path validator 구현은 source scan 0건이다. [실행](`CMD-8 -k test_shared_registry_path_module_identity`)
- **AC-52** 판정 명령 표의 test segment를 추출했을 때 모든 `-k` method가 R10.1 manifest의 named module fully-qualified ID와 정확히 1:1 대응한다. 계약 runner의 synthetic empty module, missing name, duplicate name, 일부만 존재하는 복수 `-k`, skipped·expectedFailure·unexpectedSuccess fixture는 모두 nonzero이고, direct ID와 valid targeted fixture만 기대 건수 N 전부를 실행해 result counter 5종이 0이다. 이 판정 test 자체는 `-k` 없이 direct ID로 정확히 1건 실행된다. [실행](`CMD-18 tests.test_create_worktree.CreateWorktreeInventoryTests.test_judgement_command_selection_contract`)
- **AC-53** #103 gate 정정 diff는 `tests/test_orchestrator_profiles.py`와 `tests/check_installed_orchestrator_cli_contract.py` 두 파일뿐이고, base가 `72ad4f24e9df5919773cb877de01007f641ae163`, changed-path allowlist가 R10.2 목록, `PRESERVED_PATHS`가 `dot_config/workmux`·`dot_tmux.conf.tmpl`·`dot_zshrc.tmpl`만 포함한다. 존재하지 않는 #103 evidence 경로 참조는 두 파일에서 0건이며 세 선행 gate test가 direct fully-qualified ID로 정확히 3건 실행되어 failures·errors·skips 0이다. [실행](`CMD-19 tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_changed_path_allowlist tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_file_ownership tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_portable_cli_contract`)
- **AC-54** adapter 등록 직후 정상 R5.4 조회 전 실패 fault에서 rollback 전 destination exact-path 진단 조회가 정확히 1회 실행된다. 성공한 등록 command 결과와 pre-state에 없던 exact 유일 항목이 함께 있으면 그 pair만 호출 소유로 rollback하고, 성공 결과가 없거나 0개·복수·unsafe 항목이면 진단만으로 소유권을 부여하거나 remove하지 않으며 `rollback_remaining`에 `workmux_registry_entry`와 비민감 destination을 기록한다. [실행](`CMD-7 -k test_adapter_registered_then_failed_before_handle_lookup`)
- **AC-55** temp directory의 import 가능한 unittest module에 정확히 한 개의 무조건 실패 case를 만들고 계약 runner로 module 전체를 실행했을 때, 외부 shell이 runner의 출력이나 counter를 읽지 않고 process의 OS 종료 코드가 nonzero임을 직접 단언한다. runner가 무조건 zero를 반환하면 판정 명령 자체가 nonzero로 실패하고 temp fixture는 종료 시 제거된다. [실행](`CMD-20`)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1 | `CMD-1 -k test_cli_contract` |
| R1.2 | AC-2, AC-3 | `CMD-1 -k test_session_profile_independence -k test_profile_inference` |
| R1.3 | AC-4, AC-5 | `CMD-4 -k test_branch_profile_destinations -k test_pr_forms_and_head_oid` |
| R2.1 | AC-6 | `CMD-2 -k test_workspace_profile_schema -k test_profile_enum_from_registry` |
| R2.2 | AC-7 | `CMD-2 -k test_canonical_repository_mapping` |
| R2.3 | AC-8 | `CMD-2 -k test_registry_mixed_deployment -k test_unknown_fields_rejected` |
| R2.4 | AC-9 | `CMD-2 -k test_provider_bindings -k test_single_codex_binding` |
| R3.1 | AC-10, AC-11 | `CMD-3 -k test_realpath_component_containment -k test_symlink_escape_and_prefix_confusion`; `CMD-7 -k test_toctou_symlink_swap` |
| R3.2 | AC-12, AC-49 | `CMD-3 -k test_lazy_parent_creation -k test_validation_precedes_mkdir`; `CMD-16 -k test_cold_start_missing_profile_and_repository_parent -k test_wrapper_cold_start_contract` |
| R3.3 | AC-13 | `CMD-3 -k test_no_chezmoi_profile_root_creation` |
| R3.4 | AC-14 | `CMD-9 -k test_canonical_linked_worktree_layout` |
| R4.1 | AC-15, AC-51 | `CMD-8 -k test_single_backend_contract -k test_shared_registry_path_module_identity` |
| R4.2 | AC-16 | `CMD-8 -k test_plan_apply_json_contract -k test_plan_precedes_mutation` |
| R4.3 | AC-17 | `CMD-8 -k test_exit_status_contract -k test_internal_exception_and_signal_contract` |
| R4.4 | AC-18, AC-47 | `CMD-8 -k test_creation_requires_no_verifier -k test_verifier_defect_does_not_block_creation` |
| R5.1 | AC-19, AC-20, AC-49 | `CMD-4 -k test_real_workmux_dry_run_merge`; `CMD-9 -k test_workmux_global_config_preserved`; `CMD-16 -k test_cold_start_missing_profile_and_repository_parent` |
| R5.2 | AC-21, AC-22, AC-49 | `CMD-5 -k test_wrapper_destination_contract -k test_wrapper_failure_and_permissions -k test_wrapper_unsupported -k test_git_crypt_guard`; `CMD-16 -k test_wrapper_cold_start_contract` |
| R5.3 | AC-23 | `CMD-4 -k test_session_selection_and_open_outside_configured_dir` |
| R5.4 | AC-24 | `CMD-9 -k test_post_create_verification` |
| R6.1 | AC-25, AC-26 | `CMD-6 -k test_same_profile_reuse -k test_cross_profile_existing_worktree_blocked` |
| R6.2 | AC-27 | `CMD-6 -k test_binding_adapter_atomic_or_unavailable` |
| R6.3 | AC-28 | `CMD-6 -k test_cross_profile_move_is_out_of_scope` |
| R7.1 | AC-29, AC-50 | `CMD-7 -k test_prestate_ownership_journal`; `CMD-17 -k test_runtime_lock_journal_contract -k test_stale_transaction_requires_reviewed_recovery` |
| R7.2 | AC-30, AC-31, AC-32, AC-33, AC-49, AC-54 | `CMD-7 -k test_parent_creation_rollback -k test_worktree_and_branch_rollback -k test_tmux_failure_rollback -k test_preexisting_artifacts_never_removed -k test_adapter_registered_then_failed_before_handle_lookup`; `CMD-16 -k test_cold_start_missing_profile_and_repository_parent` |
| R7.3 | AC-34 | `CMD-7 -k test_rollback_incomplete_reporting` |
| R7.4 | AC-35 | `CMD-7 -k test_repository_lock_and_external_race` |
| R7.5 | AC-50 | `CMD-17 -k test_runtime_lock_journal_contract -k test_stale_transaction_requires_reviewed_recovery` |
| R8.1 | AC-16, AC-36 | `CMD-8 -k test_plan_apply_json_contract -k test_public_output_allowlist` |
| R8.2 | AC-37 | `CMD-8 -k test_sensitive_output_and_metadata_hygiene` |
| R8.3 | AC-38 | `CMD-9 -k test_no_automatic_ai_or_server` |
| R9.1 | AC-39 | `CMD-10` |
| R9.2 | AC-40 | `CMD-11 -k test_profile_aware_worktree_documentation` |
| R9.3 | AC-41 | `CMD-9 -k test_high_risk_e2e_isolation` |
| R10.1 | AC-42 | `CMD-13 tests.test_create_worktree.CreateWorktreeInventoryTests.test_required_create_worktree_inventory_is_complete_and_unskipped` |
| R10.2 | AC-43, AC-44, AC-45, AC-46 | `CMD-12`; `CMD-13`; `CMD-14`; `CMD-15 -k test_issue_118_task_owned_path_allowlist -k test_no_persistent_or_external_mutation` |
| R10.3 | AC-46, AC-48 | `CMD-15 -k test_issue_118_task_owned_path_allowlist -k test_no_persistent_or_external_mutation`; future Report의 Deployment handoff evidence |
| R10.4 | AC-52, AC-55 | `CMD-18 tests.test_create_worktree.CreateWorktreeInventoryTests.test_judgement_command_selection_contract`; `CMD-20` |
| R10.5 | AC-53 | `CMD-19 tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_changed_path_allowlist tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_file_ownership tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_portable_cli_contract` |

## Architecture

구성요소와 책임은 다음과 같다.

1. `accounts.toml`은 기존 active accounts와 directory mappings에 더해 workspace profile enum/root/provider bindings 및 canonical repository mapping의 유일한 선언 source다. credential material은 소유하지 않는다.
2. 단일 import-only registry/path module은 strict schema parse, exact field constants, unknown-field rejection, path normalization, component containment와 provider scope coherence를 순수 함수로 제공한다. 기존 `ai-session` current-cwd 선택과 새 backend candidate-parent 선택은 반드시 이 동일 module/API를 import하지만 서로의 CLI semantics를 바꾸지 않는다.
3. `create-worktree` backend는 input normalization, repository/PR 해석, profile resolution, plan, pre-state journal, Workmux/wrapper adapter, Git/tmux post-check, binding adapter와 rollback을 단독 소유한다.
4. Workmux adapter는 independently computed repository parent만 든 invocation config를 생성하고 real Workmux dry-run/apply/open을 호출한다. wrapper adapter는 missing-parent dry-run과 destination-parent capability가 있을 때만 같은 transaction interface에 참여한다. 두 adapter 모두 dry-run의 전체 destination에서 경로 component인 `destination_basename`만 확정한다. Workmux registry 식별자인 `workmux_handle`은 생성 뒤, 또는 재사용이면 mutation 전에, exact real path로 `workmux list --json` 항목을 매칭해 그 `handle` 필드에서만 조회한다. 이는 Workmux naming을 재구현하는 것이 아니라 Workmux가 공개한 registry identity를 조회하는 것이며, 두 식별자를 같은 값으로 간주하지 않는다.
5. 두 skill 사본과 OpenAI prompt는 human-language adapter다. backend JSON을 표시하고 필요한 사용자 확인을 받지만 path나 mutation 로직을 다시 구현하지 않는다.
6. #94/#95 adapter는 optional external dependency다. backend는 availability를 plan에 공개하고 제공될 때만 atomic registration을 호출한다.
7. transaction runtime store는 profile/repository tree와 분리된 R7.5 per-user runtime root에 repository lock과 crash-recovery journal만 보관한다. 이는 task/binding의 canonical state가 아니며 정상 terminal path에서 제거된다.
8. `tests/run_unittest_contract.py`는 판정 명령의 유일한 unittest 실행기다. required-test manifest의 fully-qualified ID, exact `-k` 선택, module/discovery 수집 N과 `unittest.TestResult` counter를 한 과정에서 검증해 CLI exit 0만으로 통과하지 못하게 한다.
9. #103 gate cleanup은 `tests/test_orchestrator_profiles.py`와 `tests/check_installed_orchestrator_cli_contract.py`에만 존재하는 test infrastructure 변경이다. product component와 runtime flow에는 참여하지 않는다.

Mutation boundary는 `apply`의 public plan emission 뒤다. 새 생성 순서는 input/registry/repository/session/existing-state 검증 → independently computed repository parent를 넣은 adapter dry-run → dry-run destination의 parent/`destination_basename`/containment 검증 및 `workmux_handle` 없는 public plan → runtime root/lock/journal과 pre-state `(path, workmux_handle)` set 생성 → ancestor 재검증 → missing parent component의 명시적 생성·journal 기록 → Git/Workmux apply/open → exact created path로 list 항목을 매칭한 `workmux_handle` 확정과 post-check다. 재사용은 existing worktree exact path로 `workmux_handle`을 pre-mutation에 확정한 뒤 plan을 출력하며 새 Workmux pair의 소유권을 주장하지 않는다. P1 덕분에 dry-run-before-mkdir은 missing-root cold-start에서도 성립하고, P2 때문에 parent-before-apply는 선택이 아니라 소유권 journal의 필수 조건이다. profile root 자체가 없으면 valid apply의 선택된 chain만 만들며 다른 profile이나 repository tree를 준비하지 않는다.

## Interfaces and data flow

1. skill/TUI가 user request를 backend `plan`으로 전달한다. `--registry`는 test에서 temp file, deployed invocation에서 reviewed registry target을 가리킨다.
2. backend가 branch/PR와 target session을 파싱하고 current repository identity 또는 PR owner/name을 normalized repository ID로 만든다.
3. registry parser가 workspace profile과 canonical repository row를 고르고 provider bindings를 active accounts 및 allowed scopes에 대조한다. profile 생략 시 current real cwd만 inference input이다.
4. resolver가 `profile.root / repository.workspace_subdir` repository parent를 독립 계산하고 nearest existing ancestor부터 component containment를 검증한다. 이 단계에는 `destination_basename`, `workmux_handle`이나 full destination 계산이 없다.
5. backend가 existing worktree, session과 wrapper/git-crypt capability를 조회한 뒤 선택 adapter의 dry-run을 실행한다. dry-run이 반환한 full path의 parent가 step 4와 같고 basename이 safe component일 때만 `destination_basename`/normalized_destination을 확정한다. 새 생성 public plan에는 `workmux_handle`이 없고 `plan`은 runtime state와 filesystem mutation 없이 종료한다. 재사용이면 기존 exact path를 `workmux list --json`에 먼저 매칭해 `workmux_handle`도 plan에 넣으며 실패는 mutation 없는 exit 5다.
6. `apply`는 같은 resolution과 dry-run을 새로 수행해 plan을 출력하고 R7.5 runtime root의 repository lock과 durable pre-state journal을 만든 뒤 realpath를 재검증한다. lock JSON의 journal UUID가 해당 repository transaction journal을 찾는 유일한 pointer다.
7. 필요한 exact parent를 backend가 component별로 지연 생성·journal 기록한 뒤 wrapper 또는 Workmux로 linked worktree/window를 만든다. Git/Workmux가 parent를 암묵 생성하게 두지 않으며 각 created identity를 journal에 추가한다.
8. 새 생성은 Git, HEAD/common-dir, pane cwd와 path containment를 사후 검증하고, exact actual path에 일치하는 `workmux list --json` 유일 항목의 `handle`로 `workmux_handle`을 확정한다. 그 뒤에만 handle-keyed session state와 optional binding adapter를 처리하며 매칭 실패는 exit 6/7 rollback이다. 재사용은 step 5에서 얻은 handle을 사용한다.
9. adapter가 등록 뒤 정상 handle 조회 전에 실패하면 destination exact-path diagnostic list를 한 번 수행한다. 이 read만으로 소유권을 만들지 않고, successful registration evidence가 없으면 항목을 남겨 `rollback_remaining`으로 보고한다.
10. 성공은 `created` 또는 `reused` result를 출력한다. 실패는 journal 역순 rollback 뒤 exit 6 또는 7 error를 출력한다.

JSON event는 한 줄의 object이며 `event`, `status`, R4.2·R8.1 public fields, `phase`, `created_by_invocation`, `rolled_back`, `rollback_remaining` 외 필드를 허용하지 않는다. provider binding은 provider/account alias의 정렬된 array로 표현해 provider별 결정을 숨기지 않는다. command argv나 subprocess 원문은 public JSON에 넣지 않는다.

## Failure behavior

- parsing 또는 positional 오류는 `invalid_request`/2이고 mutation이 없다.
- malformed/unknown/ambiguous registry, profile/repository/root/scope/realpath, unsupported destination과 dry-run mismatch는 각각 `blocked_contract`/3 또는 `preflight_failed`/5이고 mutation이 없다.
- existing worktree가 다른 profile에 있거나 stored binding과 새 선택이 충돌하면 `blocked_binding`/4이고 이동이나 재사용이 없다.
- session 서버/이름 검증 실패, wrapper permission/capability failure, Workmux dry-run failure는 preflight에서 끝난다. session을 자동 생성하지 않는다.
- existing worktree 재사용의 exact-path `workmux list --json` 매칭 실패는 `preflight_failed`/5이고 mutation이 없다. 새 생성 뒤 같은 매칭 실패는 operation failure로 rollback하며 complete면 6, incomplete면 7이다. 어느 경우도 `destination_basename`을 handle로 추측하지 않는다.
- mutation 뒤 command/post-check/binding failure는 rollback을 시작한다. 완전히 정리했어도 원래 실패를 `operation_failed_rolled_back`/6으로 보존한다.
- adapter가 등록 뒤 정상 R5.4 조회 전에 실패하면 rollback 전에 exact destination diagnostic list를 한 번 실행한다. 진단 read와 pre-state 차이만으로는 소유권이 아니며, successful registration evidence가 없으면 해당 항목을 강제 제거하지 않고 `workmux_registry_entry` remaining inventory로 보고한다.
- identity drift, dirty/non-empty state, rollback command 실패 또는 되돌릴 수 없는 hook side effect가 남으면 force하지 않고 `rollback_incomplete`/7과 remaining inventory를 낸다.
- 예상하지 못한 내부 exception은 mutation 전 또는 complete rollback이면 `internal_error`/1이고 public traceback 없이 단일 redacted error를 낸다. `SIGHUP`/`SIGINT`/`SIGTERM`은 complete rollback이면 129/130/143이고, exception/signal 어느 쪽이든 remaining artifact가 있으면 `rollback_incomplete`/7이 우선한다.
- catch 불가능한 signal 또는 process crash로 R7.5 lock/journal이 남을 수 있다. 다음 호출은 repository digest의 lock JSON을 no-follow로 읽고 그 안의 journal UUID로 journal 하나를 직접 찾아 schema/UUID/digest를 교차 검증한 뒤 acquire 가능성과 PID/boot evidence로 stale을 판정한다. 자동 탈취하지 않고 `preflight_failed`/5로 redacted recovery evidence와 inventory를 operator에게 제시하며 reviewed cleanup 전에는 새 apply를 시작하지 않는다.
- reuse path에서는 새 Git artifact가 없으므로 window만 새로 만들었을 때 그 window만 rollback 대상이다.

## Security and risk

핵심 위험은 registry spoofing, path traversal/symlink escape, current-cwd와 candidate destination 혼동, cross-profile binding 오사용, TOCTOU, pre-existing artifact 삭제와 public output을 통한 민감정보 노출이다. strict allowlists, canonical mapping, realpath component containment, current repo/common-dir 일치, pre/post validation과 call-owned journal이 이를 완화한다.

TOCTOU는 완전히 제거됐다고 주장하지 않는다. Python path 검사와 external Git/Workmux 실행 사이에 다른 process가 ancestor를 교체할 수 있다. 가능한 mkdir/open은 descriptor-relative 및 no-follow를 사용하고 repository lock으로 같은 backend끼리 직렬화한다. external tool 경계는 직전과 직후의 realpath/common-dir 검증, mismatch 시 fail closed와 소유 artifact rollback으로 방어한다. symlink swap fault injection은 high-risk gate다.

Workspace profile은 account 선택/배치 경계이지 filesystem security tenant가 아니다. canonical repository의 Git common-dir는 profile root 밖 기준 저장소에 남는다. write permission과 auth isolation은 launcher issue의 책임이며 이 backend는 credential을 보거나 provider를 시작하지 않는다.

Rollback도 데이터 손실 위험이 있다. 따라서 path 아래에 있다는 사실이 아니라 pre-state set difference, create return, exact ref/OID와 window ID로 소유권을 증명하고 identity가 달라지면 남겨서 보고한다. arbitrary wrapper/hook side effect는 일반적으로 역연산할 수 없으므로 명시적으로 incomplete 상태다.

판정 command도 false pass 위험이 있다. 표준 `unittest -k`는 0건 선택이나 일부 이름 누락에서도 exit 0일 수 있으므로 R10.4 runner가 module-qualified manifest, exact 선택 N과 result counter를 검증한다. #103 gate 정정은 production source를 건드리지 않고 current-main delta를 판정하는 tests-only migration으로 제한한다.

Lock/journal은 user-controlled runtime boundary다. backend는 환경변수 문자열을 곧바로 신뢰하지 않고 R7.5의 absolute path, uid ownership, non-symlink와 mode를 검증하며 no-follow/exclusive open을 사용한다. runtime state는 dry-run 성공 전이나 plan에서 생성하지 않고 profile root·repository parent·binding registry에 두지 않는다. 따라서 crash recovery에 필요한 일시 상태는 보존하면서 A1의 profile root 선생성과 중복 canonical registry는 만들지 않는다.

## Test strategy

Unit tests는 strict registry schema, arbitrary profile enum, repository mapping, realpath containment, JSON/exit contract와 rollback journal을 다룬다. Integration tests는 temp Git common-dir와 linked worktree, fake `gh`, fake wrapper/Workmux, optional real Workmux dry-run을 사용한다. High-risk E2E는 isolated tmux shim/socket에서 branch와 PR, same/cross-profile, staged fault와 post-check를 실행한다. sentinel은 actual user roots, default tmux socket, network, provider/verifier executable 접근을 즉시 실패시킨다. 모든 unittest 판정은 R10.4 runner를 통과하며 일반 `python -m unittest ... -k ...`의 exit code만 판정 근거로 쓰지 않는다.

R10.1 required-test manifest의 exact fully-qualified ID 정본은 아래 60개다. 각 ID는 command table의 `-k` method 하나와 1:1 대응하며 다른 module의 동명 method는 manifest 충족으로 세지 않는다.

- `tests.test_create_worktree.CreateWorktreeContractTests.test_cli_contract`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_session_profile_independence`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_profile_inference`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_workspace_profile_schema`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_profile_enum_from_registry`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_canonical_repository_mapping`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_registry_mixed_deployment`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_unknown_fields_rejected`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_provider_bindings`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_single_codex_binding`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_realpath_component_containment`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_symlink_escape_and_prefix_confusion`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_lazy_parent_creation`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_validation_precedes_mkdir`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_no_chezmoi_profile_root_creation`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_branch_profile_destinations`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_pr_forms_and_head_oid`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_real_workmux_dry_run_merge`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_session_selection_and_open_outside_configured_dir`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_wrapper_destination_contract`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_wrapper_failure_and_permissions`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_wrapper_unsupported`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_git_crypt_guard`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_same_profile_reuse`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_cross_profile_existing_worktree_blocked`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_binding_adapter_atomic_or_unavailable`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_cross_profile_move_is_out_of_scope`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_toctou_symlink_swap`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_prestate_ownership_journal`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_parent_creation_rollback`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_worktree_and_branch_rollback`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_tmux_failure_rollback`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_preexisting_artifacts_never_removed`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_rollback_incomplete_reporting`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_repository_lock_and_external_race`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_adapter_registered_then_failed_before_handle_lookup`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_single_backend_contract`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_shared_registry_path_module_identity`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_plan_apply_json_contract`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_plan_precedes_mutation`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_exit_status_contract`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_internal_exception_and_signal_contract`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_creation_requires_no_verifier`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_public_output_allowlist`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_sensitive_output_and_metadata_hygiene`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_verifier_defect_does_not_block_creation`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_canonical_linked_worktree_layout`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_workmux_global_config_preserved`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_post_create_verification`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_no_automatic_ai_or_server`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_high_risk_e2e_isolation`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_skill_body_equivalence`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_skill_interface_contract`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_profile_aware_worktree_documentation`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_issue_118_task_owned_path_allowlist`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_no_persistent_or_external_mutation`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_cold_start_missing_profile_and_repository_parent`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_wrapper_cold_start_contract`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_runtime_lock_journal_contract`
- `tests.test_create_worktree.CreateWorktreeContractTests.test_stale_transaction_requires_reviewed_recovery`

### 판정 명령 표

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
| CMD-9 | `CREATE_WORKTREE_E2E_NETWORK=deny /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_canonical_linked_worktree_layout -k test_workmux_global_config_preserved -k test_post_create_verification -k test_no_automatic_ai_or_server -k test_high_risk_e2e_isolation` | 명명 module에서 다섯 ID가 각각 정확히 선택되어 N=5, `testsRun=5`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 high-risk E2E가 actual state/network/provider 접근 없이 통과한다. |
| CMD-10 | `diff -u <(awk 'BEGIN { n=0 } /^---$/ { n++; if (n == 2) { show=1; next } } show' dot_agents/skills/create-worktree/SKILL.md) <(awk 'BEGIN { n=0 } /^---$/ { n++; if (n == 2) { show=1; next } } show' dot_claude/skills/create-worktree/SKILL.md) && /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_skill_body_equivalence -k test_skill_interface_contract` | body diff가 0이고 명명 module의 두 ID가 각각 정확히 선택되어 N=2, `testsRun=2`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이다. |
| CMD-11 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_profile_aware_worktree_documentation` | 명명 module에서 ID 하나가 정확히 선택되어 N=1, `testsRun=1`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 두 운영 문서 계약이 통과한다. |
| CMD-12 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_ai_session --all --min-count 19 && /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_orchestrator_profiles --all --min-count 78 && AI_SESSION_CLI_PROBE_MODE=help-only /opt/homebrew/bin/python3 tests/check_installed_orchestrator_cli_contract.py` | R10.5 정정 뒤 각 명명 module의 수집 N이 각각 19·78 이상이고 `testsRun=N`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이며 help-only checker도 exit 0이다. |
| CMD-13 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree --id tests.test_create_worktree.CreateWorktreeInventoryTests.test_required_create_worktree_inventory_is_complete_and_unskipped --expect-count 1 && /opt/homebrew/bin/python3 tests/run_unittest_contract.py --discover-root tests --pattern 'test_*.py' --min-count 98 && git diff --check` | meta-test direct ID가 N=1, `testsRun=1`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0으로 실행되고 manifest 전체도 같은 조건을 만족한다. 정정 후 full discovery의 수집 N은 98 이상, `testsRun=N`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이며 whitespace 검사도 exit 0이다. |
| CMD-14 | `chezmoi diff --no-pager` | test module은 없음(N=0)이다. command가 exit 0이고 reviewer가 task-owned target의 의도한 diff만 있으며 profile root 선생성, 민감 material과 task 밖 drift가 없음을 기록해야 한다. |
| CMD-15 | `git diff --exit-code 72ad4f24e9df5919773cb877de01007f641ae163 -- .gitignore && /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_issue_118_task_owned_path_allowlist -k test_no_persistent_or_external_mutation` | `.gitignore` diff가 0이고 명명 module의 고유 두 ID가 각각 정확히 선택되어 N=2, `testsRun=2`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이며 R10.2 allowlist 밖 변경과 external mutation이 0건이다. |
| CMD-16 | `CREATE_WORKTREE_E2E_NETWORK=deny /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_cold_start_missing_profile_and_repository_parent -k test_wrapper_cold_start_contract` | 명명 module의 두 ID가 각각 정확히 선택되어 N=2, `testsRun=2`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 cold-start Workmux/wrapper lifecycle이 통과한다. |
| CMD-17 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree -k test_runtime_lock_journal_contract -k test_stale_transaction_requires_reviewed_recovery` | 명명 module의 두 ID가 각각 정확히 선택되어 N=2, `testsRun=2`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 runtime lock/journal lifecycle과 stale refusal이 통과한다. |
| CMD-18 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_create_worktree --id tests.test_create_worktree.CreateWorktreeInventoryTests.test_judgement_command_selection_contract --expect-count 1` | `-k`에 의존하지 않는 direct ID가 정확히 존재해 N=1, `testsRun=1`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 empty·partial·duplicate·skip 계열 synthetic runner fixture는 모두 거부된다. |
| CMD-19 | `/opt/homebrew/bin/python3 tests/run_unittest_contract.py --module tests.test_orchestrator_profiles --id tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_changed_path_allowlist --id tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_file_ownership --id tests.test_orchestrator_profiles.OrchestratorProfileContractTests.test_portable_cli_contract --expect-count 3` | R10.5의 tests-only 정정 뒤 세 direct ID가 정확히 존재해 N=3, `testsRun=3`, failures=errors=skipped=expectedFailures=unexpectedSuccesses=0이고 stale base·missing evidence·#118 산출물 금지 조건이 제거된다. |
| CMD-20 | `tmpdir="$(mktemp -d)" || exit 1; trap 'rm -rf "$tmpdir"' EXIT; printf '%s\n' 'import unittest' 'class KnownBad(unittest.TestCase):' '    def test_known_bad(self):' '        self.fail("synthetic failure")' > "$tmpdir/test_runner_known_bad.py" || exit 1; PYTHONPATH="$tmpdir" /opt/homebrew/bin/python3 -c 'import test_runner_known_bad' || exit 1; PYTHONPATH="$tmpdir" /opt/homebrew/bin/python3 tests/run_unittest_contract.py --module test_runner_known_bad --all --min-count 1 >/dev/null 2>&1; runner_status=$?; test "$runner_status" -ne 0` | temp known-bad module의 import가 먼저 exit 0이고, runner 출력·counter와 독립적으로 외부 shell이 포착한 runner process 종료 코드가 nonzero이며 unconditional-zero runner에서는 마지막 `test`가 nonzero다. trap cleanup도 실행된다. |

최종 실행 순서는 CMD-20 runner 독립 negative gate, CMD-18 runner/manifest contract, CMD-19 선행 gate 정정, CMD-1~CMD-11 targeted/contract, CMD-16 cold-start, CMD-17 runtime recovery, CMD-9 high-risk E2E 재확인, CMD-12 regression, CMD-13 inventory/full discovery, CMD-15 scope, CMD-14 operator diff review다. real Workmux case는 host state에 대해 `--dry-run`만 사용하고 mutation case는 temp Git과 isolated tmux에서 검증한다. 테스트는 profile 이름과 root를 fixture registry에서 생성해 implementation hardcoding을 감지한다.

## Decisions

### D1. 새 `workspace_profiles`와 `repositories` table을 기존 mapping 옆에 둔다

대안 1은 `workspace_directory_mappings` row에 `workspace_profile`, canonical repository와 destination 정보를 추가하는 것이다. provider마다 같은 root/repository가 반복되고 Codex 공통 binding 때문에 profile enum이 중복되며 기존 row unknown-field rejection과 직접 충돌한다. 대안 2는 account row에 workspace root/repository를 넣는 것이다. account와 placement가 결합되어 같은 Codex account를 여러 profile에 쓰는 계약을 표현하기 어렵다. 대안 3은 별도 `workspace_profiles(name, root, provider_bindings)`와 `repositories(id, canonical_path, workspace_subdir)`를 두는 것이다.

대안 3을 권고한다. 기존 mappings는 current-cwd launcher compatibility를 위해 유지하고 새 tables는 creation placement의 유일 source가 된다. parser는 profile binding과 active account/scope coherence를 검증해 두 view의 drift를 fail closed한다. 새 parser/old registry는 create만 unavailable이고 기존 launch는 유지되며 old parser/new registry는 unknown field로 안전하게 중단한다. schema version을 즉시 바꾸어 dual parser를 장기 유지하는 것보다 field allowlist와 mixed-deployment tests가 범위를 작게 유지한다.

### D2. public backend는 별도 `dot_local/bin/` command, resolver는 import-only shared module로 둔다

대안 1은 `ai-session resolve-worktree-path` 또는 전체 create subcommand다. registry parser 재사용은 쉽지만 1,957-line account launcher에 Git/gh/Workmux/tmux transaction과 rollback까지 결합되고, 기존 `select --directory`의 current-cwd invariant를 약화할 위험이 있다. 대안 2는 `dot_local/libexec/` executable을 skill prose가 직접 호출하거나 prose만으로 계산하는 방식이다. public discoverability와 stable CLI가 약하고 prose-only는 자동 test/rollback/TUI 재사용이 불가능하다. 대안 3은 전용 `dot_local/bin/executable_create-worktree`와 import-only shared registry/path module이다.

대안 3을 권고한다. backend는 plan/apply, mutation ownership과 exit taxonomy를 한 곳에서 소유하고, skill과 미래 TUI는 같은 public command를 호출한다. shared module 추출은 선택이 아니라 필수이며 `ai-session`과 backend가 동일 parser/field constants/path API를 import한다. module은 candidate repository parent를 명시적으로 받는 pure API라 `ai-session select`의 실제 cwd equality를 건드리지 않고, executable entrypoint가 아니므로 backend 계약이 둘로 갈라지지 않는다.

### D3. Workmux `--config` one-key override를 기본 adapter로 쓴다

대안 1은 mode 0600 temp config에 `worktree_dir`만 넣고 `--config`로 global config와 병합하는 방식이다. 대안 2는 `git worktree add`로 직접 생성하고 `workmux open`만 호출하는 adapter다. 목적지는 완전히 통제되지만 PR fetch/OID, base/naming/hook semantics를 재구현해야 한다. 대안 3은 global Workmux config를 호출마다 고치는 방식으로 다른 동시 작업과 chezmoi drift를 만든다.

대안 1을 권고한다. v0.1.248 P1 실측은 존재하지 않는 parent를 지정해도 dry-run이 `<root>/<workspace_subdir>/<destination_basename>`을 mutation 없이 출력하고 global auto base와 Nerd Font naming을 유지함을 보였다. Q1은 `{project}` 없는 리터럴 repository parent override에서도 출력 dirname이 byte-identical임을 확인했다. backend는 parent까지만 독립 계산하고 Workmux 출력에서 destination basename을 취득하므로 naming을 재구현하지 않는다. Q2의 조건부 `Handle:`은 참고 값일 뿐이고 registry `workmux_handle`은 Q4가 확인한 `workmux list --json`의 path/handle pair를 exact path로 조회한다. alternate config에는 worktree_dir 외 key를 금지해 panes/base/naming/hooks/nerdfont/status_format의 merge를 Workmux에 맡긴다. dry-run이 노출하지 않는 pane/status/hook는 isolated tmux E2E로 확인한다. 반환 parent가 독립 계산값과 다르면 adapter로 fallback하지 않고 preflight failure다.

### D4. chezmoi 선생성을 금지하고 backend가 exact parent만 지연 생성한다

대안 1은 install/setup에서 모든 profile roots를 미리 만드는 방식이지만 사용하지 않는 profile과 repository tree까지 host state를 만들고 invalid config도 directory를 남긴다. 대안 2는 Workmux가 ancestor를 암묵 생성하도록 맡기는 방식으로 validation-before-create와 ownership evidence가 약하다. 대안 3은 backend가 모든 검증과 dry-run 뒤 missing component를 하나씩 만들고 기록하는 방식이다.

대안 3을 권고한다. P1은 missing-root dry-run이 선행할 수 있음을, P2는 backend parent 생성이 ownership을 위해 필수임을, P3는 worktree remove 뒤 journal-owned 빈 component를 backend가 직접 지워야 함을 각각 증명한다. 따라서 A1/A2를 직접 만족하고 preflight failure 전 directory 0건, rollback의 exact owner evidence를 제공한다. source scan은 shipped profile literal만 찾지 않고 registry roots를 읽어 R3.3의 대상과 pattern별 fixture를 검사한다.

### D5. pre-state journal과 reverse rollback을 transaction 경계로 삼는다

대안 1은 실패 때 destination subtree를 재귀 삭제하는 방식으로 pre-existing data를 지울 수 있어 금지한다. 대안 2는 실패를 보고만 하고 partial artifact를 모두 남기는 방식으로 반복 호출과 binding을 오염시킨다. 대안 3은 pre-state와 create result의 set difference로 소유권을 정하고 window→worktree→branch→empty directories 역순으로 정리하는 방식이다.

대안 3을 권고한다. journal은 R7.5 per-user runtime root에 mode 0600으로 두고 apply 동안만 유지하되 crash recovery를 위해 fsync한다. repository digest lock의 exact JSON이 PID, boot identity와 소유 journal UUID를 묶고, 다음 호출은 그 UUID로 journal을 직접 찾아 교차 검증하므로 repository lock에서 crash transaction으로의 조회가 결정적이다. 이는 profile root 선생성이나 #94/#95를 복제한 영구 registry가 아니다. OID/window ID/path identity가 바뀌거나 dirty/non-empty이면 force하지 않고 rollback incomplete로 승격한다. wrapper/hook의 arbitrary external side effect는 일반적 역연산이 없으므로 remaining inventory와 reviewed recovery를 보고한다. 이 보수성은 완전 자동 cleanup보다 user data 보존을 우선한다.

### D6. profile omission과 provider admission을 분리한다

대안 1은 target session이나 provider default account에서 profile을 추론하는 방식이고 요구된 독립성을 깨뜨린다. 대안 2는 profile을 항상 필수로 만들어 ambiguity를 없애지만 이미 profile root 안에서 호출하는 안전한 legacy usage를 불필요하게 깨뜨린다. 대안 3은 real cwd가 유일 profile root 안일 때만 생략을 허용하고 기준 저장소에서는 명시를 요구하는 방식이다.

대안 3을 권고한다. profile이 정해지면 provider binding은 registry에서 모두 계획하지만 AI admission은 하지 않는다. 따라서 Claude verifier follow-up이 미해결이어도 creation AC는 통과하고, Codex는 모든 profile에서 초기 단일 binding을 유지한다.

### D7. 판정 명령은 exact-selection contract runner를 사용한다

대안 1은 기존 `python -m unittest ... -k ...`의 exit 0을 그대로 신뢰하는 방식이지만 0건 또는 일부만 선택돼도 통과할 수 있다. 대안 2는 표의 기대 건수를 사람이 출력에서 확인하는 방식으로 반복 가능성과 누락 방지가 약하다. 대안 3은 stdlib-only runner가 fully-qualified manifest, exact method 선택, 수집 N과 `TestResult` counter를 함께 검증하는 방식이다.

대안 3을 권고한다. targeted command는 `-k` 수를 N으로 고정하고 module 전체/discovery는 실행 직전 수집한 N과 baseline 하한을 함께 기록한다. manifest meta-test와 runner contract test는 direct fully-qualified ID로 실행하므로 자신이 사라져도 `NO TESTS RAN`으로 통과하지 않는다. skip과 expected failure도 완료 증거로 인정하지 않는다.

### D8. #103 전용 gate를 current-main 기준으로 tests 안에서 정정한다

대안 1은 97 tests/3 failures를 known failure로 허용하는 방식이지만 full-suite 완료 gate를 약화한다. 대안 2는 #118 산출물을 #103 당시 allowlist 밖에 두는 방식으로 구현 즉시 실패한다. 대안 3은 current main을 base로 갱신하고 #118 task-owned 경로를 명시하며 존재하지 않는 evidence 의존을 두 `tests/` 파일에서 제거하는 방식이다.

대안 3을 권고한다. `dot_claude/skills/create-worktree`만 preserved set에서 빼 R9.1과의 모순을 해소하고 Workmux/tmux/zsh source는 계속 보존한다. gate migration은 product source나 runtime semantics를 바꾸지 않으며 정정 전 97/3 baseline과 정정 후 실패 0을 모두 증거로 남긴다.

### D9. 조회 전 adapter 실패는 진단과 소유권 판정을 분리한다

대안 1은 rollback 때 destination 항목을 무조건 제거하는 방식으로 pre-existing state를 손상할 수 있다. 대안 2는 조회하지 않고 누락하는 방식으로 잔여 registry 항목을 보고하지 못한다. 대안 3은 exact-path diagnostic list를 한 번 수행하되 successful registration evidence가 있을 때만 소유권 근거에 결합하고, 그 외에는 remaining inventory로 남기는 방식이다.

대안 3을 권고한다. 진단 read 자체는 R7.1의 성공한 command 결과 조건을 대체하지 않는다. 소유권이 불명확한 항목은 force하지 않고 artifact type과 비민감 destination으로 보고해 데이터 보존과 복구 가시성을 함께 유지한다.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

신뢰 입력은 reviewed strict registry bytes, canonical Git metadata, backend code와 validated Workmux/wrapper capability다. 사용자 branch/PR/profile/session 문자열, filesystem names, symlinks, `gh`/wrapper/Workmux output, tmux state와 optional binding adapter 응답은 검증 전 신뢰하지 않는다. registry→resolver, resolver→filesystem, backend→external commands, pre-state→mutation, result→public output이 주요 trust boundary다.

공격/오류 case는 path traversal과 prefix confusion, malicious symlink swap, registry unknown field, repository spoofing, forged dry-run destination, destination basename을 Workmux handle로 혼동하는 오류, exact-path list 매칭 실패, concurrent branch/window 생성, runtime-root symlink·permission 및 lock→journal pointer 변조, wrapper partial failure와 sensitive subprocess output이다. strict allowlists, shared parser/path module, realpath containment, common-dir match, no-follow lock+journal, UUID/digest 교차 검증, exact post-check, redacted schemas와 fault injection이 control이다.

### Authorization and tenant isolation

원격 tenant authorization은 해당 없음이다. 이 기능은 local linked-worktree 생성이며 provider tenant나 credential을 조회하지 않기 때문이다. 다만 workspace profile isolation은 policy boundary로 적용한다. 요청 profile의 root/scope와 existing worktree root가 다르면 `blocked_binding`이고 다른 profile로 이동·재사용하지 않는다. 이 profile boundary는 filesystem ACL이나 repository security isolation으로 표현하지 않으며 Git common-dir가 canonical repository에 남는 사실을 문서화한다.

### Migration, compatibility, and rollback

배포 순서는 shared parser/backend와 tests, schema data, skills/docs 순의 한 reviewed change다. mixed-deployment에서는 old parser가 new field를 거부하고 new backend가 old registry에서 create를 거부하므로 wrong destination으로 degrade하지 않는다. 기존 `ai-session` launch semantics와 `workspace_directory_mappings`는 유지한다.

implementation rollback은 task-owned source files을 pre-change bytes로 복구하고 full tests/chezmoi diff를 다시 수행한다. runtime apply의 rollback은 R7 transaction이다. 이미 성공해 사용 중인 worktree를 source rollback만으로 이동/삭제하지 않으며 새 schema data 제거 전 binding/reference 0을 확인한다. main merge와 `chezmoi apply`는 automated workflow 밖의 operator action이다.

### Failure recovery and observability

각 backend event는 stable status, phase, planned destination, existing/created/reused와 rollback summary를 한 줄 public JSON으로 남긴다. 비밀 원문, raw subprocess output, traceback은 남기지 않는다. exit 1은 내부 결함과 pre-state 복원을 확인한 뒤 수정, exit 5는 input/capability/dry-run 또는 stale transaction을 reviewed recovery한 뒤 새 plan, exit 6은 pre-state가 복원됐는지 확인한 뒤 retry, exit 7은 remaining inventory를 수동 조사하고 새 plan 전에 stale lock/journal을 reviewed 절차로 해소한다. catch 불가능한 signal은 다음 호출의 durable journal 진단으로 관찰한다.

Metrics/remote alerting은 해당 없음이다. 개인 host의 on-demand CLI이며 production service가 아니기 때문이다. 대신 deterministic exit/status, transaction phase, isolated test call logs와 post-check 결과가 진단 신호다.

### High-risk end-to-end verification

CMD-9는 temp canonical Git repository, 두 arbitrary profile roots, temp strict registry, fake PR/gh와 isolated tmux shim/socket을 만들고 branch/PR create, same-profile reuse, cross-profile block, global config preservation, Git common-dir/HEAD/pane cwd post-check를 실행한다. CMD-16은 두 parent가 모두 없는 cold-start에서 P1 순서와 P2/P3 ownership lifecycle을 검증한다. CMD-7은 symlink swap과 parent/worktree/branch/window 단계 fault를, CMD-17은 runtime-root/stale transaction fault를 주입해 owner-only rollback과 reviewed recovery를 증명한다.

중단 조건은 actual user root/default tmux/network/provider/verifier 접근 sentinel hit, unexpected persistent path, pre-existing identity/byte drift, sensitive marker 유출, cross-profile mutation, failed realpath/common-dir/OID/pane check 중 하나다. 어떤 high-risk case도 skip이면 통과할 수 없다.

### No production mutation confirmation

자동 Spec/Plan/implementation 검증에는 production mutation이 없다. 실제 인증 home, user worktree, default tmux, network/provider, main merge, deployment와 `chezmoi apply`를 사용하지 않는다. real Workmux는 `--version`, help/docs와 `--dry-run`만 허용하고 mutation E2E는 temp Git과 isolated tmux에서 수행한다. 최종 local apply는 모든 gate 후 사용자가 별도로 승인·실행하는 운영 단계다.

<!-- strict-only:end -->
