# Quality Goal Specification

- Task ID: 42-dual-review-stage1
- Mode: standard
- Status: DRAFT
- Created: 2026-09-07
- Updated: 2026-09-07
- Source goal: #42 이중 리뷰 스킬의 1단계 — 독립 Claude·Codex 리뷰, 교차 비평, 종합, 로컬 보고서

## Problem and context

현재 PR 리뷰는 `pr-review-toolkit` Claude 에이전트와 Codex 리뷰를 독립 실행한 뒤 사람이 결과를 한쪽에 전달해 종합하고 게시한다. 이 단계는 그 중 게시 이전까지를 재현 가능한 로컬 워크플로로 만든다.

저장소는 `dot_claude/skills/`를 `~/.claude/skills/`에 배치하며, `quality-goal`은 `SKILL.md`, `references/`, `schemas/`, `scripts/`, `templates/`, `tests/`의 선례를 제공한다. `pr-review-toolkit`의 `code-simplifier`는 수정 에이전트이므로 finding 생산 집합에서 제외한다. Codex 플러그인 설치 경로는 4차 보고서의 `0120fb83da5d`에서 현재 `85cce0381e78`로 바뀌었으므로, 플러그인 슬래시 명령에 의존하지 않는다.

`#29`의 `codex-review-loop` 운용은 16라운드 중 가치가 초반에 집중되고 13차 이후 finding이 증가해 수렴하지 않은 실측을 남겼다. 따라서 전체 이중 리뷰 사이클을 반복하지 않는다. 또한 2026-09-06에 `codex exec` 모델 턴 무응답이 4회 관측돼, 마지막 단계인 종합은 그 경로에 두지 않는다. LLM judge 자기편향(Claude-v1 약 25% 자기 출력 선호, arXiv 2306.05685)을 줄이기 위해 종합 입력의 출처를 감춘다.

## Goals

- G1. 라운드 0에서 서로의 결과를 모르는 Claude·Codex 이중 리뷰를 수행한다.
- G2. 코드·소스 실측 근거를 요구하는 교차 비평으로 finding을 검증한다.
- G3. 출처를 감춘 Claude 종합자가 합의·불일치·신뢰도를 구조화해 로컬 보고서로 렌더링한다.
- G4. 짧고 결정적인 종료 규칙과 테스트 가능한 Python 규칙으로 비용과 회귀를 제한한다.

## Non-goals

- `gh pr review`·`gh pr comment`를 통한 PR 게시 계약, 중복 게시 방지, 게시물의 기준 커밋 SHA 표기, 재실행 갱신 정책(minimize/edit/new comment)은 2단계다.
- 게시 이력의 실행 간 지속, `resolved`/`not_re_reviewed` lifecycle, 스레드 resolve는 2단계다.
- SARIF export와 세 번째 이기종 judge 모델은 이번 범위 밖이다.
- 리뷰 대상 코드의 자동 수정, `code-simplifier` 호출, `chezmoi apply`, 플러그인 원본 수정은 하지 않는다.
- 대형 diff 분할, 장기 분석 저장소, GitHub Actions/서버 상주 실행은 이번 범위 밖이다.

## Requirements

### R1. 입력과 대상

- **R1.1** `/dual-review [--base <ref>] [--rounds 1|2]`를 해석한다. `--rounds 1`과 `--rounds=1`(2도 동일)을 모두 수용하고, 생략한 `--base`는 현재 HEAD의 첫 번째 부모로, 생략한 `--rounds`는 2로 정한다.
- **R1.2** base ref를 해석해 base SHA와 HEAD SHA를 고정하고 `git diff --name-only <base_sha> <head_sha>`로 변경 파일 목록을 만든다.
- **R1.3** 변경 파일 목록이 비면 외부 리뷰어를 호출하지 않고 `no_changes` 상태의 로컬 보고서를 만든다.
- **R1.4** 실행마다 `.claude/dual-review-state/<run_id>/` 아래에 입력 스냅샷, 원문·정규화 출력, 실제 디스패치 라운드 0 프롬프트, 호출 시작 순서, 종합 출력, provenance sidecar, 보고서를 분리해 만든다. `run_id`는 결정적 대상 식별자와 단조 실행 구분자를 합쳐 충돌하지 않게 하며 재실행은 새 디렉터리를 만든다. run root인 `.claude/dual-review-state/`에는 `*`만 담은 `.gitignore`를 만들어 산출물이 버전 관리에 노출되지 않게 한다.

### R2. 독립 이중 리뷰

- **R2.1** Claude 측은 `pr-review-toolkit:code-reviewer`, `pr-test-analyzer`, `comment-analyzer`, `silent-failure-hunter`, `type-design-analyzer` 다섯 읽기 전용 finding 생산자를 호출하고 `code-simplifier`는 호출하지 않는다. 자유 서술 Markdown에는 finding별 `severity`, `confidence`, `file`, `line`, `title`, `body`, `recommendation` 라벨을 요구하고 어댑터가 이를 schema 입력으로 추출한다; 단일 `line`은 `line_start=line_end`, 0–100 confidence는 100으로 나눈다. 자유 서술 생산자의 `원문 ID`는 라벨로 요구하지 않고, 어댑터가 생산자별 출력 문서에서 `title` 라벨부터 다음 `title` 라벨 직전 또는 문서 끝까지를 하나의 finding 블록으로 판별해 원문 등장 순서대로 검증 전에 1부터 센 순번과 생산자 에이전트명으로 결정적으로 부여한다; 거부된 블록도 순번을 소비하고 canonical 직렬화는 `producer=<생산자 에이전트명>;ordinal=<1부터의 10진 정수>`다. Claude 원문 severity는 앞뒤 공백을 제거하고 대소문자를 무시해 다음 완전 변환표를 적용한다: `Critical`→`critical`, `Important`→`high`, `High`→`high`, `Medium`→`medium`, `Low`→`low`; severity를 내지 않는 생산자는 `medium`을 기본값으로 쓰고, 표 밖의 명시 라벨은 해당 finding만 정규화 전에 거부한다.
- **R2.2** Codex 측은 스킬 소유의 reviewer JSON Schema를 `codex exec --sandbox read-only --output-schema`에 전달해 직접 호출한다.
- **R2.3** Codex 호출과 스킬 파일은 `--skip-git-repo-check`, `--dangerously-bypass-approvals-and-sandbox`, `--full-auto`, `--yolo`, `--add-dir`를 포함하지 않으며 템플릿보다 넓은 샌드박스를 쓰지 않는다.
- **R2.4** 라운드 0 독립성 계약은 Python이 구성한 두 프롬프트 문자열을 오케스트레이터가 덧붙이지 않고 그대로 디스패치하고, 양쪽 프롬프트에 상대 출력·경로·요약을 넣지 않으며, 두 호출이 모두 시작된 뒤에만 결과를 읽고 한쪽 결과를 다른 쪽에 중계하지 않는 것이다.

### R3. 정규 finding

- **R3.1** 모든 유효한 리뷰어 출력은 실제 `source`, 원문 ID, `severity`, title, body, repository-relative file, line_start, line_end, `finding_confidence`, recommendation을 가진 열 개 필수 필드의 하나의 정규 finding 레코드로 변환한다. 원문 ID는 R2.1의 `producer=<생산자 에이전트명>;ordinal=<1부터의 10진 정수>` canonical 직렬화로 파생한 값이다. R2.1 어댑터 변환 뒤 `severity` 허용값은 `critical`·`high`·`medium`·`low`이고 `finding_confidence`는 0 이상 1 이하의 수다.
- **R3.2** `finding_id`는 원문 ID와 별개 값이며, run ID 유도 익명 그룹 라벨·원문 ID·repository-relative file·10진 `line_start`·10진 `line_end`·title·body를 이 순서의 UTF-8 길이 접두어 필드(`길이:값`, 필드 사이는 NUL)로 이은 canonical 바이트 직렬화에 SHA-256을 적용한 `fid_` 뒤 64자리 소문자 16진 digest로 결정적으로 파생해 같은 정규화 입력은 같은 ID를 낸다; 실제 출처가 아니라 그룹 라벨이 ID 네임스페이스를 분리한다. 이 canonical 식별자는 원문 ID·실제 `source`·reviewer명·생산자 에이전트명의 평문 부분 문자열을 포함하지 않아 결과값에서 입력을 읽어낼 수 없고, `finding_id`와 실제 source·원문 ID의 대응은 provenance sidecar에만 둔다.
- **R3.3** R2.1의 블록 순번 부여와 severity 변환 뒤 필수 필드 누락, enum 밖 `severity` 또는 표 밖의 명시 원문 severity, 0–1 밖 `finding_confidence`, 경로 탈출, 잘못된 행 범위는 해당 finding을 정규화 전에 거부하고 원문을 유효 finding으로 추정하지 않는다; 거부된 블록의 이미 부여된 원문 ID 순번은 되돌리거나 재사용하지 않는다.
- **R3.4** 정규 레코드의 body는 라벨 순서·문단 구조·접두어를 공통 형식으로 정규화하여 그룹 신원을 형식만으로 추론할 수 없게 한다.

### R4. 교차 비평

- **R4.1** 각 교차 비평자는 자기 원문이 아니라 상대의 정규 finding과 대상 diff만 입력으로 받는다.
- **R4.2** 비평 항목은 `유지`, `반증됨`, `미검증` 중 하나의 판정과 코드·소스 실측 근거의 repository-relative 위치를 반드시 가진다.
- **R4.3** 근거 위치가 없거나 대상에서 검증할 수 없으면 반증 판정은 무효로 하고 `미검증`으로 기록한다.
- **R4.4** 비평에서 새 finding이 나오면 일반 finding 스키마로 정규화하고, 그 finding을 낳은 round와 reviewer를 보존한다.

### R5. 종료 규칙

- **R5.1** 한 교차 비평 라운드는 Claude→Codex와 Codex→Claude 두 호출의 묶음이며, 라운드별 신규 high 이상(`high`와 `critical`)은 두 호출에서 합산한다. 라운드 1은 양쪽 유효 리뷰가 있을 때 한 번 수행하고, 라운드 2는 `--rounds 2`이며 라운드 1의 신규 high 이상이 하나 이상일 때만 수행한다; 그 외에는 `requested_round_limit` 또는 `no_new_high` 후보가 생기며, 겹치면 R7.1의 우선순위가 정확히 하나를 선택한다.
- **R5.2** 라운드 0과 직후 교차 비평의 신규 high 이상 수가 연속 두 번 0일 때만 `two_quiet_rounds` 후보가 된다. 교차 비평 한 번의 0만으로 수렴을 주장하지 않으며, 다른 종료 후보와 겹치면 R7.1의 우선순위가 정확히 하나를 선택한다.
- **R5.3** 교차 비평은 최대 라운드 2에서 끝내며, 라운드 1 이상에서 독립 Claude·Codex 리뷰를 다시 실행하지 않는다. 라운드 2를 정상 완료하면 `round_cap` 후보가 되고, 다른 종료 후보와 겹치면 R7.1의 우선순위가 정확히 하나를 선택한다.
- **R5.4** 각 교차 비평 라운드 종료 직후 새 finding 중 `file`이 변경 파일 목록 밖인 비율을 계산한다. 새 finding이 0건이면 비율은 0이고 `abstraction_drift`가 아니며, 비율이 0.5를 초과하면 `abstraction_drift` 후보로 더 이상의 교차 비평을 중단하고 보고한다; 다른 종료 후보와 겹치면 R7.1의 우선순위가 정확히 하나를 선택한다.

### R6. 종합

- **R6.1** 종합자는 신선한 컨텍스트의 Claude 서브에이전트이며, 정규 finding·critique payload 외의 오케스트레이터·리뷰어 대화 컨텍스트를 상속하지 않는다.
- **R6.2** 종합자 입력 view는 모델명·reviewer명·실제 `source`·원문 ID를 제거하고 각 finding에 `group: A|B`를 치환하며 provenance sidecar는 넣지 않는다. `finding_id`는 R3.2의 불투명 canonical 식별자로만 남기고, 익명 입력 view의 모든 문자열 값에는 다섯 생산자 에이전트명과 원문 ID의 평문 부분 문자열이 없어야 한다. 후보 논점은 같은 repository-relative file에서 행 범위가 겹치는 finding을 출처 중립적으로 묶어 제공하고, 종합자는 제목·본문·양방향 critique 근거로 같은 결함인지 판단한다.
- **R6.3** Python은 run ID 유도 시드로 실제 출처의 A/B 배정을 결정하고 그 결과·시드·실행 구분자를 provenance sidecar에 기록한다; 재실행 구분자로 A/B를 교대하고 같은 run ID는 재현된다. R3.2의 불투명 canonical `finding_id`를 ASCII 바이트 오름차순으로 정규 정렬한 뒤 셔플한다.
- **R6.4** 종합자 출력은 후보 논점별로 합의·불일치·단일 출처 중 하나와 `decision_confidence`(종합 판정 신뢰도, 0–1), rationale, 양 그룹의 R3.2 불투명 `finding_id`를 구조화한다. 양 그룹이 같은 논점이고 critique가 유지/미검증이면 합의, 양 그룹 주장이 상충하거나 유효 반증이면 불일치, 한 그룹만 있으면 단일 출처다; 동일 결함 판단은 종합자에게 남기고 결정적 view 작성·그룹 검증은 Python에 둔다.
- **R6.5** 불일치 finding은 종합자가 폐기하거나 단일 결론으로 덮어쓰지 않고 별도 구조화 항목으로 보존한다.

### R7. 로컬 보고서

- **R7.1** 실행은 `<run_dir>/report.md`에 대상, 종료 사유, 리뷰어 상태, 정규 finding, 비평, 종합 결과를 담은 로컬 Markdown 보고서를 렌더링한다. 종료 사유는 정확히 하나이며 `no_changes`·`reviewer_failure`·`single_reviewer`·`abstraction_drift`·`two_quiet_rounds`·`requested_round_limit`·`no_new_high`·`round_cap` 중 하나다. 복수 후보가 성립하면 이 나열 순서가 높은 것부터 낮은 것까지의 전순서 우선순위이며, 첫 성립값만 선택한다.
- **R7.2** 보고서는 종합 후 provenance sidecar로 출처를 복원하고, `두 리뷰어가 갈린 지점` 절에 모든 불일치 finding과 양쪽 주장·근거를 표시한다.
- **R7.3** 스킬은 GitHub에 쓰지 않으며 스킬 디렉터리 전체에 `gh pr review`, `gh pr comment`, `gh api` 쓰기 호출이 없다.

### R8. 실패 처리

- **R8.1** 한쪽 리뷰어의 부재·호출 실패·스키마 위반은 상태, 보고서, 종료 상태에 구체적 원인으로 남기며 조용히 성공 처리하지 않는다.
- **R8.2** 리뷰어 출력 전체가 스키마를 통과하지 못한 경우에만 해당 리뷰어에 한 번 형식 재요청하고 재실패하면 그 출처를 제외한다; R3.3의 finding 단위 거부는 이 출처 단위 경로를 발동하지 않는다.
- **R8.3** 타임아웃은 정확히 한 번만 재시도하고 재시도 횟수와 stderr/종료 정보를 기록하며, 두 출처 모두 유효 출력이 없으면 종합하지 않고 `reviewer_failure`로 끝낸다.
- **R8.4** 한 출처만 유효한 부분 성공은 교차 비평과 양측 종합 분류를 수행하지 않고 `single_reviewer` 제한 보고서를 렌더링한다.

### R9. 패키징과 검증

- **R9.1** 스킬은 `dot_claude/skills/dual-review/`에 두며 chezmoi 배치 경로는 `~/.claude/skills/dual-review/`다.
- **R9.2** 스킬은 `SKILL.md`, `references/`, `schemas/`, `scripts/`, `templates/`, `tests/`를 가지며 frontmatter는 선례의 `name`, `version`, `description`, `argument-hint`, `disable-model-invocation`, `model`, `effort` 키를 쓴다.
- **R9.3** 라운드 0 프롬프트 구성·실제 디스패치 문자열 보존·호출/판독 순서 게이트, 정규화, ID 파생, 그룹 배정, 입력 view 작성·정렬·셔플, 종료 판정, 보고서 렌더링은 Python 표준 라이브러리 스크립트에 둔다. SKILL.md는 그 문자열을 변경하지 않고 호출하는 오케스트레이션만 맡는다.
- **R9.4** Python 단위 테스트와 `rg` 기반 내용 계약 검사를 제공하며, `rg` 검사는 대상 디렉터리 존재와 종료 코드 0(매치)·1(무매치)·그 밖의 오류를 구분한다. 타입 검사·린트·빌드는 저장소에 구성되지 않았음을 검증 문서에 명시한다.

## Acceptance criteria

- **AC-1** `--base`·`--rounds`의 유효/무효/기본값을 계약 테스트가 판정한다. [실행] (CMD-2 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_arguments`)
- **AC-2** `--rounds`는 1 또는 2만 수용함을 단위 테스트가 보인다. [실행] (CMD-2 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_arguments`)
- **AC-3** base·head SHA와 변경 파일 목록이 fixture diff에서 고정됨을 단위 테스트가 보인다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-4** 빈 변경 fixture가 리뷰어 호출 0회와 `no_changes` 보고서를 만든다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-5** run directory가 실제 프롬프트·시작 기록·sidecar·보고서와 `.claude/dual-review-state/` 루트의 `*`인 `.gitignore`를 모두 만든다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-6** 대상 식별자 부분은 동일 입력에서 결정적이고 실행 구분자를 더한 run ID는 재실행끼리 충돌하지 않는다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-7** Claude 호출 선택기는 다섯 finding 생산자만 선택 후보로 둔다. [실행] (CMD-3 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_reviewer_contract`)
- **AC-8** `code-simplifier`가 호출 목록에 없는 fixture 테스트가 있다. [실행] (CMD-3 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_reviewer_contract`)
- **AC-9** Codex 명령이 `--sandbox read-only`와 스킬 소유 schema 경로를 가진다. [실행] (CMD-3 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_reviewer_contract`)
- **AC-10** Codex 출력이 schema 검증을 통과하지 않으면 유효 리뷰로 등록되지 않는다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-11** 금지 Codex 옵션 다섯 개가 숨김·무시 파일까지 포함한 존재하는 스킬 디렉터리에 0건이다. [실행] (CMD-4 `sh -c 'test -d dot_claude/skills/dual-review || exit 2; rg -n --hidden --no-ignore --glob "*" -e "--skip-git-repo-check" -e "--dangerously-bypass-approvals-and-sandbox" -e "--full-auto" -e "--yolo" -e "--add-dir" dot_claude/skills/dual-review; code=$?; case $code in 1) exit 0;; 0) exit 1;; *) exit "$code";; esac'`)
- **AC-12** Codex 호출의 sandbox 값이 `read-only` 이외이면 계약 테스트가 실패한다. [실행] (CMD-3 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_reviewer_contract`)
- **AC-13** run directory에 보존된 실제 라운드 0 프롬프트가 상대 output·path·summary를 포함하지 않고 구성 문자열과 디스패치 문자열이 같은지를 판정한다; 손제작 fixture만으로는 통과하지 않는다. [실행] (CMD-7 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_independence`)
- **AC-14** run directory의 실제 시작 기록이 양쪽 시작 뒤 결과 판독임을 보이고, 결과 중계 또는 기록 없는 순서를 거부한다. [실행] (CMD-7 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_independence`)
- **AC-15** 정규 finding schema가 R3.1의 열 개 필드를 required로 선언한다. [실행] (CMD-8 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_schema_contract`)
- **AC-16** Claude 자유 서술 Markdown fixture가 `title` 라벨 경계로 블록을 판별해 검증 전 1부터 순번을 세고, 첫 블록이 표 밖 명시 severity로 거부되어도 `producer=pr-review-toolkit:code-reviewer;ordinal=1`을 소비한 뒤 다음 유효 블록에 정확히 `producer=pr-review-toolkit:code-reviewer;ordinal=2` 원문 ID를 부여하며, 라벨 어댑터와 0–100 환산을 거쳐 Codex fixture와 같은 정규 finding shape로 변환된다; 대소문자가 다른 `Critical`은 `critical`, `Important`는 `high`, severity 없는 생산자 출력은 `medium`이 되고 표 밖 명시 severity는 해당 finding만 거부된다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-17** 선행 거부 블록 뒤 같은 그룹 라벨과 출력 문서 순서로 파생된 정확한 원문 ID `producer=pr-review-toolkit:code-reviewer;ordinal=2`를 포함한 정규화 입력의 R3.2 불투명 `finding_id`는 재실행에서 같고 `fid_` 뒤 64자리 소문자 16진 형식이다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-18** 원문 ID만 `producer=pr-review-toolkit:code-reviewer;ordinal=1`와 `producer=pr-review-toolkit:code-reviewer;ordinal=2`로 다른 fixture 및 그룹 라벨·위치·제목·본문 중 하나가 다른 fixture는 각각 다른 `finding_id`를 낸다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-19** 누락 필수 값, R2.1 변환 뒤 enum 밖 severity 또는 표 밖 명시 severity, 잘못된 confidence, path traversal, 역행 범위를 가진 해당 finding이 거부된다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-20** 거부된 원문이 자동 보정되어 finding 목록에 들어가지 않는다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-21** Claude 비평 입력에는 Codex 정규 finding과 diff만 들어간다. [실행] (CMD-9 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_critique_contract`)
- **AC-22** Codex 비평 입력에는 Claude 정규 finding과 diff만 들어간다. [실행] (CMD-9 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_critique_contract`)
- **AC-23** critique schema가 세 판정값과 근거 위치를 required로 제한한다. [실행] (CMD-9 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_critique_contract`)
- **AC-24** 위치 없는 `반증됨` fixture는 `미검증`으로 전환된다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-25** 대상에 없는 근거 위치의 `반증됨` fixture도 `미검증`으로 전환된다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-26** 비평 신규 finding이 정규 스키마와 round·reviewer provenance를 갖는다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-27** 라운드 1은 유효한 두 리뷰가 있을 때 정확히 한 번 예약된다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-28** 라운드 1 신규 high 0 또는 `--rounds=1` fixture는 라운드 2를 예약하지 않고, 동시에 성립한 종료 후보에서는 R7.1 우선순위로 정확히 하나의 사유를 선택한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-29** `--rounds=2`와 라운드 1 신규 high 1 이상 fixture는 라운드 2를 한 번 예약하고, 이후 겹친 종료 후보에서는 R7.1 우선순위로 정확히 하나의 사유를 선택한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-30** 단일 교차 비평의 high 0은 `two_quiet_rounds`를 만들지 않고, 종료 후보가 겹치면 R7.1 우선순위로 정확히 하나의 사유를 선택한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-31** 라운드 0·1의 신규 high가 모두 0인 fixture가 `two_quiet_rounds` 후보를 만들고, 함께 성립한 `no_new_high` 또는 `requested_round_limit`을 포함한 종료 후보에서는 R7.1 우선순위로 정확히 하나의 사유를 선택한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-32** round가 2를 넘거나 round 1 이후 독립 리뷰를 재호출하려는 전이가 거부되고, 정상 라운드 2 완료에서 겹친 종료 후보는 R7.1 우선순위로 정확히 하나의 사유를 선택한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-33** 변경 파일 밖 신규 finding 비율이 0.5 초과이면 `abstraction_drift`와 중단이 발생하고, 함께 성립한 종료 후보에서는 R7.1 우선순위로 정확히 하나의 사유를 선택한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-34** 비율 0.5 이하 fixture는 `abstraction_drift`가 아니고, 남은 종료 후보가 겹치면 R7.1 우선순위로 정확히 하나의 사유를 선택한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-35** 종합자 실행 계약이 fresh Claude subagent를 지정한다. [실행] (CMD-10 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_synthesis_contract`)
- **AC-36** 종합자 입력 manifest가 정규 finding·critique 밖 대화 컨텍스트 상속을 허용하지 않는다. [실행] (CMD-10 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_synthesis_contract`)
- **AC-37** 익명 입력 view가 모델명·reviewer명·실제 source·원문 ID·provenance를 제거하고 각 finding에 유일한 `group: A|B`와 R3.2 불투명 `finding_id`만 남기며, 모든 문자열 값에서 `pr-review-toolkit:code-reviewer`·`pr-test-analyzer`·`comment-analyzer`·`silent-failure-hunter`·`type-design-analyzer` 다섯 생산자 에이전트명과 원문 ID의 평문 부분 문자열이 각각 0건이다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-38** `finding_id→실제 source/원문 ID`와 실제 source·원문 ID 매핑을 담은 provenance sidecar가 종합자 입력 파일에 포함되지 않는다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-39** 같은 run ID·finding 집합이 R3.2 불투명 `finding_id`의 ASCII 바이트 오름차순 정규 정렬 뒤 같은 셔플 순서를 낸다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-40** 다른 run ID는 시드를 다르게 기록하고 셔플 재현 정보를 남긴다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-41** synthesis schema가 합의·불일치·단일 출처 enum, `decision_confidence` 0–1, rationale, 양 그룹의 R3.2 불투명 `finding_id`를 required로 한다. [실행] (CMD-10 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_synthesis_contract`)
- **AC-42** 양 그룹이 같은 논점을 보고한 fixture가 양 그룹의 R3.2 불투명 `finding_id`를 가진 하나의 합의 항목으로 묶이고, 상충 fixture는 불일치, 한 그룹 fixture는 단일 출처로 정확히 하나를 낸다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-43** 불일치 fixture가 synthesis output에 남고 report 입력으로 전달된다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-44** 종합자가 `codex exec` 템플릿을 쓰지 않는 계약 테스트가 있다. [실행] (CMD-10 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_synthesis_contract`)
- **AC-45** 정상 실행 fixture가 run directory에 `report.md`를 만든다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-46** 보고서가 대상·종료 사유·리뷰어 상태·finding·critique·synthesis 절을 모두 가지고, 종료 사유가 R7.1의 여덟 값 enum 중 정확히 하나인지 판정한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-47** 보고서는 sidecar로 reviewer 출처를 복원한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-48** `두 리뷰어가 갈린 지점` 절이 모든 불일치 ID와 양측 주장·근거를 출력한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-49** 스킬 디렉터리에 GitHub 쓰기 문자열 세 개가 숨김·무시 파일까지 0건이다. [실행] (CMD-5 `sh -c 'test -d dot_claude/skills/dual-review || exit 2; rg -n --hidden --no-ignore --glob "*" -e "gh pr review" -e "gh pr comment" -e "gh api" dot_claude/skills/dual-review; code=$?; case $code in 1) exit 0;; 0) exit 1;; *) exit "$code";; esac'`)
- **AC-50** 자동 코드 수정 명령 또는 `code-simplifier` 호출이 없다. [실행] (CMD-6 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_no_mutation_contract`)
- **AC-51** 한쪽 호출 실패 fixture가 실패 출처·원인·종료 상태를 보고서에 출력한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-52** 실패가 유효 finding 0건인 성공으로 변환되지 않는다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-53** 리뷰어 출력 전체의 schema 위반은 정확히 한 번 재요청하고 두 번째 위반 후 출처가 제외된다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-54** 제외된 출처의 원문과 검증 오류가 run directory에 보존된다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-55** timeout fixture가 정확히 한 번 재시도하고 stderr/exit 정보를 상태와 보고서에 남긴다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-56** 양쪽이 실패한 fixture는 종합 호출 0회와 비성공 종료를 낸다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-57** 한쪽만 유효한 fixture는 cross critique와 양측 분류를 호출하지 않는다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-58** 한쪽만 유효한 fixture는 `single_reviewer` 제한과 실패 원인을 보고한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-59** skill source path와 chezmoi target path가 배치 계약 문서에 모두 있다. [실행] (CMD-11 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_packaging_contract`)
- **AC-60** 순수 배치 경로 함수가 `dot_claude/skills/dual-review/SKILL.md`를 `~/.claude/skills/dual-review/SKILL.md`로 유도함을 확인하며 `chezmoi diff` 실행은 요구하지 않는다. [실행] (CMD-11 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_packaging_contract`)
- **AC-61** 여섯 구성 요소가 존재하고 SKILL.md frontmatter가 일곱 필수 키를 모두 갖는다. [실행] (CMD-11 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_packaging_contract`)
- **AC-62** schemas·scripts·tests의 책임 경로가 파일 맵 계약에 있다. [실행] (CMD-11 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_packaging_contract`)
- **AC-63** SKILL.md가 Python 규칙 구현을 포함하지 않고 오케스트레이션 경로만 참조한다. [실행] (CMD-12 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_deterministic_boundaries`)
- **AC-64** 라운드 0 프롬프트 구성 함수·실제 디스패치 문자열 보존·양쪽 호출 뒤 판독을 강제하는 순서 게이트와 정규화·ID·셔플·종료·렌더링의 결정적 함수가 Python scripts에 있다. [실행] (CMD-12 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_deterministic_boundaries`)
- **AC-65** 결정적 규칙이 외부 Python 패키지를 import하지 않는다. [실행] (CMD-6 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_no_mutation_contract`)
- **AC-66** 전체 Python 단위 테스트가 종료 코드 0으로 끝난다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-67** grep 계약 검사가 존재하는 스킬 디렉터리에서 GitHub 쓰기와 금지 Codex 옵션의 부재를 모두 확인하고 `rg` 오류는 실패한다. [실행] (CMD-4, CMD-5 `rg` 종료 코드 0=실패, 1=통과, 그 밖=실패)
- **AC-68** 검증 문서가 타입 검사·린트·빌드의 `not configured` 상태를 선언한다. [실행] (CMD-11 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_packaging_contract`)
- **AC-69** report renderer가 입력 순서를 바꿔도 결정적 셔플 결과에 따라 같은 Markdown을 낸다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-70** 전체 계약 테스트는 확인된 외부 쓰기 0회와 코드 수정 0회를 보장한다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)
- **AC-71** A와 B의 원문 fixture가 같은 공통 body 구조로 정규화되어 라벨 순서·문단 구조·접두어만으로 그룹을 구별할 수 없다. [실행] (CMD-1 `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'`)

## Requirements traceability

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-2 | CMD-2 |
| R1.2 | AC-3 | CMD-1 |
| R1.3 | AC-4 | CMD-1 |
| R1.4 | AC-5, AC-6 | CMD-1 |
| R2.1 | AC-7, AC-8 | CMD-3 |
| R2.2 | AC-9, AC-10 | CMD-3, CMD-1 |
| R2.3 | AC-11, AC-12 | CMD-4, CMD-3 |
| R2.4 | AC-13, AC-14 | CMD-7 |
| R3.1 | AC-15, AC-16 | CMD-1, CMD-8 |
| R3.2 | AC-17, AC-18 | CMD-1 |
| R3.3 | AC-19, AC-20 | CMD-1 |
| R3.4 | AC-71 | CMD-1 |
| R4.1 | AC-21, AC-22 | CMD-9 |
| R4.2 | AC-23 | CMD-9 |
| R4.3 | AC-24, AC-25 | CMD-1 |
| R4.4 | AC-26 | CMD-1 |
| R5.1 | AC-27, AC-28, AC-29 | CMD-1 |
| R5.2 | AC-30, AC-31 | CMD-1 |
| R5.3 | AC-32 | CMD-1 |
| R5.4 | AC-33, AC-34 | CMD-1 |
| R6.1 | AC-35, AC-36 | CMD-10 |
| R6.2 | AC-37, AC-38 | CMD-1 |
| R6.3 | AC-39, AC-40 | CMD-1 |
| R6.4 | AC-41, AC-42 | CMD-1, CMD-10 |
| R6.5 | AC-43, AC-44 | CMD-1, CMD-10 |
| R7.1 | AC-45, AC-46 | CMD-1 |
| R7.2 | AC-47, AC-48 | CMD-1 |
| R7.3 | AC-49, AC-50 | CMD-5, CMD-6 |
| R8.1 | AC-51, AC-52 | CMD-1 |
| R8.2 | AC-53, AC-54 | CMD-1 |
| R8.3 | AC-55, AC-56 | CMD-1 |
| R8.4 | AC-57, AC-58 | CMD-1 |
| R9.1 | AC-59, AC-60 | CMD-11 |
| R9.2 | AC-61, AC-62 | CMD-11 |
| R9.3 | AC-63, AC-64, AC-65 | CMD-6, CMD-12 |
| R9.4 | AC-66, AC-67, AC-68, AC-69, AC-70 | CMD-1, CMD-4, CMD-5, CMD-11 |

## Architecture

`SKILL.md`는 인자 해석, 호출 순서, 실패 표면화를 조정한다. `scripts/review_state.py`는 라운드 0 프롬프트 구성·실제 디스패치 문자열 보존·호출/판독 순서 게이트를 포함한 모든 결정적 변환과 상태 전이를, `schemas/`는 reviewer·critique·synthesis 출력 검증을, `templates/report.md`는 로컬 Markdown 형식을, `tests/`는 그 계약을 담당한다.

경계는 다음과 같다. 라운드 0의 Claude·Codex 실행은 실제 프롬프트와 시작 이벤트로 격리 증명된다. 정규화 뒤에만 각 출처가 상대 finding을 비평한다. synthesis adapter는 `finding_id→실제 source/원문 ID`를 포함한 실제 출처와 원문 ID의 대응을 `<run_dir>/provenance.json`에만 두고 외부 입력에는 R3.2의 불투명 `finding_id`·A/B·후보 논점·비평 관계만 남긴다. renderer만 sidecar를 다시 읽어 출처를 표시한다.

## Interfaces and data flow

```text
args → target snapshot → Claude ∥ Codex → normalized findings
     → cross critiques (round 1, conditional round 2)
     → anonymous shuffled synthesis input → fresh Claude synthesizer
     → synthesis + provenance sidecar → local report.md
```

정규 finding의 `file`은 저장소 상대 경로이고 행은 1 이상이며 `line_start <= line_end`다. Claude 원문 severity는 R2.1 변환표를 거쳐 `critical`·`high`·`medium`·`low`만 정규 레코드에 들어가며 표 밖 명시 라벨은 해당 finding만 거부한다. `finding_confidence`는 리뷰어 finding의 0–1 신뢰도이고 `decision_confidence`는 종합 분류의 별도 0–1 신뢰도다. 종료 후보가 겹치면 R7.1의 전순서 우선순위로 하나만 보고서에 기록한다. `<run_dir>/provenance.json`은 A/B 실제 출처·reviewer 배정, seed·실행 구분자, `finding_id→실제 source/원문 ID`, `critique_id→작성자 source/reviewer`를 담고 종합 입력에는 절대 포함하지 않는다. synthesis 입력 view는 원문 ID를 제거하고 R3.2 불투명 `finding_id`와 논점별 분류·decision_confidence·rationale·양 그룹 finding ID를 반환한다.

## Failure behavior

입력 해석·base 해석·빈 diff는 외부 호출 전에 끝낸다. reviewer 출력이 스키마를 통과하지 못하면 한 번만 형식 재요청한다. 호출 실패·타임아웃·재실패은 원문과 오류를 남기고 숨기지 않는다. 양쪽 실패는 synthesis 없이 비성공 종료한다. 단일 출처 성공은 제한 보고서를 만들되 독립 이중 리뷰·교차 비평·합의 판단을 주장하지 않는다.

## Security and risk

리뷰 대상은 읽기 전용이다. Codex는 `--sandbox read-only`이며 우회·자동 승인·추가 디렉터리 옵션을 금지한다. Claude 원문 severity는 R2.1의 닫힌 변환표만 통과하고 표 밖 명시 라벨은 기본값으로 보정하지 않고 해당 finding만 거부한다. 입력에서 실제 source·원문 ID·모델명·reviewer명과 sidecar를 제거하고 R3.2의 평문 출처 식별자를 담지 않는 불투명 `finding_id`와 A/B 그룹만 남기며 R3.4의 공통 body 구조로 형식 누설을 차단한다. GitHub 쓰기 명령과 자동 코드 수정이 스킬 소스에 없도록 오류를 통과시키지 않는 `rg` 계약으로 방어한다. run directory와 `.claude/dual-review-state/` 루트의 `.gitignore`는 그 경로에만 두며 토큰·자격 증명을 읽거나 기록하지 않는다.

## Test strategy

결정적 Python 단위 테스트는 정상·빈 대상·severity 변환표의 대소문자/기본값/거부·스키마 위반·타임아웃·단일 출처·round 경계·종료 후보 충돌 우선순위·drift·익명화/셔플/복원 fixture를 다룬다. 내용 계약 테스트는 호출 템플릿, schema, 라운드 0 프롬프트 Python 소유권과 보존·순서 게이트, packaging, frontmatter, 비쓰기 제약을 확인한다. 저장소 루트에는 `pyproject.toml`, `package.json`, `tsconfig.json`, `Makefile`, 린터 설정이 없으므로 타입 검사·린트·빌드는 not configured다.

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_*.py'` | 종료 코드 0 |
| CMD-2 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_arguments` | 종료 코드 0 |
| CMD-3 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_reviewer_contract` | 종료 코드 0 |
| CMD-4 | `sh -c 'test -d dot_claude/skills/dual-review || exit 2; rg -n --hidden --no-ignore --glob "*" -e "--skip-git-repo-check" -e "--dangerously-bypass-approvals-and-sandbox" -e "--full-auto" -e "--yolo" -e "--add-dir" dot_claude/skills/dual-review; code=$?; case $code in 1) exit 0;; 0) exit 1;; *) exit "$code";; esac'` | 무매치만 종료 코드 0; 매치·오류는 비영 |
| CMD-5 | `sh -c 'test -d dot_claude/skills/dual-review || exit 2; rg -n --hidden --no-ignore --glob "*" -e "gh pr review" -e "gh pr comment" -e "gh api" dot_claude/skills/dual-review; code=$?; case $code in 1) exit 0;; 0) exit 1;; *) exit "$code";; esac'` | 무매치만 종료 코드 0; 매치·오류는 비영 |
| CMD-6 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_no_mutation_contract` | 종료 코드 0 |
| CMD-7 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_independence` | 종료 코드 0 |
| CMD-8 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_schema_contract` | 종료 코드 0 |
| CMD-9 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_critique_contract` | 종료 코드 0 |
| CMD-10 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_synthesis_contract` | 종료 코드 0 |
| CMD-11 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_packaging_contract` | 종료 코드 0 |
| CMD-12 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -m unittest discover -s dot_claude/skills/dual-review/tests -p 'test_contracts.py' -k test_deterministic_boundaries` | 종료 코드 0 |

`CMD-7`~`CMD-12`는 같은 `tests/test_contracts.py` 모듈의 서로 다른 `-k` 필터이며, `CMD-1`이 모든 테스트를 포함한다.

## Decisions

### D1. 전체 사이클은 반복하지 않고 교차 비평만 반복한다

라운드 0의 독립 이중 리뷰 뒤, 라운드 1은 서로의 finding 비평이고 라운드 2는 라운드 1 신규 high가 있을 때만 한다. 독립성은 라운드 0에만 성립하고, 겹친 종료 후보의 단일 선택은 R7.1의 우선순위를 따른다. `#29`의 16라운드 실측과 13차 이후 증가를 근거로, 교차 비평이 아닌 전체 재실행은 비용만 선형 증가시키므로 제외한다.

### D2. 신선 Claude 종합자는 신원 대신 익명 그룹 관계를 받는다

Claude 신선 서브에이전트는 실제 source·원문 ID·모델·reviewer·sidecar 없이 R3.2의 평문 출처 식별자를 담지 않는 불투명 `finding_id`, A/B 그룹, 후보 논점, critique 관계만 받고, `finding_id→실제 source/원문 ID` 대응을 담은 내부 sidecar는 renderer가 최종 보고서에 출처를 복원하는 데만 쓴다. A/B 배정은 재현·교대하고 본문은 공통 구조로 정규화한다.

### D3. 종합은 `codex exec` 경로에 두지 않는다

2026-09-06 `codex exec` 무응답 4회는 마지막 종합 단계 실패가 선행 리뷰 비용을 모두 버릴 위험을 보인다. 마지막 단계를 새 실패 지점에 얹지 않기 위해 Claude 서브에이전트로 종합한다.

### D4. Codex 리뷰어는 CLI와 스킬 자체 schema를 쓴다

플러그인의 `/codex:review`·`/codex:adversarial-review`는 프로그램 호출 불가 슬래시 명령이고 설치 경로 해시도 변한다. 그래서 `codex-cli 0.153.4`의 `codex exec --sandbox read-only --output-schema`를 직접 쓰며, 플러그인 1.0.5 schema의 verdict/summary/findings/next_steps와 finding 열은 참고만 한다.

### D5. 결정 규칙은 Python에, 오케스트레이션은 SKILL.md에 둔다

`quality-goal`의 `scripts/quality_state.py`와 `tests/test_quality_state.py` 선례처럼, 재현 가능하고 위험한 규칙은 Python 표준 라이브러리와 단위 테스트로 검증한다. 라운드 0 프롬프트 구성, 실제 디스패치 문자열 보존, 양쪽 호출 후 판독 게이트도 이 Python 경계에 둔다. 이는 서술형 지시만으로 종료·익명화·ID·보고서 결과와 독립성 증거가 달라지는 것을 막는다.

### D6. 추상화 이탈 경계는 0.5 초과다

0 초과는 보조 확인 하나에도 너무 일찍 멈추고, 1.0은 모든 새 finding이 대상 밖일 때까지 이탈을 감춘다. 변경 파일 밖 finding이 과반인 0.5 초과는 리뷰가 diff 중심 검증에서 벗어났다는 결정적 중단 신호로 채택한다.

### D7. 합의 판정은 오케스트레이터의 결정적 위치·제목 매칭으로 옮기지 않는다

위치와 제목 유사도 매칭은 단순하지만 “같은 결함인가”를 기계적으로 판단하기 어려워 오탐을 낸다. LLM 종합자를 쓰는 이유가 바로 그 판단이므로, 판단은 종합자에게 남기고 Python은 출처 중립 후보·A/B 관계·검증 가능한 정보를 정확히 제공한다.
