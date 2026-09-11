# #79 수정본 제한된 라이브 검증 — 승인 요청안

- 작성 시각: 2026-09-10
- 작성 근거: 기존 로컬 조사 자료와 현재 CLI 계약만 읽어 작성했다. 네트워크·GitHub 요청·clone·대상 코드 실행·의존성 설치·라이브 검증을 하지 않았고 기존 코드도 수정하지 않았다.
- 대상 산출물: 4차 실행이 `COMPLETED` 로 남긴 스킬 `dot_codex/skills/verifying-open-source-contribution-candidates/` (미커밋·미배포)
- 이 문서의 지위: **승인 요청안일 뿐 실행 계획이 아니다.** 아래 § 미확정 입력이 모두 정해지고 명시적 승인이 있을 때만 실행한다.
- **2차 실행의 80회 승인을 재사용하지 않는다.** 이 문서가 요청하는 예산은 아래에서 새로 산출한 값이다.

## 1. 이 라이브 검증이 무엇을 증명할 수 있고 무엇을 증명할 수 없는가

승인 판단에 필요하므로 먼저 정직하게 적는다. 4차 실행이 고친 네 항목 중 **라이브에서 실제로 확인되는 것과 확인되지 않는 것이 갈린다.**

| 항목 | 라이브에서 확인 가능한가 | 근거 |
|---|---|---|
| **I11 정적 검색 additive 계약** | **가능.** 확인 가치가 가장 높다 | 2차 라이브 산출물의 `static_search` 는 정확히 6키(`available`·`hits`·`execution_surfaces`·`skipped_files`·`clone_sha`·`error`)였다. 수정본은 실제 clone 에서 9키(`complete`·`exclusions`·`read_failures` 추가)를 내야 한다. 실제 저장소 트리에서 `exclusions` 세 계수와 `complete: true` 가 나오는지는 fixture 로 대체할 수 없다 |
| **I5 재시도 관측** | **부분 가능.** 분류 자체는 불가 | 수정본은 성공 응답에도 `request_events` 에 `retry_decision`·`retry_reason` 을 기록한다. 2차 라이브의 `retry_events` 44건에는 그 키가 없었으므로 실제 응답에서 새 키가 붙는지 확인된다. 그러나 **403 분류 경로는 라이브에서 재현할 수 없다.** 정상 인증 상태의 공개 저장소 조회는 403 을 내지 않고, 403 을 일부러 유발하는 것은 이 승인 범위가 아니다 |
| **CODE-002 code search 형태 게이트** | **부정 확인만 가능** | GitHub 이 형식 불일치 2xx 를 보내지 않으므로 게이트 발동은 볼 수 없다. 확인되는 것은 **정상 payload 가 새 게이트를 오탐 없이 통과** 하는 것뿐이다(2차 때 `available: true`, hits 2건이었다) |
| **I8 clone 정리 격리** | **부정 확인만 가능** | 정상 정리는 `removed: true` 와 경고 없음으로 끝난다(2차 때도 그랬다). 확인되는 것은 소유권 검사 강화가 **실제 clone 삭제를 막지 않는다** 는 것이다. 정리 실패 경로는 파일시스템을 일부러 망가뜨려야 하므로 제안하지 않는다 |

따라서 이 요청의 목적은 **"수정본이 실제 엔드포인트에서 회귀 없이 동작하고, additive 필드와 재시도 관측 정보가 실제 산출물에 실제로 나타난다"** 를 확인하는 것이다. **실패 분류 경로의 검증은 오프라인 전용으로 남으며 이 라이브 실행으로 대체되지 않는다.** 승인하셔도 `CODE-101`~`CODE-103` 은 해소되지 않는다.

## 2. 대상 저장소

**미확정. 사용자 선택이 필요하다.** 로컬 조사 자료에서 확인된 후보는 둘뿐이다.

`/Users/lee-kyu-hwan/code/eslint-contrib/eslint-learning-lab/docs/research/open-source-contributions/runs/2026-09-06-four-repositories/supplement-analysis.json` 의 레코드 10건이 참조하는 저장소는 `eslint-community/eslint-plugin-promise` 와 `eslint-community/eslint-plugin-n` 이다.

| 후보 | 장점 | 단점 |
|---|---|---|
| **(가) `eslint-community/eslint-plugin-promise`** | 2차 라이브의 **직접 비교 대상** 이다. 같은 저장소·같은 패턴·같은 단서로 돌리면 6키 → 9키 변화, `retry_decision` 신설, `code_search.available` 유지, `clone` 정리 동작을 2차 산출물과 1:1 대조할 수 있다. 사실 관계도 이미 안다(fork 아님, archived/disabled 아님, `has_issues: true`, default branch `main`, ISC, PVR 활성, 정책 파일 20건 조회, clone 638,967 바이트, `skipped_files: 0`) | 2차 때 PAT-001 의 경로 단서 3건이 0 히트였다. 새 후보 발견 가치는 낮다 |
| **(나) `eslint-community/eslint-plugin-n`** | 미조회 저장소라 새 정보가 있다 | 저장소 사실을 모르므로 예산 산출이 보수적이어야 하고(fork 여부 미확인 → ⑤ 요청 1회 가산 가능) 2차와의 직접 대조가 불가능하다 |

**권고는 (가)** 다. 이 실행의 목적이 새 후보 발견이 아니라 수정본의 회귀·신규 필드 확인이고, 유일한 비교 기준선이 (가)에 있다.

## 3. 정확한 PAT-* 입력 (인증 토큰이 아니다)

여기서 말하는 입력은 **분석 산출물의 패턴 식별자와 그 파일 경로** 다. GitHub 인증 토큰은 이 문서의 대상이 아니며 기존 `gh` 자격을 read-only GET 에만 쓴다.

| 항목 | 값 |
|---|---|
| `--analysis` 파일 | `/Users/lee-kyu-hwan/code/eslint-contrib/eslint-learning-lab/docs/research/open-source-contributions/runs/2026-09-06-four-repositories/supplement-analysis.json` (이 #79 워크트리 **밖** 의 읽기 전용 조사 자료. 현재 존재 확인) |
| envelope | `schema_version: 1.0.0`, `records` 10건, `patterns` 1건 |
| `--pattern` | **`PAT-001`** (이 파일의 유일한 패턴. `superseded_by: null`, `confidence.level: medium`) |
| `search_clues` | 4건: `lib/all-rules.js`, `docs/rules`, `tests/lib/rules`, `README 규칙 목록` |
| `--max-clues-per-pattern` | **4** (단서 수와 같으므로 미사용 단서 0) |

**같은 디렉터리의 `analysis.json` 은 사용할 수 없다.** `patterns` 가 0건이어서 `discover` 에 줄 패턴이 없다. 이 사실을 확인했으므로 추정이 아니다.

단서 안전성 검토: 4차 실행이 추가한 미신뢰 단서 거부(따옴표·역슬래시·제어문자)에 걸리는 단서는 없다. 네 번째 단서의 공백과 한글은 거부 대상이 아니다. 따라서 4건 모두 실제 질의에 쓰인다.

## 4. 단계별 실제 명령

**중요한 사실 정정: `assessment` 는 CLI 서브커맨드가 아니다.** 현재 CLI 의 서브커맨드는 정확히 다섯 개다. `discover`, `record`, `recheck`, `render`, `validate`. assessment 는 사람 또는 에이전트가 작성해 `record --assessment` 로 넘기는 **입력 파일** 이며 그 작성 단계는 네트워크를 쓰지 않는다.

아래 셸 변수를 전제한다. `SK=/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier/dot_codex/skills/verifying-open-source-contribution-candidates`, `PY=/opt/homebrew/bin/python3`, `OUT=<§7 의 출력 디렉터리>`, `ANALYSIS=<§3 의 분석 파일>`, `REPO=<§2 에서 선택한 저장소>`, `CLONE_ROOT=<§6 의 clone root>`.

### 4-1. discover — 라이브 (네트워크 필요)

```bash
PYTHONDONTWRITEBYTECODE=1 "$PY" "$SK/scripts/verify_candidates.py" discover \
  --analysis "$ANALYSIS" \
  --repo "$REPO" \
  --pattern PAT-001 \
  --max-clues-per-pattern 4 \
  --max-candidates-per-repo 1 \
  --max-candidates-total 1 \
  --request-budget 60 \
  --allow-clone \
  --clone-root "$CLONE_ROOT" \
  --output "$OUT/discovery.json" \
  --manifest "$OUT/verification-manifest.json"
```

`--keep-clone` 을 **주지 않는다.** clone 은 실행 종료 시 삭제돼야 한다. `--api-version` 은 기본값을 쓴다. `--fixture-dir` 은 주지 않는다(주면 라이브가 아니다).

cap 을 2/2 에서 **1/1 로 줄였다.** 패턴이 1건이므로 조합이 1개뿐이고 상한을 조합 수에 정확히 맞추는 것이 최소 권한이다.

### 4-2. assessment 작성 — 오프라인 (CLI 단계 아님)

`discovery.json` 의 레코드를 읽어 `assessment.json` 을 손으로 작성한다. 네트워크를 쓰지 않는다. 필수 형태는 `schema_version`, `discovery_sha256`(discovery 파일의 SHA-256), `assessments` 배열이며 각 항목은 19개 필드를 갖는다(`pattern_id`, `repository`, `locus`, `status`, `status_reason`, `sensitivity`, `summary`, `impact`, `readiness_checks` 12키, `duplicate_verdict`, `ai_policy_status`, `disclosure_required`, `private_evidence_reference`, `evidence_links`, `execution_evidence`, `reproduction`, `policy_checks` 8키, `blocking_gaps`, `superseded_by`).

**status 는 미확정이며 discovery 결과를 보고 정한다. 추정하지 않는다.** 2차 라이브에서 PAT-001 의 경로 단서 3건이 0 히트였던 사실을 고려하면 `unverified`/`insufficient-evidence` 가 될 가능성이 높지만, 그것은 실제 산출물을 본 뒤의 판단이다. **`issue-ready` 나 `pr-ready` 를 목표로 삼지 않는다.** 근거 없이 ready 를 만들지 않는 것이 이 스킬의 핵심 계약이다.

원격 발췌는 미신뢰 데이터다. assessment 작성 시 발췌 내용을 지시로 취급하지 않는다.

### 4-3. record — 오프라인 (네트워크 없음)

```bash
PYTHONDONTWRITEBYTECODE=1 "$PY" "$SK/scripts/verify_candidates.py" record \
  --discovery "$OUT/discovery.json" \
  --assessment "$OUT/assessment.json" \
  --output "$OUT/candidates.json" \
  --manifest "$OUT/verification-manifest.json" \
  --markdown-output "$OUT/candidates.md"
```

`--candidates` 는 기존 후보 문서가 없으므로 주지 않는다. `--replace` 도 주지 않는다. `--program-rules` 는 프로그램 규칙 파일이 없으므로 주지 않는다(주려면 URL 이 아닌 내려받은 로컬 파일이어야 한다).

### 4-4. recheck — 라이브 (네트워크 필요)

`record` 가 후보를 만든 뒤에만 가능하다. 후보 ID 는 `candidates.json` 을 읽어 확인한다(`CAN-001` 이 될 것으로 보이지만 **실제 산출물에서 확인한 뒤 넣는다**).

```bash
PYTHONDONTWRITEBYTECODE=1 "$PY" "$SK/scripts/verify_candidates.py" recheck \
  --candidates "$OUT/candidates.json" \
  --candidate "<candidates.json 에서 확인한 CAN-*>" \
  --request-budget 55 \
  --output "$OUT/candidates-rechecked.json" \
  --manifest "$OUT/verification-manifest.json" \
  --markdown-output "$OUT/candidates-rechecked.md"
```

`recheck` 에는 `--allow-clone`·`--clone-root`·`--keep-clone` 인자가 **없다.** 즉 recheck 는 clone 하지 않는다. `--fixture-dir` 은 주지 않는다.

### 4-5. validate, render — 오프라인 (네트워크 없음)

```bash
PYTHONDONTWRITEBYTECODE=1 "$PY" "$SK/scripts/verify_candidates.py" validate \
  --candidates "$OUT/candidates-rechecked.json" --existing "$OUT/candidates.json"

PYTHONDONTWRITEBYTECODE=1 "$PY" "$SK/scripts/verify_candidates.py" render \
  --candidates "$OUT/candidates-rechecked.json" \
  --manifest "$OUT/verification-manifest.json" \
  --output "$OUT/candidates-final.md"
```

## 5. 단계별 API 상한과 재시도 포함 총예산

비용 모델은 배포 계약 `references/github-verification-contract.md` 의 고정 요청 순서에서 나오며, **2차 라이브 실측(44회 소모)과 정확히 일치함을 확인했다.**

### discover

| 단계 | 요청 수 | 근거 |
|---|---|---|
| ① repository | 1 | |
| ② head commit | 1 | |
| ③ community profile | 1 | |
| ④ private vulnerability reporting | 1 | |
| ⑤ upstream repository | **0** | (가) 선택 시. 2차 실측에서 `fork: false`. (나) 선택 시 fork 여부 미확인이므로 **1 을 가산해 산출해야 한다** |
| ⑥ 정책 파일 | 20 | `POLICY_PATHS` 10경로 × (대상 저장소 + `{owner}/.github`) |
| ⑦ issue 검색 | 16 | 단서 4 × kind 2(issue·pr) × state 2(open·closed) |
| ⑧ code 검색 | 4 | 단서 4 × 1 |
| **기준 합계** | **44** | (가) 기준. (나)면 45 |

재시도 여유: 각 요청은 최대 3회 재시도(최초 포함 4회 시도)를 허용한다. 이론적 최악은 44×4 = 176 이지만 그 전량을 승인 요청하는 것은 과도하다. **4차 실행의 I5 수정으로 모호한 403 은 재시도 자체를 하지 않게 되어 재시도 표면이 2차보다 줄었다.** 429·5xx 만 재시도한다.

**요청 예산: `--request-budget 60`.** 기준 44 + 여유 16. 여유 16 은 완전 재시도(3회) 요청 5건과 1회분에 해당한다. 2차 실측 재시도는 0건이었다.

### recheck

`_recheck_repository` 의 실제 요청 순서를 코드로 확인했다. discover 와 달리 **community profile 과 private vulnerability reporting 을 조회하지 않는다.**

| 단계 | 요청 수 | 근거 |
|---|---|---|
| repository | 1 | |
| head commit | 1 | |
| duplicate 재검색 | 16 | 후보 snapshot 에 저장된 query 수. 2차 산출물의 `duplicate_search.queries` 가 정확히 16건 |
| 정책 파일 | 20 | `discover_policy_files` 동일 함수 |
| **기준 합계** | **38** | 후보 1건 기준 |

**요청 예산: `--request-budget 55`.** 기준 38 + 여유 17.

### 총예산

| 단계 | 상한 |
|---|---|
| discover | 60 |
| recheck | 55 |
| assessment·record·validate·render | 0 (네트워크 없음) |
| **라이브 총 상한** | **115** |

**이 115 는 2차 실행의 80 회 승인과 무관하게 새로 산출한 값이다.** 재시도 소모를 포함한다. 예산 소진은 종료 코드 3(usable partial)이며 전체 성공이 아니다.

## 6. clone 필요성·경로·정리

**필요하다.** 정적 검색은 clone 없이 불가능하고, 이 실행의 최우선 확인 대상인 I11 의 additive 필드(`complete`·`exclusions`·`read_failures`)는 실제 clone 트리를 순회해야 값이 생긴다. `--allow-clone` 없이는 `_static_record` 가 `available: false` 기본 객체만 내므로 검증 목적을 달성하지 못한다.

- **clone 경로**: **미확정.** 실행 시점에 `tempfile.gettempdir()` 아래 새 임시 디렉터리를 만들어 그 절대 경로를 `--clone-root` 로 준다. 워크트리 안이나 사용자 상주 경로를 쓰지 않는다. 2차 실행은 `/private/var/folders/.../ac47-clone-root-vG50Ks` 를 썼고 같은 방식을 따른다.
- **clone 방식**: `git clone --depth 1 --single-branch --branch <default_branch> --no-tags`. `GIT_LFS_SKIP_SMUDGE=1`, `GIT_TERMINAL_PROMPT=0`.
- **정리**: `--keep-clone` 을 주지 않으므로 실행 종료 시 삭제된다. 4차 실행이 소유권 검사를 강화해 `created: true` 이고 경로가 `<clone_root>/<owner>__<name>` 과 정확히 일치할 때만 삭제한다. 실행 후 `manifest.clones[].removed` 가 `true` 인지, `clone_root` 디렉터리가 비었는지 직접 확인한다.
- **대상 저장소 코드 실행은 하지 않는다.** clone 은 읽기만 한다. `execution_surfaces` 는 경로 기록일 뿐 실행이 아니다.
- **의존성 설치를 하지 않는다.** `npm install` 등을 실행하지 않는다.

## 7. 출력 경로

**미확정 요소가 하나 있다.** 상태 디렉터리에 쓸지 새 문서 디렉터리에 쓸지 선택이 필요하다.

| 안 | 경로 | 성격 |
|---|---|---|
| **(A) 권고** | `<워크트리>/.claude/quality-state/<새 실행 task-id>/live/<타임스탬프>-<repo슬러그>-pat001/` | 2차 실행과 같은 방식이다. `.gitignore` 로 제외돼 있어 작업트리 지문에 영향이 없고 실수로 커밋될 위험이 없다 |
| (B) | `<워크트리>/docs/development/2026-09-10-79-live-verification-proposal/live/` | 사람이 보기 쉽지만 미추적 산출물이 늘고 지문에 들어간다 |

(A)를 권고한다. 파일은 `discovery.json`, `verification-manifest.json`, `assessment.json`, `candidates.json`, `candidates.md`, `candidates-rechecked.json`, `candidates-rechecked.md`, `candidates-final.md`, 그리고 각 명령의 `command.txt`·`stdout.log`·`stderr.log`·`exit.txt`·`started-at.txt`·`finished-at.txt` 다. clone root 경로는 `clone-root.txt` 에 남긴다.

**어느 안이든 기존 1·2·3·4차 실행 문서와 루트 `AGENTS.md` 는 건드리지 않는다.** 4차 실행의 `report.md` 도 수정하지 않는다.

## 8. 성공·partial·중지 기준

### discover

| 판정 | 기준 |
|---|---|
| **성공** | 종료 코드 0. `status: "complete"`. `failed_scopes` 빈 배열. `records` 1건. `static_search` 가 **9키**(기존 6 + `complete`·`exclusions`·`read_failures`)이고 `available: true`·`complete: true`·`read_failures: []`. `manifest.retry_events` 각 항목에 `retry_decision`·`retry_reason` 존재. `clones[].removed: true`. `clone_sha` 가 원격 head 와 일치 |
| **usable partial** | 종료 코드 3. 예산 소진 또는 일부 불완전. **전체 성공이 아니다.** 산출물은 남기고 무엇이 불완전한지(`failed_scopes`, `duplicate_search.complete`, `code_search.available`, `read_failures`, 새 warning 접두) 그대로 보고한다 |
| **접근 실패** | 종료 코드 4. 대상 저장소가 실제 시도 후 접근 실패. 재시도하지 않고 보고한다 |
| **즉시 중지** | 종료 코드 2(입력·계약 위반), 예산 상한 초과 시도, `clone_root` 밖 삭제 흔적, `removed: true` 와 실제 경로 상태 불일치, 승인하지 않은 엔드포인트 요청, 대상 저장소 코드 실행, 네트워크 쓰기 요청(GET 이외) 중 하나라도 관측되면 즉시 멈추고 보고한다 |

### recheck

| 판정 | 기준 |
|---|---|
| **성공** | 종료 코드 0. 후보 상태·이유가 계약대로 갱신되고 `verification_history` 에 snapshot 1건 추가. top-level 과 최신 snapshot 의 상태·이유·시각·SHA 일치 |
| **usable partial** | 종료 코드 3. 부분 재검증 또는 예산 소진. 4차 실행 규칙대로 실패한 actionable 후보는 `unverified`/`insufficient-evidence` 로 차단되고 `blocking_gaps` 에 `recheck-failed` 가 붙어야 한다 |
| **즉시 중지** | discover 와 같은 조건. 추가로 후보가 근거 없이 ready 로 승격되면 즉시 멈춘다 |

### 전체

- **성공 판정에 새 후보 발견을 요구하지 않는다.** `records` 가 있고 계약대로 기록되면 성공이다. 후보 0건이나 `unverified` 는 정상 결과다.
- **`CAN-*` 를 억지로 만들지 않는다.** ready 상태를 목표로 삼지 않는다.
- 실행 후 오프라인 전체 스위트(대상 62 · 형제 30 · 108)와 보존 대상 22개 무결성을 재확인한다.
- 이 실행으로 **`#79` 완료나 배포 완료를 주장하지 않는다.** 공용 배포 검증은 `#82` 로 남는다.

## 9. 미확정 입력 (추정하지 않았다. 승인 시 지정 필요)

| # | 항목 | 상태 | 비고 |
|---|---|---|---|
| 1 | 대상 저장소 | **미확정** | (가) `eslint-community/eslint-plugin-promise` 권고, (나) `eslint-community/eslint-plugin-n`. (나) 선택 시 fork 여부 미확인이라 discover 기준 합계가 45 가 될 수 있어 예산 재산출 필요 |
| 2 | clone root 절대 경로 | **미확정** | 실행 시점에 `tempfile.gettempdir()` 아래 새로 만든다. 사전에 값을 정할 수 없다 |
| 3 | 출력 디렉터리 | **미확정** | (A) 상태 디렉터리 권고, (B) 문서 디렉터리 |
| 4 | assessment 의 `status`·`status_reason`·`readiness_checks` | **미확정** | discovery 산출물을 본 뒤 판단한다. 지금 정하면 근거 없는 사전 판정이 된다 |
| 5 | recheck 대상 후보 ID | **미확정** | `candidates.json` 을 읽어 확인한다 |
| 6 | recheck 실행 여부 | **미확정** | record 가 후보를 만들지 못하면 recheck 는 수행 불가다. discover·record 까지만 승인하고 recheck 는 결과를 보고 따로 승인하는 방식도 가능하다 |
| 7 | 새 quality-goal 실행으로 감쌀지 | **미확정** | 라이브 검증을 5차 실행의 일부로 기록할지, 4차 실행 뒤의 독립 검증 기록으로 남길지 선택이 필요하다. 4차는 이미 `COMPLETED` 이므로 그 상태를 바꾸지 않는 방식이어야 한다 |
| 8 | `--program-rules` 입력 | **미확정** | 프로그램 규칙 파일이 없어 이번에는 주지 않는 것을 전제했다. 대상 프로그램 규칙이 있다면 내려받은 로컬 파일 경로가 필요하다 |

## 10. 이 요청안이 승인을 구하지 않는 것

- 기존 코드 수정, `CODE-101`·`CODE-102`·`CODE-103` 수정
- commit, push, PR 생성, merge, `chezmoi apply`, 배포, GitHub Issue·댓글 작성
- `main`·다른 워크트리·전역 설치본·`$HOME` 설정 수정
- 대상 저장소 코드 실행, 의존성 설치
- 403 이나 형식 불일치 응답을 인위적으로 유발하는 시도
- 위 §5 의 115 회를 넘는 요청, `--fixture-dir` 없는 추가 라이브 실행, 다른 저장소·패턴으로의 확장

## 11. 승인 시 진행 순서

1. §9 의 미확정 입력 지정을 받는다.
2. 선택된 저장소가 (나)면 discover 예산을 45 기준으로 재산출해 다시 보고한다.
3. discover 1회 실행 → 산출물과 종료 코드·예산 소모·`static_search` 9키·`retry_decision` 유무·clone 정리 결과를 보고한다.
4. assessment 작성안을 근거와 함께 보고하고 승인을 받은 뒤 record 를 실행한다.
5. recheck 는 후보 존재와 별도 승인을 확인한 뒤 실행한다.
6. 오프라인 전체 스위트와 보존 무결성을 재확인하고 최종 보고한다.

각 단계 사이에 멈추고 보고한다. 한 번의 승인으로 §4 전체를 연달아 실행하지 않는다.
