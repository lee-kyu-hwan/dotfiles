# Quality Goal Specification

- Task ID: 20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900
- Mode: strict
- Status: DRAFT
- Created: 2026-09-11
- Updated: 2026-09-11
- Source goal: #105 dual-review 실행 결함 수정: 모델 선택·producer stdin 즉시 전달·reviewer/critique/synthesis strict schema 계약·chezmoi 설치본 패키징

## Problem and context

chezmoi가 관리하는 `dot_claude/skills/dual-review/` version 1.2.0은 독립적인 Claude/Codex 리뷰, 교차 검토, Claude 종합을 로컬 산출물로 남기는 읽기 전용 스킬이다. 관리 대상은 `~/.claude/skills/dual-review/`이다. 기준 커밋은 `067923b554f159cf8c12e37f353f572951824b41`, 작업 브랜치는 `105-fix/dual-review-runtime`이며 발견 시점의 작업 트리는 깨끗했다.

GitHub 이슈 #105와 2026-09-11 직접 검증에서 다음 결함이 확인됐다.

- `SKILL.md`의 `model: claude`는 Claude Code가 인식하지 못한다. 같은 임시 probe에서 `model: claude`는 `unrecognized_model`로 본문 실행 전에 실패했고 `model: opus`는 `PROBE_OK`를 반환했다. 원시 근거는 `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/p0-frontmatter-model/model-claude.stderr.txt`, `model-claude.exit.txt`, `model-opus.stdout.txt`, `model-opus.exit.txt`다.
- `_round_zero`는 다섯 Claude producer와 Codex를 전부 시작한 뒤 순차적으로 읽어 독립성을 보장하지만, `SubprocessAdapter.start()`는 stdin pipe만 만들고 `read()`의 `communicate(prompt, ...)`까지 프롬프트 전송을 미룬다. Claude Code 2.1.268은 stdin을 3초 안에 받지 못하면 입력 없음으로 종료했다. 프롬프트는 `MAX_PROMPT_DIFF_BYTES = 262144`에 부가 문구가 더해질 수 있어 pipe에 동기식으로 쓰면 macOS의 통상 64KB pipe 용량을 넘어 시작 루프를 막을 수 있다. 구현 위치는 `dot_claude/skills/dual-review/scripts/review_state.py`이고, `--allowedTools` 뒤의 위치 prompt가 흡수되는 별도 CLI 입력 경계는 `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/p4-allowedtools-variadic/stderr.txt`와 `stdout.txt`에 보존됐다.
- `reviewer.schema.json`, `critique.schema.json`, `synthesis.schema.json`은 루트와 중첩 object에 `additionalProperties: false`가 없으며, `critique.schema.json`의 `new_findings.items`는 속성조차 없는 무제약 object다. 현행 reviewer schema를 사용한 Codex `--output-schema` probe는 HTTP 400과 함께 정확히 `Invalid schema for response_format 'codex_output_schema': In context=(), 'additionalProperties' is required to be supplied and to be false.`를 반환했다. 원문과 명령은 `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/probe-findings-2026-09-11.md`, 거부된 사본은 `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/current.json`에 있다. 루트·중첩 object를 모두 닫고 `required == properties`로 맞추면서 기존 keyword와 `minItems: 1`까지 둔 `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/strict.json`은 Codex에서 수용돼 같은 디렉터리의 `strict.result.json`을 반환했다. 이는 `minItems`가 공급자에게 수용 가능하다는 증거일 뿐 목적 적합성의 증거는 아니다. 결함 없는 대상의 허위 finding을 유도하므로 reviewer `findings`에는 `minItems`를 사용하지 않는다. Claude `--json-schema`와 critique/synthesis 경로는 아직 미실증이다.
- 소스에서 93개 테스트가 통과하지만 `chezmoi archive`로 재현한 배포 트리에서는 `schemas/.gitkeep` 부재로 1개가 실패한다. 원시 결과는 `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/p6-baseline-suites/source-suite.stderr.txt`, `source-suite.exit.txt`, `archive-suite.stderr.txt`, `archive-suite.exit.txt`, `archive-members.txt`, `python-version.txt`, `archive.stderr.txt`에 있다. `scripts/.gitkeep`도 배포되지 않는다. 두 파일은 비어 있지 않은 디렉터리를 지키지 않으므로 삭제 대상이다. archive는 파일시스템 기준이라 테스트가 만든 `__pycache__`와 `.pyc`도 현재 규칙으로는 포함한다.
- 실패 보고서에는 이미 사람이 읽을 수 있는 `Termination reason`과 `Reviewer status`가 렌더링되고, 파싱 가능한 블록이 없는 Claude producer는 `scripts/review_state.py:704-716`에서 payload가 `None`으로 남아 제외된다. 마크다운 0블록은 정당한 무소견과 파싱 실패를 구분할 수 없으므로, producer prompt와 parser 사이에 명시적 `NO_FINDINGS` 표지 계약이 필요하다. 유효한 structured 응답의 `findings: []`와 이 명시적 Claude 표지는 완료된 무소견이며, 표지 없는 0블록·schema/transport/model 실패와 구분해야 한다. 또한 `main()`이 `reviewer_failure` 등 미완료 종료에서도 0을 반환하는 점을 고쳐야 한다. 현행 판정·보고·진입점 근거는 `dot_claude/skills/dual-review/scripts/review_state.py`와 `dot_claude/skills/dual-review/tests/test_execution.py`다.
- P7은 자식 argv에 `-` 없이도 닫히는 파일 stdin으로 공급한 고유 토큰 `ZEBRA7713`이 8.03초, exit 0의 유효 결과로 돌아왔음을 입증한다. 근거는 `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/p7-codex-stdin-dash/FINDING.md`, `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/p7-codex-stdin-dash/without-dash/execution-record.json`, `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/p7-codex-stdin-dash/without-dash/result.json`이다. 따라서 P5의 19분 30초 대기는 `-` 부재가 아니라 위치 prompt와 함께 상속된 stdin이 EOF에 도달하지 않은 현상이다. 구현은 명료성을 위해 `-`를 argv에 추가하되, 실제 생명주기 계약은 adapter가 prompt 뒤 EOF를 반드시 전달하는 것이다.

실증 대상은 `/Users/lee-kyu-hwan/code/zambaguni-front-landing-noindex`, 브랜치 `1406-improvement/landing-noindex`, 논리적 base `origin/develop`이다. 현재 PR 범위인 `origin/develop...HEAD`는 3파일, unified-0 diff 18,505바이트이고 기존 실행 `e7a6d2872362a4d6-000001`을 보존해야 한다. 현재 `origin/develop` tip은 브랜치의 merge-base보다 앞서 있으므로 직접 양끝 diff는 PR 범위가 아닌 7파일을 포함한다. 실증에서는 merge-base SHA를 명시적으로 계산해 지정된 3파일 범위를 고정한다.

## Goals

- 임시 프로젝트의 실제 slash 호출이 Opus 모델을 선택하고 모델 오류 없이 스킬 본문과 `no_changes` 종료까지 도달한다.
- 다섯 Claude producer와 `gpt-5.6-sol` Codex를 모두 먼저 시작하면서 각 프로세스가 시작 즉시, 정확히 한 번 프롬프트를 받게 한다.
- 세 structured-output schema를 재귀적으로 닫힌 strict 계약으로 만들고 실제 Claude/Codex API 경로에서 검증한다.
- chezmoi가 실제 배포하는 트리를 `$HOME` 변경 없이 재현해 소스와 동일한 패키지 테스트 결과를 얻는다.
- 여섯 producer 각각의 유효 응답을 요구하면서 정당한 무소견과 리뷰어/하류 실패를 구분하고, 실패는 보고서와 프로세스 종료 코드 양쪽에서 미완료로 드러낸다.
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
- **R1.2** `build_codex_command()`는 모든 Codex reviewer/critique 호출에 `--model gpt-5.6-sol`과 명시적 stdin 표시자 `-`를 각각 정확히 한 번 포함하고 기존 `--sandbox read-only`, schema, JSON event, last-message 계약을 보존해야 한다. `-`는 모든 option과 그 값 뒤의 마지막 argv여야 하고 위치 prompt는 없어야 한다. 현재 `tests/test_contracts.py:137-140`은 `-`로 시작하는 모든 argv를 flag로 모으므로 허용 집합과 정확한 tuple assertion을 함께 갱신해야 한다. 표시자와 별개로 모든 Codex 호출은 adapter가 stdin으로 prompt를 정확히 한 번 공급한 뒤 자식이 EOF를 받도록 보장해야 한다.
- **R1.3** `references/operation.md`와 계약 테스트는 Claude Code 2.1.268에서 존재가 확인된 CLI 기능 목록(`-p`, `--no-session-persistence`, `--setting-sources`, `--permission-mode`, `--permission-prompts`, `--allowedTools`, `--agent`, `--output-format`, `--json-schema`)과 production `build_claude_command()`가 실제 emit하는 flag 집합을 별도 단락 또는 별도 표와 별도 assertion으로 분리해 고정해야 한다. operation 문서의 “Every Claude invocation emits the common flags” 단정은 production 호출만 서술하며, production 공통 집합은 `-p`, `--no-session-persistence`, `--permission-mode plan`, `--permission-prompts none`, `--allowedTools Read,Glob,Grep`이고 producer의 `--agent`, critique/synthesis의 `--output-format json`·`--json-schema`만 경로별로 추가된다. `--setting-sources project`, `--permission-mode default`, `--allowedTools "Read,Glob,Grep,Bash(python3:*)"`는 CMD-6 검증 하니스 전용 목록에만 고정하고 production emit 목록에 넣지 않아야 한다. `--allowedTools`는 뒤따르는 위치 prompt까지 흡수할 수 있는 가변 인자이므로 이를 쓰는 호출은 prompt를 stdin으로만 전달하고 allowlist 뒤에 위치 prompt를 두지 않아야 한다.
- **R2.1** `_round_zero`는 다섯 Claude producer와 Codex의 `Popen`을 모두 완료한 뒤 첫 결과를 읽는 순서를 보존하면서, 각 `start()`가 반환하기 전에 해당 프롬프트와 뒤따르는 EOF를 자식의 stdin 공급원에 연결해야 한다. 구현은 256KB 초과 프롬프트에서도 자식의 pipe 소비 여부에 의해 시작 루프가 블로킹되지 않아야 하며, regular file·닫히는 pipe 등 선택한 공급 방식과 무관하게 자식이 EOF에 도달해야 한다.
- **R2.2** `read()`는 이미 연결된 프롬프트를 다시 보내지 않고 stdout/stderr 수거와 parsing만 수행해야 한다. timeout이면 기존처럼 kill 후 잔여 출력을 수거하고 exit code 124와 `timeout` status를 유지해야 한다.
- **R2.3** prompt 임시 파일과 output-last-message 임시 파일은 성공, `Popen` 실패, parse 실패, timeout, kill 후 수거 경로에서 모두 정리돼야 한다. 구현과 테스트는 Python 표준 라이브러리만 사용해야 한다.
- **R3.1** 세 schema의 모든 `type: object` 노드는 `additionalProperties: false`, 비어 있지 않은 `properties`, `properties` 전체와 정확히 같은 `required`를 가져야 한다. 모든 property와 array item에는 모호하지 않은 `type` 제약이 있어야 하고 string enum도 `type: string`을 명시해야 한다. reviewer의 `findings`에는 `minItems`를 두지 않아 유효한 `findings: []` 무소견을 표현할 수 있어야 한다. Codex 실증이 수용한 기존 `minimum`, `maximum`, `minLength`, `enum` 제약은 제거하지 않으며 Claude와 critique/synthesis의 provider 수용 여부와 호환 분기는 live probe로 닫아야 한다.
- **R3.2** `critique.schema.json`의 `new_findings.items`는 normalization이 소비하는 severity, title, body, file, line 범위, confidence, recommendation을 명시한 닫힌 object여야 하며 각 속성이 required여야 한다.
- **R3.3** Codex의 `--output-schema <path>`와 Claude의 `--json-schema <schema text>` 전달 방식을 보존하고, production builder를 쓰는 opt-in live probe가 reviewer, critique, synthesis schema 전부와 실제 사용 CLI 양쪽을 합쳐 검증해야 한다. Claude가 canonical schema를 거부하면 하니스는 진단용 메모리 사본에서 비검증 annotation인 루트 `$schema`만 먼저 제거해 해당 호출을 한 번 재시도하고 양쪽 결과를 evidence에 남겨야 한다. 재시도가 수용되면 provider별 파일을 만들지 않고 세 shared schema의 `$schema`를 함께 제거한 새 구현으로 전체 deterministic/live gate를 처음부터 다시 수행한다. 그 재시도도 거부되면 provider별 schema 파일이나 추가 keyword 완화는 이 범위에서 허용하지 않고 `CLAUDE_SCHEMA_INCOMPATIBLE` 사유의 `NEEDS_REDESIGN`으로 중단해야 한다. `DUAL_REVIEW_LIVE_API`가 설정되지 않은 기본 discover에서는 live probe 전체를 `skip`하고 어떤 모델도 호출하지 않아야 한다.
- **R4.1** 무효한 `schemas/.gitkeep`와 `scripts/.gitkeep`를 삭제하고 packaging의 `required_paths`를 `scripts/review_state.py`, 세 schema, `tests/test_live_api.py`, `tests/live_e2e.py`, 실제 테스트·template·reference 등 배포 필수 파일로 교체해야 한다. 두 live helper도 관리 대상 스킬 패키지의 일부다. `scan_source_texts()`의 `.gitkeep` 특수 허용 분기는 실제 스킬 트리에서 죽은 코드가 되므로 제거하고, `test_no_mutation_contract_ignores_binary_fixture`는 `.md`·`.py`·`.json`만 읽고 `.pyc`를 제외한다는 일반 계약을 검증하도록 대체해야 한다.
- **R4.2** packaging 회귀 가드는 스킬 아래의 모든 파일·디렉터리 이름을 검사해 chezmoi가 소스 이름을 누락하거나 다르게 해석할 숨김/예약 형태를 거부해야 하며, 수정된 소스 트리와 archive로 푼 배포 트리에서 동일하게 통과해야 한다. `tests/test_live_api.py`와 `tests/live_e2e.py`는 source/archive 상대 경로 동등성에 포함되고 배포본에서도 import·CLI 도움말 검사가 가능해야 한다.
- **R4.3** `.chezmoiignore`는 `.claude/skills/dual-review/**/__pycache__`를 배포에서 제외해야 한다. 검증은 지정 worktree의 스킬 소스 안에 유효한 `.pyc` fixture와 `__pycache__` 디렉터리를 결정론적으로 만들고 둘의 존재를 먼저 단정한 상태에서 archive 멤버에 둘 다 0건임을 확인해야 한다. archive에는 삭제된 `.gitkeep`도 없어야 하며, 검증은 worktree를 `--source`로 사용한 archive를 임시 디렉터리에 풀 뿐 `$HOME`을 변경하지 않고 생성한 fixture와 임시 archive를 종료 시 정리해야 한다.
- **R5.1** 완료된 producer 응답은 (a) process exit 0과 adapter status `ok`, (b) 예상 wire 형식의 parse 성공, (c) 필수 envelope, (d) 비어 있지 않다면 normalization primitive를 통과하는 finding 하나 이상의 조건을 만족해야 한다. Codex의 유효 structured `findings: []`는 완료된 무소견이다. Claude producer는 완전한 finding 블록 하나 이상 또는 공백을 제외한 stdout 전체가 독립 한 줄 `NO_FINDINGS`인 경우에만 parse 성공이며, 후자는 `findings: []`인 완료 응답으로 변환한다. `NO_FINDINGS`와 finding 블록의 혼합, 표지 없는 0블록, model/schema/transport 실패, 전 항목 거부는 ingestion 실패로 한 번 재시도하고 다시 실패하면 그 producer를 제외한다. 하나 이상 유효하고 일부 항목만 거부된 payload는 재시도하지 않고 유효 항목만 상위 normalization으로 넘기는 기존 계약을 보존한다. prompt는 무소견일 때 정확한 표지를 출력하도록 명시해야 한다.
- **R5.2** production producer mode에서는 다섯 Claude producer와 Codex 여섯 개가 각각 R5.1의 유효 응답을 반환해야만 round zero가 완료된다. 하나라도 재시도 뒤 제외되면 후속 교차 검토·종합을 시작하지 않고 `reviewer_failure`로 종료한다. legacy 2-adapter 경로에서는 두 source가 모두 제외되면 `reviewer_failure`, 한 source만 유효하면 `single_reviewer`를 유지하며, 교차 검토나 종합 실패는 `pipeline_failure`다. terminal `report.md`는 `Termination reason`과 producer별/각 `Reviewer status`에 사유, attempts, stderr, 하위 exit code를 계속 표시해야 한다.
- **R5.3** Python 진입점은 `reviewer_failure`, `single_reviewer`, `pipeline_failure`에서 비영(非零) 종료 코드를 반환하고 JSON 결과와 terminal 산출물을 먼저 기록해야 한다. `no_changes`와 정상적인 정책 종료는 0을 유지해 호출자가 완료와 미완료를 구분할 수 있어야 한다.
- **R6.1** 실제 slash 회귀 검증은 수정된 스킬을 임시 Git 프로젝트의 `.claude/skills/dual-review/`에 복사하고, slash prompt를 stdin으로 주며 `--setting-sources project --permission-mode default --permission-prompts none --allowedTools "Read,Glob,Grep,Bash(python3:*)"`를 사용해 `HEAD` 자신을 base로 호출해야 한다. `$HOME` 설치본을 바꾸거나 reviewer 모델들을 실행하지 않은 채 Python 진입점이 새 run 디렉터리와 정확한 `no_changes` provenance/report를 만들 때 통과한다.
- **R6.2** 실증 실행은 landing-noindex의 계산된 merge-base SHA와 HEAD SHA를 대상으로 새 증가 실행 디렉터리를 만들고, 다섯 Claude producer와 Codex의 여섯 start가 첫 read보다 앞서며 여섯 producer 전부가 R5.1의 유효 응답을 반환하고 양방향 교차 검토와 fresh-Claude 종합이 완료됐음을 producer raw status, events, synthesis, report로 입증해야 한다. 각 응답은 findings가 있거나 정당한 무소견일 수 있지만 응답 실패를 무소견으로 대체할 수 없다. 이는 이슈 #105 완료 조건 2의 기준과 같다. run id는 모델 호출 전에 계산된 `sha256(base_sha\0head_sha)[:16]` 접두사 아래 기존 6자리 번호의 최댓값을 관측하고, 해당 집합이 비었으면 최댓값을 0으로 간주해 정확히 그 값 + 1을 다음 번호로 사용해야 한다. 기존 `e7a6d2872362a4d6-000001`과 제품 HEAD/작업 트리는 보존해야 한다.
- **R6.3** source 전체 suite와 archive 배포본 suite를 Python 3.14.7의 `python3`로 실행하고, 판정에 사용한 `python3 -VV` 출력과 `sys.version_info == (3, 14, 7)` 단정 결과를 task evidence에 보존해야 한다. `references/verification.md`의 자체 명령 식별자는 `DRV-1`부터 시작하는 독립 접두사로 재번호하고, 이 Spec의 판정 표만 `CMD-1`부터 `CMD-8`을 소유한다. 문서가 Spec 명령을 가리킬 때는 `Spec CMD-<n>`으로 명시해 두 체계를 혼용하지 않아야 한다. 신규 회귀/live 검증을 설명하되 위험한 자동 변형 명령 문자열을 스킬 내부에 복제하지 않아야 하며 type check, lint, build는 구성되지 않았다는 사실을 유지해야 한다.
- **R6.4** `dot_claude/skills/dual-review/tests/test_live_api.py`는 Python 표준 라이브러리 `unittest` opt-in probe여야 한다. `DUAL_REVIEW_LIVE_API=1`과 `DUAL_REVIEW_EVIDENCE_DIR=<dir>`를 CLI 환경 인터페이스로 받아 production builder를 통해 Codex reviewer, Codex/Claude critique, Claude synthesis를 호출하고 호출별 stdout/stderr/result를 지정 디렉터리에 보존해야 한다. 이 파일은 R4.1의 `required_paths`와 R4.2의 source/archive 동등성에 포함되는 배포 산출물이다.
- **R6.5** `dot_claude/skills/dual-review/tests/live_e2e.py`는 Python 표준 라이브러리만 사용하는 실행형 CLI helper여야 한다. `--repository`, `--logical-base`, `--expected-branch`, `--expected-files`, `--expected-diff-bytes`, `--preserve-run`, `--review-state-script`, `--evidence-dir`를 필수 인터페이스로 제공하고 precondition 검증, merge-base 계산, 모델 호출 전 계산된 접두사 아래 기존 run 번호 최댓값(없으면 0) 관측, 실행, phase/run-id/무변경 사후 판정을 담당해야 한다. 이 파일은 R4.1의 `required_paths`와 R4.2의 source/archive 동등성에 포함되는 배포 산출물이다.

## Acceptance criteria

- **AC-1** 복사된 `SKILL.md`의 model 값이 정확히 `opus`이고 실제 `claude -p` slash 호출에 모델 선택 오류가 없으며, 호출 전에 비어 있던 임시 프로젝트의 `.claude/dual-review-state/` 바로 아래에 생성된 유일한 run 디렉터리의 `provenance.json`에서 `termination_reason`이 정확히 `no_changes`이고 `report.md`가 존재한다. 판정 수단: [실행] (CMD-6)
- **AC-2** contract test가 모든 `build_codex_command()` 변형에서 `--model`이 한 번이고 다음 값이 `gpt-5.6-sol`이며 read-only/schema/last-message flag가 보존되고, stdin 표시자 `-`가 정확히 한 번 마지막 argv에 있으며 위치 prompt가 없음을 정확한 command tuple로 확인한다. `tests/test_contracts.py`의 `used_flags` 허용 집합에도 `-`가 들어가야 한다. subprocess 회귀 테스트는 reviewer와 critique Codex prompt가 모두 stdin으로 정확히 한 번 전달되고 자식이 EOF를 관측한 뒤 종료함을 확인한다. 판정 수단: [실행] (CMD-2)
- **AC-3** operation 문서와 packaging contract가 (a) Claude Code 2.1.268에서 존재가 확인된 전체 CLI 기능 목록과 (b) production builder의 공통·경로별 실제 emit flag 집합을 별도 단락/표와 별도 assertion으로 구분해 일치하게 고정한다. production “Every Claude invocation emits the common flags” 문장에는 `plan`과 `Read,Glob,Grep`만 공통 권한으로 남고 `--setting-sources project`, `default` permission mode, `Bash(python3:*)`는 CMD-6 검증 하니스 전용 단락과 assertion에만 있어야 한다. 두 목록은 `--allowedTools`의 가변 인자 성질, allowlist 뒤 위치 prompt 금지와 stdin prompt 규칙을 각각의 적용 경계와 함께 고정한다. 판정 수단: [실행] (CMD-2)
- **AC-4** 결정론적 자식 프로세스가 stdin readable 여부를 3초 제한으로 검사하는 테스트에서 `start()`와 `read()` 사이를 3초 넘게 지연해도 원문 프롬프트와 뒤따르는 EOF를 받고 종료하며, 여섯 start event가 첫 read보다 앞선다. 판정 수단: [실행] (CMD-1)
- **AC-5** 262,145바이트 이상의 프롬프트와 늦게 읽는 자식으로 검증할 때 `start()`가 자식의 read 대기시간보다 먼저 반환하고 최종 byte 수와 digest가 일치해 교착·절단이 없다. 판정 수단: [실행] (CMD-1)
- **AC-6** 성공, `Popen` 실패, 자식이 exit 0이지만 stdout에서 payload를 추출할 수 없는 parse 실패, output-last-message 파일이 유효한 JSON이 아닌 parse 실패, timeout과 kill 후 수거 각각에서 output/prompt 임시 경로가 남지 않고, 시작된 자식에는 프롬프트가 정확히 한 번만 공급되며 timeout 결과가 status `timeout`, exit code 124다. 판정 수단: [실행] (CMD-1)
- **AC-7** 재귀 contract test가 세 schema의 모든 object에서 `additionalProperties`가 false이고 `required == properties`, 명시적 type, 유효한 array item을 확인하고, reviewer `findings`에 `minItems`가 없으며 `findings: []`가 schema-valid임을 확인한다. 기존 `minimum`, `maximum`, `minLength`, `enum`은 보존하며 한 파일 또는 루트만 검사하는 구현은 실패시킨다. 판정 수단: [실행] (CMD-2)
- **AC-8** critique `new_findings.items`가 요구된 finding 필드를 모두 가진 닫힌 object이고 속성 하나의 누락·추가·타입 불일치가 schema 검증에서 거부된다. 판정 수단: [실행] (CMD-2)
- **AC-9** opt-in live probe가 production command builder로 Codex reviewer, Codex/Claude critique, Claude synthesis를 실제 호출한다. 모든 Codex 명령은 마지막 argv `-`를 가지며 prompt와 EOF를 stdin으로 전달한다. 세 canonical schema가 API schema 거부 없이 유효 structured output을 반환하고 호출별 원시 결과를 지정 evidence 디렉터리에 남겨야 통과한다. Claude 거부 시 루트 `$schema`만 제거한 진단용 메모리 사본의 단 한 번 재시도와 원본/재시도 증거를 남기되 그 실행 자체는 실패이며, 재시도 수용 시 shared schema 수정·전체 gate 재실행, 재거부 시 `CLAUDE_SCHEMA_INCOMPATIBLE`/`NEEDS_REDESIGN` 분기를 판정할 수 있어야 한다. 판정 수단: [실행] (CMD-7)
- **AC-10** source packaging test가 두 `.gitkeep`의 부재, `tests/test_live_api.py`와 `tests/live_e2e.py`를 포함한 모든 실제 필수 파일의 존재, 모든 상대 경로 component의 chezmoi 배포 가능성을 확인한다. `scan_source_texts()`에는 `.gitkeep` 특수 분기가 없고 대체 fixture test는 `.md`·`.py`·`.json`을 읽으면서 `.pyc`를 제외함을 확인한다. 판정 수단: [실행] (CMD-2)
- **AC-11** 지정 worktree의 스킬 소스에 `__pycache__` 디렉터리와 유효한 `.pyc` fixture가 실제로 존재함을 먼저 단정한 상태에서, `chezmoi archive` 파일·디렉터리 상대 경로 집합이 두 live helper를 포함하고 runtime cache를 제외한 source 집합과 같으며 archive 멤버의 `.gitkeep`, `__pycache__`, `.pyc`가 각각 0건이다. 푼 트리의 전체 suite가 통과하고 생성한 cache fixture와 임시 archive는 종료 시 정리된다. 판정 수단: [실행] (CMD-5)
- **AC-12** Codex의 exit 0·유효 envelope `findings: []`와 Claude stdout의 정확한 단독 `NO_FINDINGS`는 재시도 없이 완료된 무소견으로 유지된다. Claude의 표지 없는 zero-block, 표지와 finding 혼합, model/schema/transport 실패, 전 항목 거부는 각각 한 번 재시도 후 producer 제외와 production `reviewer_failure`를 만든다. 같은 테스트 묶음은 group label과 diff line range 없이 판정 가능함과, 유효 항목과 거부 항목이 섞인 payload는 재시도하지 않고 유효 producer로 유지됨을 확인한다. 판정 수단: [실행] (CMD-3)
- **AC-13** production producer 하나의 재시도 후 실패, legacy 전체 reviewer 실패, legacy 단일 reviewer, critique/synthesis 실패 fixture 각각의 report가 올바른 termination reason과 producer별/reviewer status의 사유·attempts·stderr·exit를 포함한다. 판정 수단: [실행] (CMD-3)
- **AC-14** `main()` 회귀 테스트가 terminal JSON/report 작성 뒤 `reviewer_failure`, `single_reviewer`, `pipeline_failure`에는 비영 종료, `no_changes`와 정상 정책 종료에는 0을 확인한다. 판정 수단: [실행] (CMD-3)
- **AC-15** `DUAL_REVIEW_LIVE_API`를 제거한 기본 discover가 `test_live_api.py`를 수집하되 live cases를 skip하고 모델 호출 없이, `sys.version_info[:3] == (3, 14, 7)`인 Python으로 0개보다 많은 나머지 source 테스트를 100% 통과한다. 같은 판정이 `python3 -VV` 출력을 task evidence의 `environment/python-version.txt`에 보존한다. 판정 수단: [실행] (CMD-4)
- **AC-16** landing-noindex 실증에서 다섯 Claude producer와 Codex의 여섯 start event가 첫 read보다 앞서고, 여섯 producer 각각이 유효한 응답을 반환하며, 양방향 cross critique가 각 1회 이상이고 fresh-Claude synthesis가 정확히 1회 실행되며 report가 생성된다. 각 producer의 정당한 무소견은 유효 응답이므로 허용하지만 하나의 producer라도 model/schema/transport/parser 실패이면 전체 E2E가 실패한다. 이 기준은 이슈 #105 완료 조건 2와 동일하다. 판정 수단: [실행] (CMD-8)
- **AC-17** 실증 전후 제품 HEAD와 `git status --porcelain`이 같고 기존 실행 `e7a6d2872362a4d6-000001`이 그대로 보존된다. helper가 모델 호출 전에 계산한 merge-base SHA와 HEAD SHA로 `sha256(base_sha\0head_sha)[:16]` 접두사를 산출하고, 그 시점에 관측한 해당 접두사의 기존 6자리 run 번호 최댓값(없으면 0)에 정확히 1을 더한 번호가 새 run 번호여야 하며 별도 디렉터리와 quality evidence를 남긴다. 따라서 기존 집합이 비었으면 새 run은 계산된 접두사의 `-000001`이다. 판정 수단: [실행] (CMD-8)
- **AC-18** verification/operation/packaging 계약의 문언과 테스트가 갱신된 model, CLI, stdin/EOF, schema, archive 명령과 Python 3.14.7 version evidence를 일치하게 설명하고, verification 자체 명령은 `DRV-<n>`, 이 Spec 판정 명령은 `Spec CMD-<n>`으로만 참조해 동일한 `CMD-<n>`을 서로 다른 의미로 정의하지 않는다. type check·lint·build가 `not configured`임과 표준 라이브러리 import 제한도 확인한다. 판정 수단: [실행] (CMD-2)
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
- command builder는 Claude/Codex CLI flag와 schema 전달을 소유한다. Codex 모델 고정과 마지막 argv `-`는 이 경계에서 모든 Codex 경로에 적용하고, adapter는 Codex prompt를 위치 인자가 아니라 stdin으로만 공급해 EOF까지 닫는다.
- `_round_zero`는 “전부 시작 후 수거” 순서, 재시도, producer/source 집계를 소유한다. 전송 구현을 바꾸더라도 이 호출 순서는 바꾸지 않는다. Claude producer parser는 완전한 finding 블록과 stdout 전체가 독립 한 줄 `NO_FINDINGS`인 경우만 서로 배타적으로 수용한다. `_round_zero`가 envelope 통과 payload를 받은 직후 호출하는 검증 전용 helper는 `_markdown_records`와 `normalize_reviewer_findings()`가 공유하는 parsing·필드 검사 primitive를 사용하지만 group label, changed-file line range, finding ID를 요구하지 않는다. structured 빈 배열과 명시적 표지는 유효하며, 비어 있지 않은 payload에서 하나 이상 유효하고 일부만 거부되면 재시도하지 않는다. production mode는 여섯 producer 각각의 유효 여부를 집계하며 하나라도 실패하면 source-level 성공으로 축약하지 않는다.
- `SubprocessAdapter`는 process, stdin 공급원, output-last-message 파일, target fingerprint, timeout/kill, 임시 자원 lifecycle을 소유한다. 권고 구현은 prompt를 mode 0600 임시 regular file에 완전히 기록하고 offset을 처음으로 돌린 뒤 그 열린 handle을 `Popen(stdin=...)`에 넘기는 방식이다. `Popen` 뒤 부모 handle과 이름을 안전하게 닫고 제거하되 자식이 상속한 descriptor는 EOF까지 읽을 수 있어야 한다. `read()`는 `communicate(timeout=...)`에 input을 주지 않는다.
- schema 파일은 API 수준 wire contract이고 `_envelope`, 명시적 Claude 무소견 parser, 검증 전용 normalization, ID materialization, critique/synthesis normalization은 애플리케이션 수준 의미 계약이다. schema 통과와 producer 응답 유효성을 별도 층에서 검사하되 finding 존재 자체는 요구하지 않는다. `run_dual_review()`는 여섯 producer가 모두 유효한 뒤에만 `assign_anonymous_groups()`를 호출하고, finding이 있는 응답의 validation 결과에 group label을 결합해 `normalize_reviewer_findings()`가 stable finding ID를 만든다.
- `_new_run`, `write_terminal_run_artifacts`, `render_report`는 로컬 상태와 사람용 진단을 소유한다. `main()`은 결과를 출력한 뒤 termination reason을 프로세스 성공/미완료로 매핑한다.
- packaging test와 `chezmoi archive` 검증은 source-to-managed-tree 경계를 맡는다. `$HOME` 설치본은 이번 workflow의 입력도 출력도 아니다.

## Interfaces and data flow

1. slash 호출이 `--base`와 `--rounds`를 Python 진입점에 전달한다. no-change probe는 임시 프로젝트의 `HEAD`를 사용해 reviewer 호출 전에 종료한다.
2. 실 실행은 base/head/files/unified-0 diff를 snapshot으로 만들고 Claude용 prompt 하나와 Codex용 prompt 하나를 생성한다.
3. 각 reviewer `start(source, prompt)`는 prompt 임시 파일을 완성한 뒤 해당 파일 descriptor를 stdin으로 연결해 process handle을 반환한다. regular file은 pipe backpressure와 무관하므로 256KB 초과 입력도 다른 reviewer 시작을 막지 않으며, 파일 끝이 자식에게 EOF가 된다. Codex command의 마지막 argv `-`는 이 stdin 입력을 명시하지만 EOF 생명주기를 대신하지 않는다.
4. 여섯 start 뒤 `read(handle)`이 순차적으로 timeout을 적용하고 output을 수거한다. prompt input 인자는 다시 전달하지 않는다. output-last-message 또는 stdout에서 payload를 추출하고 target fingerprint를 대조한다.
5. reviewer payload는 닫힌 schema와 envelope를 통과한 뒤 `_round_zero`의 group-independent validation에서 항목별로 검사된다. Codex의 구조화 빈 배열과 Claude의 단독 `NO_FINDINGS`는 완료된 무소견이다. Claude 표지 없는 0블록, 표지/블록 혼합, 전 항목 거부 또는 호출 실패는 raw/provenance에 구체적 reason을 남기고 한 번 재시도한다. 일부만 거부되고 하나 이상 유효하면 재시도하지 않는다. 여섯 producer 모두 이 관문을 통과해야 다음 단계로 간다.
6. 여섯 producer가 유효해진 뒤 `run_dual_review()`가 source별 finding을 결합하고 anonymous group을 정해, 앞 단계와 같은 validation primitive를 통과한 항목에만 group label을 사용한 stable finding ID를 부여한다. 무소견 producer는 유효하지만 materialize할 finding이 없다. diff line range는 finding location의 별도 하류 검증에 사용하며 무소견 유효성의 선행 조건이 아니다.
7. 두 source가 유효하면 반대 source finding만 양방향 critique에 전달하고, 익명화된 전체 view를 fresh Claude synthesis에 전달한다. 실제 사용 경로는 Codex reviewer schema, Codex/Claude critique schema, Claude synthesis schema다.
8. terminal reason, reviewer/phase status, normalized findings, critiques, synthesis, provenance, report를 새 `.claude/dual-review-state/<run-id>/`에 쓴 뒤 진입점이 완료 여부에 맞는 종료 코드를 반환한다.
9. 검증 evidence는 dotfiles workflow의 `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/`에 저장한다. 제품 저장소에는 기존 규칙대로 새 run 디렉터리만 생기며 추적 파일은 바뀌지 않는다.

## Failure behavior

- prompt 임시 파일 생성·기록·seek 또는 `Popen`이 실패하면 열린 descriptor와 prompt/output 임시 파일을 정리하고 start failure를 기록한다. 시작하지 못한 process를 read하지 않는다.
- 자식이 조기 종료해도 regular-file stdin 공급은 별도 writer 예외를 만들지 않는다. nonzero exit, parse 실패, 표지 없는 Claude 0블록은 raw stdout/stderr와 명시적 reason을 보존한다. 구조화 빈 배열과 명시적 `NO_FINDINGS`는 실패 사유가 아니다.
- timeout 시 process를 kill하고 input 없는 두 번째 `communicate()`로 pipe를 drain한다. cleanup은 finally에서 수행하며 prompt를 재전송하지 않는다.
- production producer mode에서 한 번의 재시도 뒤 한 producer라도 유효하지 않으면 교차 검토와 종합을 시작하지 않고 `reviewer_failure`로 종료한다. legacy 2-adapter mode에서 한 source만 남으면 `single_reviewer`, 둘 다 없으면 `reviewer_failure`다. 하류 structured output 또는 coverage가 실패하면 `pipeline_failure`다.
- 결함이 없는 대상의 정당한 무소견은 Codex 구조화 빈 배열 또는 Claude의 명시적 표지로 완료된다. 표지 없는 Claude 0블록은 의미를 추측하지 않고 ingestion 실패로 처리하므로 실패가 무소견으로 위장하지 못한다. `minItems`로 finding 생성을 강제하지 않아 허위 finding 유인도 만들지 않는다.
- terminal 산출물 쓰기가 모델/phase 실패보다 먼저 완료돼야 한다. 호출자는 JSON의 termination reason과 비영 process exit 모두로 미완료를 감지할 수 있다.
- live schema probe 또는 E2E 모델 호출이 실패하면 증거를 지우거나 실행 번호를 초기화하지 않는다. Claude schema 거부에는 루트 `$schema`만 제거한 메모리 사본으로 한 번 진단 재시도한다. 그 결과가 수용이면 shared schema만 수정해 전체 gate를 새로 실행하고, 재거부면 provider별 schema로 갈라지거나 strict keyword를 더 빼지 않고 `CLAUDE_SCHEMA_INCOMPATIBLE`/`NEEDS_REDESIGN`으로 중단한다. 같은 run 디렉터리를 고쳐 쓰지 않는다.
- 실증 precondition인 branch, merge-base diff 3파일/18,505바이트, clean worktree, 기존 run이 하나라도 다르면 모델 호출 전에 중단하고 범위 변경으로 보고한다.

## Security and risk

- Claude/Codex는 리뷰 대상 diff를 외부 모델 서비스로 전송한다. 이는 기존 dual-review의 신뢰 가정 안에서만 수행하며 credential, 환경변수, 사용자 설정 파일을 prompt/evidence에 추가하지 않는다.
- dual-review가 생성하는 reviewer 호출의 `build_claude_command()` 계약은 계속 `plan` permission mode와 `Read,Glob,Grep` allowlist만 사용하고, Codex는 `--sandbox read-only`를 유지한다. CMD-6의 slash 검증 하니스만 임시 프로젝트 안의 Python 진입점을 실행하기 위해 `--permission-mode default --permission-prompts none --allowedTools "Read,Glob,Grep,Bash(python3:*)"`를 사용한다. 이는 `python3` 명령에만 범위를 한정한 명시적 allowlist이며 sandbox/permission bypass가 아니고 production builder 계약을 넓히지 않는다. 검증은 금지된 bypass flag나 GitHub write 명령을 추가하지 않는다.
- prompt 임시 파일에는 소스 diff가 있으므로 OS 임시 영역에 예측 불가능한 이름과 소유자 전용 권한으로 만들고 모든 종료 경로에서 제거한다.
- chezmoi 검증은 archive 생성과 임시 경로 추출만 수행한다. `$HOME` 설치본을 갱신하는 동작은 별도 통합 주체의 책임이며 이 Spec의 판정 명령에 없다.
- 제품 저장소에서는 모델이 읽기 전용이고 추적 파일을 변경하지 못하도록 전후 HEAD와 worktree status를 대조한다. 로컬 run/evidence 외 commit, push, PR, review, comment는 금지한다.
- dotfiles 저장소 관련 변경의 commit·push·PR 생성은 구현·검증·리뷰 뒤 승인된 별도 통합 행위다. 본 자동 검증은 이를 수행하지 않으며 제품 저장소 권한으로 확장하지 않는다.
- 모델 출력은 신뢰하지 않지만 finding 수를 신뢰성 대용치로 쓰지 않는다. `minItems`를 제거해 결함 없는 대상에서 schema 충족용 허위 finding을 만들 유인을 없애고, 호출 성공·parse/envelope·필드 validation과 명시적 Claude 무소견 표지로 응답 완전성을 판정한다.

## Test strategy

자동 회귀와 실제 모델/API 증거를 분리한다. 먼저 CMD-1부터 CMD-4까지 결정론적 테스트를 실행한다. CMD-5 자체가 지정 source 안에 유효한 cache fixture를 만들고 존재를 단정한 뒤 archive 제외를 검사하며 trap에서 그 fixture와 임시 archive를 정리하므로 CMD-4의 bytecode 설정에 의존하지 않는다. CMD-4와 archive에서 푼 suite는 `DUAL_REVIEW_LIVE_API`를 명시적으로 제거해 live probe를 수집하되 skip시킨다. 그 뒤 모델 호출을 명시적으로 수반하는 CMD-6, CMD-7, CMD-8을 순서대로 실행한다. 모든 Codex model command는 마지막 argv `-`를 갖고 production adapter가 prompt 뒤 EOF를 stdin으로 전달한다. live 명령의 stdout/stderr와 structured 결과는 task evidence에 보존한다. 이 저장소에는 type check, lint, build가 구성돼 있지 않으므로 해당 범주를 통과로 꾸미지 않고 `references/verification.md` 근거로 `not configured`로 기록한다.

기존 테스트 영향은 다음처럼 고정한다.

- `test_producer_markdown_that_parses_to_zero_findings_is_not_a_valid_review`는 **유지**한다. 표지 없는 0블록이 ingestion 실패라는 계약을 계속 검증하고, 단독 `NO_FINDINGS`가 빈 payload로 수용되는 대칭 테스트를 추가한다.
- `test_zero_parse_producer_is_excluded_rather_than_reported_as_a_clean_review`는 **수정**한다. zero-parse producer가 clean review로 둔갑하지 않는 assertion을 보존하면서, production mode에서는 다섯 Claude 중 하나라도 최종 실패하면 source별 최소 하나로 완화하지 않고 전체 `reviewer_failure`가 됨을 확인한다.
- `test_invalid_finding_is_rejected_without_retrying_its_valid_source`는 **유지**한다. 한 payload 안의 일부 거부와 producer 응답 자체 실패를 구분하며, 유효 finding이 하나 이상이면 기존 무재시도 계약을 보존한다.
- `test_round_zero_starts_every_adapter_before_any_result_is_read`, `test_live_shape_starts_five_claude_producers_and_codex_before_reads`, `test_dispatches_constructed_prompts_before_any_read`와 `findings: []` fixture들은 **수정**한다. 빈 structured Codex 응답과 명시적 Claude 무소견을 유효하게 표현하고 여섯 producer 전부의 유효 응답 및 start-before-read를 함께 고정한다.
- `test_no_mutation_contract_ignores_binary_fixture`는 **대체**한다. `.gitkeep` 수용 assertion을 제거하고 일반 `.md`·`.py`·`.json` 수집과 `.pyc` 제외를 검증한다.

이전 Spec 대비 영향은 R1.2·R2.1의 stdin 표시자/EOF, R3.1·R3.3의 빈 배열/schema 호환 분기, R4.1·R4.3의 `.gitkeep`/cache, R5.1·R5.2·R6.2의 무소견/여섯 producer gate, R6.3의 Python version evidence다. 이에 따라 AC-2·AC-4·AC-7·AC-9·AC-10·AC-11·AC-12·AC-13·AC-15·AC-16·AC-18과 CMD-2·CMD-3·CMD-4·CMD-5·CMD-7·CMD-8을 수정한다. R3.2·R4.2·R6.4·R6.5의 정의는 유지하지만 공유 AC 변경의 파급 대상이며, 나머지 요구사항·AC·판정 명령의 의미는 유지한다.

CMD-6/AC-1 조합의 실행 가능성은 이미 보존된 `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/p3-slash-no-changes/command.txt`, `SKILL.md.used`, 2,225바이트 `stdout.txt`, 정상 성공이라 0바이트인 `stderr.txt`, `exit.txt`, `run-dirs.txt`, `provenance.json`, `report.md`, `snapshot.json`으로 확인한다. 이 전사는 project 스킬의 `model: opus`, stdin slash prompt, 한정된 `Bash(python3:*)` 하니스, `exit=0`, 직속 run 디렉터리 정확히 1개, `termination_reason: no_changes`, terminal report 생성을 함께 입증하며 CMD-6은 수정 뒤 같은 경계를 다시 판정한다. 스키마 400/수용의 선행 근거는 같은 task evidence의 `current.json`, `strict.json`, `strict.result.json`이고, 소스/archive 기준선은 `p6-baseline-suites/`의 원시 전사다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_execution.ExecutionTests.test_subprocess_adapter_delivers_prompt_before_read_after_delay test_execution.ExecutionTests.test_subprocess_adapter_large_prompt_does_not_block_start test_execution.ExecutionTests.test_subprocess_adapter_unextractable_exit_zero_cleans_temp_files test_execution.ExecutionTests.test_subprocess_adapter_invalid_output_last_message_json_cleans_temp_files test_execution.ExecutionTests.test_subprocess_adapter_timeout_kills_without_resending_and_cleans_prompt` | Python 3.14.7에서 다섯 테스트가 모두 통과하고 지연 전달, 262,145바이트 이상 무교착·무절단, exit 0이지만 payload 추출 불가인 parse 실패, output-last-message의 invalid JSON parse 실패, timeout/kill 뒤 prompt/output 임시 파일 cleanup을 실제 자식 process로 확인한다. |
| CMD-2 | `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py'` | 빈 선택이 아닌 contract suite가 model과 CLI 2.1.268의 확인 기능 목록을 production builder의 실제 emit 목록과 별도 단락·별도 assertion으로 구분한다. 모든 Codex command tuple에는 `-`가 정확히 한 번 마지막에 있고 위치 prompt가 없으며 `used_flags.issubset(allowed)`의 `allowed`에도 `-`가 포함된다. 또한 가변 `--allowedTools`/stdin·EOF 규칙, reviewer `findings`의 `minItems` 부재와 빈 배열 수용, recursive schema와 보존 keyword, `.gitkeep` 특수 분기 제거와 대체 fixture, 두 live helper, packaging/cache guard, `DRV-*` 문서 체계를 모두 통과한다. |
| CMD-3 | `cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_execution.ExecutionTests.test_explicit_no_findings_and_structured_empty_findings_are_valid test_execution.ExecutionTests.test_producer_markdown_that_parses_to_zero_findings_is_not_a_valid_review test_execution.ExecutionTests.test_zero_parse_producer_is_excluded_rather_than_reported_as_a_clean_review test_execution.ExecutionTests.test_all_six_producers_must_return_valid_reviews test_execution.ExecutionTests.test_all_rejected_findings_are_incomplete test_execution.ExecutionTests.test_invalid_finding_is_rejected_without_retrying_its_valid_source test_execution.ExecutionTests.test_validation_only_normalization_needs_no_group_or_line_ranges test_execution.ExecutionTests.test_failure_reports_keep_termination_and_reviewer_status test_execution.ExecutionTests.test_main_exit_code_distinguishes_incomplete_runs` | structured 빈 배열과 명시적 Claude 무소견은 무재시도 완료되고, 표지 없는 zero-block·표지/블록 혼합·all-rejected·호출 실패는 재시도 후 제외된다. production 여섯 producer 중 하나의 실패도 `reviewer_failure`이며 valid+invalid 혼합 payload의 기존 무재시도, failure report와 entrypoint exit 매핑도 통과한다. |
| CMD-4 | `evidence_root="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/environment" && mkdir -p "$evidence_root" && PATH="/opt/homebrew/bin:$PATH" python3 -VV 2>&1 | tee "$evidence_root/python-version.txt" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import sys; assert sys.version_info[:3] == (3, 14, 7), sys.version' && env -u DUAL_REVIEW_LIVE_API PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/dual-review/tests -v` | `python-version.txt`가 `python3 -VV` 출력을 보존하고 version tuple 단정이 통과한 Python 3.14.7로 0개보다 많은 전체 테스트를 실행해 failure/error 없이 통과한다. `test_live_api.py`는 수집되지만 live cases는 skip되고 모델 호출/evidence 생성은 없다. type check, lint, build는 `not configured`로 기록한다. |
| CMD-5 | `archive_tmp="$(mktemp -d /tmp/dual-review-package.XXXXXX)" && skill_src="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/dot_claude/skills/dual-review" && cache_dir="$skill_src/scripts/__pycache__" && cache_fixture="$cache_dir/spec-cache-fixture.pyc" && cleanup_cache_fixture() { PATH="/opt/homebrew/bin:$PATH" python3 -c 'import pathlib,shutil,sys; fixture=pathlib.Path(sys.argv[1]); cache=fixture.parent; fixture.unlink(missing_ok=True); cache.rmdir() if cache.exists() and not any(cache.iterdir()) else None; shutil.rmtree(sys.argv[2], ignore_errors=True)' "$cache_fixture" "$archive_tmp"; } && trap cleanup_cache_fixture EXIT && mkdir -p "$cache_dir" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)' "$skill_src/scripts/review_state.py" "$cache_fixture" && test -d "$cache_dir" && test -f "$cache_fixture" && chezmoi --source "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime" archive --output "$archive_tmp/dual-review.tar" --format tar ~/.claude/skills/dual-review && mkdir "$archive_tmp/root" && tar -xf "$archive_tmp/dual-review.tar" -C "$archive_tmp/root" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import pathlib,sys,tarfile; src=pathlib.Path(sys.argv[1]); fixture=pathlib.Path(sys.argv[2]); prefix=".claude/skills/dual-review/"; assert fixture.is_file() and fixture.parent.is_dir(); keep=lambda p: "__pycache__" not in p.parts and p.suffix != ".pyc"; source={str(p.relative_to(src)) for p in src.rglob("*") if keep(p.relative_to(src))}; members={m.name.rstrip("/")[len(prefix):] for m in tarfile.open(sys.argv[3]).getmembers() if m.name.rstrip("/").startswith(prefix) and m.name.rstrip("/") != prefix.rstrip("/")}; assert source == members, (source-members, members-source); assert {"tests/test_live_api.py","tests/live_e2e.py"}.issubset(members); assert not [p for p in members if ".gitkeep" in pathlib.PurePosixPath(p).parts or "__pycache__" in pathlib.PurePosixPath(p).parts or p.endswith(".pyc")], members' "$skill_src" "$cache_fixture" "$archive_tmp/dual-review.tar" && cd "$archive_tmp/root/.claude/skills/dual-review" && env -u DUAL_REVIEW_LIVE_API PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` | source의 `scripts/__pycache__`와 유효 `.pyc` fixture가 archive 전에 실재함을 단정한 뒤, `$HOME` 변경 없이 만든 archive에는 cache/`.gitkeep`가 0건이고 두 live helper와 cache 제외 source 집합이 정확히 일치한다. 푼 배포본 suite가 통과하며 shell `EXIT` trap이 fixture와 임시 archive를 성공·실패 모두에서 정리한다. |
| CMD-6 | `evidence_root="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence" && slash_tmp="$(mktemp -d /tmp/dual-review-slash.XXXXXX)" && mkdir -p "$evidence_root" "$slash_tmp/project/.claude/skills" && cp -R "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/dot_claude/skills/dual-review" "$slash_tmp/project/.claude/skills/dual-review" && git -C "$slash_tmp/project" init -q && git -C "$slash_tmp/project" config user.email fixture@example.test && git -C "$slash_tmp/project" config user.name Fixture && touch "$slash_tmp/project/README.md" && git -C "$slash_tmp/project" add README.md && git -C "$slash_tmp/project" commit -qm initial && cd "$slash_tmp/project" && printf '%s' "/dual-review --base HEAD" | claude -p --no-session-persistence --setting-sources project --permission-mode default --permission-prompts none --allowedTools "Read,Glob,Grep,Bash(python3:*)" > "$evidence_root/slash-no-changes.txt" 2> "$evidence_root/slash-no-changes.stderr" && PATH="/opt/homebrew/bin:$PATH" python3 -c 'import json,pathlib,sys; skill=pathlib.Path(sys.argv[1]).read_text(); out=pathlib.Path(sys.argv[2]).read_text(); err=pathlib.Path(sys.argv[3]).read_text(); state_root=pathlib.Path(sys.argv[4]); runs=[p for p in state_root.iterdir() if p.is_dir()]; assert "model: opus" in skill; assert "unrecognized_model" not in out+err and "issue with the selected model" not in out+err; assert len(runs) == 1, runs; provenance=json.loads((runs[0] / "provenance.json").read_text()); assert provenance["termination_reason"] == "no_changes", provenance; assert (runs[0] / "report.md").is_file()' "$slash_tmp/project/.claude/skills/dual-review/SKILL.md" "$evidence_root/slash-no-changes.txt" "$evidence_root/slash-no-changes.stderr" "$slash_tmp/project/.claude/dual-review-state"` | bypass flag 0개와 Python-only Bash allowlist를 사용하고, 가변 `--allowedTools` 뒤에 위치 prompt를 두지 않은 stdin slash 호출이 project 스킬을 선택한다. 모델 오류 없이 Python 진입점이 실행돼 직속 run 디렉터리 하나를 만들고, 그 `provenance.json`의 `termination_reason`이 정확히 `no_changes`이며 `report.md`가 존재해야 한다. 이 명령은 Claude 모델 호출 1회를 수반한다. |
| CMD-7 | `evidence_root="/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/schema-live" && mkdir -p "$evidence_root" && cd dot_claude/skills/dual-review/tests && PATH="/opt/homebrew/bin:$PATH" DUAL_REVIEW_LIVE_API=1 DUAL_REVIEW_EVIDENCE_DIR="$evidence_root" PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -p 'test_live_api.py' -v < /dev/null` | production builder로 Codex reviewer, Codex/Claude critique, Claude synthesis를 실제 호출하며 모든 Codex command는 마지막 argv `-`와 EOF에 도달하는 stdin을 사용한다. 세 canonical schema가 모두 수용되고 호출별 stdout/stderr/result가 evidence에 남아야 통과한다. Claude schema 거부 시 `$schema`만 제거한 메모리 사본으로 해당 호출을 한 번 진단 재시도하고 원본·재시도 증거 및 shared-schema 재실행 또는 `CLAUDE_SCHEMA_INCOMPATIBLE`/`NEEDS_REDESIGN` 분기 정보를 남기되 명령은 실패한다. |
| CMD-8 | `PATH="/opt/homebrew/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 python3 dot_claude/skills/dual-review/tests/live_e2e.py --repository "/Users/lee-kyu-hwan/code/zambaguni-front-landing-noindex" --logical-base origin/develop --expected-branch 1406-improvement/landing-noindex --expected-files 3 --expected-diff-bytes 18505 --preserve-run e7a6d2872362a4d6-000001 --review-state-script "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/dot_claude/skills/dual-review/scripts/review_state.py" --evidence-dir "/Users/lee-kyu-hwan/code/dotfiles__worktrees/105-fix-dual-review-runtime/.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence" < /dev/null` | branch/clean/triple-dot 3파일·18,505바이트/기존 run을 선검사하고 계산한 merge-base SHA와 HEAD SHA로 실제 리뷰를 실행한다. 여섯 start-before-read와 여섯 producer 각각의 유효 응답(각각 findings 또는 명시적 무소견), 양방향 critique, synthesis 1회, report, 선관측 최댓값+1 run/evidence가 생겨야 한다. 하나의 producer 실패도 전체를 실패시키며 기존 run과 제품 HEAD/clean 상태가 보존된다. 내부 Codex 명령은 마지막 argv `-`와 EOF stdin을 사용한다. |

CMD-1은 “read 호출 시 prompt를 쓰는” 현행 구현을 지연 child에서 실패시키고, “start에서 pipe에 동기식 write”하는 잘못된 수정은 대용량 child에서 실패시킨다. CMD-2의 재귀 walker는 세 파일 전체와 모든 중첩 object를 방문해야 한다. CMD-3은 무소견과 ingestion 실패, 여섯 producer 전원 조건, 전부/일부 거부의 재시도 경계를 분리한다. CMD-5는 자체 생성해 존재를 단정한 cache가 실제 archive에서 빠짐을 입증하므로 CMD-4의 `PYTHONDONTWRITEBYTECODE=1`과 독립적이다. CMD-6부터 CMD-8은 비용과 외부 API 의존성이 있으므로 deterministic gate가 모두 통과한 뒤 실행하고 증거 경로를 삭제하지 않는다.

## Decisions

### D1. prompt stdin은 임시 regular file을 권고한다

비교한 접근은 다음 두 가지다.

- 접근 A — prompt를 임시 파일에 완전히 쓴 뒤 `Popen(stdin=<opened file>)`로 넘긴다. 장점은 자식 시작 시점부터 데이터와 EOF가 준비되고 pipe backpressure가 없어 start loop 독립성을 보존하며 writer thread 예외가 없다는 점이다. 실패 모드는 파일 생성·write·seek·Popen 실패와 민감한 prompt 파일 잔존이다. mode 0600, start 예외 cleanup, `Popen` 뒤 부모 descriptor close/unlink, read finally의 방어적 cleanup으로 통제한다. timeout/kill 후 `communicate()`에는 input을 주지 않는다.
- 접근 B — `Popen(stdin=PIPE)` 뒤 daemon thread가 prompt를 쓰고 닫으며 `read()`가 join한다. start loop를 막지 않는 장점은 있지만 BrokenPipe와 writer 예외를 main thread로 전달할 공유 상태가 필요하고, timeout kill·두 번째 communicate·thread join 순서가 경쟁하거나 영구 block하지 않도록 별도 상태 기계가 필요하다. daemon thread가 cleanup 뒤에도 살아 있는 문제와 prompt 중복 전송 방지도 추가 검증 대상이다.

접근 A가 lifecycle과 timeout 상호작용이 더 단순하고 Claude CLI가 권고한 명시적 stdin redirection과 같으므로 선택한다.

### D2. Claude CLI 문서 pin을 2.1.268로 갱신한다

2.1.263을 유지하면 실제 stdin 실패 재현과 flag 확인에 사용한 실행 환경을 문서가 거짓으로 가리킨다. 2.1.268에서 `-p`, `--no-session-persistence`, `--setting-sources`, `--permission-mode`, `--permission-prompts`, `--allowedTools`, `--agent`, `--output-format`, `--json-schema` 기능의 존재가 확인됐으므로 pin과 기능 목록 test를 함께 갱신한다. 이 기능 목록은 production emit 계약이 아니다. operation의 “Every Claude invocation emits the common flags” 문장은 production builder의 `plan`·`Read,Glob,Grep` 공통 flag와 producer/structured-output별 추가 flag만 서술하고, CMD-6의 `--setting-sources project`·`default`·`Bash(python3:*)` 조합은 별도 검증 하니스 단락과 assertion에만 둔다. `--allowedTools`는 뒤따르는 위치 prompt를 도구 목록으로 흡수하는 가변 인자임이 `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/p4-allowedtools-variadic/stderr.txt`에서 확인됐으므로 관련 호출은 prompt를 stdin으로 전달한다. 임의 최신 버전 호환을 주장하지 않는다.

### D3. runtime cache는 `.chezmoiignore`에서 제외한다

archive가 Git 추적 여부가 아니라 파일시스템을 읽으므로 source에 생긴 무시된 bytecode도 배포 후보가 된다. 기존 quality-goal 패턴과 대칭인 dual-review `__pycache__` 규칙을 추가한다. 판정은 bytecode 억제 환경에 기대지 않고 `review_state.py`에서 유효 `.pyc` fixture를 source의 `scripts/__pycache__`에 만든 뒤 실재를 단정하고, archive 상대 경로 집합과 cache 0건을 함께 검사한다. fixture와 임시 archive는 정확한 경로만 trap으로 정리하며 `.gitignore`는 바꾸지 않는다.

### D4. 유효한 빈 finding은 완료된 무소견이다

Finding 수와 응답 유효성은 다른 축이다. reviewer schema의 `findings`에서 `minItems`를 제거해 `findings: []`를 허용한다. P2는 `minItems: 1`이 Codex에 수용됨을 보여 줬지만, 수용 가능하다는 사실은 결함 없는 대상에 허위 finding을 만들 수 있는 제약을 목적에 맞게 만들지 않는다. Codex structured empty와 Claude의 명시적 `NO_FINDINGS`는 완료된 무소견이고, 표지 없는 Claude 0블록과 호출·schema·parse 실패는 미완료다. 기존 한 번 재시도와 exclusion/termination reason은 실패에만 적용하며, 일부 거부지만 하나 이상 유효한 finding이 있는 payload의 무재시도 계약은 보존한다.

### D5. 실증 base는 `origin/develop`의 merge-base SHA로 고정한다

현재 `origin/develop...HEAD`가 사용자가 지정한 3파일·18,505바이트 PR diff지만 `origin/develop` tip과 HEAD의 직접 양끝 diff는 develop 쪽 후속 변경까지 포함한다. 모델 호출 전 triple-dot precondition을 검사한 뒤 `git merge-base origin/develop HEAD` 결과를 Python `--base`에 전달한다. 이 선택은 검증 대상을 보존하며 production base 해석을 변경하지 않는다.

### D6. 실제 API 검증은 opt-in으로 분리한다

기본 suite는 `DUAL_REVIEW_LIVE_API`가 없으면 live module을 명시적으로 skip해 네트워크와 모델 비용 없이 결정론적으로 strict schema 구조를 검사한다. 별도 opt-in test는 실제 production builder를 통해 운영상 쓰이는 조합인 Codex reviewer, Codex/Claude critique, Claude synthesis를 호출한다. 두 층이 각각 구조 회귀와 공급자 acceptance를 담당한다.

### D7. strict 폐쇄를 유지하고 Claude 거부는 `$schema`만 먼저 진단한다

P1의 실제 400은 루트 object에서 `additionalProperties`가 없음을 단일 거부 원인으로 지목했다. P2에서는 재귀적 `additionalProperties: false`, `required == properties`와 기존 `minimum`, `maximum`, `minLength`, `enum` 및 실험용 `minItems: 1`을 둔 schema가 Codex에서 수용됐다. 목적상 부적합한 reviewer `minItems`만 제거하고 strict 폐쇄와 나머지 validation keyword는 보존한다. Claude `--json-schema`가 canonical reviewer/critique/synthesis 중 하나를 거부하면 하니스는 비검증 annotation인 루트 `$schema`만 제거한 메모리 사본으로 그 호출을 한 번 진단 재시도한다. 수용되면 세 shared schema에서 `$schema`를 함께 제거해 provider별 분기를 만들지 않고 전체 gate를 다시 수행한다. 다시 거부되면 `additionalProperties`, `required`, `type`, 범위/enum 등을 더 제거하거나 provider별 schema 파일을 허용하지 않으며 `CLAUDE_SCHEMA_INCOMPATIBLE` 사유의 `NEEDS_REDESIGN`으로 중단한다.

### D8. 모델 CLI prompt는 stdin으로 고정한다

P7의 `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/p7-codex-stdin-dash/FINDING.md`, `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/p7-codex-stdin-dash/without-dash/execution-record.json`, `.claude/quality-state/20260911T052557Z-105-dual-review-실행-결함-수정-실행-2-실행-1이-revi-2d96c900/evidence/p7-codex-stdin-dash/without-dash/result.json`은 argv에 `-`가 없어도 파일 stdin의 EOF와 함께 prompt가 소비돼 exit 0, 8.03초, `ZEBRA7713` 반환이 가능함을 보였다. P5는 `-` 없는 위치 prompt 호출이 열린 상속 stdin을 기다린 경우라 원인은 표시자 부재가 아니라 EOF 부재다. 실제 correctness 계약은 prompt 뒤 EOF이며 adapter 회귀 테스트로 고정한다. 별도로 CLI 의도를 명료하게 하고 위치 prompt 부재를 tuple에서 단정하기 위해 `build_codex_command()`의 마지막 argv에 `-`를 정확히 한 번 추가하고, `tests/test_contracts.py:137-140`의 flag allowlist도 함께 고친다. Claude도 P4의 가변 `--allowedTools` 뒤에 위치 prompt를 두지 않는다.

### D9. Claude 마크다운 무소견은 단독 `NO_FINDINGS`로 표현한다

현행 `scripts/review_state.py:704-716`은 Claude producer stdout이 0블록이면 payload를 `None`으로 두며, 자유 문구만으로는 무소견과 parser drift를 구분할 수 없다. round-zero prompt가 무소견일 때 공백을 제외한 stdout 전체를 정확히 한 줄 `NO_FINDINGS`로 반환하도록 요구하고 adapter가 그 경우만 빈 findings envelope로 승격한다. finding 블록과 표지가 섞이거나 다른 자유 문구가 있으면 실패다. structured-output으로 producer 전체를 바꾸는 대안은 다섯 agent 출력 계약과 변경 폭을 넓히므로 이번 최소 수정에서는 채택하지 않는다.

### D10. `.gitkeep` 텍스트 특수 분기는 제거한다

두 `.gitkeep`가 삭제되면 `scan_source_texts()`의 `path.name == ".gitkeep"` 분기는 실제 스킬 패키지에서 죽은 코드다. 일반 fixture 계약으로 남길 실익보다 검사 대상 확장이 숨은 placeholder 텍스트를 안전 계약에 섞는 혼동이 크므로 분기를 제거한다. `test_no_mutation_contract_ignores_binary_fixture`는 `.md`·`.py`·`.json` 수집과 `.pyc` 제외를 검증하는 일반 fixture로 대체한다.

<!-- strict-only:start -->

This block is required only for strict work. Any inapplicable subsection must be removed for non-strict work; within strict work, mark it as not applicable with a reason before review.

### Threat and trust boundaries

- 신뢰하는 입력은 이 worktree의 versioned skill/schema/test와 검증 직전에 확인한 target Git refs다. GitHub 이슈 문언과 모델 출력은 검증 전까지 신뢰하지 않는다.
- 모델 API 경계로 대상 diff가 나간다. prompt에 diff와 필요한 metadata만 넣고 credential/user configuration은 포함하지 않는다.
- 모델 출력은 adversarial/untrusted data다. strict JSON schema, envelope, 명시적 Claude 무소견 또는 normalization, file/range validation, synthesis coverage를 통과하기 전에는 report의 유효 결과로 승격하지 않는다. Finding 존재 자체는 신뢰성 조건이 아니다.
- 임시 파일과 `.claude/quality-state`, 제품의 `.claude/dual-review-state`는 민감할 수 있는 코드·리뷰 내용을 담는다. 소유자 전용 임시 권한, repository ignore, 명시적 evidence 위치, prompt cleanup으로 노출을 제한한다.
- subprocess가 target을 변경할 위험은 전후 tree fingerprint와 read-only CLI policy로 탐지·차단한다. 제품 실증은 추가로 Git HEAD와 porcelain status를 대조한다.

### Authorization and tenant isolation

해당 없음 — dual-review는 단일 사용자의 로컬 CLI workflow로 tenant나 애플리케이션 권한 모델이 없다. production reviewer 권한 경계는 Codex read-only sandbox와 Claude `Read,Glob,Grep` allowlist로 유지한다. 별도 CMD-6 임시 fixture만 `Bash(python3:*)`를 추가해 스킬의 Python 진입점 실행을 허용하며 그 밖의 shell이나 bypass 권한은 주지 않는다. `$HOME` 설치본과 제품 저장소의 외부 게시 권한은 어떤 검증 명령에도 부여하지 않는다.

### Migration, compatibility, and rollback

- migration은 데이터 backfill이 아니라 chezmoi source 패키징 변경이다. 두 불필요한 `.gitkeep`와 그 전용 scanner 분기 삭제, 실제 required path 고정, `.chezmoiignore` cache 규칙 추가가 source에서 archive target으로 함께 이동한다.
- `SubprocessAdapter`의 외부 `start`/`read` 인터페이스, 여섯 start-before-read 순서, raw/provenance/report 형식과 기존 termination reason 문자열은 호환 유지한다. handle 내부 모양은 구현 세부라 변경할 수 있다.
- rollback trigger는 deterministic suite 실패, live helper 누락, archive/source 경로 불일치, prompt 절단·중복·EOF 부재·잔존, target mutation, E2E phase 누락이다. 이 경우 `$HOME` 적용이나 통합을 진행하지 않고 알려진 P1 400 또는 P5 대기를 재도입하지 않는 범위에서 실패한 새 source 변경만 fix-forward하거나 되돌린 뒤 전체 gate를 다시 수행한다. 기존 실행 기록은 rollback 대상이 아니다.
- Claude live schema 거부는 rollback trigger가 아니다. 루트 `$schema` 제거 진단 분기를 수행하고, 성공하면 shared schema의 해당 annotation만 제거한 새 수정으로 전체 gate를 반복하며, 실패하면 strict closure를 되돌리지 않고 `NEEDS_REDESIGN`으로 중단한다. frontmatter를 무효한 식별자로 되돌리거나 pipe 지연 전송·Codex 400 schema를 복원하는 부분 rollback은 금지한다.

### Failure recovery and observability

- 관찰 신호는 process exit, timeout 124, stderr, retry count, producer별 `valid`와 `explicit_no_findings`, events start/read 순서, terminal reason, normalized/rejected finding, critique/synthesis status다.
- 각 run은 snapshot, prompt, raw result, events, normalized findings, critiques, synthesis, provenance, report를 별도 증가 디렉터리에 남긴다. live probe/slash stdout·stderr는 task evidence에 남긴다.
- `reviewer_failure`, `single_reviewer`, `pipeline_failure`는 report 문자열과 비영 process exit로 이중 노출한다. 정당한 무소견은 producer raw/provenance의 명시 상태로, 표지 없는 0블록과 호출 실패는 구체적 실패 reason으로 구분돼야 한다.
- 재시도는 현행 reviewer invalid/timeout의 한 번으로 제한한다. 실패 증거를 삭제하거나 같은 run 번호를 재사용하지 않는다.
- 별도 alert, metric backend, distributed trace는 해당 없음 — 로컬 일회성 CLI이며 durable run artifacts와 exit code가 소비자 관측 인터페이스다.

### High-risk end-to-end verification

- deterministic gate와 archive gate가 먼저 전부 통과해야 live 모델 호출을 시작한다.
- CMD-6은 `$HOME`을 변경하지 않은 실제 slash/Opus 경로를 no-change fixture로 검증한다.
- CMD-7은 P2에서 남은 Claude 및 critique/synthesis를 포함해 세 canonical schema의 실제 provider acceptance를 검증하고 호출별 원시 증거를 보존한다. Codex command는 마지막 argv `-`와 EOF에 도달하는 stdin을 사용하며, Claude 거부 시 `$schema`-only 진단 및 중단 분기를 증거로 남긴다.
- CMD-8은 지정 branch/계산된 merge-base와 HEAD/3파일/18,505바이트/clean/기존 run precondition을 확인한 뒤에만 실행한다. 여섯 start-before-read, 여섯 producer 각각의 유효 응답, 양방향 critique, fresh-Claude synthesis 1회, terminal report, 계산된 base/head 접두사의 증가 run 번호, 제품 무변경이 모두 필요하다. 유효 응답의 findings는 비어 있어도 된다.
- 어느 precondition, producer 응답, model call, schema, phase, artifact, exit 또는 무변경 검사가 실패해도 strict E2E는 실패다. 정당한 무소견은 성공으로 인정하지만 남은 producer 결과로 실패한 producer를 대체하지 않고 통합을 중단한다.

### No production mutation confirmation

자동 workflow에는 production 또는 제품 저장소 mutation이 없다. chezmoi는 archive만 생성하며 `$HOME`에 적용하지 않는다. zambaguni-front에서는 읽기 전용 리뷰와 ignored local run artifact만 허용하고 commit, push, PR 생성, review 게시, comment 게시를 하지 않는다. dotfiles 관련 commit·push·PR은 모든 gate 뒤 별도 승인된 통합 단계로만 수행되며 이 판정 명령에는 포함되지 않는다.

<!-- strict-only:end -->
