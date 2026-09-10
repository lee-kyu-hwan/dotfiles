# Quality Goal Report

- Task ID: 20260906T194200Z-79-verifying-open-source-contribution-ca-f0ac72ad
- Mode: strict
- Status: **COMPLETED** — 코드 리뷰 라운드 3 PASS(91), 미해결 blocker 없음, 검증이 리뷰된 지문(f07741b4…)에 묶여 계약상 종결 조건을 만족했다. 워크플로 종결이며 이슈 #79 전체 완료와는 다르다(§ Final status)
- Created: 2026-09-06T19:42:00Z
- Updated: 2026-09-07T09:40:14Z (COMPLETED 전이 후 라운드 3 결과 기록만을 위한 편집)
- Source goal: #79 verifying-open-source-contribution-candidates 스킬 제한된 Plan 재설계 — 이전 실행 20260906T125225Z-…-ec840cba(NEEDS_REDESIGN) 계승, PLAN-012·PLAN-013·PLAN-007 해소

## Classification

요청 모드 auto → **strict**. 근거(이전 실행과 동일): 신뢰하지 않는 외부 저장소 코드의 clone·실행 권한 경계, 네트워크·비밀정보 격리, 프롬프트 인젝션 방어라는 보안 통제 설계(#79 범위, 설계문서 § 12); 보안 민감 후보의 비공개 분리 규칙(#79 완료기준, 설계문서 § 7); CAN-* 계약은 #80~#82 가 소비하는 스킬 간 호환 계약. 이슈 라벨은 위험 라벨이 아니며 routing-rules 6항(불확실성 → 상위 모드)도 strict 를 가리킨다. 기준 커밋 6d60011cbdaead7946b191d3f12029eef5c141c8, 기준선 dirty 경로는 이전 실행 문서 디렉터리 하나(보존 대상). 설치 quality-goal v5.0.0(계약 파일은 저장소 소스와 바이트 동일; tests 디렉터리만 2026-09-07 에 갱신됨).

### 이전 실행과의 관계

이 실행은 `20260906T125225Z-79-…-ec840cba`(NEEDS_REDESIGN, `REVIEW_LIMIT_EXHAUSTED:plan`, blocker PLAN-012)의 제한된 재설계다. 이전 실행의 state·리뷰·스냅숏·문서 다섯 파일(`docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/`)은 편집하지 않았고 `preserved-run.sha256`(CMD-8)으로 불변을 판정한다. 설치 quality-goal 은 Plan-only 재개를 지원하지 않으므로 정상 절차(INTAKE → 분류 → Spec 리뷰 → Plan 리뷰 → 승인 → 구현 → 코드 리뷰)를 처음부터 밟았고 이전 PASS 는 승계하지 않았다. 상세는 `redesign.md`.

### Spec 변경 요약(이전 PASS 본 대비)

라운드 1 본문은 이전 PASS Spec(e672be97…)과 바이트 동일했으나 이 실행 라운드 1 리뷰(SPEC-016~022)로 개정했다: R3.1 reason 값, R3.5 요청 발행 순서·소진 outcome, R5.1 recheck 가변/불변 필드, R5.3 스냅숏 evidence(duplicate_verdict·observed_head_sha), R6.3 여덟째 모순, R7.1 recheck 값 규칙, R8.1 repositories[] 완전성·여섯째 outcome `budget-exhausted`·reason, R8.2 종료 코드 단일 규칙(전부 접근 실패만 4, 예산 소진은 항상 3), R11.1 문서 경로·이전 디렉터리 보존, AC-13·24·30·32·33·35·46·47·51 개정, AC-52·CMD-8·D12·D13 신설. 요구사항 49 유지, AC 51→52. 최종 Spec digest b60eb22ca66d1682313614dc02adc0daeaa29a33bd1069ab3004244d39d173c9.

## Review history

| 산출물 | 라운드 | 점수 | 판정 | 요약 |
|---|---|---|---|---|
| spec | 1 | 83 | REVISE | SPEC-020(High, 새 디렉터리 배치로 경로 계약 불일치) + SPEC-016·017·018·019·022(Medium) + SPEC-021(Low) |
| spec | 2 | 94 | PASS | 전부 해소 확인. Medium SPEC-023(redesign.md 대조 절 옛 문언 — 문서 갱신으로 해소). 첫 응답은 "PASS 에 verified:false 금지" 검증에 걸려 1회 재시도 |
| plan | 1 | 77 | REVISE | PLAN-014(Critical, 롤백 pathspec 이 보존 디렉터리)·PLAN-015·016(High) + PLAN-017(Medium) + PLAN-018(Low) — 오케스트레이터의 동기화 누락 |
| plan | 2 | 93 | PASS | 전부 해소 확인. Low PLAN-019(redesign.md 문장 — 갱신), PLAN-020('그대로 실행 가능' 문구) |
| code | 1 | 86 | REVISE | CODE-001(Medium, AC-35 end-to-end 단정 부족)·CODE-002(Medium, report.md 부재로 CMD-7 실패)·CODE-003(Low, 픽스처 파일명 Plan 미신고). 첫 시도는 리뷰어 24턴 한도로 JSON 미제출 → record-review-error 후 재시도 |
| code | 2 | 93 | PASS | CODE-001~003 해소 확인. Low CODE-004(보고서 CMD-7 행이 재실행 전 값) |
| code | 3 | 91 | PASS | LIVE-1·LIVE-2 수정과 CODE-004 해소 확인. 신규 Low CODE-005(디렉터리 `entry_count` 가 해시 대상 이름 수와 다를 수 있음)·CODE-006(Spec R3.2 필드 목록과 배포 계약 문서의 필드 수 불일치). 게이트 네 조건 모두 확인, 리뷰 지문 = 검증 지문 = f07741b4…. 첫 시도는 리뷰어 정체로 JSON 미제출 → `record-review-error` 후 1회 재시도로 해소 |

Plan 최종 digest 28f5dd672ad65370c21b041ff617df5a32d7ac148bc4aa6e2c900c882ecb70dd.

코드 리뷰 라운드 3(마지막 허용 라운드)은 이 보고서가 렌더된 뒤의 워크스페이스(지문 f07741b419fca7f227af3a7c2521482f1f7d2bc6475d84430236284feb4889e1)를 대상으로 수행해 PASS(91)를 받았다. 그 지문이 record-verification 에 기록된 지문과 같아 `CODE_REVIEW → COMPLETED` 가드를 만족했다. 이 절과 § Final status 의 라운드 3 기록은 전이 **후** 추가한 편집이며, 그 편집은 판정 기록만을 담는다(권위 기록은 `state.json`).

## Blocking-finding resolutions

- SPEC-020(High): R11.1·AC-46·AC-47·AC-51·AC-52·CMD-5·CMD-7·CMD-8·D13 으로 문서 경로를 이 실행 디렉터리로 특정하고 이전 디렉터리 불변 판정을 추가. 라운드 2 리뷰어 해소 확인.
- PLAN-014(Critical)·PLAN-015·PLAN-016(High): 롤백 대상을 이 실행의 두 경로로, File map report.md 경로 정정, 성공 판정을 기준선 dirty 필터 + digest 사본 shasum 으로. 라운드 2 리뷰어 해소 확인.
- 이전 실행 PLAN-012(High): 이 실행 Spec R8.2 단일 규칙과 Plan T3 `discover_exit_code` 로 해소. 코드 리뷰 라운드 1 이 구현과 테스트에서 규칙을 확인함(evidence 2·3·4).
- 코드 라운드 1 CODE-001~003: 해소 방법은 § Remaining advisory findings 와 라운드 2 리뷰 기록 참조.

## Plan approval

- Approval timestamp: 2026-09-06T21:40:31Z (사용자 지시 "새 Spec(94 PASS)·Plan(93 PASS)을 기준으로 구현을 진행" 접수, 현재 Plan SHA-256 이 마지막 PASS 리뷰 digest 와 일치함을 확인한 뒤 approve-plan)
- Plan digest: 28f5dd672ad65370c21b041ff617df5a32d7ac148bc4aa6e2c900c882ecb70dd

## Changed files

이 실행의 코드 변경은 새 디렉터리 하나뿐이다(형제 스킬·추적 파일 불변: CMD-3c·CMD-5 종료 0, 이전 실행 문서 다섯 파일 불변: CMD-8 종료 0).

- `dot_codex/skills/verifying-open-source-contribution-candidates/agents/openai.yaml` — 4행
- `dot_codex/skills/verifying-open-source-contribution-candidates/evals/behavioral-eval.md` — 31행
- `dot_codex/skills/verifying-open-source-contribution-candidates/references/github-verification-contract.md` — 82행
- `dot_codex/skills/verifying-open-source-contribution-candidates/references/verification-contract.md` — 140행
- `dot_codex/skills/verifying-open-source-contribution-candidates/scripts/verify_candidates.py` — 3350행
- `dot_codex/skills/verifying-open-source-contribution-candidates/SKILL.md` — 25행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/budget/analysis.json` — 23행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/budget/combo-stage/case.json` — 1행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/budget/repo-stage/case.json` — 1행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/budget/unstarted/case.json` — 1행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/candidates-existing.json` — 4행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/caps/analysis.json` — 65행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/common/analysis.json` — 71행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/failures/all-404/case.json` — 1행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/failures/cases.json` — 9행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/injection/analysis.json` — 29행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/injection/fixture.json` — 3행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/injection/responses.json` — 83행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/insufficient/case.json` — 7행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/insufficient/responses.json` — 42행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/mixed/case.json` — 7행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/negative/cases.json` — 7행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/negative/responses.json` — 71행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/positive/assessment-issue-ready.json` — 6행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/positive/responses.json` — 138행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/redaction/analysis.json` — 29행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/redaction/responses.json` — 76행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/security/assessments.json` — 17행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/stale/cases.json` — 9행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/fixtures/stale/responses.json` — 46행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/test_skill_contract.py` — 161행
- `dot_codex/skills/verifying-open-source-contribution-candidates/tests/test_verify_candidates.py` — 2676행

라이브 결함 수정 라운드(fix2)가 바꾼 파일: `scripts/verify_candidates.py`, `tests/test_verify_candidates.py`, `tests/fixtures/positive/responses.json`, `references/github-verification-contract.md` 네 개.

구현 라운드: Codex gpt-5.6-sol high, workspace-write. 라운드 구성은 T1+T2 / T3 / T4 / T5+T6 / T7+T8(결정적) + 코드 리뷰 수정 라운드(fix1b) + 라이브 결함 수정 라운드(fix2). 실행 사고 INC-1~5 는 § Remaining advisory findings.

## Verification evidence (독립 재실행 2026-09-07T09:08:41Z — LIVE-1·LIVE-2 수정 후)

| ID | 종료 코드 | 출력 요약 |
|---|---|---|
| CMD-1 | 0 | Ran 44 tests in 1.260s  OK  |
| CMD-3a | 0 | Ran 30 tests in 1.778s  OK  |
| CMD-3b | 0 | Ran 108 tests in 1.558s  OK  |
| CMD-3c | 0 |   |
| CMD-4 | 0 | Skill is valid!  |
| CMD-5 | 0 |   |
| CMD-6 | 0 |   |
| CMD-7 | 0 |   |
| CMD-8 | 0 | docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/report.md: OK docs/development/2026-09-06-79-verifying-open-sou |
| LINES-SKILL | 0 |       25  |
| LINES-REFS | 0 |       82 dot_codex/skills/verifying-open-source-contribution-candidates/references/github-verification-contract.md      140 dot_codex/skills |

오케스트레이터가 직접 실행했다. CMD-1 새 스킬 44 테스트 OK(Plan 추적표의 테스트 이름 44개와 정확히 일치, 신규 이름 없음) · CMD-3 형제 30·108 OK 와 base 대비 불변 · CMD-4 quick_validate OK · CMD-5 변경 경로가 허용 세 접두어 안 · CMD-6 3.9 문법 파싱 · CMD-7 이 실행 문서 다섯 파일 존재 · CMD-8 이전 실행 문서 다섯 파일 SHA-256 불변.

표적 회귀 테스트(각 1건 OK): `test_policy_files_discovery_and_untrusted_excerpts`, `test_policy_checks_shape_and_sha_binding`, `test_repository_checks_and_upstream`, `test_exit_code_matrix`, `test_injection_fixture_is_inert`, `test_secret_like_strings_redacted`.

오케스트레이터의 독립 재현(네트워크 없이 모듈을 직접 호출):

- 정책 결과 세 상태가 서로 구분됨 — 디렉터리 배열 응답 → `status: found`·`entry_count: 3`·`size: null`·정렬된 이름 목록의 정규 JSON SHA-256 일치·미신뢰 발췌에 이름 전부 포함; 404 → `status: absent`(경고 없음); 403 → `status: request-failed` + `request-failed:<path>:http-403` 경고; 2xx 이지만 dict/list 아님 → `status: request-failed` + `invalid-policy-payload` 경고; 정상 파일 → `status: found` + 내용 SHA-256 일치.
- `POLICY_PATHS` 에 후행 슬래시가 남아 있지 않고 ISSUE_TEMPLATE 항목은 `.github/ISSUE_TEMPLATE` 다.
- 키워드 매칭 양성 7건 전부 검출(`CLA`, `cla-assistant.io`, `CLAs`, `DCO`, `Signed-off-by:`, `Developer Certificate of Origin`, `Contributor License Agreement`), 음성 8건 전부 0건(실제 관측 문장 "responsible for clarifying the standards"·"further defined and clarified" 포함, 그리고 `declaration`·`class`·`nomenclature`·`dcode`·`unclassified`·`declarative`).

미구성 범주: type check·lint·build 는 이 저장소에 구성이 없어 `not configured`(근거: `.pre-commit-config.yaml` 에 gitleaks 훅만, pyproject·Makefile 없음).

### AC-47 제한된 실제 실행 — 1회 수행 (2026-09-07)

#### 유보 이력 (보존)

최초 승인(2026-09-06T21:40:31Z) 시 사용자 결정 원문: "실제 대상 저장소·PAT 입력·요청 예산·clone 허용을 아직 정하지 않았으므로 AC-47 라이브 검증은 사용자 결정까지 유보한다." 그 단계에서는 **AC-47 deferred by user** 로 기록했고 라이브 검증을 수행하지 않았다. 이 이력은 사실로 보존한다.

#### 이번 승인 범위와 시각

2026-09-07 사용자가 유보를 이 범위에서만 해제했다: 대상 `eslint-community/eslint-plugin-promise` **하나**, 패턴 **PAT-001**, 단서 상한 4(기존 4개 전부, 원본 수정 금지), API 요청 예산 **80**(재시도 포함), 후보 조합 상한 저장소당 2·전체 2, clone **명시 허용**(세션 임시 영역에 shallow clone 1개, 정적 읽기만, `--keep-clone` 금지). 예산 상향·추가 discover 실행·assessment/record/recheck 는 이 승인에 포함되지 않는다. 오케스트레이터 모델은 이 단계에서 사용자의 `/model` 변경에 따라 **Opus 5 (1M context) / effort high** 였고, Codex 구현 라운드는 계약대로 gpt-5.6-sol high 였다(모델 대체 없음). 상세 사전 확인은 `.claude/quality-state/<task-id>/live/run-record.md`.

#### 실행한 명령

```bash
/opt/homebrew/bin/python3 dot_codex/skills/verifying-open-source-contribution-candidates/scripts/verify_candidates.py discover \
  --analysis /Users/lee-kyu-hwan/code/eslint-contrib/eslint-learning-lab/docs/research/open-source-contributions/runs/2026-09-06-four-repositories/supplement-analysis.json \
  --repo eslint-community/eslint-plugin-promise \
  --pattern PAT-001 \
  --max-clues-per-pattern 4 \
  --request-budget 80 \
  --max-candidates-per-repo 2 \
  --max-candidates-total 2 \
  --allow-clone \
  --clone-root "$(mktemp -d "$(python3 -c 'import tempfile;print(tempfile.gettempdir())')/ac47-clone-root-XXXXXX")" \
  --output  <task-state>/live/20260907T0300Z-promise-pat001/discovery.json \
  --manifest <task-state>/live/20260907T0300Z-promise-pat001/verification-manifest.json
```

작업 코드 revision `sha256:4caeacac…`(설치본 없음, 저장소 코드로 실행). 입력 분석 파일 SHA-256 `6c1dd0c6…` 실행 전후 동일. 출력 경로는 `.gitignore:25` 로 무시됨(`git check-ignore` 확인).

#### 실제 결과

| 항목 | 값 |
|---|---|
| 종료 코드 | **0** (stdout 첫 줄 `complete: discovered 1 candidate combinations`, stderr 비어 있음) |
| 실행 시각 | 2026-09-07T07:31:51Z → 07:32:14Z (23초) |
| manifest `status` / `outcome` | `complete` / `discovered` (run RUN-001) |
| `budget.requests_consumed` | **44** / 예산 80 (초과 시도 없음; 200 응답 29건, 404 응답 15건, 재시도 0건) |
| `repositories[]` | 1건: `outcome: checked`, `reason: null`, `stages_completed: [repository, head, community_profile, private_vulnerability_reporting, policy_files]`, `head_sha: e73585efc03ddf17df0273fa3b8dad0b66c51168` |
| `failed_scopes` / `warnings` / `skipped_by_cap` | 모두 비어 있음 |
| `method_limitations` | "GitHub search index delay can omit recently created or updated matches." |
| `evidence_status` | `remote+static` |

**저장소 확인**: archived false, disabled false, fork false(따라서 upstream 조회 없음), has_issues true, default_branch `main`, visibility public, license `ISC`, private vulnerability reporting **true**, community profile 여섯 항목 모두 true.

**observed remote SHA 와 clone SHA**: 원격 head `e73585ef…` 와 clone `rev-parse HEAD` `e73585ef…` 가 **동일** — `head-moved-during-run` 경고 없음.

**clone 정리 증거**: `clones[]` = `{path: <tempdir>/ac47-clone-root-…/eslint-community__eslint-plugin-promise, sha: e73585ef…, removed: true, size_bytes: 638967}`. 실행 후 파일 시스템에서 그 경로가 존재하지 않음을 직접 확인했고, 오케스트레이터가 만든 빈 clone-root 도 제거했다. 다른 실행의 임시 파일·clone 은 건드리지 않았다(`verify-candidates-*` 잔여 0건). 정적 읽기만 수행했고 `execution_surfaces` 에는 `package.json` 경로만 기록됐다(실행·설치·빌드·테스트·submodule 초기화 없음).

**중복 검색**(`complete: true`, `unused_clues: []` — 단서 4개 전부 사용, 조합당 16 요청): `lib/all-rules.js` 와 `README 규칙 목록` 은 네 조합 모두 0건. `tests/lib/rules` 는 closed issue 1건(#222). `docs/rules` 는 open issue 3건(#599·#109·#151), closed issue 11건(#220·#214·#118 등), open PR 2건(#652·#649), closed PR 30건 — 그중 **#396 "docs: automate docs with `eslint-doc-generator`"** 가 확인됐다.

**코드 검색**(`available: true`): `docs/rules` 2건(`README.md`, `rules/lib/get-docs-url.js`), 나머지 세 단서 0건.

**정적 탐색**: hits 35건 전부 `docs/rules` 단서(대부분 `README.md` 규칙 표 영역), `skipped_files` 0.

#### 구조 차이·자동 생성에 대한 관찰 (판정 아님)

입력 단서는 `eslint-plugin-n` PR #553·#554(PAT-001 근거 PR-002·PR-004)에서 도출됐다. promise 에서 관찰된 사실은 다음과 같다: `lib/all-rules.js` 와 `tests/lib/rules` 경로는 원격 코드 검색·정적 탐색 모두 0건이고, 규칙 코드는 `rules/`(예: `rules/lib/get-docs-url.js`) 아래에 있으며, closed PR #396 은 문서를 `eslint-doc-generator` 로 자동 생성하도록 바꿨다. 즉 PAT-001 의 경로 단서는 이 저장소에 1:1 로 대응하지 않고, PAT-001 의 countercondition("등록·문서가 자동 생성되는 프로젝트는 생성 소스를 수정해야 한다")에 해당할 가능성이 있다.

이는 **관찰이지 판정이 아니다.** 경로 미일치나 검색 0건만으로 적용 불가·후보 없음·정책 허용을 단정하지 않는다. 이번 승인은 `discover` 실경로 검증이며 `assessment`·`record`·`recheck` 는 실행하지 않았고 `CAN-*` 레코드나 ready 상태는 만들지 않았다. 후보 성립 여부는 사람의 평가(assessment)와 `record` 게이트를 거쳐야 하며 그 단계는 별도 승인 사항이다.

#### 누락 근거·제한 (exit 0 이라도 남는 한계)

- **검색 인덱스 지연**은 manifest `method_limitations` 에 상시 기록된다. 검색 0건이 부재의 증명은 아니다.
- **저장소 수준 `SECURITY.md` 부재**: 조직 기본 저장소 `eslint-community/.github` 의 `SECURITY.md`(880 bytes)만 발견됐다. 조직 기본 파일로 커버되지만 저장소 자체에는 없다.
- **`.github/ISSUE_TEMPLATE/` 는 `found: false`** 로 기록됐는데 같은 실행의 community profile 은 `issue_template: true` 다. 요청 경로가 `/contents/.github/ISSUE_TEMPLATE/?ref=main`(후행 슬래시)로 404 를 받은 것이 원인으로 보인다 → 아래 LIVE-1. **템플릿이 없다고 단정하지 않는다.**
- **CLA/DCO 신호 없음**: `keyword_hits` 는 `CODE_OF_CONDUCT.md` 의 `CLA` 1건뿐이며, 실제 문맥은 "clarifying"·"clarified" 내부 부분 문자열이다(오탐) → LIVE-2. CLA/DCO 요구 존재 여부는 이 실행으로 확인되지 않았다.
- **AI 보조 기여 정책·프로그램 규칙**: `--program-rules` 는 `record` 전용 옵션이므로 이 discover 실행에서는 확인 대상이 아니었다. 미확인.
- 저장소 1개·패턴 1개·단서 4개·조합 상한 2 범위의 1회 실행이다. 예산 44/80 소진으로 여유가 있었고 rate limit 대기·재시도는 발생하지 않았다.

## Remaining advisory findings

- **AC-47**: 2026-09-06 유보(사실로 보존) 뒤 2026-09-07 승인 범위에서 라이브 discover 1회를 수행했다(위 § AC-47 참조, 종료 코드 0). strict 고위험 E2E 경로 중 **실제 GET 요청과 실제 shallow clone·정리**는 이제 실증됐다. 다만 `assessment`·`record`·`recheck` 의 실경로와 후보 재현은 여전히 미검증이며, 이 실행은 #79 전체 완료가 아니다.
- **LIVE-1 (Medium, 해소)**: 원인은 `POLICY_PATHS` 의 `.github/ISSUE_TEMPLATE/` 후행 슬래시로 Contents API 가 404 를 반환한 것, 그리고 `_policy_result` 가 디렉터리(배열) 응답을 처리하지 않고 404(실제 부재)와 비2xx(조회 실패)를 구분하지 않은 것이다. 수정: 요청·보고 경로를 `.github/ISSUE_TEMPLATE` 로 바꾸고 `record` 쪽 `key_paths["issue_template"]` 두 곳과 `references/github-verification-contract.md` 를 함께 갱신; 배열 응답은 `found: true`·`entry_count`·정렬된 항목 이름의 정규 JSON SHA-256(record 의 sha256 결합 유지)·미신뢰 발췌로 기록; 모든 정책 결과에 `status`(`found`/`absent`/`request-failed`)를 추가해 존재·부재·조회 실패를 구분한다. 회귀 테스트는 `test_policy_files_discovery_and_untrusted_excerpts`(디렉터리·404·403·비정상 payload)와 `test_policy_checks_shape_and_sha_binding`(디렉터리 sha256 결합 수락·불일치 거부)에 들어갔고, 오케스트레이터가 네트워크 없이 다섯 응답 형태를 직접 재현해 확인했다.
- **LIVE-2 (Low, 해소)**: 원인은 `keyword.lower() in lower_text` 부분 문자열 매칭이다. 수정: `POLICY_KEYWORD_PATTERNS` 로 단어 경계 정규식(`\bclas?\b`, `\bdcos?\b`, `\bsigned-off-by\b`, `\bdeveloper certificate\b`, `\bcontributor license\b`, 모두 대소문자 무시)을 쓰고 보고 라벨은 그대로 유지했다. 양성 7건·음성 8건을 회귀 테스트와 오케스트레이터 독립 재현으로 확인했다(실제 관측된 "clarifying"·"clarified" 오탐 제거).
- **INC-6 (설치본 버전 변경, 보고 사항)**: 실행 중 설치된 quality-goal 이 **5.0.0 → 5.1.0** 으로 갱신됐다(다른 pane 의 #70 배포로 추정, 개입하지 않음). 조용히 섞지 않고 대조했다 — `CODE_REVIEW → COMPLETED` 가드는 바이트 동일, `REQUIRED_CHECKS`·`SCORE_THRESHOLD`(85)·`record-review`·`record-verification`·`transition`·`set-artifact`·`fingerprint` 인자와 구현/수정 라운드 라우팅(strict → gpt-5.6-sol high)도 동일하며, 5.0.0 으로 만든 이 상태 파일이 5.1.0 스크립트에서 정상 로드된다(`readiness` 키 부재는 지연 생성으로 면제). 추가된 Spec author·advisory readiness 절차는 Spec 단계용이며 **이 실행에 소급 적용하지 않았다**(readiness 는 계약상 advisory 로 전이를 결정하지 않는다). 남은 단계는 5.1.0 스크립트로 수행했다. 근거: `.claude/quality-state/<task-id>/orchestrator-deviations.md` INC-6.
- PLAN-020(Low): 롤백 성공 판정 문구 "그대로 실행 가능" 은 `<task-id>` 치환과 `QG_BASE` 설정이 먼저 필요하다. 실제 값: task-id `20260906T194200Z-79-verifying-open-source-contribution-ca-f0ac72ad`, `QG_BASE=6d60011cbdaead7946b191d3f12029eef5c141c8`.
- 이전 실행 계승: SPEC-016·017·018(이 실행 Spec 본문에 반영), PLAN-019(redesign.md 갱신), DEV-1(이전 실행 절차 순서 편차).
- 운영 사고(quality-goal 결함 아님, `.claude/quality-state/<task-id>/orchestrator-deviations.md`): INC-1 Codex 하위 에이전트 `wait` 정체(감시자 종료) → 단일 스레드 지시로 재실행; INC-2·INC-3 호스트 메모리 부족으로 하네스가 백그라운드 래퍼 종료 → nohup 분리 실행으로 전환; INC-4 T5·T6 완료 후 모델 턴 정체로 결과 JSON 미제출 → 독립 검증 + 다음 라운드 결과 계약에 포함. 코드 리뷰 라운드 1 첫 시도는 리뷰어 24턴 한도 소진(record-review-error, 1회 재시도로 해소).
- quality-goal 관찰(문서화 여지, 수정하지 않음): `classify --reasons`·`record-review-error --errors` 는 JSON 파일 경로를 받는다; `approve-plan` 인자는 `--plan`·`--approved-at`; 코드 리뷰어 maxTurns 24 는 7,000행 diff 에 부족했다(인덱스 파일 제공으로 우회).

## Final status

- Status: completed (quality-goal 워크플로)
- Machine-readable reason: (없음 — `state.json` 의 `status_reason` 은 null)

**종결 근거**: 코드 리뷰 라운드 3 PASS(91), blocker 0, 미해결 code finding 0, `verification.valid: true`, 검증 지문 == 마지막 통과 리뷰 지문(f07741b4…). 과거 PASS 지문을 재사용하지 않았고 상태 파일을 수동 편집하거나 이력을 초기화하지 않았다.

**이 종결이 뜻하지 않는 것 (이슈 #79 전체 완료 아님)**

- **라이브 검증 범위**: `discover` 실경로만 1회(승인 범위) 검증됐다. `assessment`·`record`·`recheck` 는 실제 GitHub 에 대해 한 번도 실행되지 않았고 픽스처 기반 테스트로만 입증된다. `CAN-*` 레코드도, 검증된 기여 후보도 없다. discover 성공 ≠ 기여 후보 검증.
- **남은 advisory**: CODE-005(Low, 디렉터리 `entry_count` 와 해시 대상 이름 수 불일치 가능), CODE-006(Low, Spec R3.2 필드 목록 vs 배포 계약 문서 11 키 불일치). 라운드 한도가 소진돼 이 실행에서 코드를 더 바꾸지 않았다 — 후속 작업으로 남긴다.
- **배포·공용 지원**: `chezmoi apply` 미실행, `~/.codex/skills` 에 배포 안 됨. Claude Code/Codex 공용 배포·실행 검증(#82)과 행동 평가 실행(Non-goal 8)은 이 실행 밖이다.
- **버전 경계**: 이 실행의 Spec·Plan 은 quality-goal 5.0.0 절차로 만들어졌고, 실행 중 설치본이 5.1.0 이 됐다(INC-6). 5.1.0 의 Spec author·advisory readiness 절차는 소급 적용하지 않았다.
- **형상 관리**: commit·push·PR·merge 미실행. 워크트리에는 세 개의 미추적 디렉터리(이 실행 문서, 이전 실행 문서, 새 스킬)만 있다.
- **#80~#82**: 트래커 수집·일반 Issue 입력·전체 워크플로 연결은 손대지 않았다.
