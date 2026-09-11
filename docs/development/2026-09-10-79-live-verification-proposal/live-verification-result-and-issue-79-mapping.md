# #79 제한된 라이브 검증 결과와 이슈 완료 기준 근거 매핑

- 최초 작성: 2026-09-10. **개정: 2026-09-10 (root 검토 반영)**
- 라이브 기록: `.claude/quality-state/live-verification-20260910/20260910T105102Z-promise-pat001/` (기존 COMPLETED 상태 밖의 별도 기록. 1·2·3·4차 실행 상태와 보고서, 원시 라이브 artifact 는 수정하지 않았다)
- 승인 근거: `docs/development/2026-09-10-79-live-verification-proposal/proposal.md` 와 같은 라이브 기록의 `approval-record.md`

## 0. 개정 이력 (root 검토 반영)

root 검토에서 네 가지를 지적받아 **이 문서만** 정정했다. 과거 보고서·원시 라이브 artifact·코드는 건드리지 않았다.

| # | 지적 | 정정 |
|---|---|---|
| 1 | 경로 단서 불일치만으로 "PAT-001 이 적용되지 않는다 / 구조적 전제가 성립하지 않는다"고 단정할 수 없다. PAT 는 등록·문서·테스트 동반 갱신의 일반 패턴이며 다른 폴더 구조에서도 성립한다 | § 4 의 단정을 삭제하고 **"적용 가능성과 실제 결함 모두 미확인"** 으로 바꿨다 |
| 2 | `docs/rules` 는 3+11+2+30 = **46** 이고 전체 47 에는 `tests/lib/rules` closed issue 1 이 포함된다. 또한 이 수치는 질의별 hit 합계이므로 고유 항목 수로 단정할 수 없다 | § 4 의 산술을 정정하고 고유 항목 수를 별도 실측(46)으로 구분해 적었다 |
| 3 | 스킬 diff 6 파일 표기가 실제 변경 5 파일과 다르다. 원인을 확인해 정정하라 | § 3 에서 원인을 확인해 정정했다. 6번째는 git 무시 대상 bytecode 캐시였다 |
| 4 | #79 최신 본문의 완료 기준은 8개다. 기존 Goals 5개를 이 8개로 매핑하고, 실제 CAN 1개 `unverified` 와 `no-actionable` 이 같은 실행이므로 독립된 양성·음성 두 사례가 아님을 명시하라 | § 5 를 8개 기준 매핑으로 다시 썼고 § 5.3 에 같은 실행 문제를 명시했다. § 6·§ 7 에 #79 자동 close 보류와 #82 추적을 적었다 |

root 가 지적하지 않았지만 정정 근거를 실측하는 과정에서 **스스로 찾은 사실 오류 두 건** 도 함께 고쳤다. § 3 의 "스킬 파일 수 34" 를 소스 33 + bytecode 캐시 1 로 분해했고(정정 3과 같은 혼동이었다), § 6·§ 7 의 "미커밋" 서술을 § 3.1 의 실측으로 대체했다.

## 1. 라이브 검증 실행 결과

승인 범위대로 정확히 discover 1회와 recheck 1회만 실행했다. 대상은 `eslint-community/eslint-plugin-promise`, 패턴 `PAT-001`(단서 4개), cap 1/1 이다.

| 단계 | 종료 코드 | 요청 소모 | 결과 |
|---|---|---|---|
| discover (라이브) | **0** | 44 / 60 | `complete: discovered 1 candidate combinations` |
| assessment 작성 | — | 0 | 오프라인. CLI 단계가 아니라 입력 파일 작성 |
| record (오프라인) | **0** | 0 | `complete: recorded 1 candidates` |
| validate (오프라인) | **0** | 0 | `valid` |
| render (오프라인) | **0** | 0 | Markdown 생성 |
| recheck (라이브) | **0** | 38 / 55 | `complete: rechecked 1 candidates` |
| **라이브 합계** | | **82 / 115** | 승인 상한 내. 실제 재시도 0건 |

요청 소모가 산출 모델과 정확히 일치했다. discover 44 = 저장소 단계 24(① repository 1 + ② head 1 + ③ community profile 1 + ④ PVR 1 + ⑥ 정책 20) + 조합 단계 20(⑦ issue 16 + ⑧ code 4). recheck 38 = repository 1 + head 1 + duplicate 재검색 16 + 정책 20. recheck 가 community profile 과 PVR 을 조회하지 않는다는 사전 분석도 실측으로 확인됐다(`stages_completed` 가 `repository, head, duplicate_search, policy_files`).

## 2. 4차 실행 수정 4건의 라이브 확인 결과

proposal § 1 에서 "확인 가능"과 "부정 확인만"으로 나눠 예고한 그대로 나왔다.

| 항목 | 예고 | 실제 결과 |
|---|---|---|
| **I11 정적 검색 additive 계약** | 확인 가능. 가치 최고 | **확인됨.** `static_search` 가 2차 라이브의 **6키에서 9키로** 늘었다. 실측 키는 `available`, `clone_sha`, `complete`, `error`, `exclusions`, `execution_surfaces`, `hits`, `read_failures`, `skipped_files` 다. 실제 clone(638,967 바이트)에서 `complete: true`, `exclusions {symlink: 0, oversize: 0, binary: 0}`, `read_failures: []`, `skipped_files: 0` 을 얻었다. fixture 로 대체할 수 없는 확인이다 |
| **I5 재시도 관측** | 부분 확인. 403 분류는 재현 불가 | **부분 확인됨.** `retry_events` **44/44 전부** 에 `retry_decision` 과 `retry_reason` 이 붙었다(2차에는 없던 키). 값은 모두 `return`/`not-retryable` 로 200 응답에 대해 정확하다. recheck 에서도 38/38 동일. 보존 헤더는 허용목록 5종(`Content-Type`, `ETag`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`)뿐이고 `Authorization` 은 없다. **403 분류 경로는 예고대로 재현되지 않았다** |
| **CODE-002 code search 게이트** | 부정 확인만 | **부정 확인됨.** 정상 payload 4질의가 새 게이트를 통과해 `available: true`, hits 2건(`README.md`, `rules/lib/get-docs-url.js`)이고 `invalid-search-payload` 경고가 없다. 오탐 없음 |
| **I8 clone 소유 정리** | 부정 확인만 | **부정 확인됨.** clone 이 `<clone_root>/eslint-community__eslint-plugin-promise` 에 만들어지고 `removed: true` 로 삭제됐다. 실행 후 clone root 는 **0개 항목** 이다. 강화된 소유권 검사가 실제 삭제를 막지 않았다. `clones` 항목은 계약대로 다섯 필드다 |

추가 확인: 4차가 아니라 3차가 넣은 정책 3상태(`found`/`absent`/`request-failed`)도 실제 응답에서 작동했다. 20개 경로 중 `found` 5 · `absent` 15 · `request-failed` 0 이다.

## 3. 라이브 후 회귀와 보존 무결성

| 점검 | 결과 |
|---|---|
| 대상 스킬 오프라인 스위트 | **Ran 62 tests OK** |
| 형제 `analyzing-open-source-pr-patterns` | **Ran 30 tests OK** |
| 형제 `collecting-recent-closed-prs` | **Ran 108 tests OK** |
| 보존 대상 22개 (루트 `AGENTS.md` + 1·2·3차 실행 문서) | **22/22 OK** |
| 스킬 파일 수 | 소스 **33** + bytecode 캐시 1 = 34 (변동 없음) |
| **스킬 소스 변경 (구현 전 스냅숏 대비)** | **5 파일.** 아래 정정 참조 |
| 4차 `report.md` 해시 | `04b40736723712e636f7624aa108d956e44258a73d0d733a9a94679281738794` (종결 시점과 동일) |
| 4차 state stage | `COMPLETED` (변경 없음) |
| clone root 잔여 | 0개 항목 |

### 정정: "스킬 diff 6 파일" → 실제 소스 변경 5 파일

초판이 적은 "6 파일"은 `diff -qr` 출력의 **줄 수를 그대로 센 값** 이었다. 실제로 열거하면 여섯 항목 중 다섯이 소스이고 하나는 bytecode 캐시다.

| 항목 | 성격 |
|---|---|
| `scripts/verify_candidates.py` | 소스 변경 |
| `tests/test_verify_candidates.py` | 소스 변경 |
| `tests/test_skill_contract.py` | 소스 변경 |
| `references/verification-contract.md` | 소스 변경 |
| `references/github-verification-contract.md` | 소스 변경 |
| `scripts/__pycache__/verify_candidates.cpython-314.pyc` | **소스가 아니다.** Python bytecode 캐시 |

따라서 **실제 소스 변경은 5 파일** 이며 4차 실행의 `verification-r1.json` 이 기록한 `claimed 5 / actual 5` 와 일치한다. 초판의 6은 오기였고 4차 검증 결과와 모순되지 않는다.

`.pyc` 에 대한 실측 사실은 다음이다.

- `.gitignore:21` 의 `__pycache__/` 규칙에 걸린다(`git check-ignore -v` 로 확인). **커밋 대상이 아니다.**
- 구현 전 스냅숏에도 이미 존재했다(스냅숏 사본 mtime 2026-09-09 10:58 로컬). 즉 라이브가 새로 만든 파일이 아니다.
- 현재 파일 mtime 은 2026-09-10 10:07 로컬이고 **라이브 실행 창(2026-09-10T10:52Z~10:55Z, 로컬 19:52~19:55) 이전** 이다.
- 라이브 창 이후 `scripts/__pycache__` 아래 변경 파일은 `find -newermt` 로 **0건** 이다.
- 라이브 시작 전 기준선과 라이브 후 확인이 **모두 같은 값** 이었으므로 라이브 실행은 이 항목을 바꾸지 않았다.

### 3.1 추가 정정: 저장소 상태 — 로컬 커밋이 생겼다

이 문서 초판은 스킬을 "미커밋·미배포"로 적었다. 개정 시점에 상태를 다시 실측한 결과 **미커밋은 더 이상 사실이 아니다.** 정확한 상태를 적는다.

| 항목 | 실측 |
|---|---|
| 브랜치의 추가 커밋 | `983a2aac7cac180c0db08c6d05aa70d39771d430` — "feat(skills): 다른 저장소의 기여 후보 탐색·검증 스킬을 추가한다 (#79)" |
| 생성 시각 | 2026-09-10T20:00:26+09:00. 라이브 실행 종료(로컬 19:55) **이후** |
| 포함 파일 | **33개.** 전부 `dot_codex/skills/verifying-open-source-contribution-candidates/` 하위 소스다. 9,946 insertions |
| 미포함 | 루트 `AGENTS.md`, `docs/development/**` 전체, `.claude/quality-state/**`, `__pycache__` bytecode |
| 푸시 여부 | **아니다.** `origin/79-feat/contribution-candidate-verifier` 는 여전히 `6d60011` 이다 |
| 배포 여부 | 아니다. `chezmoi apply` 를 실행하지 않았고 `#82` 에 남아 있다 |

**이 커밋은 이 작업 세션이 만들지 않았다.** 이 세션은 전 구간에서 `git commit` 을 한 번도 실행하지 않았고 권한도 받지 않았다. 시각과 내용으로 보아 root 오케스트레이터가 검증 후 수행한 것으로 보이지만, 이 세션이 확인한 것은 상태 실측 사실뿐이다. 이 커밋을 수정·reset 하지 않았다.

한계 하나를 함께 기록한다. 이 커밋은 보존 대상 22건 중 `docs/development/**` 와 루트 `AGENTS.md` 를 포함하지 않는다. 그 파일들은 여전히 **미추적** 이며 어떤 커밋에도 들어 있지 않으므로, 이력으로 남길지 여부는 root 가 따로 판단해야 한다.

## 4. 후보 결과 — 억지 생성하지 않았다

`CAN-001` 이 실제로 생성됐고 **`unverified` / `insufficient-evidence`** 다. 후보 필드 29개, `next_recheck_required: false`, `verification_history` 2 snapshot(record → recheck), top-level 과 최신 snapshot 의 상태·이유·시각·SHA 일치, `validate` 통과다.

`blocking_gaps` 는 여섯이다. `pattern-loci-absent-on-head`, `duplicate-candidates-unreviewed`, `ai-policy-unknown`, `cla-dco-evidence-not-found`, `no-reproduction-performed`, `program-rules-omitted`.

### 4.1 정정: 패턴 적용 가능성에 대한 판단

**초판은 "PAT-001 의 구조적 전제가 성립하지 않는다", "PAT-001 이 이 저장소에 적용되지 않는다"고 적었다. 이 단정을 철회한다.** 경로 단서가 맞지 않는 것은 **그 단서로 이 저장소를 찾지 못했다** 는 사실일 뿐, 패턴 자체가 적용 불가라는 근거가 아니다.

PAT-001 은 **규칙 등록·문서·테스트를 함께 갱신하는 일반 패턴** 이며 폴더 구조가 달라도 성립할 수 있다. 이 저장소는 `rules/` 구조를 쓰고 `docs/rules/*.md` 문서와 `README.md` 규칙 목록을 가지고 있어 패턴이 말하는 세 요소가 형태만 다르게 존재할 가능성이 있다.

따라서 정확한 판정은 **"적용 가능성과 실제 결함 모두 미확인"** 이다.

- 적용 가능성 미확인: 등록·문서·테스트 세 지점을 이 저장소의 실제 구조(`rules/`, `docs/rules/`, `test/` 또는 이에 준하는 경로)에 다시 대응시켜 조사하지 않았다. 이번 단서 집합은 다른 저장소의 경로를 그대로 쓴 것이다.
- 실제 결함 미확인: 세 지점 사이의 실제 불일치(예: 규칙은 등록됐으나 문서나 테스트가 누락)를 확인하지 않았다. 대상 코드 실행이 금지돼 재현도 하지 않았다.

`blocking_gaps` 의 `pattern-loci-absent-on-head` 라는 항목명은 원시 라이브 artifact(`assessment.json`, `candidates*.json`)에 이미 기록됐고 그 artifact 는 수정하지 않는다. **그 항목명은 "이번 단서 집합으로 loci 를 찾지 못했다"로 읽어야 하며 패턴 부적용을 뜻하지 않는다.** 이 해석 정정을 여기에 남긴다.

### 4.2 정정: 중복 검색 산술

| 단서 | 질의별 total_count 합 |
|---|---|
| `docs/rules` | **46** (open issue 3 + closed issue 11 + open PR 2 + closed PR 30) |
| `tests/lib/rules` | **1** (closed issue) |
| `lib/all-rules.js` | 0 |
| `README 규칙 목록` | 0 |
| **16 질의 합계** | **47** |

**초판은 47 을 `docs/rules` 의 수치로 서술했다. 정정한다. `docs/rules` 는 46 이고 전체 47 에는 `tests/lib/rules` closed issue 1 이 포함된다.**

또한 이 47 은 **질의별 hit 합계이며 고유 항목 수가 아니다.** 실측하면 `html_url` 기준 고유 항목은 **46** 이다. 즉 최소 한 항목이 둘 이상의 질의에 걸렸다. **47 이나 46 중 어느 값도 "서로 다른 중복 후보 개수"로 단정할 수 없다.**

부수 정정: 초판 § 4 는 `tests/lib/rules` 를 "0건"으로 묶어 서술했다. 정확히는 **code search 0 · 정적 검색 0 · 중복 검색 1** 이다. 같은 취지의 서술이 원시 artifact `assessment.json` 의 `duplicate_verdict.matched_items` 에도 "나머지 단서 3개는 모든 상태에서 0건"으로 들어가 있는데 **그 문장은 부정확하다.** 원시 artifact 는 승인 지시에 따라 수정하지 않으므로 이 정정을 여기에 기록한다. 다만 그 항목의 결론(`judgment`: 중복 여부 미확정, 중복 없음이라고 단정하지 않는다)은 정정 후에도 유효하다.

### 4.3 그 밖의 gap 근거 (변경 없음)

- **AI 정책 unknown**: 조회 범위에서 AI 사용 정책 문서를 찾지 못해 `ai_policy_status: unknown` 이다. 게이트 규칙상 `unknown` 은 ready 를 차단한다.
- **CLA·DCO 근거 없음**: 정책 파일 20건의 `keyword_hits` 가 모두 빈 배열이다. 서명 요구가 없다고 단정하지 않고 근거를 찾지 못했다고 기록했다.
- **재현 없음**: 대상 저장소 코드 실행이 금지돼 재현하지 않았다. 정적 히트 35건은 `docs/rules` 문자열 일치일 뿐 패턴 재현이 아니다.
- **프로그램 규칙 생략**: 승인대로 `--program-rules` 를 주지 않아 `policy_checks.program_rules.found` 가 `null` 이다.

**`issue-ready`·`pr-ready` 를 목표로 삼지 않았고 만들지 않았다.** run outcome 도 record·recheck 모두 `no-actionable-candidates` 다.

## 5. #79 완료 기준 8개 근거 매핑

root 가 #79 최신 본문을 읽어 전달한 완료 기준 8개를 기준으로 매핑한다. 초판이 쓴 1차 실행 보존 Goals 5개는 § 5.2 에 교차 참조로 남긴다.

### 5.1 8개 기준 매핑

| # | 완료 기준 | 판정 | 근거 |
|---|---|---|---|
| 1 | **계약 확정** | **충족** | 후보 필드 29 · `RECHECK_MUTABLE_FIELDS` 9와 여집합 default-deny · `STATUS_REASON_TABLE` · `READINESS_KEYS` 12 · `POLICY_CHECK_KEYS` 8 · `FAILED_SCOPE_REASONS` 5 · `ACCESS_FAILURE_OUTCOMES` 4 · `SNAPSHOT_EVIDENCE_FIELDS` 8 · `INHERITED_EVIDENCE_FIELDS` 4 · `COMMUNITY_PROFILE_KEYS` 6 · `ALLOWED_RESPONSE_HEADERS` 7 · `schema_version` · 종료 코드 0/1/2/3/4 와 우선순위가 `references/verification-contract.md`·`references/github-verification-contract.md` 에 문서화되고 4차 신설 계약 테스트 `test_closed_sets_manifest_schema_and_exit_contract` 가 코드·산출물과 직접 대조한다. 라이브 산출물도 후보 29필드·clone 5필드로 계약을 지켰다 |
| 2 | **근거 없는 ready 금지** | **충족** | 게이트가 `readiness_checks` 12키 전부 `confirmed`(단 `rejection_still_valid` 는 `not-applicable` 허용), `ai_policy_status` 가 `unknown`/`prohibited` 가 아닐 것, `sensitivity` 가 security-sensitive 가 아닐 것, `evidence_status != none`, archived/disabled 아님, 정책 경로 `request-failed` 없음을 모두 요구한다. 3차가 정책 `request-failed` ready 차단을, 4차가 그 판정을 유지했고 변이 테스트가 게이트 삭제 시 실패를 증명한다. **라이브에서 실제로 작동했다.** `ai_policy_status: unknown` 과 미확정 근거 때문에 후보가 `unverified` 로 남고 ready 가 되지 않았다 |
| 3 | **HEAD·제안 직전 재검증** | **충족** | discover 가 default branch `main` 의 head `e73585ef…` 를 관측해 `verified_base_sha` 로 기록하고 `clone_sha` 가 일치했다. recheck 를 라이브로 실행해 `verification_history` 에 두 번째 snapshot(`inputs.kind: recheck`)이 append-only 로 붙고 top-level 과 최신 snapshot 의 상태·이유·시각·SHA 가 일치함을 확인했다. 3차가 recheck 실패 시 actionable 차단과 `next_recheck_required` 갱신을 넣었고 4차가 유지했다 |
| 4 | **안전 실행 중단** | **충족** | `run_child` 가 실행 파일·서브커맨드·HTTP 메서드 허용목록을 fail-closed 로 강제하고 4차가 그 위반을 transport 오류와 분리해 재시도·sleep 없이 종료 2로 만들었다. 4차가 `_retryable` 을 헤더 기반으로 바꿔 **모호한 403 은 재시도하지 않고 즉시 판정된 접근 실패로 끝난다.** 라이브에서 GET 만 발생했고 `retry_decision`/`retry_reason` 이 44/44·38/38 기록됐다. clone 정리는 `created: true` 이고 경로가 정확히 일치할 때만 삭제하며 실패해도 예외를 밖으로 내보내지 않는다 |
| 5 | **보안 민감 분리** | **충족** | `sensitivity: security-sensitive` 는 `issue-ready`/`pr-ready` 를 차단하고 `private-report-ready` 로만 갈 수 있으며, 그 경로는 `private_evidence_reference` 와 SECURITY.md 또는 private vulnerability reporting 채널을 요구하고 `execution_evidence.output_excerpt` 및 `reproduction.public_steps` 를 금지한다. 발췌·요약·evidence_links 에 private reference 노출도 거부한다. 오프라인 `security/assessments.json` 픽스처와 `test_private_report_ready_gate_and_render` 가 판정한다. 라이브 후보는 보안 민감이 아니어서 이 경로를 타지 않았다 |
| 6 | **정상·부정·증거 부족·stale·injection fixture** | **충족** | `tests/fixtures/` 에 `positive`·`negative`·`insufficient`·`stale`·`injection` 이 모두 있고 62개 오프라인 테스트가 판정한다. injection 픽스처는 프롬프트 주입 문구를 담은 정책 본문이 미신뢰 발췌로만 저장되고 후보가 `unverified` 로 남는지 단정한다. 4차가 그 픽스처를 실제 contents API 형태(base64)로 정규화하면서 주입 payload 와 단정을 그대로 유지했다 |
| 7 | **허용 범위 실제 후보와 후보 없음 사례** | **미충족.** § 5.3 참조 | 이번 라이브는 **단일 실행 1건** 이다. 실제 `CAN-001`(`unverified`)과 run outcome `no-actionable-candidates` 가 **같은 실행에서 나온 같은 사실의 두 표현** 이므로 독립된 양성·음성 두 사례가 아니다 |
| 8 | **근거 링크·미검증 포함 Markdown·JSON** | **충족** | 라이브가 JSON(`discovery.json`, `candidates.json`, `candidates-rechecked.json`, `verification-manifest.json`)과 Markdown(`candidates.md`, `candidates-rechecked.md`, `candidates-render.md`)을 모두 산출했다. 후보 JSON 의 `evidence_links` 에 근거 링크가 있고 `blocking_gaps` 6건·`readiness_checks` 의 `not-confirmed` 8건·`ai_policy_status: unknown`·`policy_checks.program_rules.found: null` 로 **미검증을 숨기지 않고 표시** 한다. Markdown 도 run status 와 미검증 사유를 담는다. `render` 는 근거 없는 run 상태를 `complete` 로 추정하지 않고 `unknown` 으로 표시한다(4차 확인) |

### 5.2 초판 Goals 5개와의 교차 참조

| 초판 Goal | 8개 기준 대응 |
|---|---|
| 1 스킬 추가와 현재 HEAD 대조 `CAN-*` 생성 | 기준 1·3 |
| 2 기계 확인은 스크립트 강제, 해석은 평가 파일 + 게이트 | 기준 1·2 |
| 3 근거 부족·중복·재현 실패·정책 부적합·stale·후보 없음의 정직한 표현과 ready 거부 | 기준 2·6·8 |
| 4 원격 텍스트를 데이터로만, 설치·실행·쓰기의 권한 경계 | 기준 4·5 |
| 5 결정적 테스트와 제한된 실제 실행 검증 | 기준 6·7 |

### 5.3 기준 7 미충족 사유 (root 지적 반영)

초판은 이번 실행을 "근거 부족 경로의 실증"으로 적으면서 기준 3(정직한 정상 결과)의 충족 근거로 썼다. 그 서술은 유지하되 **기준 7 의 관점에서는 충족이 아니다.**

- 이번 라이브는 **저장소 1개 · 패턴 1개 · 실행 1회** 다.
- 생성된 `CAN-001` 의 `unverified`/`insufficient-evidence` 와 run outcome `no-actionable-candidates` 는 **같은 실행의 같은 사실을 후보 층과 run 층에서 각각 표현한 것** 이다. 후보가 actionable 이 아니므로 outcome 이 `no-actionable-candidates` 가 된 것이며 인과가 하나다.
- 따라서 이것은 **"허용 범위의 실제 후보 사례"와 "후보 없음 사례"의 독립된 두 실증이 아니다.**
- 기준 7 의 후속 검증에서는 (가) 실제 저장소의 근거에 연결된 후보 판정과 (나) 후보 없음 판정을 독립적으로 확인한다. 원문은 actionable 또는 ready 후보 발견을 강제하지 않으며, 그런 발견을 스킬의 성공 조건으로 추가하지 않는다. 실제 결함이 확인되지 않으면 unverified를 유지한다. 단일 unverified 기록을 독립된 두 사례로 중복 계산하지 않고, 빈 records와 no-actionable 결과도 구분한다. 부족한 실사례 범위는 #82 통합 검증에서 명시적으로 다룬다.

## 6. 미충족 조건 (root 가 push·PR·merge 판단 전에 알아야 할 것)

| # | 미충족 항목 | 성격 | 영향 |
|---|---|---|---|
| 1 | **완료 기준 7 미충족** | 실사례 부족 | § 5.3. 독립된 양성·음성 두 실사례가 없다. **#79 자동 close 를 보류하는 직접 사유다** |
| 2 | **403 분류 경로가 라이브 미검증** | 원리적 한계 | 정상 인증 상태의 공개 저장소는 403 을 내지 않는다. I5 의 권한 거부/rate limit 분류는 오프라인 테스트(두 transport, 헤더 12조합)로만 검증됐다. 403 을 인위적으로 유발하는 것은 승인 범위 밖이다 |
| 3 | **CODE-002·I8 의 실패 경로가 라이브 미검증** | 원리적 한계 | GitHub 이 형식 불일치 2xx 를 보내지 않고, clone 정리 실패는 파일시스템을 일부러 망가뜨려야 한다. 부정 확인(오탐·오차단 없음)만 얻었다 |
| 4 | **`CODE-101` 미해결** | 후속 승인 필요 | 403 이 파싱 가능한 음수 `Retry-After` 와 유효한 `Remaining: 0`/`Reset` 를 함께 가지면 재시도는 하되 지연이 0.0초가 된다. Spec R2.2 가 `Retry-After` 우선을 명시하므로 고치려면 Spec 변경이 필요하다. 경계(`MAX_RETRIES` 3, ≤300초, 예산)는 유지된다 |
| 5 | **`CODE-102` 미해결** | 후속 승인 필요 | `read_failures` 가 상한 없는 배열이고 clone root 밖 walk 오류 경로가 `.` 로 합쳐진다. 이번 라이브에서는 `read_failures` 가 빈 배열이어서 발현하지 않았다 |
| 6 | **`CODE-103` 미해결** | 후속 승인 필요 | 계약 스위트가 `sys.path` 조작으로 행위 스위트 헬퍼를 import 해 결합돼 있다 |
| 7 | **`#82` 공용 배포 검증 미수행** | 별도 이슈 | `chezmoi apply` 로 `~/.codex/skills` 에 배포하고 설치본에서 동작을 확인하는 단계는 `#82` 다. 스킬은 여전히 **미푸시·미배포** 다. § 3.1 참조 |
| 8 | **패턴 적용 가능성·실제 결함 미확인** | 조사 범위 | § 4.1. 이번 단서 집합은 다른 저장소 경로를 그대로 썼다. 대상 구조에 맞춘 단서로 다시 조사해야 판정 가능하다 |
| 9 | **중복 항목 미검토** | 승인 범위 밖 | 질의 hit 합계 47(고유 46)을 개별 검토하지 않았다. 중복 여부 미확정으로 기록했다 |
| 10 | **다른 저장소·패턴으로의 일반화 미검증** | 표본 한계 | 라이브 표본은 저장소 1개 · 패턴 1개다 |

## 7. root 오케스트레이터에게 넘기는 판단 사항

1. **구현 인프라는 merge 가능하다.** 완료 기준 8개 중 1·2·3·4·5·6·8 이 충족이고, 계약·게이트·재검증·안전 경계·보안 분리·픽스처·산출물 형태가 코드와 62개 오프라인 테스트, 그리고 이번 라이브 실행으로 확인됐다. 라이브 후 회귀도 62 · 30 · 108 전부 OK 다.
2. **다만 #79 자동 close 는 보류한다.** 완료 기준 7(허용 범위 실제 후보 사례와 후보 없음 사례)이 미충족이며, 이번 단일 실행은 § 5.3 대로 독립된 두 실사례가 아니다. PR 본문에 `Refs #79` 를 쓰고 `Closes`·`Fixes` 를 쓰지 않아야 한다.
3. **후속 실사례 검증은 `#82` 통합에서 추적한다.** 배포된 설치본의 실제 후보 판정 및 후보 없음 경로를 각각 검증하고 기준 7과 대조한 뒤 #79 close를 판단한다. actionable 후보를 반드시 발견해야 한다는 요구로 확대하지 않는다.
4. **§ 6 의 2·3 은 원리적 한계** 이므로 코드 수정으로 해소되지 않는다. 결함이 아니라 검증 범위의 성격으로 다뤄야 한다.
5. **§ 6 의 4·5·6(`CODE-101`~`CODE-103`)** 은 이번 승인에서 수정이 금지됐다. PR 에 포함할지, 후속 이슈로 분리할지는 root 결정이다.
6. **이 세션은 commit·push·PR 생성·merge 를 수행하지 않았다.** 다만 개정 시점에 브랜치에 로컬 커밋 `983a2aa` 가 존재한다. 이 세션이 만든 것이 아니며 § 3.1 에 실측을 적었다. 푸시는 되지 않았고 `docs/development/**` 와 루트 `AGENTS.md` 는 그 커밋에 포함되지 않았다. 남은 push·PR·merge 판단은 root 의 것이다. **공개 원격 원본은 커밋하지 않는다.**

## 8. 이 실행이 하지 않은 것

기존 코드 수정, `CODE-101`~`CODE-103` 수정, 과거 보고서·상태·원시 라이브 artifact 변경, 타 워크트리·전역 설치본 수정, 대상 저장소 코드 실행, 의존성 설치, 승인 상한(115) 초과 요청, GET 이외 요청, ready 판정 강제, 후보 억지 생성, commit·push·PR·merge·`chezmoi apply`·배포, #80 이동.
