# Quality Goal Implementation Plan

- Task ID: 20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900
- Mode: strict
- Status: DRAFT
- Created: 2026-09-11
- Updated: 2026-09-11
- Source goal: #105 dual-review 실행 결함 수정: 모델 선택·producer stdin 즉시 전달·reviewer/critique/synthesis strict schema 계약·chezmoi 설치본 패키징

## Spec link

- 승인된 Spec: `docs/development/2026-09-11-105-fix-dual-review-runtime-2/spec.md`
- 구현 기준 SHA-256: `186e1eb4e27bb29cef181ca5556440585250737b78518c856d229589ca6cee4e`
- Spec 심사: `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/reviews/spec-r2b.json` — PASS, score 89, blockers 0
- 보존 실행 근거 색인: `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/INDEX.md`

## Global constraints

- 구현 범위는 `dot_claude/skills/dual-review/`와 저장소 루트 `.chezmoiignore`로 한정한다. 제품 저장소 `zambaguni-front`의 추적 파일은 수정하지 않는다.
- 모든 행위 변경은 실패 테스트 작성 → 의도한 실패 확인 → 최소 구현 → 같은 테스트 통과 확인 순서로 수행한다. 태스크 사이에는 선행 태스크의 통과 상태를 유지한다.
- Python 3.14.7과 표준 라이브러리만 사용한다. 특히 `scripts/*.py`, `tests/test_live_api.py`, `tests/live_e2e.py`에 제3자 import를 추가하지 않는다.
- `tests/test_contracts.py::PackagingContractTests.test_no_mutation_contract`가 스킬의 `.md`·`.py`·`.json` 전체에서 금지된 자동 변형 명령 문자열을 검사하므로, 스킬 소스의 코드·문서에는 해당 문자열을 직접 쓰지 않는다. 명령 식별자가 필요한 문서에서는 기존의 안전한 대체 토큰을 유지한다.
- chezmoi 검증은 `chezmoi archive --source <worktree>`와 임시 디렉터리만 사용한다. `$HOME` 설치본 적용은 이 workflow 밖의 별도 주체가 수행하며, 어떤 검증도 `$HOME`을 변경하지 않는다.
- 제품 저장소 실증은 읽기 전용 모델 호출과 ignore되는 로컬 `.claude/dual-review-state/<run-id>/` 생성만 허용한다. commit, push, PR 생성, review 게시, comment 게시를 하지 않는다.
- 기존 제품 실행 `e7a6d2872362a4d6-000001`과 이 task의 `.claude/quality-state/.../evidence/`를 삭제·덮어쓰기·번호 초기화하지 않는다. 새 evidence와 run은 별도 증가 경로에 남긴다.
- type check, lint, build는 이 저장소에 구성돼 있지 않다. `references/verification.md`를 근거로 각각 `not configured`로 기록하며 성공으로 보고하지 않는다.
- 구현·테스트·코드 리뷰 뒤 dotfiles 저장소의 관련 변경만 commit·push하고 PR을 만드는 작업은 별도 승인된 통합 단계다. 본 Plan의 판정 명령에는 포함하지 않는다.
- Spec의 D9를 그대로 적용해 Claude producer 무소견은 `stdout.strip() == "NO_FINDINGS"`인 경우에만 인정한다. 이 엄격 동치는 자유 문구를 무소견으로 오인하는 fail-open을 막고 기존 markdown wire 형식을 넓히지 않기 위한 선택이다. 대신 prompt가 이 규칙을 명시하게 하고, 위반 시 원시 stdout과 `missing_no_findings_marker`, `nonexclusive_no_findings_marker`, `all_findings_rejected`를 구분해 보존한다.
- Spec advisory 해소는 다음과 같이 고정한다.
  - `SPEC-008`: T4에서 `build_round_zero_prompts()['claude']`에 `NO_FINDINGS`와 finding 블록과의 배타 사용 규칙이 모두 있는지 `test_round_zero_claude_prompt_requires_exclusive_no_findings_marker`로 판정한다.
  - `SPEC-009`: Plan의 CMD-1에 기존 `test_round_zero_starts_every_adapter_before_any_result_is_read`와 `test_live_shape_starts_five_claude_producers_and_codex_before_reads`를 추가해 2-adapter와 production 6-producer 시작 순서를 모두 직접 판정한다.
  - `SPEC-010`: 엄격 동치를 유지하고 T4의 `test_no_findings_marker_requires_exact_stdout_and_preserves_diagnostics`로 앞뒤 자유 문구·finding 혼합을 거부하며, producer raw JSON에 원시 stdout과 세분화된 reason이 남는지 확인한다. 기존 zero-parse 테스트는 표지 없는 자유 문구가 계속 실패한다는 회귀 가드로 유지한다.

## File map

| 파일/경로 | 조치 | 책임과 영향받는 인터페이스 |
|---|---|---|
| `docs/development/2026-09-11-105-fix-dual-review-runtime-2/plan.md` | 생성 | 승인 전 구현 handoff인 이 Plan. 구현 단계에서는 읽기 전용이다. |
| `docs/development/2026-09-11-105-fix-dual-review-runtime-2/spec.md` | 조사, 변경 없음 | 승인 요구사항·AC·CMD의 정본이다. |
| `docs/development/2026-09-11-105-fix-dual-review-runtime-2/spec-revision-notes.md` | 조사, 변경 없음 | Spec 라운드 2 파급·치환 근거다. |
| `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/reviews/spec-r2b.json` | 조사, 변경 없음 | `SPEC-008`~`SPEC-010` advisory의 정본이다. |
| `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/` | 기존 보존, 검증 evidence 추가 | P0~P8은 불변이다. CMD-4/6/7/8의 환경·slash·schema-live·E2E 원시 evidence를 별도 파일로 추가한다. |
| `dot_claude/skills/dual-review/SKILL.md` | 수정 | frontmatter `model`을 `opus`로 고정한다. slash routing과 Python 진입점 위임 문맥은 보존한다. |
| `dot_claude/skills/dual-review/scripts/review_state.py` | 수정 | `build_codex_command`, `build_round_zero_prompts`, `SubprocessAdapter.start/read`, `_round_zero`, `run_dual_review`, `main`, `scan_source_texts`를 변경한다. `SubprocessAdapter` handle은 정확히 `(process, source, prompt_path, output_path, before)` 순서로 유지해 `handle[3] == output_path`인 기존 인덱스 계약을 보존한다. prompt/EOF 수명주기, strict producer 유효성, raw reason, 여섯 producer gate, 종료 코드를 소유한다. |
| `dot_claude/skills/dual-review/schemas/reviewer.schema.json` | 수정 | 재귀적으로 닫힌 reviewer wire contract와 유효한 `findings: []`를 정의한다. |
| `dot_claude/skills/dual-review/schemas/critique.schema.json` | 수정 | 모든 object를 닫고 `new_findings.items`의 normalization 필드를 모두 required로 정의한다. |
| `dot_claude/skills/dual-review/schemas/synthesis.schema.json` | 수정 | decision과 `claims`를 포함한 모든 object를 닫고 명시적 type을 갖게 한다. |
| `dot_claude/skills/dual-review/references/operation.md` | 수정 | Claude Code 2.1.268의 확인 기능 목록, production emit 목록, CMD-6 하니스 목록을 분리하고 stdin/EOF 및 가변 `--allowedTools` 경계를 문서화한다. |
| `dot_claude/skills/dual-review/references/verification.md` | 수정 | 자체 명령을 `DRV-1`부터 재번호하고 신규 deterministic/live/archive 검증, Python 3.14.7 evidence, `not configured` 범주를 설명한다. Spec 명령은 `Spec CMD-<n>`으로만 참조한다. |
| `dot_claude/skills/dual-review/templates/report.md` | 조사, 변경 없음 | `render_report()`가 소비하는 기존 heading 계약을 보존한다. 신규 진단은 기존 `Reviewer status` 행과 raw/provenance JSON으로 노출한다. |
| `dot_claude/skills/dual-review/tests/test_contracts.py` | 수정 | model/command tuple, Claude 기능 대 production emit, recursive schema, prompt marker, packaging, scanner, live helper 정적 계약을 고정한다. |
| `dot_claude/skills/dual-review/tests/test_execution.py` | 수정 | start-before-read, regular-file stdin/EOF/cleanup, 엄격 marker와 raw reason, validation-only normalization, 여섯 producer gate, report, `main()` exit를 실제 subprocess와 fixture로 고정한다. |
| `dot_claude/skills/dual-review/tests/test_live_api.py` | 생성 | `unittest` opt-in API probe. 두 환경변수, 기본 skip, production builder 호출, `$schema`-only 진단, 호출별 evidence 보존을 제공한다. |
| `dot_claude/skills/dual-review/tests/live_e2e.py` | 생성 | 여덟 필수 CLI option, 제품 precondition, merge-base, 실행 전 run 번호 관측, review 실행, phase/run-id/무변경 사후 판정을 제공한다. |
| `dot_claude/skills/dual-review/tests/test_critique.py` | 조사, 변경 없음 | strict critique schema와 normalization 변경 뒤 기존 critique 의미 회귀를 CMD-4/CMD-5로 확인한다. |
| `dot_claude/skills/dual-review/tests/test_normalization.py` | 조사, 변경 없음 | group-independent 선행 validation이 기존 stable ID·normalization 계약을 깨지 않는지 확인한다. |
| `dot_claude/skills/dual-review/tests/test_reporting.py` | 조사, 변경 없음 | raw/provenance reason 추가 뒤 기존 report heading·복원 계약을 확인한다. |
| `dot_claude/skills/dual-review/tests/test_rounds.py` | 조사, 변경 없음 | 여섯 producer gate 이후 critique round 정책이 유지되는지 확인한다. |
| `dot_claude/skills/dual-review/tests/test_synthesis.py` | 조사, 변경 없음 | synthesis schema 폐쇄 뒤 익명 view와 coverage 계약을 확인한다. |
| `dot_claude/skills/dual-review/schemas/.gitkeep` | 삭제 | chezmoi archive에 배포되지 않는 무효 필수 경로를 제거한다. |
| `dot_claude/skills/dual-review/scripts/.gitkeep` | 삭제 | 실제 `review_state.py`가 디렉터리를 유지하므로 불필요한 marker를 제거한다. |
| `.chezmoiignore` | 수정 | `.claude/skills/dual-review/**/__pycache__`를 archive에서 제외한다. |
| `/Users/lee-kyu-hwan/code/zambaguni-front-landing-noindex/.claude/dual-review-state/` | 읽기 및 ignore된 새 run 생성만 | 기존 `e7a6d2872362a4d6-000001`을 보존하고 계산된 접두사의 다음 번호에 E2E 산출물을 쓴다. 제품 추적 파일은 변경하지 않는다. |

## Task dependencies

1. T1이 model·CLI·문서 용어 계약을 확정한다.
2. T2와 T3은 T1 뒤에 순서대로 수행한다. T2가 stdin/EOF process 경계를, T3이 structured schema 경계를 확정하며 서로의 파일은 겹치지 않는다.
3. T4는 T2의 adapter lifecycle과 T3의 빈-array schema 의미를 소비해 producer ingestion과 종료 정책을 구현한다.
4. T5는 T1~T3의 production builder와 schema를 소비해 live API probe를 만든다. canonical Claude schema가 거부되면 T3으로 돌아가 루트 `$schema`만 shared schema 세 파일에서 함께 제거한 뒤 T1~T5 deterministic gate를 다시 실행하거나 `NEEDS_REDESIGN`으로 중단한다.
5. T6은 T1, T2, T4, T5가 제공한 production 실행·진단 계약을 소비해 E2E helper를 만든다.
6. T7은 T5와 T6의 신규 파일이 존재한 뒤 packaging required path와 source/archive 동등성을 확정한다.
7. 구현은 좁힌 직렬 배치로 수행한다: B1=T1~T2, B2=T3~T4, B3=T5~T7과 T8이다. 공유 파일 `review_state.py`, `test_contracts.py`, `test_execution.py`에 병렬 수정하지 않는다. B1은 T2의 보완 CMD-1·CMD-2·CMD-4가 모두 통과해야 B2로, B2는 CMD-2·CMD-3·advisory 진단·CMD-4가 모두 통과해야 B3로 넘어간다. B3의 deterministic/archive 단계는 CMD-1~CMD-5가 모두 통과해야 T8의 CMD-6~CMD-8을 시작한다.
8. 추적 파일 rollback의 1차 수단은 baseline commit `067923b554f159cf8c12e37f353f572951824b41`에서 태스크 소유 경로만 복원하는 `git checkout 067923b554f159cf8c12e37f353f572951824b41 -- <경로...>`이다. 태스크별 `/tmp` 사본과 셸 변수는 같은 셸 세션에서만 쓰는 보조 수단이며, 기존 evidence와 제품 run은 어느 rollback에도 포함하지 않는다.

## Tasks

### T1. 모델·CLI command와 운영 문서 계약 고정

대상 AC: AC-1 (CMD-6), AC-2 (CMD-2 CMD-1), AC-3 (CMD-2), AC-18 (CMD-2)

의존성: 없음. T2, T5, T6의 선행 계약이다.

1. 변경 전 사본을 만든다: `t1_backup="$(mktemp -d /tmp/dual-review-t1.XXXXXX)" && cp -p dot_claude/skills/dual-review/SKILL.md "$t1_backup/SKILL.md" && cp -p dot_claude/skills/dual-review/scripts/review_state.py "$t1_backup/review_state.py" && cp -p dot_claude/skills/dual-review/references/operation.md "$t1_backup/operation.md" && cp -p dot_claude/skills/dual-review/references/verification.md "$t1_backup/verification.md" && cp -p dot_claude/skills/dual-review/tests/test_contracts.py "$t1_backup/test_contracts.py"`. 기대 결과는 다섯 사본이 모두 regular file인 것이다.
2. `test_packaging_contract`에 frontmatter `model == "opus"`, Claude Code 2.1.268 기능 목록/production emit/CMD-6 하니스 목록의 분리 assertion을 추가한다. `test_reviewer_contract`에는 reviewer/critique 양쪽 `build_codex_command()`의 정확한 tuple, 단일 `--model gpt-5.6-sol`, 단일 마지막 `-`, 위치 prompt 부재, 기존 read-only/schema/JSON/last-message 보존 및 `used_flags` 허용 집합의 `-`를 추가한다. `references/verification.md`의 `DRV-*`, `Spec CMD-*`, Python 3.14.7, `not configured` 문언 assertion도 추가한다.
3. 실패 검증: `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py'`
   - 기대 결과: 구현 전 `model: claude`, Claude Code 2.1.263 문언, 누락된 Codex model/마지막 `-`, 기존 `CMD-*` 문서 때문에 새 assertion이 FAIL한다. 기존 무관 assertion의 error는 없어야 한다.
4. 최소 구현: `SKILL.md`를 `model: opus`로 바꾸고, `build_codex_command()`가 기존 option 뒤에 `--model`, `gpt-5.6-sol`, 최종 `-`를 정확히 배치하게 한다. `operation.md`에서 확인 기능, production emit, 검증 하니스 flag를 별도 표/단락으로 분리하고 stdin prompt·EOF·allowlist 뒤 위치 prompt 금지를 명시한다. `verification.md` 자체 표를 `DRV-1`부터 재번호하고 신규 gate와 Python 버전 evidence를 반영한다.
5. 통과 검증: 3번과 같은 명령을 실행한다.
   - 기대 결과: contract suite가 비어 있지 않고 exit 0이며 model, 두 Codex command 변형, Claude 세 command 변형, 문서의 세 경계와 식별자 체계가 모두 일치한다.
6. 실패 처리·롤백: 새 assertion 이외의 기존 계약이 깨지거나 command tuple에 read-only/schema/JSON/last-message 중 하나가 빠지면 T1을 중단한다. 1차 rollback은 `git checkout 067923b554f159cf8c12e37f353f572951824b41 -- dot_claude/skills/dual-review/SKILL.md dot_claude/skills/dual-review/scripts/review_state.py dot_claude/skills/dual-review/references/operation.md dot_claude/skills/dual-review/references/verification.md dot_claude/skills/dual-review/tests/test_contracts.py`다. 같은 셸 세션에서는 1번의 `$t1_backup` 사본을 보조 수단으로 쓸 수 있다. 보존 evidence와 제품 run은 건드리지 않는다.

### T2. start 시점 regular-file stdin과 자원 수명주기 구현

대상 AC: AC-2 (CMD-2 CMD-1), AC-4 (CMD-1 test_round_zero_starts_every_adapter_before_any_result_is_read test_live_shape_starts_five_claude_producers_and_codex_before_reads), AC-5 (CMD-1 test_subprocess_adapter_large_prompt_does_not_block_start), AC-6 (CMD-1 test_subprocess_start_failure_cleans_its_temporary_output을)

의존성: T1 통과. `build_codex_command()`의 마지막 `-`와 adapter EOF를 서로 독립적으로 판정한다.

1. 변경 전 사본을 만든다: `t2_backup="$(mktemp -d /tmp/dual-review-t2.XXXXXX)" && cp -p dot_claude/skills/dual-review/scripts/review_state.py "$t2_backup/review_state.py" && cp -p dot_claude/skills/dual-review/tests/test_execution.py "$t2_backup/test_execution.py"`. 기대 결과는 두 사본이 모두 regular file인 것이다.
2. `test_subprocess_adapter_delivers_prompt_before_read_after_delay`, `test_subprocess_adapter_large_prompt_does_not_block_start`, `test_subprocess_adapter_unextractable_exit_zero_cleans_temp_files`, `test_subprocess_adapter_invalid_output_last_message_json_cleans_temp_files`, `test_subprocess_adapter_timeout_kills_without_resending_and_cleans_prompt`를 먼저 작성한다. 실제 Python child가 3초 내 stdin readable, 262,145바이트 이상의 byte count/digest, EOF, 한 번 전송, exit 0 parse 실패, invalid last-message JSON, timeout 124, prompt/output 임시 경로 제거를 각각 관측하게 한다. 기존 `test_subprocess_start_failure_cleans_its_temporary_output`은 output뿐 아니라 prompt 임시 경로도 `Popen` 실패 뒤 사라지는지 확장한다. `test_subprocess_adapter_success_cleans_temporary_output`과 `test_timeout_mutation_is_nonretryable_and_cleans_temporary_output`은 `handle[3]` output-path 호환성과 cleanup을 계속 단정하고, `test_dispatches_constructed_prompts_before_any_read`는 생성된 prompt가 모든 read 전에 dispatch되는 계약을 계속 단정한다. 기존 `test_round_zero_starts_every_adapter_before_any_result_is_read`와 `test_live_shape_starts_five_claude_producers_and_codex_before_reads`의 fake adapter가 직접 반환하는 구조화 payload `findings: []`는 D4에 따라 이미 유효한 빈 배열이므로 T2에서 변경하지 않는다. stdout marker fixture로 바꾸는 작업은 parse 경계를 소유하는 T4로만 한정한다.
3. 실패 검증: 아래 보완된 CMD-1을 실행한다.

   `cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_execution.ExecutionTests.test_subprocess_adapter_delivers_prompt_before_read_after_delay test_execution.ExecutionTests.test_subprocess_adapter_large_prompt_does_not_block_start test_execution.ExecutionTests.test_subprocess_adapter_unextractable_exit_zero_cleans_temp_files test_execution.ExecutionTests.test_subprocess_adapter_invalid_output_last_message_json_cleans_temp_files test_execution.ExecutionTests.test_subprocess_adapter_timeout_kills_without_resending_and_cleans_prompt test_execution.ExecutionTests.test_subprocess_start_failure_cleans_its_temporary_output test_execution.ExecutionTests.test_subprocess_adapter_success_cleans_temporary_output test_execution.ExecutionTests.test_timeout_mutation_is_nonretryable_and_cleans_temporary_output test_execution.ExecutionTests.test_dispatches_constructed_prompts_before_any_read test_execution.ExecutionTests.test_round_zero_starts_every_adapter_before_any_result_is_read test_execution.ExecutionTests.test_live_shape_starts_five_claude_producers_and_codex_before_reads`

   - 기대 결과: 현행 `start()`가 prompt를 연결하지 않고 `read()`가 `communicate(prompt)`로 늦게 보내므로 지연·대용량·prompt cleanup assertion이 FAIL한다. 두 기존 순서 테스트는 회귀 기준을 제공한다.
4. 최소 구현: `start()`가 mode 0600 `NamedTemporaryFile`에 prompt를 완전히 기록·flush·seek한 뒤 열린 descriptor를 `Popen(stdin=...)`에 전달하도록 한다. `Popen` 뒤 부모 descriptor와 경로를 닫고 unlink하되 자식 descriptor는 파일 끝에서 EOF를 받게 한다. handle tuple은 정확히 `(process, source, prompt_path, output_path, before)` 순서로 고정하고 prompt 문자열은 보유하지 않는다. 따라서 기존 인덱스 소비자에 대해 `handle[3] == output_path`를 유지하며, `read()`도 같은 순서로 unpack한다. `read()`는 input 없는 `communicate(timeout=...)`로 수거하고 timeout kill 뒤에도 input 없이 다시 drain한다. 파일 작성·seek·command builder·`Popen` 실패 및 read finally에서 prompt/output 경로를 정리한다.
5. 통과 검증: 3번의 보완된 CMD-1을 실행한 뒤, 마지막으로 CMD-4와 동일한 `evidence_root="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/environment" && mkdir -p "$evidence_root" && PATH="/opt/homebrew/bin:$PATH" python3 -VV 2>&1 | tee "$evidence_root/python-version.txt" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import sys; assert sys.version_info[:3] == (3, 14, 7), sys.version' && env -u DUAL_REVIEW_LIVE_API PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -v`를 실행한다.
   - 기대 결과: 보완 CMD-1의 열한 테스트가 Python 3.14.7에서 exit 0이고, `handle[3]` output-path 계약, 모든 start-before-first-read, 생성 prompt dispatch, 대용량 prompt digest와 EOF, 모든 성공/실패 cleanup이 통과한다. 마지막 전체 discover는 수집 테스트 수가 0보다 크고 failure/error가 0이다.
6. 실패 처리·롤백: start가 child 소비를 기다리거나 handle 순서, prompt digest/EOF/한 번 전송/timeout 124/cleanup 중 하나가 어긋나면 T2를 중단한다. 1차 rollback은 `git checkout 067923b554f159cf8c12e37f353f572951824b41 -- dot_claude/skills/dual-review/scripts/review_state.py dot_claude/skills/dual-review/tests/test_execution.py`다. 같은 셸 세션에서는 보조로 `cp -p "$t2_backup/review_state.py" dot_claude/skills/dual-review/scripts/review_state.py && cp -p "$t2_backup/test_execution.py" dot_claude/skills/dual-review/tests/test_execution.py`를 쓸 수 있다. known-bad 지연 pipe 구현으로 부분 rollback하지 않는다.

### T3. 세 shared schema의 strict 폐쇄와 critique finding 계약 구현

대상 AC: AC-7 (CMD-2 test_schema_contract), AC-8 (CMD-2 test_critique_contract), AC-9 (CMD-7)

의존성: T1 통과. T5의 production provider probe가 이 산출물을 소비한다.

1. 변경 전 사본을 만든다: `t3_backup="$(mktemp -d /tmp/dual-review-t3.XXXXXX)" && cp -p dot_claude/skills/dual-review/schemas/reviewer.schema.json "$t3_backup/reviewer.schema.json" && cp -p dot_claude/skills/dual-review/schemas/critique.schema.json "$t3_backup/critique.schema.json" && cp -p dot_claude/skills/dual-review/schemas/synthesis.schema.json "$t3_backup/synthesis.schema.json" && cp -p dot_claude/skills/dual-review/tests/test_contracts.py "$t3_backup/test_contracts.py"`. 기대 결과는 네 사본이 모두 regular file인 것이다.
2. `test_schema_contract`, `test_critique_contract`, `test_synthesis_contract`를 먼저 확장한다. 재귀 walker가 모든 object에서 `additionalProperties is False`, 비어 있지 않은 `properties`, `set(required) == set(properties)`를 확인하고 모든 property/array item의 명시적 type과 string enum의 `type: string`을 검사하게 한다. reviewer `findings`의 `minItems` 부재와 빈 array 수용, 기존 `minimum`·`maximum`·`minLength`·`enum` 보존을 단정한다. critique `new_findings.items`에는 `severity`, `title`, `body`, `file`, `line_start`, `line_end`, `finding_confidence`, `recommendation`이 모두 required이고 누락·추가·타입 불일치 fixture가 test-local 표준 라이브러리 validator에서 거부되는지 확인한다.
3. 실패 검증: `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py'`
   - 기대 결과: 현행 열린 object, enum type 누락, 무제약 `new_findings.items` 때문에 schema 관련 테스트가 FAIL한다.
4. 최소 구현: 세 schema의 모든 object를 닫고 properties 전체를 required로 맞춘다. reviewer finding과 critique `new_findings`의 normalization 필드를 동일한 typed shape로 정의하되 reviewer `findings`에는 `minItems`를 두지 않는다. synthesis의 nested `claims`도 닫는다. 기존 range·length·enum 제약은 보존한다.
5. 통과 검증: 3번과 같은 명령을 실행한 뒤, 마지막으로 CMD-4와 동일한 `evidence_root="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/environment" && mkdir -p "$evidence_root" && PATH="/opt/homebrew/bin:$PATH" python3 -VV 2>&1 | tee "$evidence_root/python-version.txt" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import sys; assert sys.version_info[:3] == (3, 14, 7), sys.version' && env -u DUAL_REVIEW_LIVE_API PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -v`를 실행한다.
   - 기대 결과: recursive walker와 positive/negative fixture가 모두 exit 0이고 세 canonical schema가 shared file 하나씩으로 유지된다. 마지막 전체 discover는 수집 테스트 수가 0보다 크고 failure/error가 0이다.
6. 실패 처리·롤백: object 하나라도 열린 채 남거나 기존 검증 keyword가 사라지거나 `findings: []`가 거부되면 T3을 중단한다. 1차 rollback은 `git checkout 067923b554f159cf8c12e37f353f572951824b41 -- dot_claude/skills/dual-review/schemas/reviewer.schema.json dot_claude/skills/dual-review/schemas/critique.schema.json dot_claude/skills/dual-review/schemas/synthesis.schema.json dot_claude/skills/dual-review/tests/test_contracts.py`다. 같은 셸 세션에서는 1번의 `$t3_backup` 사본을 보조 수단으로 쓸 수 있다. live Claude 거부는 여기서 기존 열린 schema로 되돌리는 trigger가 아니며 T5의 `$schema`-only 분기를 따른다.

### T4. 명시적 무소견·여섯 producer gate·실패 진단과 종료 코드 구현

대상 AC: AC-12 (CMD-2 test_round_zero_claude_prompt_requires_exclusive_no_findings_marker CMD-3 test_explicit_no_findings_and_structured_empty_findings_are_valid test_no_findings_marker_requires_exact_stdout_and_preserves_diagnostics), AC-13 (CMD-3 test_failure_reports_keep_termination_and_reviewer_status), AC-14 (CMD-3 test_main_exit_code_distinguishes_incomplete_runs), AC-16 (CMD-8)

의존성: T2와 T3 통과. regular-file adapter와 유효한 structured 빈 배열을 전제로 한다.

1. 변경 전 사본을 만든다: `t4_backup="$(mktemp -d /tmp/dual-review-t4.XXXXXX)" && cp -p dot_claude/skills/dual-review/scripts/review_state.py "$t4_backup/review_state.py" && cp -p dot_claude/skills/dual-review/tests/test_contracts.py "$t4_backup/test_contracts.py" && cp -p dot_claude/skills/dual-review/tests/test_execution.py "$t4_backup/test_execution.py"`. 기대 결과는 세 사본이 모두 regular file인 것이다.
2. `test_round_zero_claude_prompt_requires_exclusive_no_findings_marker`를 먼저 추가해 `build_round_zero_prompts()['claude']`가 `NO_FINDINGS`, stdout 전체의 정확한 단독 한 줄 조건, finding 블록과 섞지 말라는 배타 규칙을 모두 포함하는지 검사한다. 이는 `SPEC-008`의 prompt 측 계약을 직접 판정한다.
3. CMD-3에 이름이 지정된 `test_explicit_no_findings_and_structured_empty_findings_are_valid`, `test_all_six_producers_must_return_valid_reviews`, `test_all_rejected_findings_are_incomplete`, `test_validation_only_normalization_needs_no_group_or_line_ranges`, `test_failure_reports_keep_termination_and_reviewer_status`, `test_main_exit_code_distinguishes_incomplete_runs`를 작성한다. 기존 `test_producer_markdown_that_parses_to_zero_findings_is_not_a_valid_review`, `test_zero_parse_producer_is_excluded_rather_than_reported_as_a_clean_review`, `test_invalid_finding_is_rejected_without_retrying_its_valid_source`는 Spec에 정한 유지/수정 관계대로 보존한다.
4. `SPEC-010` 전용 `test_no_findings_marker_requires_exact_stdout_and_preserves_diagnostics`를 작성한다. `"\n NO_FINDINGS \n"`만 빈 findings로 수용하고, `NO_FINDINGS` 앞뒤 자유 문구와 standalone marker+finding block은 한 번 재시도 뒤 각각 `nonexclusive_no_findings_marker`로 제외하며, marker 없는 자유 문구는 `missing_no_findings_marker`, 전 항목 normalization 거부는 `all_findings_rejected`로 구분하는지 검사한다. 각 경우 두 attempt의 원시 stdout이 producer별 `raw-<producer>.json`에 그대로 남고 report/provenance의 status reason이 일치하는지도 단정한다.
5. 실패 검증:
   - prompt 계약: `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py'`
   - ingestion 계약: `cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_execution.ExecutionTests.test_explicit_no_findings_and_structured_empty_findings_are_valid test_execution.ExecutionTests.test_producer_markdown_that_parses_to_zero_findings_is_not_a_valid_review test_execution.ExecutionTests.test_zero_parse_producer_is_excluded_rather_than_reported_as_a_clean_review test_execution.ExecutionTests.test_all_six_producers_must_return_valid_reviews test_execution.ExecutionTests.test_all_rejected_findings_are_incomplete test_execution.ExecutionTests.test_invalid_finding_is_rejected_without_retrying_its_valid_source test_execution.ExecutionTests.test_validation_only_normalization_needs_no_group_or_line_ranges test_execution.ExecutionTests.test_failure_reports_keep_termination_and_reviewer_status test_execution.ExecutionTests.test_main_exit_code_distinguishes_incomplete_runs`
   - advisory 진단: `cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_execution.ExecutionTests.test_no_findings_marker_requires_exact_stdout_and_preserves_diagnostics`
   - 기대 결과: 현행 prompt에 marker 지시가 없고 parser가 marker를 수용하지 않으며 source별 한 payload로 축약하고 all-rejected를 유효 처리하며 `main()`이 exit를 반환하지 않아 새 테스트가 FAIL한다. 기존 zero-parse와 valid+invalid 테스트는 의미 기준선으로 유지된다.
6. 최소 구현: Claude producer parse 경계에서 `stdout.strip() == "NO_FINDINGS"`만 `findings: []`와 `explicit_no_findings: true`인 유효 envelope로 승격한다. standalone marker line이 있으나 전체 strict equality가 아니면 `nonexclusive_no_findings_marker`, marker와 완전한 block이 모두 있으면 같은 fail-closed reason, marker도 완전한 block도 없으면 `missing_no_findings_marker`를 반환한다. `_round_zero()`의 group-independent helper는 `_markdown_records()`와 `normalize_reviewer_findings()`의 필드 primitive를 재사용하되 group label·stable ID·diff line range를 요구하지 않고, 전 항목 거부를 `all_findings_rejected`로 재시도하며 일부 거부+하나 이상 유효는 무재시도로 유지한다.
7. 최소 구현을 이어서 production mode의 다섯 Claude producer와 Codex를 producer별로 각각 유효 판정하고 하나라도 재시도 뒤 실패하면 `reviewer_failure`로 종료하며 critique/synthesis를 호출하지 않는다. legacy 2-adapter의 `reviewer_failure`/`single_reviewer`와 downstream `pipeline_failure`는 보존한다. raw record에는 producer, valid, explicit marker 여부, reason, attempts, stderr, exit code, 시도별 원시 stdout을 남긴다. `main()`은 terminal JSON/report 작성 뒤 `reviewer_failure`, `single_reviewer`, `pipeline_failure`에는 1, 나머지 정상 policy reason에는 0을 반환하고 module guard가 그 값을 `SystemExit`에 전달하게 한다.
8. 통과 검증: 5번의 세 명령을 모두 다시 실행한 뒤, 마지막으로 CMD-4와 동일한 `evidence_root="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/environment" && mkdir -p "$evidence_root" && PATH="/opt/homebrew/bin:$PATH" python3 -VV 2>&1 | tee "$evidence_root/python-version.txt" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import sys; assert sys.version_info[:3] == (3, 14, 7), sys.version' && env -u DUAL_REVIEW_LIVE_API PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -v`를 실행한다.
   - 기대 결과: contract CMD-2, CMD-3의 아홉 테스트, advisory 진단 테스트가 모두 exit 0이다. exact marker와 structured empty는 무재시도이고, free prose/mixed/all-rejected/transport 실패는 reason과 raw를 보존한 채 한 번만 재시도하며 production 한 producer 실패가 전체를 막는다. 마지막 전체 discover는 수집 테스트 수가 0보다 크고 failure/error가 0이다.
9. 실패 처리·롤백: 정확한 marker가 거부되거나 자유 문구가 clean review가 되거나 원시 stdout/reason이 사라지거나 여섯 producer 조건이 source별 성공으로 완화되거나 terminal artifact보다 먼저 exit하면 T4를 중단한다. 1차 rollback은 `git checkout 067923b554f159cf8c12e37f353f572951824b41 -- dot_claude/skills/dual-review/scripts/review_state.py dot_claude/skills/dual-review/tests/test_contracts.py dot_claude/skills/dual-review/tests/test_execution.py`다. 같은 셸 세션에서는 1번의 `$t4_backup` 사본을 보조 수단으로 쓸 수 있다. 기존 zero-parse 테스트를 삭제하는 방식으로 통과시키지 않는다.

### T5. opt-in production API schema probe 생성

대상 AC: AC-9 (CMD-7), AC-15 (CMD-4), AC-19 (CMD-2 test_live_api_contract)

의존성: T1~T4 통과. production command builder, adapter, 세 canonical schema를 그대로 사용한다.

1. 변경 전 사본을 만든다: `t5_backup="$(mktemp -d /tmp/dual-review-t5.XXXXXX)" && cp -p dot_claude/skills/dual-review/tests/test_contracts.py "$t5_backup/test_contracts.py"`. 기대 결과는 사본이 regular file이고 `tests/test_live_api.py`는 아직 존재하지 않는 것이다.
2. `test_live_api_contract`를 먼저 추가해 `tests/test_live_api.py`의 존재, 표준 라이브러리 import, `DUAL_REVIEW_LIVE_API`/`DUAL_REVIEW_EVIDENCE_DIR`, 환경변수 부재 시 class-level skip, `build_codex_command`/`build_claude_command`/`SubprocessAdapter` 사용, 호출별 stdout·stderr·result evidence, `$schema`-only diagnostic 표면을 정적으로 검사한다.
3. 실패 검증: `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py'`
   - 기대 결과: `tests/test_live_api.py`가 아직 없어 `test_live_api_contract`가 FAIL한다.
4. 최소 구현: `test_live_api.py`를 표준 라이브러리 `unittest`로 만든다. 기본 discover에서는 전체 live case를 명시적으로 skip하고 subprocess/model을 시작하지 않는다. opt-in에서는 production builder와 adapter로 Codex reviewer, Codex critique, Claude critique, Claude synthesis를 호출하고 Codex tuple의 마지막 `-`, stdin EOF, structured payload를 단정하며 호출별 command metadata·stdout·stderr·result를 지정 evidence 디렉터리의 서로 다른 파일에 쓴다.
5. Claude canonical schema 거부 처리: 실패한 원본 command/result를 보존하고, canonical `build_claude_command(schema_name=...)` tuple에서 `--json-schema` 바로 다음 값만 루트 `$schema`를 제거한 `json.dumps()` 메모리 사본으로 치환해 해당 호출을 정확히 한 번 재시도한다. 원본/재시도 evidence를 별도 파일에 남긴 뒤 test 자체는 실패시킨다. 재시도 수용이면 세 shared schema 파일에서 루트 `$schema`를 함께 제거하는 T3 최소 변경으로 돌아가 CMD-1~CMD-7을 처음부터 다시 실행한다. 재시도도 거부하면 `CLAUDE_SCHEMA_INCOMPATIBLE` evidence를 기록하고 `NEEDS_REDESIGN`으로 중단한다. provider별 schema나 다른 keyword 완화는 구현하지 않는다.
6. 통과 검증:
   - 기본 skip/정적 계약: `env -u DUAL_REVIEW_LIVE_API PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_live_api.py' -v`
   - deterministic contract: 3번 명령
   - 기대 결과: 첫 명령은 live case를 수집해 skip하고 model evidence를 만들지 않으며 exit 0, 둘째 명령은 `test_live_api_contract` 포함 전체 contract가 exit 0이다.
7. 실패 처리·롤백: 기본 실행이 모델을 호출하거나 evidence가 지정 디렉터리 밖에 생기거나 production builder를 우회하면 T5를 중단한다. 1차 rollback은 `git checkout 067923b554f159cf8c12e37f353f572951824b41 -- dot_claude/skills/dual-review/tests/test_contracts.py && rm -f dot_claude/skills/dual-review/tests/test_live_api.py`다. 같은 셸 세션에서는 1번의 `$t5_backup` 사본을 보조 수단으로 쓸 수 있다. 이미 생성된 task evidence는 rollback 대상이 아니며 삭제하지 않는다.

### T6. landing-noindex 읽기 전용 E2E helper 생성

대상 AC: AC-16 (CMD-8), AC-17 (CMD-8), AC-20 (CMD-2 test_live_e2e_contract)

의존성: T1, T2, T4, T5 통과. T7 packaging 전에 파일 인터페이스를 확정한다.

1. 변경 전 사본을 만든다: `t6_backup="$(mktemp -d /tmp/dual-review-t6.XXXXXX)" && cp -p dot_claude/skills/dual-review/tests/test_contracts.py "$t6_backup/test_contracts.py"`. 기대 결과는 사본이 regular file이고 `tests/live_e2e.py`는 아직 존재하지 않는 것이다.
2. `test_live_e2e_contract`를 먼저 추가해 `tests/live_e2e.py`의 존재, 표준 라이브러리 import, 정확한 여덟 required option, branch/clean/triple-dot file·byte precondition, `git merge-base`, 모델 호출 전 `sha256(base_sha\0head_sha)[:16]`와 `max(existing, default=0)+1` 관측, preserve-run, phase, HEAD/status 무변경 assertion을 정적으로 검사한다.
3. 실패 검증: `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py'`
   - 기대 결과: `tests/live_e2e.py`가 아직 없어 `test_live_e2e_contract`가 FAIL한다.
4. 최소 구현: 표준 라이브러리만 사용하는 executable helper를 만들고 `--repository`, `--logical-base`, `--expected-branch`, `--expected-files`, `--expected-diff-bytes`, `--preserve-run`, `--review-state-script`, `--evidence-dir`를 required로 선언한다. 모델 호출 전에 branch, clean porcelain, `logical-base...HEAD`의 파일 수/`--unified=0` byte 수, preserve-run 존재, merge-base/head SHA, 접두사와 기존 6자리 최댓값을 기록한다. precondition 하나라도 다르면 review script를 호출하지 않고 nonzero로 종료한다.
5. 최소 구현을 이어서 계산한 merge-base SHA를 `review_state.py --base`에 전달하고, 새 run의 events에서 여섯 start-before-read, producer raw 여섯 개의 valid/명시적 무소견, 양방향 critique 각 1회 이상, synthesis 정확히 1회, report 존재, 예상 next run ID를 판정한다. 실행 전후 제품 HEAD와 porcelain을 byte-identical하게 비교하고 기존 run의 필수 파일 digest를 비교해 보존을 확인하며 task evidence에 pre/post 및 새 run 요약을 쓴다.
6. 통과 검증:
   - CLI shape: `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 dot_claude/skills/dual-review/tests/live_e2e.py --help`
   - static contract: 3번 명령
   - 기대 결과: help가 여덟 option을 표시하고 exit 0, contract suite가 helper의 precondition/run-id/phase/무변경 경계를 확인해 exit 0이다. 이 단계에서는 제품 모델 호출을 하지 않는다.
7. 실패 처리·롤백: helper가 precondition 전에 모델을 호출하거나 fixed `-000002`를 가정하거나 preserve-run/HEAD/status/phase 하나를 판정하지 않으면 T6를 중단한다. 1차 rollback은 `git checkout 067923b554f159cf8c12e37f353f572951824b41 -- dot_claude/skills/dual-review/tests/test_contracts.py && rm -f dot_claude/skills/dual-review/tests/live_e2e.py`다. 같은 셸 세션에서는 1번의 `$t6_backup` 사본을 보조 수단으로 쓸 수 있다. 제품의 기존/새 run과 quality evidence는 삭제하거나 번호를 재사용하지 않는다.

### T7. source/archive packaging과 전체 검증 문서 계약 완성

대상 AC: AC-10 (CMD-2 test_packaging_contract test_no_mutation_contract_ignores_binary_fixture), AC-11 (CMD-5), AC-15 (CMD-4), AC-18 (CMD-2), AC-19 (CMD-2 test_live_api_contract), AC-20 (CMD-2 test_live_e2e_contract)

의존성: T5와 T6 완료. 두 신규 helper가 required path로 실재해야 한다.

1. 변경 전 사본을 만든다: `t7_backup="$(mktemp -d /tmp/dual-review-t7.XXXXXX)" && cp -p dot_claude/skills/dual-review/scripts/review_state.py "$t7_backup/review_state.py" && cp -p dot_claude/skills/dual-review/tests/test_contracts.py "$t7_backup/test_contracts.py" && cp -p dot_claude/skills/dual-review/references/verification.md "$t7_backup/verification.md" && cp -p .chezmoiignore "$t7_backup/.chezmoiignore" && cp -p dot_claude/skills/dual-review/schemas/.gitkeep "$t7_backup/schemas.gitkeep" && cp -p dot_claude/skills/dual-review/scripts/.gitkeep "$t7_backup/scripts.gitkeep"`. 기대 결과는 여섯 사본이 모두 regular file인 것이다.
2. `test_packaging_contract`를 먼저 바꿔 실제 배포 필수 파일 전부를 요구한다: `SKILL.md`, `scripts/review_state.py`, 세 schema, `references/operation.md`, `references/verification.md`, `templates/report.md`, `tests/test_contracts.py`, `tests/test_execution.py`, `tests/test_critique.py`, `tests/test_normalization.py`, `tests/test_reporting.py`, `tests/test_rounds.py`, `tests/test_synthesis.py`, `tests/test_live_api.py`, `tests/live_e2e.py`. 두 `.gitkeep` 부재와 `.chezmoiignore`의 dual-review cache rule도 검사한다. `SKILL_ROOT.rglob("*")`의 파일·디렉터리 각 상대 component에 대해 leading `.`, suffix `.tmpl`, source-state prefix `after_`, `before_`, `create_`, `dot_`, `empty_`, `encrypted_`, `exact_`, `executable_`, `literal_`, `modify_`, `once_`, `private_`, `readonly_`, `remove_`, `run_`, `symlink_`가 하나도 없음을 단정하고, 최종 CMD-5의 literal source/archive 상대 경로 동등성으로 누락된 chezmoi 해석도 잡는다. `test_no_mutation_contract_ignores_binary_fixture`는 일반 `.md`·`.py`·`.json` 수집과 `.pyc`·기타 binary 제외 assertion으로 대체한다.
3. 실패 검증: `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py'`
   - 기대 결과: 현행 두 `.gitkeep`, `scan_source_texts()` 특수 분기, 누락된 dual-review cache ignore 때문에 packaging/scanner assertion이 FAIL한다.
4. 최소 구현: 두 `.gitkeep`를 삭제하고 `scan_source_texts()`를 `.md`·`.py`·`.json` suffix만 읽도록 단순화한다. `.chezmoiignore`에 `.claude/skills/dual-review/**/__pycache__`를 추가한다. `verification.md`는 T1의 `DRV-*` 체계를 유지하면서 CMD-1~CMD-8의 새 경계를 `Spec CMD-*`로만 설명하고 source/archive suite, 기본 live skip, live API, E2E, Python 3.14.7 evidence를 일치시킨다.
5. 통과 검증:
   - contract: 3번 명령
   - source 전체/Python evidence: CMD-4
   - archive 동등성: CMD-5
   - 기대 결과: contract가 exit 0이고, CMD-4가 Python 3.14.7에서 0개보다 많은 전체 suite를 live call 없이 통과하며, CMD-5가 실제 cache fixture 존재를 먼저 단정한 뒤 `$HOME` 변경 없이 source/archive 상대 경로 동등성·cache/`.gitkeep` 0건·배포본 전체 suite 통과를 확인한다.
6. 실패 처리·롤백: required path 누락, 숨김/예약 component, source/archive 차이, cache 포함, archive suite 실패, cleanup 잔존 중 하나라도 있으면 T7을 중단한다. 1차 rollback은 `git checkout 067923b554f159cf8c12e37f353f572951824b41 -- dot_claude/skills/dual-review/scripts/review_state.py dot_claude/skills/dual-review/tests/test_contracts.py dot_claude/skills/dual-review/references/verification.md .chezmoiignore dot_claude/skills/dual-review/schemas/.gitkeep dot_claude/skills/dual-review/scripts/.gitkeep`다. 같은 셸 세션에서는 1번의 `$t7_backup` 사본을 보조 수단으로 쓸 수 있다. 백업 시 두 marker는 각각 `schemas.gitkeep`, `scripts.gitkeep` basename으로 저장한다. 기존 execution/evidence는 rollback 대상이 아니다.

### T8. 유료·외부 모델 strict 검증 실행과 중단 판정

대상 AC: AC-1 (CMD-6), AC-9 (CMD-7), AC-16 (CMD-8), AC-17 (CMD-8)

의존성: B3의 T5~T7 완료와 CMD-1~CMD-5 전부 통과. 이 태스크는 소스를 수정하지 않고 CMD-6~CMD-8의 실행과 evidence 판정을 소유한다.

1. CMD-6을 실행한다. project-local 임시 복사본에서 stdin slash가 `model: opus`를 선택하고 모델 오류 없이 유일한 `no_changes` run, provenance, report를 남기며 `$HOME` 설치본을 변경하지 않아야 한다. nonzero, 모델 선택 오류, run 수 불일치 또는 report 부재이면 즉시 중단하고 CMD-7을 실행하지 않는다.
2. CMD-6 통과 뒤 CMD-7을 실행한다. production builder의 Codex reviewer·양쪽 critique·Claude synthesis가 canonical shared schema로 성공하고 호출별 raw evidence가 남아야 한다. Claude schema 거부 시 원본과 `$schema`-only 단일 진단 재시도 evidence를 보존한 채 중단한다. 진단 재시도가 수용되면 T3의 허용된 shared-schema fix-forward 뒤 B2와 B3의 CMD-1~CMD-5를 다시 통과하고 T8을 CMD-6부터 재실행하며, 재거부면 `CLAUDE_SCHEMA_INCOMPATIBLE`/`NEEDS_REDESIGN`으로 판정한다.
3. CMD-7 통과 뒤 CMD-8을 실행한다. 모델 호출 전 branch/clean/triple-dot 3파일·18,505바이트/preserve-run precondition을 모두 확인하고, 이후 여섯 start-before-read, 여섯 유효 producer, 양방향 critique, synthesis 1회, report, 정확한 증가 run ID, 제품 HEAD/status와 기존 run 보존을 확인해야 한다. 어느 precondition이나 사후 조건도 실패하면 즉시 중단하고 실패 evidence를 보존한다.
4. CMD-6~CMD-8이 순서대로 모두 exit 0일 때만 T8을 통과로 판정한다. 실패 원인을 고친 뒤에는 CMD-1~CMD-5 deterministic/archive gate를 다시 통과하고 CMD-6부터 순서대로 재실행한다. T8 rollback은 소스 복원이 아니라 새 실패 evidence와 증가 run을 삭제·재사용하지 않은 채 마지막 통과 source 상태를 유지하는 것이다. 기존 evidence와 제품 run `e7a6d2872362a4d6-000001`은 rollback 대상이 아니다.

## Verification commands

실행 순서는 CMD-1 → CMD-2 → CMD-3 → CMD-4 → CMD-5의 deterministic/archive gate를 먼저 완료하고, 그 뒤 비용과 외부 API가 있는 CMD-6 → CMD-7 → CMD-8 순서다. CMD-1은 Spec 문자열의 다섯 신규 lifecycle 테스트에 기존 Popen-failure cleanup, `handle[3]` output-path 소비 테스트 두 개, constructed-prompt dispatch 테스트, 2-adapter/production 시작 순서 테스트 두 개를 결합한다. CMD-2~CMD-8 문자열은 승인 Spec과 동일하다.

| ID | 명령 | 기대 성공 결과 |
|---|---|---|
| CMD-1 | `cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_execution.ExecutionTests.test_subprocess_adapter_delivers_prompt_before_read_after_delay test_execution.ExecutionTests.test_subprocess_adapter_large_prompt_does_not_block_start test_execution.ExecutionTests.test_subprocess_adapter_unextractable_exit_zero_cleans_temp_files test_execution.ExecutionTests.test_subprocess_adapter_invalid_output_last_message_json_cleans_temp_files test_execution.ExecutionTests.test_subprocess_adapter_timeout_kills_without_resending_and_cleans_prompt test_execution.ExecutionTests.test_subprocess_start_failure_cleans_its_temporary_output test_execution.ExecutionTests.test_subprocess_adapter_success_cleans_temporary_output test_execution.ExecutionTests.test_timeout_mutation_is_nonretryable_and_cleans_temporary_output test_execution.ExecutionTests.test_dispatches_constructed_prompts_before_any_read test_execution.ExecutionTests.test_round_zero_starts_every_adapter_before_any_result_is_read test_execution.ExecutionTests.test_live_shape_starts_five_claude_producers_and_codex_before_reads` | Python 3.14.7에서 열한 테스트가 통과한다. prompt 즉시 전달·EOF·대용량 무교착·무절단·parse/timeout cleanup, `handle[3] == output_path`, 생성 prompt dispatch와 2-adapter/production 6-producer의 모든 start-before-first-read를 확인한다. |
| CMD-2 | `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py'` | 빈 선택이 아닌 contract suite가 model, Claude CLI 2.1.268 기능/production emit/harness 분리, Codex tuple, prompt marker 배타 지시, strict schema, packaging/cache, scanner, 두 live helper, `DRV-*` 문서와 표준 라이브러리 제한을 모두 통과한다. |
| CMD-3 | `cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_execution.ExecutionTests.test_explicit_no_findings_and_structured_empty_findings_are_valid test_execution.ExecutionTests.test_producer_markdown_that_parses_to_zero_findings_is_not_a_valid_review test_execution.ExecutionTests.test_zero_parse_producer_is_excluded_rather_than_reported_as_a_clean_review test_execution.ExecutionTests.test_all_six_producers_must_return_valid_reviews test_execution.ExecutionTests.test_all_rejected_findings_are_incomplete test_execution.ExecutionTests.test_invalid_finding_is_rejected_without_retrying_its_valid_source test_execution.ExecutionTests.test_validation_only_normalization_needs_no_group_or_line_ranges test_execution.ExecutionTests.test_failure_reports_keep_termination_and_reviewer_status test_execution.ExecutionTests.test_main_exit_code_distinguishes_incomplete_runs` | structured 빈 배열과 exact Claude marker는 무재시도 완료되고, marker 없는 zero-block·marker/block 혼합·all-rejected·호출 실패는 재시도 후 제외된다. production 여섯 producer 조건, valid+invalid 무재시도, failure report, entrypoint exit가 통과한다. |
| CMD-4 | `evidence_root="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/environment" && mkdir -p "$evidence_root" && PATH="/opt/homebrew/bin:$PATH" python3 -VV 2>&1 | tee "$evidence_root/python-version.txt" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import sys; assert sys.version_info[:3] == (3, 14, 7), sys.version' && env -u DUAL_REVIEW_LIVE_API PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -v` | `python-version.txt`가 version 출력을 보존하고 Python 3.14.7 tuple assertion과 0개보다 많은 전체 source suite가 failure/error 없이 통과한다. live cases는 수집 후 skip되며 type check, lint, build는 `not configured`로 기록한다. |
| CMD-5 | `archive_tmp="$(mktemp -d /tmp/dual-review-package.XXXXXX)" && skill_src="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/dot_claude/skills/dual-review" && cache_dir="$skill_src/scripts/__pycache__" && cache_fixture="$cache_dir/spec-cache-fixture.pyc" && cleanup_cache_fixture() { PATH="/opt/homebrew/bin:$PATH" python3 -c 'import pathlib,shutil,sys; fixture=pathlib.Path(sys.argv[1]); cache=fixture.parent; fixture.unlink(missing_ok=True); cache.rmdir() if cache.exists() and not any(cache.iterdir()) else None; shutil.rmtree(sys.argv[2], ignore_errors=True)' "$cache_fixture" "$archive_tmp"; } && trap cleanup_cache_fixture EXIT && mkdir -p "$cache_dir" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)' "$skill_src/scripts/review_state.py" "$cache_fixture" && test -d "$cache_dir" && test -f "$cache_fixture" && chezmoi --source "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime" archive --output "$archive_tmp/dual-review.tar" --format tar ~/.claude/skills/dual-review && mkdir "$archive_tmp/root" && tar -xf "$archive_tmp/dual-review.tar" -C "$archive_tmp/root" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import pathlib,sys,tarfile; src=pathlib.Path(sys.argv[1]); fixture=pathlib.Path(sys.argv[2]); prefix=".claude/skills/dual-review/"; assert fixture.is_file() and fixture.parent.is_dir(); keep=lambda p: "__pycache__" not in p.parts and p.suffix != ".pyc"; source={str(p.relative_to(src)) for p in src.rglob("*") if keep(p.relative_to(src))}; members={m.name.rstrip("/")[len(prefix):] for m in tarfile.open(sys.argv[3]).getmembers() if m.name.rstrip("/").startswith(prefix) and m.name.rstrip("/") != prefix.rstrip("/")}; assert source == members, (source-members, members-source); assert {"tests/test_live_api.py","tests/live_e2e.py"}.issubset(members); assert not [p for p in members if ".gitkeep" in pathlib.PurePosixPath(p).parts or "__pycache__" in pathlib.PurePosixPath(p).parts or p.endswith(".pyc")], members' "$skill_src" "$cache_fixture" "$archive_tmp/dual-review.tar" && cd "$archive_tmp/root/.claude/skills/dual-review" && env -u DUAL_REVIEW_LIVE_API PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | source의 cache fixture가 실제 존재한 뒤에도 `$HOME` 변경 없는 archive에서 cache/`.gitkeep`가 0건이고 두 helper를 포함한 source 집합과 archive 집합이 같다. 푼 배포본 suite가 통과하고 EXIT trap이 fixture와 archive를 정리한다. |
| CMD-6 | `evidence_root="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence" && slash_tmp="$(mktemp -d /tmp/dual-review-slash.XXXXXX)" && mkdir -p "$evidence_root" "$slash_tmp/project/.claude/skills" && cp -R "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/dot_claude/skills/dual-review" "$slash_tmp/project/.claude/skills/dual-review" && git -C "$slash_tmp/project" init -q && git -C "$slash_tmp/project" config user.email fixture@example.test && git -C "$slash_tmp/project" config user.name Fixture && touch "$slash_tmp/project/README.md" && git -C "$slash_tmp/project" add README.md && git -C "$slash_tmp/project" commit -qm initial && cd "$slash_tmp/project" && printf '%s' "/dual-review --base HEAD" | claude -p --no-session-persistence --setting-sources project --permission-mode default --permission-prompts none --allowedTools "Read,Glob,Grep,Bash(python3:*)" > "$evidence_root/slash-no-changes.txt" 2> "$evidence_root/slash-no-changes.stderr" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import json,pathlib,sys; skill=pathlib.Path(sys.argv[1]).read_text(); out=pathlib.Path(sys.argv[2]).read_text(); err=pathlib.Path(sys.argv[3]).read_text(); state_root=pathlib.Path(sys.argv[4]); runs=[p for p in state_root.iterdir() if p.is_dir()]; assert "model: opus" in skill; assert "unrecognized_model" not in out+err and "issue with the selected model" not in out+err; assert len(runs) == 1, runs; provenance=json.loads((runs[0] / "provenance.json").read_text()); assert provenance["termination_reason"] == "no_changes", provenance; assert (runs[0] / "report.md").is_file()' "$slash_tmp/project/.claude/skills/dual-review/SKILL.md" "$evidence_root/slash-no-changes.txt" "$evidence_root/slash-no-changes.stderr" "$slash_tmp/project/.claude/dual-review-state"` | stdin slash 호출이 project의 `model: opus` 스킬을 선택하고 모델 오류 없이 Python 진입점까지 도달한다. 유일한 run이 `no_changes` provenance와 report를 남긴다. `$HOME` 설치본은 변경하지 않는다. |
| CMD-7 | `evidence_root="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/schema-live" && mkdir -p "$evidence_root" && cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" DUAL_REVIEW_LIVE_API=1 DUAL_REVIEW_EVIDENCE_DIR="$evidence_root" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -p 'test_live_api.py' -v < /dev/null` | production builder로 Codex reviewer, 양쪽 critique, Claude synthesis가 실제 호출되고 canonical schema 세 개가 수용된다. Codex는 마지막 `-`와 EOF stdin을 사용하며 호출별 raw evidence가 남는다. Claude 거부 시 `$schema`-only 진단 evidence를 남기고 이 명령은 실패한다. |
| CMD-8 | `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 dot_claude/skills/dual-review/tests/live_e2e.py --repository "/Users/lee-kyu-hwan/code/zambaguni-front-landing-noindex" --logical-base origin/develop --expected-branch 1406-improvement/landing-noindex --expected-files 3 --expected-diff-bytes 18505 --preserve-run e7a6d2872362a4d6-000001 --review-state-script "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/dot_claude/skills/dual-review/scripts/review_state.py" --evidence-dir "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence" < /dev/null` | branch/clean/triple-dot 3파일·18,505바이트/기존 run precondition 뒤 계산된 merge-base로 실행한다. 여섯 start-before-read, 여섯 유효 producer, 양방향 critique, synthesis 1회, report, 정확한 증가 run/evidence와 제품 HEAD/status/기존 run 보존을 확인한다. |

`SPEC-008`/`SPEC-010` 보완 검증은 CMD-2와 CMD-3 통과 뒤 다음 명령으로도 직접 실행한다.

`cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_contracts.PackagingContractTests.test_round_zero_claude_prompt_requires_exclusive_no_findings_marker test_execution.ExecutionTests.test_no_findings_marker_requires_exact_stdout_and_preserves_diagnostics`

기대 결과는 prompt가 exact marker와 배타 규칙을 포함하고, exact marker만 성공하며 앞뒤 자유 문구·marker/finding 혼합·marker 없는 zero-block·all-rejected가 구분된 reason과 원시 stdout을 보존한 채 실패하는 것이다.

## Rollout and rollback

1. rollout은 좁힌 직렬 배치 B1=T1~T2, B2=T3~T4, B3=T5~T7과 T8로 수행한다. B1은 보완 CMD-1·CMD-2·CMD-4, B2는 CMD-2·CMD-3·advisory 진단·CMD-4, B3의 deterministic/archive 단계는 CMD-1~CMD-5가 각각 모두 통과해야 다음 경계로 진행한다. 그 뒤 T8이 CMD-6→CMD-7→CMD-8을 순서대로 소유한다. `$HOME` 적용과 dotfiles commit·push·PR은 이 rollout에 포함하지 않는다.
2. CMD-6은 임시 프로젝트 복사본만 사용한다. CMD-7은 canonical shared schema를 사용하고, Claude 거부 시 원본과 `$schema`-only 단일 재시도 evidence를 보존한다. 재시도 수용은 세 shared schema의 루트 `$schema`를 함께 제거하는 fix-forward trigger이며 CMD-1부터 다시 실행한다. 재거부는 `CLAUDE_SCHEMA_INCOMPATIBLE`/`NEEDS_REDESIGN` trigger다.
3. CMD-8은 branch, clean status, triple-dot 3파일·18,505바이트, preserve-run이 모두 맞을 때만 모델 호출한다. precondition 불일치, producer 하나의 최종 실패, phase 누락, run-id 불일치, 제품 mutation은 즉시 중단 trigger다.
4. 태스크별 rollback은 추적 파일에 대해 각 T1~T7 마지막 단계의 baseline commit `067923b554f159cf8c12e37f353f572951824b41` 기반 `git checkout <baseline> -- <태스크 소유 경로>`를 1차 수단으로 사용한다. rollback 전에 `git diff -- <태스크 소유 경로>`와 `git status --short -- <태스크 소유 경로>`로 정확한 대상을 확인하며, 구현 시작 뒤 사용자가 별도로 수정한 경로가 보이면 자동 복원하지 않고 중단한다. `/tmp` 사본과 `$tN_backup`은 같은 셸 세션에서만 가능한 보조 수단이다.
5. 전체 rollback도 baseline commit에서 이번 Plan의 추적 구현 대상 파일만 명시적으로 복원한다. baseline에 없는 신규 `tests/test_live_api.py`, `tests/live_e2e.py`만 명시적으로 제거하고 삭제했던 두 `.gitkeep`는 baseline에서 복원한다. 기존 P0~P8 evidence, 새 실패 evidence, 제품의 기존 `e7a6d2872362a4d6-000001`, 이미 생성된 증가 run은 rollback 대상이 아니며 삭제·재사용하지 않는다.
6. rollback 후에는 CMD-1~CMD-5를 다시 실행해 기준선 상태를 기록한다. known-bad `model: claude`, read-time prompt 전송, 열린 schema, source별 producer 축약을 부분적으로 되살리는 rollback은 허용하지 않으며, 해당 경우 전체 태스크 사본 복원 또는 fix-forward 중 하나만 선택한다.
7. 완료 순서는 구현과 모든 검증 evidence 수집 → durable 산출물 `report.md` 확정 및 등록 → 최종 workspace verification fingerprint 기록 → 그 fingerprint를 입력으로 한 Code review 순서로 고정한다. `report.md` 등 durable 산출물이 확정되기 전에 최종 fingerprint나 Code review를 시작하지 않는다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T1 | `CMD-6` | 복사된 project 스킬이 `opus`로 실행되고 모델 오류 없이 유일한 `no_changes` run과 report를 만든다. |
| AC-1 | T8 | `CMD-6` | 복사된 project 스킬이 `opus`로 실행되고 모델 오류 없이 유일한 `no_changes` run과 report를 만든다. |
| AC-2 | T1 | `CMD-2`, `CMD-1` | 모든 Codex tuple이 model/마지막 `-`/read-only/schema를 보존하고 reviewer·critique prompt가 stdin으로 한 번 전달된 뒤 EOF로 끝난다. |
| AC-2 | T2 | `CMD-2`, `CMD-1` | 모든 Codex tuple이 model/마지막 `-`/read-only/schema를 보존하고 reviewer·critique prompt가 stdin으로 한 번 전달된 뒤 EOF로 끝난다. |
| AC-3 | T1 | `CMD-2` | Claude 2.1.268 확인 기능, production emit, CMD-6 하니스 flag가 문서와 별도 assertion에서 구분되고 위치 prompt가 금지된다. |
| AC-4 | T2 | `CMD-1 test_round_zero_starts_every_adapter_before_any_result_is_read test_live_shape_starts_five_claude_producers_and_codex_before_reads` | 3초 지연 중에도 prompt/EOF가 도착하고 2-adapter 및 여섯 production start가 첫 read보다 앞선다. |
| AC-5 | T2 | `CMD-1 test_subprocess_adapter_large_prompt_does_not_block_start` | 262,145바이트 이상 prompt에서 start가 block되지 않고 최종 byte 수와 digest가 같다. |
| AC-6 | T2 | `CMD-1`은 `test_subprocess_start_failure_cleans_its_temporary_output`을 포함한다 | 성공·Popen/두 parse 실패·timeout/kill 경로에서 prompt/output 임시 파일이 사라지고 timeout은 124이며 prompt를 재전송하지 않는다. |
| AC-7 | T3 | `CMD-2 test_schema_contract` | 세 schema의 모든 object가 strict closed이고 type/required가 완전하며 reviewer 빈 findings가 유효하고 기존 keyword가 보존된다. |
| AC-8 | T3 | `CMD-2 test_critique_contract` | critique `new_findings.items`가 완전한 닫힌 finding이며 누락·추가·타입 불일치 fixture를 거부한다. |
| AC-9 | T3 | `CMD-7` | production builder의 Codex reviewer·양쪽 critique·Claude synthesis가 canonical schema로 성공하고 호출별 evidence가 남는다. |
| AC-9 | T5 | `CMD-7` | production builder의 Codex reviewer·양쪽 critique·Claude synthesis가 canonical schema로 성공하고 호출별 evidence가 남는다. |
| AC-9 | T8 | `CMD-7` | production builder의 Codex reviewer·양쪽 critique·Claude synthesis가 canonical schema로 성공하고 호출별 evidence가 남는다. |
| AC-10 | T7 | `CMD-2 test_packaging_contract test_no_mutation_contract_ignores_binary_fixture` | `.gitkeep`와 scanner 특수 분기가 없고 모든 필수 파일·배포 가능 component·text/binary 경계가 고정된다. |
| AC-11 | T7 | `CMD-5` | 실재 cache fixture가 archive에서 제외되고 source/archive 경로 집합이 같으며 배포본 전체 suite와 cleanup이 통과한다. |
| AC-12 | T4 | `CMD-2 test_round_zero_claude_prompt_requires_exclusive_no_findings_marker`; `CMD-3 test_explicit_no_findings_and_structured_empty_findings_are_valid`; `test_no_findings_marker_requires_exact_stdout_and_preserves_diagnostics` | prompt가 marker의 단독·배타 규칙을 요구하고 structured empty/exact marker만 완료되며 zero-block·혼합·실패·all-rejected는 한 번 재시도 뒤 reason/raw를 남겨 제외되고 valid+invalid는 무재시도다. |
| AC-13 | T4 | `CMD-3 test_failure_reports_keep_termination_and_reviewer_status` | production/legacy/downstream fixture가 정확한 termination reason과 attempts/stderr/exit/status를 report에 남긴다. |
| AC-14 | T4 | `CMD-3 test_main_exit_code_distinguishes_incomplete_runs` | terminal JSON/report 뒤 세 미완료 reason은 nonzero, `no_changes`와 정상 policy reason은 0이다. |
| AC-15 | T5 | `CMD-4` | Python 3.14.7 evidence가 보존되고 기본 discover는 live cases를 skip하며 나머지 전체 source suite가 통과한다. |
| AC-15 | T7 | `CMD-4` | Python 3.14.7 evidence가 보존되고 기본 discover는 live cases를 skip하며 나머지 전체 source suite가 통과한다. |
| AC-16 | T4 | `CMD-8` | 여섯 start-before-read와 producer별 유효 응답, 양방향 critique, fresh-Claude synthesis 1회, report가 모두 확인된다. |
| AC-16 | T6 | `CMD-8` | 여섯 start-before-read와 producer별 유효 응답, 양방향 critique, fresh-Claude synthesis 1회, report가 모두 확인된다. |
| AC-16 | T8 | `CMD-8` | 여섯 start-before-read와 producer별 유효 응답, 양방향 critique, fresh-Claude synthesis 1회, report가 모두 확인된다. |
| AC-17 | T6 | `CMD-8` | 제품 HEAD/status와 기존 run을 보존하고 선관측 `max(default=0)+1`의 새 run과 quality evidence를 만든다. |
| AC-17 | T8 | `CMD-8` | 제품 HEAD/status와 기존 run을 보존하고 선관측 `max(default=0)+1`의 새 run과 quality evidence를 만든다. |
| AC-18 | T1 | `CMD-2` | model/CLI/stdin/schema/archive/Python 문서와 `DRV-*`/`Spec CMD-*`, `not configured`, 표준 라이브러리 제한이 일치한다. |
| AC-18 | T7 | `CMD-2` | model/CLI/stdin/schema/archive/Python 문서와 `DRV-*`/`Spec CMD-*`, `not configured`, 표준 라이브러리 제한이 일치한다. |
| AC-19 | T5 | `CMD-2 test_live_api_contract` | live API helper의 두 환경변수, 기본 skip, production builder, 표준 라이브러리와 evidence 계약이 고정된다. |
| AC-19 | T7 | `CMD-2 test_live_api_contract` | live API helper의 두 환경변수, 기본 skip, production builder, 표준 라이브러리와 evidence 계약이 고정된다. |
| AC-20 | T6 | `CMD-2 test_live_e2e_contract` | E2E helper의 여덟 required option과 precondition·merge-base·동적 run-id·무변경 판정 인터페이스가 고정된다. |
| AC-20 | T7 | `CMD-2 test_live_e2e_contract` | E2E helper의 여덟 required option과 precondition·merge-base·동적 run-id·무변경 판정 인터페이스가 고정된다. |

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

- 신뢰 경계 안에는 승인 digest의 Spec, 이 worktree의 versioned source/test/schema, 검증 직전 다시 읽은 제품 Git refs만 둔다. 모델 stdout/stderr/structured output은 schema, envelope, explicit marker 또는 normalization을 통과하기 전까지 untrusted다.
- 대상 diff는 Claude/Codex 외부 모델 경계를 넘는다. production Claude는 `plan`과 `Read,Glob,Grep`, Codex는 `--sandbox read-only`를 유지하고 credential·사용자 설정·환경변수 값은 prompt/evidence에 넣지 않는다.
- prompt regular file과 output-last-message file은 민감한 diff를 담으므로 mode 0600, 예측 불가능한 임시 이름, 모든 성공/실패 경로 cleanup을 CMD-1로 검증한다.
- source-to-managed-tree 경계는 CMD-5의 source/archive 상대 경로 동등성으로 검증한다. chezmoi archive만 만들고 `$HOME`에 적용하지 않는다.
- 제품 경계는 CMD-8의 pre/post HEAD·porcelain·preserve-run digest로 잠근다. 모델 호출은 로컬 ignored run만 만들 수 있고 추적 파일 mutation은 즉시 실패다.
- `NO_FINDINGS`는 모델 출력이므로 문자열 존재만 신뢰하지 않는다. stdout 전체 strict equality와 finding block 배타성, producer별 normalization을 모두 통과해야 유효한 무소견이다.

### Authorization and tenant isolation

해당 없음 — dual-review는 단일 사용자의 로컬 CLI이고 tenant 식별자나 다중 tenant 데이터 저장소가 없다. 대신 권한 경계는 CMD-2에서 production Claude `Read,Glob,Grep`/Codex read-only를, CMD-6에서 임시 fixture의 한정된 `Bash(python3:*)`만을, CMD-8에서 제품 HEAD/status 무변경을 검사한다. denied case는 production builder에 쓰기 도구·bypass flag·외부 게시 action이 들어가면 `test_no_mutation_contract`와 command tuple assertion이 실패하는 것이다. 어떤 command도 `$HOME` 적용이나 제품 게시 권한을 갖지 않는다.

### Migration, compatibility, and rollback

- 데이터 migration은 없다. source 패키징 migration으로 두 `.gitkeep` 삭제, required path 실파일 교체, dual-review cache ignore를 한 묶음으로 적용한다.
- `SubprocessAdapter.start(source, prompt)`/`read(handle)` 외부 호출 형태, `_round_zero`의 전부 start 후 read 순서, run/provenance/report 파일명, 기존 termination reason 문자열은 호환 유지한다. handle 내부 tuple도 `(process, source, prompt_path, output_path, before)`로 고정해 기존 테스트 소비자인 `handle[3] == output_path`를 유지하며, prompt 문자열만 regular-file 경로 상태로 치환한다.
- schema는 provider별 fork 없이 세 shared file을 유지한다. canonical Claude 거부 시 허용되는 호환 변경은 루트 `$schema` annotation의 세 파일 동시 제거뿐이고, 그 뒤 전체 gate evidence가 필요하다.
- rollback trigger와 실제 복원 명령은 T1~T7 및 `Rollout and rollback`에 명시했다. deterministic/live/archive/E2E failure, target mutation, prompt 잔존·중복·EOF 부재가 trigger다. 기존 evidence와 `e7a6d2872362a4d6-000001`은 복원·삭제 대상이 아니다.

### Failure recovery and observability

- adapter는 process exit, timeout 124, stderr, 시도별 raw stdout, prompt/output cleanup 결과를 보존한다. producer record는 `valid`, `explicit_no_findings`, `reason`, `attempts`, `stderr`, `exit_code`, raw 배열을 가진다.
- strict marker 위반은 `missing_no_findings_marker`, `nonexclusive_no_findings_marker`, normalization 전부 거부는 `all_findings_rejected`로 구분한다. transport/model/schema/timeout reason도 기존 status와 함께 보존해 자유 문구 때문에 전체 gate가 실패한 경우를 parser drift와 호출 실패에서 분리한다.
- `reviewer_failure`, `single_reviewer`, `pipeline_failure`는 terminal JSON/report가 먼저 기록된 뒤 nonzero process exit로 이중 노출된다. `no_changes`와 정상 policy 종료는 0이다.
- retry는 ingestion failure당 기존 한 번으로 제한한다. 실패한 run이나 evidence를 고쳐 쓰거나 번호를 초기화하지 않는다.
- 해당 없음 — 별도 metric backend, alert, distributed trace는 로컬 일회성 CLI에 존재하지 않는다. durable run artifacts와 exit code가 승인된 관측 인터페이스다.

### High-risk end-to-end verification

- CMD-1~CMD-5가 모두 통과한 뒤에만 CMD-6~CMD-8을 실행한다.
- CMD-6은 project-local 복사본의 Opus slash/no-change 경계를 한 번 실제 호출하고 `$HOME` 설치본을 변경하지 않는다.
- CMD-7은 production builder를 통한 Codex reviewer, Codex/Claude critique, Claude synthesis와 세 canonical schema를 실제 provider에서 검증하고 호출별 raw evidence를 보존한다. Claude 거부는 `$schema`-only 단일 진단 재시도 뒤 fix-forward 전체 재검증 또는 `NEEDS_REDESIGN`으로 처리한다.
- CMD-8은 제품 branch/clean/triple-dot 3파일·18,505바이트/preserve-run precondition 뒤 계산된 merge-base로 실행한다. 여섯 start-before-read, producer 여섯 개 각각의 유효 response, 양방향 critique, fresh-Claude synthesis 정확히 1회, report, next run ID, 제품 무변경이 모두 있어야 exit 0이다.
- 하나의 producer failure도 다른 producer의 finding이나 무소견으로 대체하지 않는다. exact marker는 성공이지만 자유 문구를 동반한 marker는 raw reason을 남기는 E2E 실패다.

### No production mutation confirmation

자동 검증에 production mutation은 없다. chezmoi는 source 지정 archive만 만들며 `$HOME`을 적용하지 않는다. `zambaguni-front`에서는 읽기 전용 모델 호출과 ignored local run artifact만 허용하고 commit, push, PR, review, comment를 생성하지 않는다. dotfiles commit·push·PR도 구현·테스트·리뷰 완료 뒤 별도 승인된 통합 단계이므로 CMD-1~CMD-8에 포함하지 않는다.

<!-- strict-only:end -->
