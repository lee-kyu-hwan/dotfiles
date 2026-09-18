# Quality Goal Specification

- Task ID: 20260911T025854Z-105-dual-review-실행-결함-수정-모델-선택-producer-ced012ff
- Mode: strict
- Status: DRAFT
- Created: 2026-09-11
- Updated: 2026-09-11
- Source goal: #105 dual-review 실행 결함 수정: 모델 선택·producer stdin 즉시 전달·reviewer/critique/synthesis strict schema 계약·chezmoi 설치본 패키징

## Problem and context

chezmoi가 관리하는 `dot_claude/skills/dual-review/` version 1.2.0은 독립적인 Claude/Codex 리뷰, 교차 검토, Claude 종합을 로컬 산출물로 남기는 읽기 전용 스킬이다. 관리 대상은 `~/.claude/skills/dual-review/`이다. 기준 커밋은 `067923b554f159cf8c12e37f353f572951824b41`, 작업 브랜치는 `105-fix/dual-review-runtime`이며 발견 시점의 작업 트리는 깨끗했다.

GitHub 이슈 #105와 2026-09-11 직접 검증에서 다음 결함이 확인됐다.

- `SKILL.md`의 `model: claude`는 Claude Code가 인식하지 못한다. 같은 임시 probe에서 `model: claude`는 `unrecognized_model`로 본문 실행 전에 실패했고 `model: opus`는 `PROBE_OK`를 반환했다.
- `_round_zero`는 다섯 Claude producer와 Codex를 전부 시작한 뒤 순차적으로 읽어 독립성을 보장하지만, `SubprocessAdapter.start()`는 stdin pipe만 만들고 `read()`의 `communicate(prompt, ...)`까지 프롬프트 전송을 미룬다. Claude Code 2.1.268은 stdin을 3초 안에 받지 못하면 입력 없음으로 종료했다. 프롬프트는 `MAX_PROMPT_DIFF_BYTES = 262144`에 부가 문구가 더해질 수 있어 pipe에 동기식으로 쓰면 macOS의 통상 64KB pipe 용량을 넘어 시작 루프를 막을 수 있다.
- `reviewer.schema.json`, `critique.schema.json`, `synthesis.schema.json`은 루트와 중첩 object에 `additionalProperties: false`가 없으며, `critique.schema.json`의 `new_findings.items`는 속성조차 없는 무제약 object다. 현행 reviewer schema를 사용한 Codex `--output-schema` probe는 HTTP 400과 함께 정확히 `Invalid schema for response_format 'codex_output_schema': In context=(), 'additionalProperties' is required to be supplied and to be false.`를 반환했다. 원문과 명령은 `.claude/quality-state/20260911T025854Z-105-dual-review-실행-결함-수정-모델-선택-producer-ced012ff/evidence/probe-findings-2026-09-11.md`, 거부된 사본은 같은 디렉터리의 `current.json`에 있다. 루트·중첩 object를 모두 닫고 `required == properties`로 맞추되 기존 `minimum`, `maximum`, `minLength`, `enum`과 신규 `minItems: 1`을 그대로 둔 `strict.json`은 Codex에서 exit 0으로 수용됐고 `strict.result.json`을 반환했다. 이 증거는 Codex reviewer 경로만 확정하며 Claude `--json-schema`와 critique/synthesis 경로는 아직 미실증이다.
- 소스에서 93개 테스트가 통과하지만 `chezmoi archive`로 재현한 배포 트리에서는 `schemas/.gitkeep` 부재로 1개가 실패한다. `scripts/.gitkeep`도 배포되지 않는다. 두 파일은 비어 있지 않은 디렉터리를 지키지 않으므로 삭제 대상이다. archive는 파일시스템 기준이라 테스트가 만든 `__pycache__`와 `.pyc`도 현재 규칙으로는 포함한다.
- 실패 보고서에는 이미 사람이 읽을 수 있는 `Termination reason`과 `Reviewer status`가 렌더링되고, 파싱 가능한 블록이 없는 Claude producer는 이미 제외된다. 새로 메울 구멍은 Codex를 포함한 유효 envelope의 빈 `findings`가 성공으로 집계되는 점과 `main()`이 `reviewer_failure` 등 미완료 종료에서도 0을 반환하는 점이다.

실증 대상은 `/Users/lee-kyu-hwan/code/zambaguni-front-landing-noindex`, 브랜치 `1406-improvement/landing-noindex`, 논리적 base `origin/develop`이다. 현재 PR 범위인 `origin/develop...HEAD`는 3파일, unified-0 diff 18,505바이트이고 기존 실행 `e7a6d2872362a4d6-000001`을 보존해야 한다. 현재 `origin/develop` tip은 브랜치의 merge-base보다 앞서 있으므로 직접 양끝 diff는 PR 범위가 아닌 7파일을 포함한다. 실증에서는 merge-base SHA를 명시적으로 계산해 지정된 3파일 범위를 고정한다.

## Goals

- 임시 프로젝트의 실제 slash 호출이 Opus 모델을 선택하고 모델 오류 없이 스킬 본문과 `no_changes` 종료까지 도달한다.
- 다섯 Claude producer와 `gpt-5.6-sol` Codex를 모두 먼저 시작하면서 각 프로세스가 시작 즉시, 정확히 한 번 프롬프트를 받게 한다.
- 세 structured-output schema를 재귀적으로 닫힌 strict 계약으로 만들고 실제 Claude/Codex API 경로에서 검증한다.
- chezmoi가 실제 배포하는 트리를 `$HOME` 변경 없이 재현해 소스와 동일한 패키지 테스트 결과를 얻는다.
- 빈 finding과 리뷰어/하류 실패를 성공으로 오인하지 않고 보고서와 프로세스 종료 코드 양쪽에서 미완료를 드러낸다.
- 지정된 landing-noindex PR 범위에서 독립 리뷰, 교차 검토, fresh-Claude 종합을 끝까지 실행하고 증거를 보존한다.

## Non-goals

- PR 자동 게시, 재실행 기반 갱신 등 dual-review 2단계 기능.
- Codex용 dual-review 스킬 배포.
- 제품 저장소 `zambaguni-front`의 리뷰 대상 코드 변경, commit, push, PR 생성, PR 리뷰 게시 또는 PR 댓글 게시. 실증은 읽기 전용 모델 호출과 무시되는 로컬 상태 산출물 생성까지만 허용한다.
- dual-review의 리뷰 품질이나 프롬프트 문구 개선, 라운드 정책 또는 종료 사유 체계 재설계.
- 이 저장소의 `.gitignore` 변경. 배포 오염 방지를 위한 `.chezmoiignore`의 dual-review cache 규칙 추가는 범위 안이다.
- 이 Spec 작성 라운드에서 구현, chezmoi의 `$HOME` 적용, commit, push 또는 PR 생성. 구현·테스트·리뷰 완료 뒤 dotfiles 저장소의 관련 변경만 commit·push하고 PR을 만드는 일은 별도 승인된 통합 단계이며 제품 저장소에는 적용되지 않는다.
- 현재 범위를 벗어난 `--base` 의미 변경. 실증 명령에서 merge-base SHA를 계산하는 것은 지정된 PR diff를 고정하기 위한 검증 입력 선택이지 런타임 base 정책 변경이 아니다.

## Requirements

- **R1.1** `dot_claude/skills/dual-review/SKILL.md` frontmatter의 Claude 모델 식별자는 사용자가 선택한 `opus`여야 하며, 임시 프로젝트에 복사한 실제 slash 호출에서 인식돼야 한다.
- **R1.2** `build_codex_command()`는 모든 Codex reviewer/critique 호출에 `--model gpt-5.6-sol`을 정확히 한 번 포함하고 기존 `--sandbox read-only`, schema, JSON event, last-message 계약을 보존해야 한다. 모든 Codex 호출은 위치 인자 prompt 없이 stdin으로 prompt와 EOF를 전달해야 하며, 현행 stdin 계약을 회귀 고정해야 한다.
- **R1.3** `references/operation.md`의 검증된 Claude CLI 계약은 실제 재현과 flag 확인에 사용한 Claude Code 2.1.268로 갱신하고, 계약 테스트도 이 값과 `-p`, `--no-session-persistence`, `--setting-sources`, `--permission-mode`, `--permission-prompts`, `--allowedTools`, `--agent`, `--output-format`, `--json-schema`를 고정해야 한다. `--allowedTools`는 뒤따르는 위치 prompt까지 흡수할 수 있는 가변 인자이므로 이를 쓰는 호출은 prompt를 stdin으로만 전달하고 allowlist 뒤에 위치 prompt를 두지 않아야 한다.
- **R2.1** `_round_zero`는 다섯 Claude producer와 Codex의 `Popen`을 모두 완료한 뒤 첫 결과를 읽는 순서를 보존하면서, 각 `start()`가 반환하기 전에 해당 프롬프트를 자식의 stdin 공급원에 연결해야 한다. 구현은 256KB 초과 프롬프트에서도 자식의 pipe 소비 여부에 의해 시작 루프가 블로킹되지 않아야 한다.
- **R2.2** `read()`는 이미 연결된 프롬프트를 다시 보내지 않고 stdout/stderr 수거와 parsing만 수행해야 한다. timeout이면 기존처럼 kill 후 잔여 출력을 수거하고 exit code 124와 `timeout` status를 유지해야 한다.
- **R2.3** prompt 임시 파일과 output-last-message 임시 파일은 성공, `Popen` 실패, parse 실패, timeout, kill 후 수거 경로에서 모두 정리돼야 한다. 구현과 테스트는 Python 표준 라이브러리만 사용해야 한다.
- **R3.1** 세 schema의 모든 `type: object` 노드는 `additionalProperties: false`, 비어 있지 않은 `properties`, `properties` 전체와 정확히 같은 `required`를 가져야 한다. 모든 property와 array item에는 모호하지 않은 `type` 제약이 있어야 하고 string enum도 `type: string`을 명시해야 한다. reviewer의 `findings`는 Codex에서 수용이 확인된 `minItems: 1`로 최소 한 항목을 요구해야 한다. Codex 실증이 수용한 기존 `minimum`, `maximum`, `minLength`, `enum` 제약은 제거하지 않으며 Claude와 critique/synthesis의 provider 수용 여부는 live probe로 닫아야 한다.
- **R3.2** `critique.schema.json`의 `new_findings.items`는 normalization이 소비하는 severity, title, body, file, line 범위, confidence, recommendation을 명시한 닫힌 object여야 하며 각 속성이 required여야 한다.
- **R3.3** Codex의 `--output-schema <path>`와 Claude의 `--json-schema <schema text>` 전달 방식을 보존하고, production builder를 쓰는 opt-in live probe가 reviewer, critique, synthesis schema 전부와 실제 사용 CLI 양쪽을 합쳐 검증해야 한다. `DUAL_REVIEW_LIVE_API`가 설정되지 않은 기본 discover에서는 live probe 전체를 `skip`하고 어떤 모델도 호출하지 않아야 한다.
- **R4.1** 무효한 `schemas/.gitkeep`와 `scripts/.gitkeep`를 삭제하고 packaging의 `required_paths`를 `scripts/review_state.py`, 세 schema, `tests/test_live_api.py`, `tests/live_e2e.py`, 실제 테스트·template·reference 등 배포 필수 파일로 교체해야 한다. 두 live helper도 관리 대상 스킬 패키지의 일부다.
- **R4.2** packaging 회귀 가드는 스킬 아래의 모든 파일·디렉터리 이름을 검사해 chezmoi가 소스 이름을 누락하거나 다르게 해석할 숨김/예약 형태를 거부해야 하며, 수정된 소스 트리와 archive로 푼 배포 트리에서 동일하게 통과해야 한다. `tests/test_live_api.py`와 `tests/live_e2e.py`는 source/archive 상대 경로 동등성에 포함되고 배포본에서도 import·CLI 도움말 검사가 가능해야 한다.
- **R4.3** `.chezmoiignore`는 `.claude/skills/dual-review/**/__pycache__`를 배포에서 제외해야 한다. archive에는 `__pycache__`, `.pyc`, 삭제된 `.gitkeep`가 없어야 하며 검증은 지정 worktree를 `--source`로 사용한 archive를 임시 디렉터리에 풀 뿐 `$HOME`을 변경하지 않아야 한다.
- **R5.1** reviewer 응답은 schema 형태뿐 아니라 normalization 규칙상 최소 한 개의 유효 finding이 있어야 완성된 리뷰다. `_round_zero`는 익명 group label과 diff line range가 생기기 전에, `normalize_reviewer_findings()`와 동일한 parsing·필드 유효성 primitive를 쓰되 finding ID를 만들지 않는 검증 전용 경로로 유효 항목 수를 판정한다. exit 0의 빈 `findings`, 파싱 결과 0개, 전 항목 거부는 빈 리뷰 사유로 한 번의 기존 재시도 대상이 되고, 재시도 뒤에도 비면 해당 producer/source에서 제외돼야 한다. 하나 이상 유효하고 일부만 거부된 payload는 재시도하지 않고 유효 항목만 상위 normalization으로 넘기는 기존 계약을 보존해야 한다.
- **R5.2** 두 source가 모두 제외되면 `reviewer_failure`, 한 source만 유효하면 `single_reviewer`, 교차 검토나 종합이 실패하면 `pipeline_failure`를 유지해야 한다. terminal `report.md`는 `Termination reason`과 각 `Reviewer status`에 사유, attempts, stderr, 하위 exit code를 계속 표시해야 한다.
- **R5.3** Python 진입점은 `reviewer_failure`, `single_reviewer`, `pipeline_failure`에서 비영(非零) 종료 코드를 반환하고 JSON 결과와 terminal 산출물을 먼저 기록해야 한다. `no_changes`와 정상적인 정책 종료는 0을 유지해 호출자가 완료와 미완료를 구분할 수 있어야 한다.
- **R6.1** 실제 slash 회귀 검증은 수정된 스킬을 임시 Git 프로젝트의 `.claude/skills/dual-review/`에 복사하고, slash prompt를 stdin으로 주며 `--setting-sources project --permission-mode default --permission-prompts none --allowedTools "Read,Glob,Grep,Bash(python3:*)"`를 사용해 `HEAD` 자신을 base로 호출해야 한다. `$HOME` 설치본을 바꾸거나 reviewer 모델들을 실행하지 않은 채 Python 진입점이 새 run 디렉터리와 정확한 `no_changes` provenance/report를 만들 때 통과한다.
- **R6.2** 실증 실행은 landing-noindex의 계산된 merge-base SHA와 HEAD SHA를 대상으로 새 증가 실행 디렉터리를 만들고, 다섯 Claude producer와 Codex의 여섯 start가 첫 read보다 앞서며 source마다 최소 한 producer가 유효하고 양방향 교차 검토와 fresh-Claude 종합이 완료됐음을 raw status, events, synthesis, report로 입증해야 한다. run id는 계산된 `sha256(base_sha\0head_sha)[:16]` 접두사에서 다음 증가 번호를 사용해야 하며, 기존 `e7a6d2872362a4d6-000001`과 제품 HEAD/작업 트리는 보존해야 한다.
- **R6.3** source 전체 suite와 archive 배포본 suite를 Python 3.14.7의 `python3`로 실행해야 한다. `references/verification.md`의 자체 명령 식별자는 `DRV-1`부터 시작하는 독립 접두사로 재번호하고, 이 Spec의 판정 표만 `CMD-1`부터 `CMD-8`을 소유한다. 문서가 Spec 명령을 가리킬 때는 `Spec CMD-<n>`으로 명시해 두 체계를 혼용하지 않아야 한다. 신규 회귀/live 검증을 설명하되 위험한 자동 변형 명령 문자열을 스킬 내부에 복제하지 않아야 하며 type check, lint, build는 구성되지 않았다는 사실을 유지해야 한다.
- **R6.4** `dot_claude/skills/dual-review/tests/test_live_api.py`는 Python 표준 라이브러리 `unittest` opt-in probe여야 한다. `DUAL_REVIEW_LIVE_API=1`과 `DUAL_REVIEW_EVIDENCE_DIR=<dir>`를 CLI 환경 인터페이스로 받아 production builder를 통해 Codex reviewer, Codex/Claude critique, Claude synthesis를 호출하고 호출별 stdout/stderr/result를 지정 디렉터리에 보존해야 한다. 이 파일은 R4.1의 `required_paths`와 R4.2의 source/archive 동등성에 포함되는 배포 산출물이다.
- **R6.5** `dot_claude/skills/dual-review/tests/live_e2e.py`는 Python 표준 라이브러리만 사용하는 실행형 CLI helper여야 한다. `--repository`, `--logical-base`, `--expected-branch`, `--expected-files`, `--expected-diff-bytes`, `--preserve-run`, `--review-state-script`, `--evidence-dir`를 필수 인터페이스로 제공하고 precondition 검증, merge-base 계산, 실행, phase/run-id/무변경 사후 판정을 담당해야 한다. 이 파일은 R4.1의 `required_paths`와 R4.2의 source/archive 동등성에 포함되는 배포 산출물이다.

## Acceptance criteria

- **AC-1** 복사된 `SKILL.md`의 model 값이 정확히 `opus`이고 실제 `claude -p` slash 호출에 모델 선택 오류가 없으며, 호출 전에 비어 있던 임시 프로젝트의 `.claude/dual-review-state/` 바로 아래에 생성된 유일한 run 디렉터리의 `provenance.json`에서 `termination_reason`이 정확히 `no_changes`이고 `report.md`가 존재한다. 판정 수단: [실행] (CMD-6)
- **AC-2** contract test가 모든 `build_codex_command()` 변형에서 `--model`이 한 번이고 다음 값이 `gpt-5.6-sol`이며 read-only/schema/last-message flag가 보존되고 위치 prompt가 없음을 확인한다. subprocess 회귀 테스트는 reviewer와 critique Codex prompt가 모두 stdin으로 정확히 한 번 전달되고 EOF 뒤 종료함을 확인한다. 판정 수단: [실행] (CMD-2)
- **AC-3** operation 문서와 packaging contract가 Claude Code 2.1.268, 확인된 전체 flag 집합, `--allowedTools`의 가변 인자 성질, allowlist 뒤 위치 prompt 금지와 stdin prompt 규칙을 일치하게 고정한다. 판정 수단: [실행] (CMD-2)
- **AC-4** 결정론적 자식 프로세스가 stdin readable 여부를 3초 제한으로 검사하는 테스트에서 `start()`와 `read()` 사이를 3초 넘게 지연해도 원문 프롬프트를 받고, 여섯 start event가 첫 read보다 앞선다. 판정 수단: [실행] (CMD-1)
- **AC-5** 262,145바이트 이상의 프롬프트와 늦게 읽는 자식으로 검증할 때 `start()`가 자식의 read 대기시간보다 먼저 반환하고 최종 byte 수와 digest가 일치해 교착·절단이 없다. 판정 수단: [실행] (CMD-1)
- **AC-6** 성공, `Popen` 실패, 자식이 exit 0이지만 stdout에서 payload를 추출할 수 없는 parse 실패, output-last-message 파일이 유효한 JSON이 아닌 parse 실패, timeout과 kill 후 수거 각각에서 output/prompt 임시 경로가 남지 않고, 시작된 자식에는 프롬프트가 정확히 한 번만 공급되며 timeout 결과가 status `timeout`, exit code 124다. 판정 수단: [실행] (CMD-1)
- **AC-7** 재귀 contract test가 세 schema의 모든 object에서 `additionalProperties`가 false이고 `required == properties`, 명시적 type, 유효한 array item을 확인하고, reviewer의 `minItems: 1`과 기존 `minimum`, `maximum`, `minLength`, `enum`이 보존됨을 확인하며 한 파일 또는 루트만 검사하는 구현은 실패시킨다. 판정 수단: [실행] (CMD-2)
- **AC-8** critique `new_findings.items`가 요구된 finding 필드를 모두 가진 닫힌 object이고 속성 하나의 누락·추가·타입 불일치가 schema 검증에서 거부된다. 판정 수단: [실행] (CMD-2)
- **AC-9** opt-in live probe가 production command builder로 Codex reviewer, Codex/Claude critique, Claude synthesis를 실제 호출한다. 모든 Codex prompt는 위치 인자 없이 stdin으로 전달되며, 세 schema가 API schema 거부 없이 유효 structured output을 반환하고 호출별 원시 결과를 지정 evidence 디렉터리에 남긴다. 판정 수단: [실행] (CMD-7)
- **AC-10** source packaging test가 두 `.gitkeep`의 부재, `tests/test_live_api.py`와 `tests/live_e2e.py`를 포함한 모든 실제 필수 파일의 존재, 모든 상대 경로 component의 chezmoi 배포 가능성을 확인한다. 판정 수단: [실행] (CMD-2)
- **AC-11** 지정 worktree의 `chezmoi archive` 파일·디렉터리 상대 경로 집합이 두 live helper를 포함하고 runtime cache를 제외한 source 집합과 같고 `.gitkeep`, `__pycache__`, `.pyc`가 없으며, 푼 트리의 전체 suite가 통과한다. 판정 수단: [실행] (CMD-5)
- **AC-12** Codex의 exit 0 유효 envelope `findings: []`, Claude의 zero-block 출력, 검증 전용 normalization에서 유효 finding 0개를 각각 주입한 테스트가 `_round_zero`의 한 번 재시도 후 producer/source 제외와 `reviewer_failure` 또는 `single_reviewer`를 확인한다. 같은 테스트 묶음은 group label과 diff line range 없이 판정 가능함과, 유효 항목과 거부 항목이 섞인 payload는 재시도하지 않고 유효 source로 유지됨을 확인한다. 판정 수단: [실행] (CMD-3)
- **AC-13** 전체 reviewer 실패, 단일 reviewer, critique/synthesis 실패 fixture 각각의 report가 올바른 termination reason과 reviewer status의 사유·attempts·stderr·exit를 포함한다. 판정 수단: [실행] (CMD-3)
- **AC-14** `main()` 회귀 테스트가 terminal JSON/report 작성 뒤 `reviewer_failure`, `single_reviewer`, `pipeline_failure`에는 비영 종료, `no_changes`와 정상 정책 종료에는 0을 확인한다. 판정 수단: [실행] (CMD-3)
- **AC-15** `DUAL_REVIEW_LIVE_API`를 제거한 기본 discover가 `test_live_api.py`를 수집하되 live cases를 skip하고 모델 호출 없이, Python 3.14.7로 0개보다 많은 나머지 source 테스트를 100% 통과한다. 판정 수단: [실행] (CMD-4)
- **AC-16** landing-noindex 실증에서 다섯 Claude producer와 Codex의 여섯 start event가 첫 read보다 앞서고, Claude와 Codex 각 source에 최소 한 개의 유효 producer가 있어 두 source status가 valid이며, 양방향 cross critique가 각 1회 이상이고 fresh-Claude synthesis가 정확히 1회 실행되며 report가 생성된다. 개별 Claude producer의 정당한 무소견은 해당 source의 다른 producer가 유효하면 전체 E2E 실패 사유가 아니다. 판정 수단: [실행] (CMD-8)
- **AC-17** 실증 전후 제품 HEAD와 `git status --porcelain`이 같고 기존 실행 `e7a6d2872362a4d6-000001`이 그대로 보존된다. helper가 모델 호출 전에 계산한 merge-base SHA와 HEAD SHA로 `sha256(base_sha\0head_sha)[:16]` 접두사를 산출하고, 새 run은 그 접두사를 가진 기존 run 중 최댓값보다 큰 증가 번호의 별도 디렉터리와 quality evidence를 남긴다. 판정 수단: [실행] (CMD-8)
- **AC-18** verification/operation/packaging 계약의 문언과 테스트가 갱신된 model, CLI, stdin, schema, archive 명령을 일치하게 설명하고, verification 자체 명령은 `DRV-<n>`, 이 Spec 판정 명령은 `Spec CMD-<n>`으로만 참조해 동일한 `CMD-<n>`을 서로 다른 의미로 정의하지 않는다. type check·lint·build가 `not configured`임과 표준 라이브러리 import 제한도 확인한다. 판정 수단: [실행] (CMD-2)
- **AC-19** contract test가 `tests/test_live_api.py`의 존재, 표준 라이브러리 import만 사용함, 두 환경변수 인터페이스, 기본 skip guard, production builder 사용, 호출별 evidence 파일 계약을 정적으로 확인한다. 판정 수단: [실행] (CMD-2)
- **AC-20** contract test가 `tests/live_e2e.py`의 존재, 표준 라이브러리 import만 사용함, 여덟 필수 CLI option과 precondition·merge-base·동적 run-id·무변경 판정 인터페이스를 확인한다. 판정 수단: [실행] (CMD-2)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1 | [실행] CMD-6 |
| R1.2 | AC-2, AC-9 | [실행] CMD-2, CMD-7 |
| R1.3 | AC-3 | [실행] CMD-2 |
| R2.1 | AC-4, AC-5 | [실행] CMD-1 |
| R2.2 | AC-6 | [실행] CMD-1 |
| R2.3 | AC-6 | [실행] CMD-1 |
| R3.1 | AC-7, AC-9 | [실행] CMD-2, CMD-7 |
| R3.2 | AC-8, AC-9 | [실행] CMD-2, CMD-7 |
| R3.3 | AC-9, AC-15, AC-19 | [실행] CMD-7, CMD-4, CMD-2 |
| R4.1 | AC-10, AC-11 | [실행] CMD-2, CMD-5 |
| R4.2 | AC-10, AC-11 | [실행] CMD-2, CMD-5 |
| R4.3 | AC-11 | [실행] CMD-5 |
| R5.1 | AC-12 | [실행] CMD-3 |
| R5.2 | AC-13 | [실행] CMD-3 |
| R5.3 | AC-14 | [실행] CMD-3 |
| R6.1 | AC-1 | [실행] CMD-6 |
| R6.2 | AC-16, AC-17 | [실행] CMD-8 |
| R6.3 | AC-15, AC-18 | [실행] CMD-4, CMD-2 |
| R6.4 | AC-9, AC-15, AC-19 | [실행] CMD-7, CMD-4, CMD-2 |
| R6.5 | AC-16, AC-17, AC-20 | [실행] CMD-8, CMD-2 |

## Architecture

구성요소와 책임 경계는 다음과 같다.

- `SKILL.md`는 Claude slash routing과 Opus 선택만 담당한다. 실제 실행 상태 기계는 계속 `scripts/review_state.py`가 소유한다.
- command builder는 Claude/Codex CLI flag와 schema 전달을 소유한다. Codex 모델 고정은 이 경계에서 모든 Codex 경로에 적용하고, adapter는 Codex prompt를 위치 인자가 아니라 stdin으로만 공급한다.
- `_round_zero`는 “전부 시작 후 수거” 순서, 재시도, producer/source 집계를 소유한다. 전송 구현을 바꾸더라도 이 호출 순서는 바꾸지 않는다. `_round_zero`가 envelope 통과 payload를 받은 직후 호출하는 검증 전용 helper는 `_markdown_records`와 `normalize_reviewer_findings()`가 공유하는 parsing·필드 검사 primitive를 사용하지만 group label, changed-file line range, finding ID를 요구하지 않는다. 유효 항목이 0개일 때만 기존 한 번 재시도를 사용하며, 유효 항목이 하나 이상이면 나머지 항목이 거부돼도 재시도하지 않는다.
- `SubprocessAdapter`는 process, stdin 공급원, output-last-message 파일, target fingerprint, timeout/kill, 임시 자원 lifecycle을 소유한다. 권고 구현은 prompt를 mode 0600 임시 regular file에 완전히 기록하고 offset을 처음으로 돌린 뒤 그 열린 handle을 `Popen(stdin=...)`에 넘기는 방식이다. `Popen` 뒤 부모 handle과 이름을 안전하게 닫고 제거하되 자식이 상속한 descriptor는 EOF까지 읽을 수 있어야 한다. `read()`는 `communicate(timeout=...)`에 input을 주지 않는다.
- schema 파일은 API 수준 wire contract이고 `_envelope`, 검증 전용 normalization, ID materialization, critique/synthesis normalization은 애플리케이션 수준 의미 계약이다. schema 통과와 “유효 finding 최소 1개”를 별도 층에서 모두 검사한다. `run_dual_review()`는 두 source가 살아남은 뒤에만 `assign_anonymous_groups()`를 호출하고, 동일한 validation 결과에 group label을 결합해 `normalize_reviewer_findings()`가 stable finding ID를 만든다.
- `_new_run`, `write_terminal_run_artifacts`, `render_report`는 로컬 상태와 사람용 진단을 소유한다. `main()`은 결과를 출력한 뒤 termination reason을 프로세스 성공/미완료로 매핑한다.
- packaging test와 `chezmoi archive` 검증은 source-to-managed-tree 경계를 맡는다. `$HOME` 설치본은 이번 workflow의 입력도 출력도 아니다.

## Interfaces and data flow

1. slash 호출이 `--base`와 `--rounds`를 Python 진입점에 전달한다. no-change probe는 임시 프로젝트의 `HEAD`를 사용해 reviewer 호출 전에 종료한다.
2. 실 실행은 base/head/files/unified-0 diff를 snapshot으로 만들고 Claude용 prompt 하나와 Codex용 prompt 하나를 생성한다.
3. 각 reviewer `start(source, prompt)`는 prompt 임시 파일을 완성한 뒤 해당 파일 descriptor를 stdin으로 연결해 process handle을 반환한다. regular file은 pipe backpressure와 무관하므로 256KB 초과 입력도 다른 reviewer 시작을 막지 않는다.
4. 여섯 start 뒤 `read(handle)`이 순차적으로 timeout을 적용하고 output을 수거한다. prompt input 인자는 다시 전달하지 않는다. output-last-message 또는 stdout에서 payload를 추출하고 target fingerprint를 대조한다.
5. reviewer payload는 닫힌 schema와 envelope를 통과한 뒤 `_round_zero`의 group-independent validation에서 항목별로 검사된다. 전부 거부되거나 비어 있으면 raw/provenance에 구체적 reason을 남기고 한 번 재시도하며, 일부만 거부되고 하나 이상 유효하면 재시도하지 않는다. source마다 하나 이상의 producer가 이 관문을 통과해야 다음 단계로 간다.
6. 두 source가 유효해진 뒤 `run_dual_review()`가 anonymous group을 정하고, 앞 단계와 같은 validation primitive를 통해 통과한 항목에만 group label을 사용한 stable finding ID를 부여한다. 이때 diff line range는 finding location의 별도 하류 검증에 사용하며 빈 리뷰 재시도의 선행 조건이 아니다.
7. 두 source가 유효하면 반대 source finding만 양방향 critique에 전달하고, 익명화된 전체 view를 fresh Claude synthesis에 전달한다. 실제 사용 경로는 Codex reviewer schema, Codex/Claude critique schema, Claude synthesis schema다.
8. terminal reason, reviewer/phase status, normalized findings, critiques, synthesis, provenance, report를 새 `.claude/dual-review-state/<run-id>/`에 쓴 뒤 진입점이 완료 여부에 맞는 종료 코드를 반환한다.
9. 검증 evidence는 dotfiles workflow의 `.claude/quality-state/20260911T025854Z-105-dual-review-실행-결함-수정-모델-선택-producer-ced012ff/evidence/`에 저장한다. 제품 저장소에는 기존 규칙대로 새 run 디렉터리만 생기며 추적 파일은 바뀌지 않는다.

## Failure behavior

- prompt 임시 파일 생성·기록·seek 또는 `Popen`이 실패하면 열린 descriptor와 prompt/output 임시 파일을 정리하고 start failure를 기록한다. 시작하지 못한 process를 read하지 않는다.
- 자식이 조기 종료해도 regular-file stdin 공급은 별도 writer 예외를 만들지 않는다. nonzero exit, parse 실패, empty finding은 raw stdout/stderr와 명시적 reason을 보존한다.
- timeout 시 process를 kill하고 input 없는 두 번째 `communicate()`로 pipe를 drain한다. cleanup은 finally에서 수행하며 prompt를 재전송하지 않는다.
- 한 번의 기존 재시도 뒤 한 source만 남으면 교차 검토와 종합을 시작하지 않고 `single_reviewer`로 종료한다. 둘 다 없으면 `reviewer_failure`다. 하류 structured output 또는 coverage가 실패하면 `pipeline_failure`다.
- 결함이 없는 대상에서 reviewer가 정당하게 빈 결과를 내더라도 현재 wire contract에는 “검증된 무소견”과 “불완전 응답”을 구분하는 별도 attestation이 없다. 따라서 빈 리뷰를 `reviewer_failure`/`single_reviewer`와 비영 종료로 보수적으로 보고하는 false-negative를 수용한다. 이는 빈 응답을 성공으로 오인하는 false-positive보다 안전하다는 선택이며, 사용자는 증거를 보존한 새 run으로 재실행하거나 명시적 no-finding attestation을 다루는 후속 설계로 해결해야 한다.
- terminal 산출물 쓰기가 모델/phase 실패보다 먼저 완료돼야 한다. 호출자는 JSON의 termination reason과 비영 process exit 모두로 미완료를 감지할 수 있다.
- live schema probe 또는 E2E 모델 호출이 실패하면 증거를 지우거나 실행 번호를 초기화하지 않는다. 같은 run 디렉터리를 고쳐 쓰지 않고 원인을 판정한 뒤 별도 실행으로만 재검증한다.
- 실증 precondition인 branch, merge-base diff 3파일/18,505바이트, clean worktree, 기존 run이 하나라도 다르면 모델 호출 전에 중단하고 범위 변경으로 보고한다.

## Security and risk

- Claude/Codex는 리뷰 대상 diff를 외부 모델 서비스로 전송한다. 이는 기존 dual-review의 신뢰 가정 안에서만 수행하며 credential, 환경변수, 사용자 설정 파일을 prompt/evidence에 추가하지 않는다.
- dual-review가 생성하는 reviewer 호출의 `build_claude_command()` 계약은 계속 `plan` permission mode와 `Read,Glob,Grep` allowlist만 사용하고, Codex는 `--sandbox read-only`를 유지한다. CMD-6의 slash 검증 하니스만 임시 프로젝트 안의 Python 진입점을 실행하기 위해 `--permission-mode default --permission-prompts none --allowedTools "Read,Glob,Grep,Bash(python3:*)"`를 사용한다. 이는 `python3` 명령에만 범위를 한정한 명시적 allowlist이며 sandbox/permission bypass가 아니고 production builder 계약을 넓히지 않는다. 검증은 금지된 bypass flag나 GitHub write 명령을 추가하지 않는다.
- prompt 임시 파일에는 소스 diff가 있으므로 OS 임시 영역에 예측 불가능한 이름과 소유자 전용 권한으로 만들고 모든 종료 경로에서 제거한다.
- chezmoi 검증은 archive 생성과 임시 경로 추출만 수행한다. `$HOME` 설치본을 갱신하는 동작은 별도 통합 주체의 책임이며 이 Spec의 판정 명령에 없다.
- 제품 저장소에서는 모델이 읽기 전용이고 추적 파일을 변경하지 못하도록 전후 HEAD와 worktree status를 대조한다. 로컬 run/evidence 외 commit, push, PR, review, comment는 금지한다.
- dotfiles 저장소 관련 변경의 commit·push·PR 생성은 구현·검증·리뷰 뒤 승인된 별도 통합 행위다. 본 자동 검증은 이를 수행하지 않으며 제품 저장소 권한으로 확장하지 않는다.

## Test strategy

자동 회귀와 실제 모델/API 증거를 분리한다. 먼저 CMD-1부터 CMD-4까지 결정론적 테스트를 실행하고, CMD-4가 만든 Python cache가 배포에서 제외되는 상태로 CMD-5를 실행한다. CMD-4와 CMD-5는 `DUAL_REVIEW_LIVE_API`를 명시적으로 제거해 live probe를 수집하되 skip시킨다. 그 뒤 모델 호출을 명시적으로 수반하는 CMD-6, CMD-7, CMD-8을 순서대로 실행한다. 모든 Codex 모델 prompt는 production adapter가 stdin으로 전달하며 어떤 판정 명령도 Codex 위치 prompt에 의존하지 않는다. live 명령의 stdout/stderr와 structured 결과는 task evidence에 보존한다. 이 저장소에는 type check, lint, build가 구성돼 있지 않으므로 해당 범주를 통과로 꾸미지 않고 `references/verification.md` 근거로 `not configured`로 기록한다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_execution.ExecutionTests.test_subprocess_adapter_delivers_prompt_before_read_after_delay test_execution.ExecutionTests.test_subprocess_adapter_large_prompt_does_not_block_start test_execution.ExecutionTests.test_subprocess_adapter_unextractable_exit_zero_cleans_temp_files test_execution.ExecutionTests.test_subprocess_adapter_invalid_output_last_message_json_cleans_temp_files test_execution.ExecutionTests.test_subprocess_adapter_timeout_kills_without_resending_and_cleans_prompt` | Python 3.14.7에서 다섯 테스트가 모두 통과하고 지연 전달, 262,145바이트 이상 무교착·무절단, exit 0이지만 payload 추출 불가인 parse 실패, output-last-message의 invalid JSON parse 실패, timeout/kill 뒤 prompt/output 임시 파일 cleanup을 실제 자식 process로 확인한다. |
| CMD-2 | `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py'` | 빈 선택이 아닌 contract suite가 model, CLI 2.1.268와 전체 확인 flag/가변 `--allowedTools`/stdin 규칙, recursive schema와 보존 keyword, 두 live helper의 경로·표준 라이브러리·인터페이스, 실제 packaging paths, chezmoi name/cache guard, `DRV-*` 문서 체계를 모두 통과한다. |
| CMD-3 | `cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_execution.ExecutionTests.test_empty_findings_are_retried_then_excluded test_execution.ExecutionTests.test_all_rejected_findings_are_incomplete test_execution.ExecutionTests.test_invalid_finding_is_rejected_without_retrying_its_valid_source test_execution.ExecutionTests.test_validation_only_normalization_needs_no_group_or_line_ranges test_execution.ExecutionTests.test_failure_reports_keep_termination_and_reviewer_status test_execution.ExecutionTests.test_main_exit_code_distinguishes_incomplete_runs` | 빈 Codex/Claude/all-rejected fixture는 group/line-range 독립 판정과 재시도·제외를, valid+invalid 혼합 fixture는 무재시도와 유효 source 유지를 확인하고 세 실패 reason의 report와 entrypoint exit 매핑도 모두 통과한다. |
| CMD-4 | `env -u DUAL_REVIEW_LIVE_API PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -v` | Python 3.14.7로 0개보다 많은 전체 테스트를 실행하고 failure/error 없이 통과하며, `test_live_api.py`가 수집됐지만 live cases는 skip되고 모델 호출/evidence 생성은 없다. type check, lint, build는 실행 대상이 아니라 `not configured`로 기록한다. |
| CMD-5 | `archive_tmp="$(mktemp -d /tmp/dual-review-package.XXXXXX)" && chezmoi --source "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime" archive --output "$archive_tmp/dual-review.tar" --format tar ~/.claude/skills/dual-review && mkdir "$archive_tmp/root" && tar -xf "$archive_tmp/dual-review.tar" -C "$archive_tmp/root" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import pathlib,sys,tarfile; src=pathlib.Path(sys.argv[1]); prefix=".claude/skills/dual-review/"; keep=lambda p: "__pycache__" not in p.parts and p.suffix != ".pyc"; source={str(p.relative_to(src)) for p in src.rglob("*") if keep(p.relative_to(src))}; members={m.name.rstrip("/")[len(prefix):] for m in tarfile.open(sys.argv[2]).getmembers() if m.name.rstrip("/").startswith(prefix) and m.name.rstrip("/") != prefix.rstrip("/")}; assert source == members, (source-members, members-source); assert {"tests/test_live_api.py","tests/live_e2e.py"}.issubset(members); assert all(".gitkeep" not in pathlib.PurePosixPath(p).parts and "__pycache__" not in pathlib.PurePosixPath(p).parts and not p.endswith(".pyc") for p in members)' "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/dot_claude/skills/dual-review" "$archive_tmp/dual-review.tar" && cd "$archive_tmp/root/.claude/skills/dual-review" && env -u DUAL_REVIEW_LIVE_API PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | `$HOME`을 바꾸지 않고 실제 worktree의 archive와 두 live helper를 포함한 source 상대 경로가 같고 cache/`.gitkeep`가 없으며, 푼 배포본 전체 suite에서 live probe가 skip되고 나머지가 통과한다. |
| CMD-6 | `evidence_root="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T025854Z-105-dual-review-실행-결함-수정-모델-선택-producer-ced012ff/evidence" && slash_tmp="$(mktemp -d /tmp/dual-review-slash.XXXXXX)" && mkdir -p "$evidence_root" "$slash_tmp/project/.claude/skills" && cp -R "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/dot_claude/skills/dual-review" "$slash_tmp/project/.claude/skills/dual-review" && git -C "$slash_tmp/project" init -q && git -C "$slash_tmp/project" config user.email fixture@example.test && git -C "$slash_tmp/project" config user.name Fixture && touch "$slash_tmp/project/README.md" && git -C "$slash_tmp/project" add README.md && git -C "$slash_tmp/project" commit -qm initial && cd "$slash_tmp/project" && printf '%s' "/dual-review --base HEAD" | claude -p --no-session-persistence --setting-sources project --permission-mode default --permission-prompts none --allowedTools "Read,Glob,Grep,Bash(python3:*)" > "$evidence_root/slash-no-changes.txt" 2> "$evidence_root/slash-no-changes.stderr" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import json,pathlib,sys; skill=pathlib.Path(sys.argv[1]).read_text(); out=pathlib.Path(sys.argv[2]).read_text(); err=pathlib.Path(sys.argv[3]).read_text(); state_root=pathlib.Path(sys.argv[4]); runs=[p for p in state_root.iterdir() if p.is_dir()]; assert "model: opus" in skill; assert "unrecognized_model" not in out+err and "issue with the selected model" not in out+err; assert len(runs) == 1, runs; provenance=json.loads((runs[0] / "provenance.json").read_text()); assert provenance["termination_reason"] == "no_changes", provenance; assert (runs[0] / "report.md").is_file()' "$slash_tmp/project/.claude/skills/dual-review/SKILL.md" "$evidence_root/slash-no-changes.txt" "$evidence_root/slash-no-changes.stderr" "$slash_tmp/project/.claude/dual-review-state"` | bypass flag 0개와 Python-only Bash allowlist를 사용하고, 가변 `--allowedTools` 뒤에 위치 prompt를 두지 않은 stdin slash 호출이 project 스킬을 선택한다. 모델 오류 없이 Python 진입점이 실행돼 직속 run 디렉터리 하나를 만들고, 그 `provenance.json`의 `termination_reason`이 정확히 `no_changes`이며 `report.md`가 존재해야 한다. 이 명령은 Claude 모델 호출 1회를 수반한다. |
| CMD-7 | `evidence_root="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T025854Z-105-dual-review-실행-결함-수정-모델-선택-producer-ced012ff/evidence/schema-live" && mkdir -p "$evidence_root" && cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" DUAL_REVIEW_LIVE_API=1 DUAL_REVIEW_EVIDENCE_DIR="$evidence_root" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -p 'test_live_api.py' -v < /dev/null` | 표준 라이브러리 opt-in test가 production builder로 Codex reviewer, Codex/Claude critique, Claude synthesis를 실제 호출하고, 각 Codex prompt를 위치 인자 없이 adapter stdin으로 전달한다. 세 schema가 API schema 거부 없이 모두 통과하고 호출별 stdout/stderr/result를 evidence에 남겨야 한다. 이 명령은 Codex/Claude 모델 호출을 수반하며 P2에서 미실증이던 Claude 및 critique/synthesis 경로를 닫는다. |
| CMD-8 | `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 dot_claude/skills/dual-review/tests/live_e2e.py --repository "/Users/lee-kyu-hwan/code/zambaguni-front-landing-noindex" --logical-base origin/develop --expected-branch 1406-improvement/landing-noindex --expected-files 3 --expected-diff-bytes 18505 --preserve-run e7a6d2872362a4d6-000001 --review-state-script "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/dot_claude/skills/dual-review/scripts/review_state.py" --evidence-dir "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T025854Z-105-dual-review-실행-결함-수정-모델-선택-producer-ced012ff/evidence" < /dev/null` | 표준 라이브러리 helper가 branch/clean/triple-dot 3파일·18,505바이트/기존 run을 선검사하고 계산한 merge-base SHA와 HEAD SHA로 실제 리뷰와 기대 run-id 접두사를 만든다. 여섯 start-before-read, source별 최소 한 유효 producer, 양방향 critique, synthesis 1회, report, 해당 접두사의 기존 최댓값보다 큰 증가 run과 evidence가 생기며 기존 run과 제품 HEAD/clean 상태가 보존돼야 한다. 내부 Codex 호출은 모두 prompt를 stdin으로 받는다. 이 명령은 다수의 Claude/Codex 모델 호출을 수반한다. |

CMD-1은 “read 호출 시 prompt를 쓰는” 현행 구현을 지연 child에서 실패시키고, “start에서 pipe에 동기식 write”하는 잘못된 수정은 대용량 child에서 실패시킨다. CMD-2의 재귀 walker는 세 파일 전체와 모든 중첩 object를 방문해야 한다. CMD-3은 전부 거부와 일부 거부의 재시도 경계를 분리한다. CMD-5는 CMD-4 뒤 생긴 cache까지 archive에서 빠짐을 입증하며 archive 이외의 chezmoi 동작을 사용하지 않는다. CMD-6부터 CMD-8은 비용과 외부 API 의존성이 있으므로 deterministic gate가 모두 통과한 뒤 실행하고 증거 경로를 삭제하지 않는다.

## Decisions

### D1. prompt stdin은 임시 regular file을 권고한다

비교한 접근은 다음 두 가지다.

- 접근 A — prompt를 임시 파일에 완전히 쓴 뒤 `Popen(stdin=<opened file>)`로 넘긴다. 장점은 자식 시작 시점부터 데이터와 EOF가 준비되고 pipe backpressure가 없어 start loop 독립성을 보존하며 writer thread 예외가 없다는 점이다. 실패 모드는 파일 생성·write·seek·Popen 실패와 민감한 prompt 파일 잔존이다. mode 0600, start 예외 cleanup, `Popen` 뒤 부모 descriptor close/unlink, read finally의 방어적 cleanup으로 통제한다. timeout/kill 후 `communicate()`에는 input을 주지 않는다.
- 접근 B — `Popen(stdin=PIPE)` 뒤 daemon thread가 prompt를 쓰고 닫으며 `read()`가 join한다. start loop를 막지 않는 장점은 있지만 BrokenPipe와 writer 예외를 main thread로 전달할 공유 상태가 필요하고, timeout kill·두 번째 communicate·thread join 순서가 경쟁하거나 영구 block하지 않도록 별도 상태 기계가 필요하다. daemon thread가 cleanup 뒤에도 살아 있는 문제와 prompt 중복 전송 방지도 추가 검증 대상이다.

접근 A가 lifecycle과 timeout 상호작용이 더 단순하고 Claude CLI가 권고한 명시적 stdin redirection과 같으므로 선택한다.

### D2. Claude CLI 문서 pin을 2.1.268로 갱신한다

2.1.263을 유지하면 실제 stdin 실패 재현과 flag 확인에 사용한 실행 환경을 문서가 거짓으로 가리킨다. 2.1.268에서 `-p`, `--no-session-persistence`, `--setting-sources`, `--permission-mode`, `--permission-prompts`, `--allowedTools`, `--agent`, `--output-format`, `--json-schema`가 확인됐으므로 pin과 test를 함께 갱신한다. `--allowedTools`는 뒤따르는 위치 prompt를 도구 목록으로 흡수하는 가변 인자임이 P4에서 확인됐으므로 관련 호출은 prompt를 stdin으로 전달한다. 임의 최신 버전 호환을 주장하지 않는다.

### D3. runtime cache는 `.chezmoiignore`에서 제외한다

archive가 Git 추적 여부가 아니라 파일시스템을 읽으므로 unit test 뒤 생긴 무시된 bytecode도 배포된다. 기존 quality-goal 패턴과 대칭인 dual-review `__pycache__` 규칙을 추가하고 archive 상대 경로 집합과 cache 부재를 함께 검사한다. `.gitignore`는 바꾸지 않는다.

### D4. 빈 finding은 의미상 불완전으로 닫는다

단지 envelope key가 있다는 이유로 빈 reviewer 결과를 성공시키지 않는다. schema의 `minItems`, `_round_zero`의 group-independent validation, producer/source 집계로 방어층을 두고 기존 한 번 재시도와 exclusion 정책에 연결한다. 전부 거부된 결과만 재시도하고 일부 거부지만 하나 이상 유효한 결과는 재시도하지 않는다. 이 선택은 결함 없는 대상의 정당한 무소견도 미완료로 분류할 수 있지만, 명시적 no-finding 증명 계약이 없는 상태에서 빈 응답을 성공으로 오인하는 위험보다 보수적 false-negative를 택한 것이다. 이미 구현된 report 절과 termination reason 구분은 재설계하지 않고 회귀 고정한다.

### D5. 실증 base는 `origin/develop`의 merge-base SHA로 고정한다

현재 `origin/develop...HEAD`가 사용자가 지정한 3파일·18,505바이트 PR diff지만 `origin/develop` tip과 HEAD의 직접 양끝 diff는 develop 쪽 후속 변경까지 포함한다. 모델 호출 전 triple-dot precondition을 검사한 뒤 `git merge-base origin/develop HEAD` 결과를 Python `--base`에 전달한다. 이 선택은 검증 대상을 보존하며 production base 해석을 변경하지 않는다.

### D6. 실제 API 검증은 opt-in으로 분리한다

기본 suite는 `DUAL_REVIEW_LIVE_API`가 없으면 live module을 명시적으로 skip해 네트워크와 모델 비용 없이 결정론적으로 strict schema 구조를 검사한다. 별도 opt-in test는 실제 production builder를 통해 운영상 쓰이는 조합인 Codex reviewer, Codex/Claude critique, Claude synthesis를 호출한다. 두 층이 각각 구조 회귀와 공급자 acceptance를 담당한다.

### D7. strict 폐쇄만 추가하고 수용된 schema keyword는 보존한다

P1의 실제 400 원문은 루트 object에서 `additionalProperties`가 없음을 단일 거부 원인으로 지목했다. P2에서는 루트와 모든 중첩 object에 `additionalProperties: false`를 넣고 `required == properties`로 닫은 뒤에도 기존 `minimum`, `maximum`, `minLength`, `enum`과 신규 `minItems: 1`을 그대로 둔 schema가 Codex `--output-schema`에서 exit 0과 schema-conformant payload를 반환했다. 따라서 provider 호환을 이유로 이 키워드를 제거하지 않는다. 다만 이 결론은 Codex reviewer 경로에만 실증됐으며 Claude `--json-schema`와 critique/synthesis는 미실증이므로 CMD-7이 그 잔여 위험을 실제 운영 조합으로 검증한다.

### D8. 모델 CLI prompt는 stdin으로 고정한다

P5에서 유효 schema를 사용한 Codex 위치 인자 prompt 호출이 상속된 stdin을 기다리며 19분 30초 멈췄고, 같은 호출을 stdin prompt와 EOF로 바꾸자 exit 0으로 끝났다. 따라서 현행 `build_codex_command()`의 “명령 tuple에 위치 prompt를 넣지 않고 adapter stdin으로 전달” 계약을 reviewer와 critique 모두에 고정한다. Claude도 P4의 가변 `--allowedTools` 뒤에 위치 prompt를 두지 않으며 CMD-6은 slash prompt를 stdin으로 전달한다.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

- 신뢰하는 입력은 이 worktree의 versioned skill/schema/test와 검증 직전에 확인한 target Git refs다. GitHub 이슈 문언과 모델 출력은 검증 전까지 신뢰하지 않는다.
- 모델 API 경계로 대상 diff가 나간다. prompt에 diff와 필요한 metadata만 넣고 credential/user configuration은 포함하지 않는다.
- 모델 출력은 adversarial/untrusted data다. strict JSON schema, envelope, normalization, file/range validation, nonempty finding, synthesis coverage를 통과하기 전에는 report의 유효 결과로 승격하지 않는다.
- 임시 파일과 `.claude/quality-state`, 제품의 `.claude/dual-review-state`는 민감할 수 있는 코드·리뷰 내용을 담는다. 소유자 전용 임시 권한, repository ignore, 명시적 evidence 위치, prompt cleanup으로 노출을 제한한다.
- subprocess가 target을 변경할 위험은 전후 tree fingerprint와 read-only CLI policy로 탐지·차단한다. 제품 실증은 추가로 Git HEAD와 porcelain status를 대조한다.

### Authorization and tenant isolation

해당 없음 — dual-review는 단일 사용자의 로컬 CLI workflow로 tenant나 애플리케이션 권한 모델이 없다. production reviewer 권한 경계는 Codex read-only sandbox와 Claude `Read,Glob,Grep` allowlist로 유지한다. 별도 CMD-6 임시 fixture만 `Bash(python3:*)`를 추가해 스킬의 Python 진입점 실행을 허용하며 그 밖의 shell이나 bypass 권한은 주지 않는다. `$HOME` 설치본과 제품 저장소의 외부 게시 권한은 어떤 검증 명령에도 부여하지 않는다.

### Migration, compatibility, and rollback

- migration은 데이터 backfill이 아니라 chezmoi source 패키징 변경이다. 두 불필요한 `.gitkeep` 삭제, 실제 required path 고정, `.chezmoiignore` cache 규칙 추가가 source에서 archive target으로 함께 이동한다.
- `SubprocessAdapter`의 외부 `start`/`read` 인터페이스, 여섯 start-before-read 순서, raw/provenance/report 형식과 기존 termination reason 문자열은 호환 유지한다. handle 내부 모양은 구현 세부라 변경할 수 있다.
- rollback trigger는 deterministic suite 실패, live helper 누락, archive/source 경로 불일치, prompt 절단·중복·잔존, live schema 거부, target mutation, E2E phase 누락이다. 이 경우 `$HOME` 적용이나 통합을 진행하지 않고 관련 source 변경을 새 수정으로 되돌린 뒤 전체 gate를 다시 수행한다. 기존 실행 기록은 rollback 대상이 아니다.
- frontmatter를 무효한 식별자로 되돌리거나 pipe 지연 전송을 복원하는 부분 rollback은 허용하지 않는다. 안전한 대안이 필요하면 Spec/Plan 재검토로 돌아간다.

### Failure recovery and observability

- 관찰 신호는 process exit, timeout 124, stderr, retry count, producer별 `valid`, events start/read 순서, terminal reason, normalized/rejected finding, critique/synthesis status다.
- 각 run은 snapshot, prompt, raw result, events, normalized findings, critiques, synthesis, provenance, report를 별도 증가 디렉터리에 남긴다. live probe/slash stdout·stderr는 task evidence에 남긴다.
- `reviewer_failure`, `single_reviewer`, `pipeline_failure`는 report 문자열과 비영 process exit로 이중 노출한다. 빈 finding은 raw/provenance의 구체적 reason으로 진단 가능해야 한다.
- 재시도는 현행 reviewer invalid/timeout의 한 번으로 제한한다. 실패 증거를 삭제하거나 같은 run 번호를 재사용하지 않는다.
- 별도 alert, metric backend, distributed trace는 해당 없음 — 로컬 일회성 CLI이며 durable run artifacts와 exit code가 소비자 관측 인터페이스다.

### High-risk end-to-end verification

- deterministic gate와 archive gate가 먼저 전부 통과해야 live 모델 호출을 시작한다.
- CMD-6은 `$HOME`을 변경하지 않은 실제 slash/Opus 경로를 no-change fixture로 검증한다.
- CMD-7은 P2에서 남은 Claude 및 critique/synthesis를 포함해 세 schema의 실제 provider acceptance를 검증하고 호출별 원시 증거를 보존한다. Codex prompt는 stdin과 EOF로 전달한다.
- CMD-8은 지정 branch/계산된 merge-base와 HEAD/3파일/18,505바이트/clean/기존 run precondition을 확인한 뒤에만 실행한다. 여섯 start-before-read, source별 최소 한 유효 producer, 양방향 critique, fresh-Claude synthesis 1회, terminal report, 계산된 base/head 접두사의 증가 run 번호, 제품 무변경이 모두 필요하다.
- 어느 precondition, model call, schema, phase, artifact, exit 또는 무변경 검사가 실패해도 strict E2E는 실패다. 남은 한쪽 결과나 빈 findings를 성공으로 대체하지 않고 통합을 중단한다.

### No production mutation confirmation

자동 workflow에는 production 또는 제품 저장소 mutation이 없다. chezmoi는 archive만 생성하며 `$HOME`에 적용하지 않는다. zambaguni-front에서는 읽기 전용 리뷰와 ignored local run artifact만 허용하고 commit, push, PR 생성, review 게시, comment 게시를 하지 않는다. dotfiles 관련 commit·push·PR은 모든 gate 뒤 별도 승인된 통합 단계로만 수행되며 이 판정 명령에는 포함되지 않는다.

<!-- strict-only:end -->
