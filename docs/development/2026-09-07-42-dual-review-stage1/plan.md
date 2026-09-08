# Quality Goal Implementation Plan

- Task ID: 42-dual-review-stage1
- Mode: standard
- Status: APPROVED-SPEC-PLAN
- Created: 2026-09-07
- Updated: 2026-09-07
- Source goal: #42 이중 리뷰 스킬의 1단계 — 독립 Claude·Codex 리뷰, 교차 비평, 종합, 로컬 보고서

## Spec link

승인된 [spec.md](spec.md)를 정본으로 사용한다. 사용한 SHA-256은 `9962ce1beea4f16bd62f62d918d5538d2eb4c7686d25faf9f346b092bcd95e5f`이며, 이 계획은 그 요구사항을 변경하지 않는다.

## Global constraints

- 새 스킬만 `dot_claude/skills/dual-review/`에 만들며 기존 파일 수정은 0건이다. `chezmoi apply`, 커밋, 머지, PR 생성은 실행하지 않는다.
- 결정 규칙은 Python 3.14 표준 라이브러리로 구현하고, `SKILL.md`는 문자열을 바꾸지 않는 호출 오케스트레이션만 둔다. Codex 실행의 허용 플래그 정확 집합은 `{-C, --sandbox, --ephemeral, --model, -c, --output-schema, --output-last-message, --json}`이며, `--sandbox` 값은 `read-only`다.
- `rg`의 0은 매치, 1은 무매치, 2는 경로 부재다. 따라서 부재 검사 wrapper는 오직 무매치만 성공으로 바꾼다. `unittest discover -k`의 0개 일치는 종료 코드 5이므로 공허 통과로 취급하지 않는다.
- `dot_claude/skills/dual-review/` 아래 어떤 파일도 CMD-4가 찾는 다섯 Codex 옵션 리터럴이나 CMD-5가 찾는 세 GitHub 쓰기 리터럴을 축자로 담지 않는다. 우회 표기는 목적 전용의 `<forbidden-codex-option-N>`·`<github-write-command-N>` placeholder로만 하고, 이 placeholder들은 두 `rg` 패턴 어느 것과도 일치하지 않는다. `references/verification.md`는 CMD-4·CMD-5를 목적과 종료 코드 계약으로만 설명하며 패턴 리터럴을 인용하지 않는다. 계약 테스트는 허용 `codex exec` 플래그 정확 집합 `{-C, --sandbox, --ephemeral, --model, -c, --output-schema, --output-last-message, --json}` 및 `--sandbox`의 `read-only` 값만 단정하고, 필요한 금지 토큰은 `tempfile.TemporaryDirectory()` 아래 스캔 대상 밖에서 프로그램적으로 구성한다.
- 실행 fixture의 run 상태 루트는 항상 `tempfile.TemporaryDirectory()`가 만든 임시 repository root의 `.claude/dual-review-state/`다. 테스트는 이 임시 루트 밖의 워크트리 상태를 만들지 않으며, 컨텍스트 종료가 run state를 제거한다.
- 저장소에는 타입 검사·린트·빌드 구성이 없으므로 `not configured`으로 문서화한다. 기존 테스트 중 dual-review 상태 경로를 리터럴로 고정한 갱신 대상은 0건이므로 기존 테스트 갱신 태스크를 만들지 않는다.
- `chezmoi diff`와 `chezmoi apply`는 실행하지 않는다. source directory가 이 워크트리가 아니므로, 배치 계약은 순수 경로 함수와 계약 테스트만으로 판정한다.
- SPEC-015: Codex 원문 ID는 응답 `findings` 배열의 1-based 순번과 producer 토큰 `codex`으로 정한다. 비평 산 finding은 producer 토큰 `cross-critique:<작성 source>` 및 그 비평 응답 `findings` 배열의 1-based 순번을 쓴다. 두 경우 모두 거부 블록도 순번을 소비한다.
- SPEC-016: 익명 view의 문자열에 금지 평문이 발견되면 결정적으로 `<redacted:sha256-12>` 토큰으로 치환하고, 원문·토큰·필드 경로·사유를 provenance sidecar에 기록한다. finding을 조용히 제거하지 않는다.
- SPEC-017: synthesis의 `group_a_finding_ids`와 `group_b_finding_ids`는 항상 존재하며, 단일 출처는 없는 쪽을 빈 배열 `[]`로 직렬화한다.
- SPEC-018: confidence가 1 초과이면 0–100 척도로 간주해 100으로 나누고, 1 이하면 이미 0–1 척도로 보존한다. 변환 후 범위를 벗어나면 해당 finding을 거부한다.

## File map

| File | Responsibility and interface |
|---|---|
| `dot_claude/skills/dual-review/SKILL.md` | 슬래시 명령, frontmatter, 읽기 전용 호출 순서, Python 경계 참조를 선언한다. |
| `dot_claude/skills/dual-review/references/operation.md` | reviewer·critique·fresh synthesis 호출 계약, 배치 source/target 경로, 비쓰기 범위를 설명한다. |
| `dot_claude/skills/dual-review/references/verification.md` | CMD-1~12의 목적·`not configured` 상태·`rg` 종료 코드 의미를 문서화하되, CMD-4·CMD-5의 패턴 리터럴은 쓰지 않는다. |
| `dot_claude/skills/dual-review/schemas/reviewer.schema.json` | Codex reviewer와 정규 finding 입력의 구조를 제한한다. |
| `dot_claude/skills/dual-review/schemas/critique.schema.json` | critique verdict·근거 위치·신규 finding 구조를 제한한다. |
| `dot_claude/skills/dual-review/schemas/synthesis.schema.json` | 익명 synthesis 결정과 양 그룹 ID 배열을 제한한다. |
| `dot_claude/skills/dual-review/scripts/review_state.py` | T3의 `build_round_zero_prompts()`, `execute_round_zero()`, `write_terminal_run_artifacts()` 및 terminal-subset `render_report()`; T4의 `normalize_reviewer_findings()`와 `derive_finding_id(group_label, original_id, file, line_start, line_end, title, body)`; T5의 `validate_and_record_critique()`; T6의 `advance_critique_rounds()`와 `select_termination_reason()`; T7의 `assign_anonymous_groups()`와 `sort_and_shuffle_findings()`; T8이 full report로 확장하는 같은 `render_report()`를 둔다. 이 함수들이 입력, run directory, 실제 dispatch 증거, 정규화, 비평, 종료, 익명 view, sidecar, renderer의 결정적 경계다. |
| `dot_claude/skills/dual-review/templates/report.md` | 로컬 보고서의 섹션 순서와 렌더링 골격이다. |
| `dot_claude/skills/dual-review/tests/test_contracts.py` | 명령어·스키마·오케스트레이션·패키징·비쓰기의 내용 계약을 판정한다. |
| `dot_claude/skills/dual-review/tests/test_execution.py` | 실제 실행 산출물의 입력, run-directory, 호출/판독 순서, 실패 경로를 fixture로 판정한다. |
| `dot_claude/skills/dual-review/tests/test_normalization.py` | Markdown/Codex 어댑터, 원문 ID, confidence, finding ID, body 정규화를 판정한다. |
| `dot_claude/skills/dual-review/tests/test_critique.py` | 교차 비평의 입력 경계와 반증 강등·신규 finding provenance를 판정한다. |
| `dot_claude/skills/dual-review/tests/test_rounds.py` | 라운드 예약, 종료 후보 우선순위, drift 중단을 판정한다. |
| `dot_claude/skills/dual-review/tests/test_synthesis.py` | A/B 배정·정렬·셔플·마스킹·sidecar 분리·결정 분류를 판정한다. |
| `dot_claude/skills/dual-review/tests/test_reporting.py` | 보고서 재현성, 출처 복원, 불일치 섹션을 판정한다. |

## Task dependencies

T1이 스킬 골격과 계약 테스트의 초기 구조를 만든다. T2는 그 골격에 schema와 정적 호출 계약을 추가한다. T3가 실제 라운드 0 실행 산출물을 만들고, T4~T8이 동일한 `review_state.py` 경계를 순서대로 확장한다. T7은 T4 이후에만 시작하여 `finding_id`의 그룹 네임스페이스와 A/B 익명 view가 분리되지 않게 한다. T9는 완성된 모든 산출물을 대상으로 전체 검증을 고정한다.

## Tasks

### T1. 스킬 골격과 패키징 계약을 만든다

- 대상 AC: AC-59, AC-60, AC-61, AC-62, AC-68
- AC-59 `CMD-11` `test_packaging_contract`
- AC-60 `CMD-11` `test_packaging_contract`
- AC-61 `CMD-11` `test_packaging_contract`
- AC-62 `CMD-11` `test_packaging_contract`
- AC-68 `CMD-11` `test_packaging_contract`
- 선행 태스크: 없음
- 생성·수정 파일: `dot_claude/skills/dual-review/SKILL.md`, `dot_claude/skills/dual-review/references/operation.md`, `dot_claude/skills/dual-review/references/verification.md`, `dot_claude/skills/dual-review/schemas/.gitkeep`, `dot_claude/skills/dual-review/scripts/.gitkeep`, `dot_claude/skills/dual-review/templates/report.md`, `dot_claude/skills/dual-review/tests/test_contracts.py`
- [실패 확인] `CMD-11` → 기대: 누락된 여섯 구성 요소, frontmatter 키, 경로 계약 또는 `not configured` 선언을 assertion failure로 보인다.
- [구현] 여섯 구성 요소 디렉터리와 일곱 frontmatter 키를 만들며, `schemas/.gitkeep`과 `scripts/.gitkeep`으로 여섯 구성 요소 존재가 빈 디렉터리가 아닌 추적 가능한 산출물에 근거하게 한다. source `dot_claude/skills/dual-review/SKILL.md`에서 target `~/.claude/skills/dual-review/SKILL.md`를 유도하는 순수 경로 계약을 `test_contracts.py`에 두고 검증 문서를 작성한다. `references/verification.md`는 CMD-4·CMD-5를 목적·종료 코드 계약으로만 서술하고 패턴 리터럴 대신 Global constraints의 안전 placeholder 규약을 참조한다.
- [통과 확인] `CMD-11` → 기대: `test_packaging_contract`가 종료 코드 0이며 경로 계약과 파일 맵을 모두 확인한다.

### T2. reviewer·critique·synthesis 스키마와 정적 안전 계약을 만든다

- 대상 AC: AC-7, AC-8, AC-9, AC-11, AC-12, AC-15, AC-21, AC-22, AC-23, AC-35, AC-36, AC-41, AC-44, AC-49, AC-50, AC-65
- AC-7 `CMD-3` `test_reviewer_contract`
- AC-8 `CMD-3` `test_reviewer_contract`
- AC-9 `CMD-3` `test_reviewer_contract`
- AC-11 `CMD-4`
- AC-12 `CMD-3` `test_reviewer_contract`
- AC-15 `CMD-8` `test_schema_contract`
- AC-21 `CMD-9` `test_critique_contract`
- AC-22 `CMD-9` `test_critique_contract`
- AC-23 `CMD-9` `test_critique_contract`
- AC-35 `CMD-10` `test_synthesis_contract`
- AC-36 `CMD-10` `test_synthesis_contract`
- AC-41 `CMD-10` `test_synthesis_contract`
- AC-44 `CMD-10` `test_synthesis_contract`
- AC-49 `CMD-5`
- AC-50 `CMD-6` `test_no_mutation_contract`
- AC-65 `CMD-6` `test_no_mutation_contract`
- 선행 태스크: T1
- 생성·수정 파일: `dot_claude/skills/dual-review/SKILL.md`, `dot_claude/skills/dual-review/references/operation.md`, `dot_claude/skills/dual-review/schemas/reviewer.schema.json`, `dot_claude/skills/dual-review/schemas/critique.schema.json`, `dot_claude/skills/dual-review/schemas/synthesis.schema.json`, `dot_claude/skills/dual-review/tests/test_contracts.py`
- [실패 확인] `CMD-3` `CMD-6` `CMD-8` `CMD-9` `CMD-10` → 기대: 허용되지 않은 reviewer, sandbox, schema required 필드, fresh synthesis, 수정 호출 또는 외부 import가 있으면 각각 비영으로 실패한다. `CMD-4`·`CMD-5`는 실패시키는 검증이 아니라 T1부터 성립하는 부재 불변식이다. 각 명령은 스킬 디렉터리 존재를 확인하고 내부 `rg`가 종료 코드 1(무매치)을 보고하는 비공허 조건을 관측한다. AC-65의 import 검사는 `scripts/` 아래 Python 파일을 적어도 하나 실제로 검사해야 하나, 이 시점에는 T2가 불변식만 고정하고 `review_state.py`가 생기는 T3의 `CMD-1`이 첫 비공허 관측이다.
- [구현] Claude 다섯 생산자만 선택하고 Codex에는 스킬 소유 schema와 read-only sandbox를 주는 템플릿을 선언한다. critique는 상대 정규 finding+diff만 받게 하고, synthesis는 fresh Claude만 쓰며 `group_a_finding_ids`·`group_b_finding_ids`를 required로 한다. 계약 테스트는 `codex exec`의 허용 플래그 정확 집합 `{-C, --sandbox, --ephemeral, --model, -c, --output-schema, --output-last-message, --json}`과 `--sandbox=read-only`만 allowlist로 단정해 금지 옵션을 열거하지 않고, 확장된 안전 플래그가 CMD-4 패턴과 일치하지 않음을 확인한다. 필요한 거부 token fixture는 `tempfile.TemporaryDirectory()` 아래 스캔 대상 밖에서 프로그램적으로 구성하고, GitHub 쓰기·자동 수정은 목적 기반 contract로 막는다. AC-65 import 검사는 `scripts/`의 Python 파일을 최소 하나 검사하도록 고정하되 T3의 `CMD-1`에서 처음 비공허하게 관측한다.
- [판정 대상 분리] R2.2의 AC-9는 정적 호출 템플릿이라 `test_reviewer_contract`로, AC-10은 실제 schema-위반 등록 경로라 T3의 실행 fixture로 판정한다. R3.1·R6.4·R6.5의 schema 선언 AC-15·AC-41·AC-44는 이 태스크의 schema 계약으로, 동작 AC-16·AC-42·AC-43은 각각 T4·T7 실행 fixture로 판정한다. R7.3의 AC-49는 전체 소스 부재 scan, AC-50은 오케스트레이션 비수정 동작이라 서로 다른 CMD를 쓴다.
- [통과 확인] `CMD-3` `CMD-4` `CMD-5` `CMD-6` `CMD-8` `CMD-9` `CMD-10` → 기대: 각 필터가 종료 코드 0이고 CMD-4·CMD-5의 스킬 디렉터리 전체 scan은 무매치 경로만 성공한다. CMD-6의 import 불변식은 고정됐으며 실제 `scripts/` Python 검사 비공허성은 T3의 `CMD-1`에서 처음 확인한다.

### T3. 입력·실제 라운드 0 디스패치·run directory 경계를 구현한다

- 대상 AC: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-10, AC-13, AC-14, AC-51, AC-52, AC-53, AC-54, AC-55, AC-56, AC-57, AC-58
- AC-1 `CMD-2` `test_arguments`
- AC-2 `CMD-2` `test_arguments`
- AC-3 `CMD-1` `test_*.py`
- AC-4 `CMD-1` `test_*.py`
- AC-5 `CMD-1` `test_*.py`
- AC-6 `CMD-1` `test_*.py`
- AC-10 `CMD-1` `test_*.py`
- AC-13 `CMD-7` `test_independence`
- AC-14 `CMD-7` `test_independence`
- AC-51 `CMD-1` `test_*.py`
- AC-52 `CMD-1` `test_*.py`
- AC-53 `CMD-1` `test_*.py`
- AC-54 `CMD-1` `test_*.py`
- AC-55 `CMD-1` `test_*.py`
- AC-56 `CMD-1` `test_*.py`
- AC-57 `CMD-1` `test_*.py`
- AC-58 `CMD-1` `test_*.py`
- 선행 태스크: T1, T2
- 생성·수정 파일: `dot_claude/skills/dual-review/scripts/review_state.py`, `dot_claude/skills/dual-review/tests/test_execution.py`, `dot_claude/skills/dual-review/tests/test_contracts.py`
- [실패 확인] `CMD-1` `CMD-2` `CMD-7` → 기대: 잘못된 인자, 빈 diff, fixture-only 프롬프트 증명, 한쪽을 먼저 판독한 이벤트 또는 재시도 횟수 오류가 assertion failure가 된다.
- [구현] `build_round_zero_prompts()`·`execute_round_zero()`로 인자·SHA·변경 파일을 고정하고, run ID의 결정적 대상 부분과 단조 실행 구분자를 분리한다. 실제 executor가 `build_round_zero_prompts()`의 반환값을 덧붙임 없이 dispatch하여 `<run_dir>/round0-*.prompt`에 저장하고, `started:claude`, `started:codex` 뒤에만 `read:*` 이벤트를 append하는 gate를 둔다. AC-13 테스트는 이 executor를 실제로 실행한 임시 run directory의 보존 프롬프트·dispatch 기록을 읽으며, 손으로 만든 fixture만으로 통과하지 못하게 한다. 임시 root의 `.claude/dual-review-state/.gitignore`에는 정확히 `*`를 쓴다. `write_terminal_run_artifacts()`와 terminal-subset `render_report()`는 `no_changes`·`reviewer_failure`·`single_reviewer`마다 T1 template에서 `<run_dir>/report.md`를 내보내고, `<run_dir>/provenance.json`에 source 상태·실패 원인·재시도 수·원문/검증 오류 또는 stderr/exit 정보의 최소 run-directory 계약을 쓴다. 형식 재요청은 리뷰어 출력 전체가 schema 검증에 실패한 경우에만 정확히 한 번 발동하며, 두 번째 전체 위반 뒤 출처를 제외한다. 양쪽 실패는 synthesis 호출 없이 비성공으로 끝내고, 한쪽만 유효하면 cross critique와 양측 분류를 호출하지 않은 채 제한 상태를 기록한다.
- [판정 대상 분리] R2.2의 AC-10은 schema-위반 출력이 실제 유효 리뷰 등록을 막는 실행 동작이므로, T2의 정적 Codex 명령 계약 AC-9와 달리 이 태스크의 `CMD-1` fixture로 판정한다. PLAN-001은 (A)를 선택한다. T3가 이미 실패·timeout·단일 출처 상태를 보존하므로 그 종결 경로의 최소 report/sidecar 작성도 이 경계가 소유하는 편이 자연스럽다. T8은 같은 `render_report()`를 critique·synthesis·`두 리뷰어가 갈린 지점` 절로 확장하며, 그 부분은 AC-45~AC-48·AC-69가 소유한다.
- [통과 확인] `CMD-1` `CMD-2` `CMD-7` → 기대: 이 시점에 존재하는 지정 테스트가 종료 코드 0이고 실제 run-directory 증거가 구성 문자열=디스패치 문자열 및 양쪽 시작 후 판독을 입증한다.

### T4. 정규 finding·원문 ID·불투명 식별자를 구현한다

- 대상 AC: AC-16, AC-17, AC-18, AC-19, AC-20, AC-71
- AC-16 `CMD-1` `test_*.py`
- AC-17 `CMD-1` `test_*.py`
- AC-18 `CMD-1` `test_*.py`
- AC-19 `CMD-1` `test_*.py`
- AC-20 `CMD-1` `test_*.py`
- AC-71 `CMD-1` `test_*.py`
- 선행 태스크: T2, T3
- 생성·수정 파일: `dot_claude/skills/dual-review/scripts/review_state.py`, `dot_claude/skills/dual-review/tests/test_normalization.py`
- [실패 확인] `CMD-1` → 기대: severity 변환, 순번 소비, 0–100 confidence, path/행 검증, body 공통화 또는 명시적 group 인자와 나머지 여섯 입력의 `fid_` canonical 직렬화가 어긋난 fixture가 assertion failure가 된다.
- [구현] `normalize_reviewer_findings()`는 Claude `title` 경계 블록에 producer별 검증 전 1-based ordinal을 부여하고, Codex에는 `codex`+응답 findings 배열 1-based ordinal을 부여한다. 비평 신규 finding은 `cross-critique:<작성 source>`+그 응답 배열 1-based ordinal을 쓴다. 1 초과 confidence만 100으로 나눈다. `derive_finding_id(group_label, original_id, file, line_start, line_end, title, body)`는 주어진 group 인자와 나머지 여섯 입력의 R3.2 길이 접두어/NUL/SHA-256로 불투명 ID를 순수 파생한다. 거부 finding은 보정·재사용하지 않으며, finding 단위 거부는 출처 단위 재시도 카운터를 올리지 않고 출처를 제외하지도 않는다. T4 fixture는 이 불변식과 A/B body의 같은 라벨 순서·문단 구조·접두어를 `CMD-1`으로 단정한다.
- [판정 대상 분리] R3.1의 AC-15는 schema의 required 열이라는 정적 선언이라 T2의 `CMD-8`로, AC-16은 `normalize_reviewer_findings()` adapter와 confidence 변환의 실행 결과라 이 태스크의 `CMD-1`로 판정한다. T4는 명시적 group 인자를 받는 순수 `derive_finding_id()`와 fixture 검증만 소유하고, 실제 source의 group 값 공급은 T7의 `assign_anonymous_groups()` 통합 경계가 소유한다.
- [통과 확인] `CMD-1` → 기대: 이 시점에 존재하는 전체 테스트가 종료 코드 0이고 거부 전 ordinal, 주어진 group 인자와 서로 다른 입력의 서로 다른 `fid_`, 공통 body 형식을 확인한다.

### T5. 교차 비평의 근거 검증과 신규 finding provenance를 구현한다

- 대상 AC: AC-24, AC-25, AC-26
- AC-24 `CMD-1` `test_*.py`
- AC-25 `CMD-1` `test_*.py`
- AC-26 `CMD-1` `test_*.py`
- 선행 태스크: T2, T3, T4
- 생성·수정 파일: `dot_claude/skills/dual-review/scripts/review_state.py`, `dot_claude/skills/dual-review/tests/test_critique.py`
- [실패 확인] `CMD-1` → 기대: 근거 위치가 없거나 대상 밖인 `반증됨`, 혹은 round/reviewer provenance가 없는 신규 finding이 assertion failure가 된다.
- [구현] `validate_and_record_critique()`가 critique payload의 repository-relative 근거를 대상 snapshot으로 검증해 무효 반증을 `미검증`으로 강등하고, 신규 finding은 T4의 `normalize_reviewer_findings()` 경로로 보내며 T3의 최소 sidecar를 확장해 round와 reviewer를 기록한다.
- [통과 확인] `CMD-1` → 기대: 전체 테스트가 종료 코드 0이고 두 무효 반증 fixture가 `미검증`이며 신규 finding provenance가 보존된다.

### T6. 교차 비평 라운드와 종료 우선순위를 구현한다

- 대상 AC: AC-27, AC-28, AC-29, AC-30, AC-31, AC-32, AC-33, AC-34
- AC-27 `CMD-1` `test_*.py`
- AC-28 `CMD-1` `test_*.py`
- AC-29 `CMD-1` `test_*.py`
- AC-30 `CMD-1` `test_*.py`
- AC-31 `CMD-1` `test_*.py`
- AC-32 `CMD-1` `test_*.py`
- AC-33 `CMD-1` `test_*.py`
- AC-34 `CMD-1` `test_*.py`
- 선행 태스크: T3, T5
- 생성·수정 파일: `dot_claude/skills/dual-review/scripts/review_state.py`, `dot_claude/skills/dual-review/tests/test_rounds.py`
- [실패 확인] `CMD-1` → 기대: 잘못된 round 2 예약, 한 번의 quiet를 수렴 처리, round 2 초과, 독립 리뷰 재호출, 0.5 경계 오류 또는 복수 종료 사유가 assertion failure가 된다.
- [구현] `advance_critique_rounds()`가 양쪽 유효 리뷰 뒤의 round 1, `--rounds=2`+신규 high 뒤의 단 한 번 round 2를 상태 전이로 제한한다. `select_termination_reason()`이 후보 종료 사유를 R7.1 전순서로 하나 선택하고, 변경 파일 밖 비율이 0.5 초과일 때만 drift로 중단한다.
- [통과 확인] `CMD-1` → 기대: 전체 테스트가 종료 코드 0이고 모든 겹친 후보 fixture가 정확히 하나의 우선순위 종료 사유를 가진다.

### T7. 익명 A/B view·마스킹·종합 결정 경계를 구현한다

- 대상 AC: AC-37, AC-38, AC-39, AC-40, AC-42, AC-43
- AC-37 `CMD-1` `test_*.py`
- AC-38 `CMD-1` `test_*.py`
- AC-39 `CMD-1` `test_*.py`
- AC-40 `CMD-1` `test_*.py`
- AC-42 `CMD-1` `test_*.py`
- AC-43 `CMD-1` `test_*.py`
- 선행 태스크: T4, T5, T6
- 생성·수정 파일: `dot_claude/skills/dual-review/scripts/review_state.py`, `dot_claude/skills/dual-review/tests/test_synthesis.py`
- [실패 확인] `CMD-1` → 기대: 실제 source의 A/B 배정→그룹 공급→ID 파생→ASCII 정렬·seeded shuffle 호출 순서 위반, source/원문 ID/생산자 평문 또는 sidecar 누출, 불안정한 그룹/셔플, 단일 출처 빈 배열 누락, 마스킹 없이 finding 제거, 불일치 소거가 assertion failure가 된다.
- [구현] `assign_anonymous_groups()`가 먼저 run ID 유도 시드와 실행 구분자로 실제 source의 A/B 배정을 결정한다. 이어 그 group 값을 T4의 순수 `derive_finding_id()`에 공급해 `finding_id`를 확정하고, `sort_and_shuffle_findings()`가 확정 ID를 ASCII 바이트 오름차순으로 정렬한 뒤 seeded shuffle한다. sidecar에는 seed·실제 source↔group·원문 ID↔`finding_id` 매핑·마스킹 사실을 기록하고, 익명 view에는 group·불투명 ID·후보 논점·critique만 남긴다. 다섯 생산자명과 원문 ID 평문은 `<redacted:sha256-12>`으로 결정 치환하며 finding은 유지한다. synthesis 결과의 양 그룹 ID 필드는 항상 존재시키고 단일 출처 반대편은 `[]`로 하며 불일치는 별도 항목으로 보존한다.
- [판정 대상 분리] R6.4의 AC-41은 schema required 선언이라 T2의 `CMD-10`으로, AC-42는 그룹 입력에 따른 결정 결과라 이 태스크의 `CMD-1`로 판정한다. R6.5의 AC-44는 Codex template 부재 계약, AC-43은 불일치 보존 동작이므로 각각 T2와 이 태스크의 판정 대상을 쓴다.
- [통과 확인] `CMD-1` → 기대: 이 시점에 존재하는 전체 테스트가 종료 코드 0이고 실제 source의 A/B 배정→group 공급→ID 파생→ASCII 정렬·seeded shuffle 순서와 sidecar 매핑, A/B 교대·동일 run 재현·sidecar 분리·마스킹 provenance·합의/불일치/단일 출처 결과를 확인한다.

### T8. provenance 복원 로컬 보고서를 결정적으로 렌더링한다

- 대상 AC: AC-45, AC-46, AC-47, AC-48, AC-63, AC-64, AC-69
- AC-45 `CMD-1` `test_*.py`
- AC-46 `CMD-1` `test_*.py`
- AC-47 `CMD-1` `test_*.py`
- AC-48 `CMD-1` `test_*.py`
- AC-63 `CMD-12` `test_deterministic_boundaries`
- AC-64 `CMD-12` `test_deterministic_boundaries`
- AC-69 `CMD-1` `test_*.py`
- 선행 태스크: T1, T3, T4, T5, T6, T7
- 생성·수정 파일: `dot_claude/skills/dual-review/scripts/review_state.py`, `dot_claude/skills/dual-review/templates/report.md`, `dot_claude/skills/dual-review/tests/test_contracts.py`, `dot_claude/skills/dual-review/tests/test_reporting.py`
- [실패 확인] `CMD-1` `CMD-12` → 기대: `report.md` 부재, 종료 사유 0개/복수, sidecar 출처 미복원, 불일치 주장·근거 누락 또는 입력 순서별 Markdown 차이가 assertion failure가 된다. AC-63의 SKILL.md 내 Python 규칙 구현 또는 오케스트레이션 경로 부재, AC-64의 라운드 0 dispatch·순서 gate·정규화·ID·셔플·종료·렌더링 결정적 경계 부재도 assertion failure가 된다.
- [구현] report template에 대상·종료 사유·reviewer 상태·정규 finding·critique·synthesis 및 `두 리뷰어가 갈린 지점` 절을 고정한다. T3의 terminal-subset `render_report()`를 full `render_report()`로 확장하고, 이 renderer만 sidecar를 읽어 출처를 복원하며 T7의 결정적 순서를 소비해 같은 논리 입력에는 같은 Markdown을 만든다. `test_deterministic_boundaries`는 SKILL.md가 Python 규칙을 포함하지 않고 오케스트레이션 경로만 참조하는지와 `build_round_zero_prompts()`·`execute_round_zero()`·`write_terminal_run_artifacts()`, `normalize_reviewer_findings()`·`derive_finding_id(group_label, original_id, file, line_start, line_end, title, body)`, `validate_and_record_critique()`, `advance_critique_rounds()`·`select_termination_reason()`, `assign_anonymous_groups()`·`sort_and_shuffle_findings()`, full `render_report()`가 Python scripts에 모두 있는지를 함께 판정한다.
- [판정 대상 분리] AC-63과 AC-64는 같은 `CMD-12` 필터가 SKILL.md의 오케스트레이션 경로와 모든 결정적 Python 경계를 함께 판정하므로, T3 시점에는 정규화·ID·셔플·종료·렌더링이 아직 없어 통과할 수 없다. 두 AC를 다섯 경계가 모두 존재하는 T8로 옮기고, AC-45~AC-48·AC-69의 보고서 동작 `CMD-1`과 분리해 `CMD-12`로 판정한다.
- [통과 확인] `CMD-1` `CMD-12` → 기대: 이 시점에 존재하는 전체 테스트와 `test_deterministic_boundaries`가 종료 코드 0이고 모든 필수 절, 단 하나의 종료 사유, 모든 불일치 ID/양측 주장/근거, 입력 순서 불변 Markdown, AC-63의 SKILL.md 오케스트레이션 참조, AC-64의 라운드 0 dispatch·순서 gate·정규화·ID·셔플·종료·렌더링 Python 경계를 확인한다.

### T9. 전체 검증 계약과 비쓰기 보증을 마감한다

- 대상 AC: AC-66, AC-67, AC-70
- AC-66 `CMD-1` `test_*.py`
- AC-67 `CMD-4` `CMD-5`
- AC-70 `CMD-1` `test_*.py`
- 선행 태스크: T1, T2, T3, T4, T5, T6, T7, T8
- 생성·수정 파일: `dot_claude/skills/dual-review/references/verification.md`, `dot_claude/skills/dual-review/tests/test_contracts.py`
- [실패 확인] `CMD-1` `CMD-4` `CMD-5` → 기대: test discovery의 빈 선택·실패, 금지 문자열 매치, 또는 `rg` 경로/실행 오류가 비영으로 실패하고 외부 쓰기/코드 수정 spy가 assertion failure가 된다.
- [구현] 전체 suite가 실제 테스트를 발견하는지, 두 `rg` wrapper가 0=실패·1=성공·그 밖=실패인지, orchestration spy가 외부 쓰기와 코드 수정 0회인지 고정한다. Global constraints의 리터럴 부재 불변식을 재확인해 verification 문서는 CMD-4·CMD-5의 목적·종료 코드 계약만 유지하고, contract tests는 allowlist·스캔 대상 밖 프로그램적 token 구성만 유지한다. 따라서 최종 scan은 범위를 줄이지 않은 스킬 디렉터리 전체에서 비공허하면서 무매치다.
- [판정 대상 분리] R9.4는 전체 suite AC-66·AC-70, 두 부재 scan AC-67, 패키징 문서 AC-68, renderer 결정성 AC-69를 함께 요구한다. 각 AC는 검증하는 산출물 경계가 달라 Spec이 정한 CMD-1·CMD-4/5·CMD-11을 그대로 유지한다.
- [통과 확인] `CMD-1` `CMD-4` `CMD-5` → 기대: 전체 Python suite와 두 부재 검사가 모두 종료 코드 0이고 확인된 외부 쓰기 및 코드 수정이 0회다.

## Verification commands

다음 순서로 실행한다. `CMD-1`은 최종 전체 회귀 검사이므로 개별 계약 검사 뒤에 실행한다.

| ID | Command | Expected outcome |
|---|---|---|
| CMD-2 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_arguments` | 종료 코드 0 |
| CMD-3 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_reviewer_contract` | 종료 코드 0 |
| CMD-7 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_independence` | 종료 코드 0 |
| CMD-8 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_schema_contract` | 종료 코드 0 |
| CMD-9 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_critique_contract` | 종료 코드 0 |
| CMD-10 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_synthesis_contract` | 종료 코드 0 |
| CMD-11 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_packaging_contract` | 종료 코드 0 |
| CMD-12 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_deterministic_boundaries` | 종료 코드 0 |
| CMD-6 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_no_mutation_contract` | 종료 코드 0 |
| CMD-4 | `sh -c 'test -d dot_claude/skills/dual-review || exit 2; rg -n --hidden --no-ignore --glob "*" -e "--skip-git-repo-check" -e "--dangerously-bypass-approvals-and-sandbox" -e "--full-auto" -e "--yolo" -e "--add-dir" dot_claude/skills/dual-review; code=$?; case $code in 1) exit 0;; 0) exit 1;; *) exit "$code";; esac'` | 무매치만 종료 코드 0; 매치·오류는 비영 |
| CMD-5 | `sh -c 'test -d dot_claude/skills/dual-review || exit 2; rg -n --hidden --no-ignore --glob "*" -e "gh pr review" -e "gh pr comment" -e "gh api" dot_claude/skills/dual-review; code=$?; case $code in 1) exit 0;; 0) exit 1;; *) exit "$code";; esac'` | 무매치만 종료 코드 0; 매치·오류는 비영 |
| CMD-1 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'` | 종료 코드 0이며 빈 선택의 종료 코드 5가 아님 |

## Rollout and rollback

구현은 T1→T9 순서로 새 파일만 만든다. 각 태스크에서 `[실패 확인]`의 비영 결과를 먼저 관찰하고 해당 태스크의 `[통과 확인]`이 종료 코드 0이 아니면 다음 태스크로 진행하지 않는다. T2의 CMD-4·CMD-5는 예외적으로 T1 이후 성립하는 부재 불변식이라 내부 `rg`의 무매치 종료 코드 1을 관찰한다. 부분 구현은 `CMD-1`의 실패 test name, 생성된 스킬 디렉터리의 파일 목록, 그리고 존재하면 임시 fixture root의 `.claude/dual-review-state/<run_id>/`의 `started:`/`read:` 이벤트와 provenance sidecar로 판별한다.

호출 실패·schema 위반·timeout은 구현 결과가 아니라 스킬 실행의 보고 가능한 상태이며, report와 run directory에서 원인·재시도·제외 여부를 확인한다. 이 변경은 신규 파일만 만들고 기존 파일 수정은 0건이므로, 롤백 trigger는 최종 `CMD-1`/`CMD-4`/`CMD-5` 실패 또는 계약 위반이다. 롤백은 새로 만든 `dot_claude/skills/dual-review/` 디렉터리만 삭제하여 수행하며, 기존 파일을 복원하거나 Git 쓰기 명령을 사용하지 않는다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T3 | CMD-2 `test_arguments` | 종료 코드 0 |
| AC-2 | T3 | CMD-2 `test_arguments` | 종료 코드 0 |
| AC-3 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-4 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-5 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-6 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-7 | T2 | CMD-3 `test_reviewer_contract` | 종료 코드 0 |
| AC-8 | T2 | CMD-3 `test_reviewer_contract` | 종료 코드 0 |
| AC-9 | T2 | CMD-3 `test_reviewer_contract` | 종료 코드 0 |
| AC-10 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-11 | T2 | CMD-4 | 무매치만 종료 코드 0 |
| AC-12 | T2 | CMD-3 `test_reviewer_contract` | 종료 코드 0 |
| AC-13 | T3 | CMD-7 `test_independence` | 종료 코드 0 |
| AC-14 | T3 | CMD-7 `test_independence` | 종료 코드 0 |
| AC-15 | T2 | CMD-8 `test_schema_contract` | 종료 코드 0 |
| AC-16 | T4 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-17 | T4 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-18 | T4 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-19 | T4 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-20 | T4 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-21 | T2 | CMD-9 `test_critique_contract` | 종료 코드 0 |
| AC-22 | T2 | CMD-9 `test_critique_contract` | 종료 코드 0 |
| AC-23 | T2 | CMD-9 `test_critique_contract` | 종료 코드 0 |
| AC-24 | T5 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-25 | T5 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-26 | T5 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-27 | T6 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-28 | T6 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-29 | T6 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-30 | T6 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-31 | T6 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-32 | T6 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-33 | T6 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-34 | T6 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-35 | T2 | CMD-10 `test_synthesis_contract` | 종료 코드 0 |
| AC-36 | T2 | CMD-10 `test_synthesis_contract` | 종료 코드 0 |
| AC-37 | T7 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-38 | T7 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-39 | T7 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-40 | T7 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-41 | T2 | CMD-10 `test_synthesis_contract` | 종료 코드 0 |
| AC-42 | T7 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-43 | T7 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-44 | T2 | CMD-10 `test_synthesis_contract` | 종료 코드 0 |
| AC-45 | T8 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-46 | T8 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-47 | T8 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-48 | T8 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-49 | T2 | CMD-5 | 무매치만 종료 코드 0 |
| AC-50 | T2 | CMD-6 `test_no_mutation_contract` | 종료 코드 0 |
| AC-51 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-52 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-53 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-54 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-55 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-56 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-57 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-58 | T3 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-59 | T1 | CMD-11 `test_packaging_contract` | 종료 코드 0 |
| AC-60 | T1 | CMD-11 `test_packaging_contract` | 종료 코드 0 |
| AC-61 | T1 | CMD-11 `test_packaging_contract` | 종료 코드 0 |
| AC-62 | T1 | CMD-11 `test_packaging_contract` | 종료 코드 0 |
| AC-63 | T8 | CMD-12 `test_deterministic_boundaries` | 종료 코드 0 |
| AC-64 | T8 | CMD-12 `test_deterministic_boundaries` | 종료 코드 0 |
| AC-65 | T2 | CMD-6 `test_no_mutation_contract` | 종료 코드 0 |
| AC-66 | T9 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-67 | T9 | CMD-4 CMD-5 | 둘 다 무매치만 종료 코드 0 |
| AC-68 | T1 | CMD-11 `test_packaging_contract` | 종료 코드 0 |
| AC-69 | T8 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-70 | T9 | CMD-1 `test_*.py` | 종료 코드 0 |
| AC-71 | T4 | CMD-1 `test_*.py` | 종료 코드 0 |
