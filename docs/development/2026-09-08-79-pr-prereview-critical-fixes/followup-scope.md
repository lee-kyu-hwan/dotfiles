# #79 사전 리뷰 차단 문제 수정 — 작업 범위와 지적 목록 (압축 대비 기록)

이 문서는 컨텍스트 압축 이후에도 작업을 이어갈 수 있도록 **먼저** 기록한 것이다. 기록 시각 2026-09-08(KST). 작업 경로는 `/Users/lee-kyu-hwan/code/dotfiles__worktrees/79-feat-contribution-candidate-verifier`, 브랜치 `79-feat/contribution-candidate-verifier`, 기준 커밋 `6d60011cbdaead7946b191d3f12029eef5c141c8`.

## 실행 연결 (역사 보존)

| 실행 | ID / 경로 | 상태 | 이 작업과의 관계 |
|---|---|---|---|
| 1차 설계·계획 | `.claude/quality-state/20260906T125225Z-79-…-ec840cba`, 문서 `docs/development/2026-09-06-79-verifying-open-source-contribution-candidates/` | NEEDS_REDESIGN (`REVIEW_LIMIT_EXHAUSTED:plan`) | 보존. 편집 금지. `preserved-run.sha256` 로 불변 판정 |
| 2차 재설계·구현 | `.claude/quality-state/20260906T194200Z-79-verifying-open-source-contribution-ca-f0ac72ad`, 문서 `docs/development/2026-09-07-79-verifying-open-source-contribution-candidates-plan-redesign/` | **COMPLETED** (spec 2 / plan 2 / code 3, 마지막 코드 리뷰 PASS 91, 지문 `f07741b419fca7f227af3a7c2521482f1f7d2bc6475d84430236284feb4889e1`) | 보존. 라운드 한도·이력 수정 금지. 종결 후 `report.md` 편집으로 현재 지문은 `c4c29870ae2d13d224551e9498f4a69be057432cbd877e2b706033c12ab7a05b` 로 달라진 상태였다 |
| PR 사전 리뷰 | 원문 `pre-review-summary.md`(이 디렉터리, 임시 원본과 SHA-256 동일 `6940af1d…`), 초안 `pr-draft-title.txt`·`pr-draft-body.md` | 완료, 판정 **PR 준비 차단** | 이 작업의 입력 |
| 3차(이번) 수정 실행 | 새 quality-goal 실행 — ID 는 아래 § 진행 로그에 기록 | 진행 | Critical 4 + 관련 Important 최소 수정 |

원문 임시 경로(참조용, 사라질 수 있음): `/private/tmp/claude-501/-Users-lee-kyu-hwan-code-dotfiles--worktrees-79-feat-contribution-candidate-verifier/5e4ac2c2-0d4e-48e1-98ff-bd54897d9029/scratchpad/pr-prereview-20260908/`.

## 승인 범위와 금지 사항 (이번 작업)

승인: 사전 리뷰 차단 문제 수정, 실패 회귀 테스트 → 최소 수정 → 전체 로컬 테스트 → 독립 코드 리뷰 순서의 새 quality-goal 실행, `#79` 자체 로컬 테스트 실행, 이 문서 영역에 후속 문서 작성.

금지: 추가 GitHub 요청·`discover` 라이브 재실행·대상 저장소 코드 실행·의존성 설치, commit·push·PR 생성·merge·`chezmoi apply`·배포, GitHub 이슈·댓글 작성, `main`·다른 워크트리·전역 설치본 수정, 기존 실행의 상태·리뷰·라운드 한도 수동 조작, 종결 후 보고서 수정으로 지문 재불일치.

유지해야 하는 한계 주장: `discover` 실경로만 1회 라이브 검증됐다. `assessment`·`record`·`recheck` 실경로는 미검증이고 `CAN-*` 도 없다. `#79` 전체 완료·배포 완료를 주장하지 않는다.

## Critical 4건 (모두 사전 리뷰에서 코드 직접 확인됨)

- **C1 예산 소진 시 조합 누락** — `dot_codex/skills/verifying-open-source-contribution-candidates/scripts/verify_candidates.py:1758`(저장소 단계 `except BudgetExhausted` 가 자기 저장소 패턴만 `failed_scopes` 에 넣음), `:1786`(`if not exhausted:` 로 조합 단계 전체 건너뜀). 저장소 A 완주 후 B 소진 시 A 의 조합은 `records`·`failed_scopes`·`skipped_by_cap` 어디에도 없고 A 는 manifest 에 `outcome: checked, reason: null`. Spec R3.5·R3.6 위반. 재현 픽스처 `tests/fixtures/budget/unstarted/case.json`(저장소 단계 4 + 정책 20 = 24, 예산 24). 기존 테스트 `tests/test_verify_candidates.py:2129-2135` 와 `:2004-2013`(mixed/AC-33)은 종료 코드와 `repositories[].outcome` 만 단정해 잡지 못한다.
- **C2 거부 분기를 검증하지 않는 테스트** — 게이트 `scripts/verify_candidates.py:2794`(`if record is None or combo in forbidden_combos`), `forbidden_combos` 구성 `:2779-2783`. 테스트 `tests/test_verify_candidates.py:1762` 가 헬퍼에 최상위 `"skipped"`·`"failed"` 키를 넘기는데 실제 필드명은 `skipped_by_cap`·`failed_scopes`(헬퍼 `tests/test_verify_candidates.py:362-379`, 전달부 `:519-525`)이고 동시에 `records=[]` 이라 거부가 `record is None` 분기에서 발생한다. `forbidden_combos` 블록을 지워도 44개가 통과한다. Spec AC-28 의 두 문구 실질 미충족.
- **C3 정책 `request-failed` 가 ready 를 차단하지 않음** — 생산자 `scripts/verify_candidates.py:1101`·`:1148`(`status: request-failed`), 소비자는 `_policy_sha_values:2042` 와 `_reobserved_policy_checks:3018` 뿐이며 둘 다 `found` 만 본다. 파일 전체에 `status == "request-failed"` 를 읽는 코드가 없다. 해시 대조는 `found: true` 주장에만 발동(`:2185-2191`). 결과적으로 조회 실패가 "정책 없음" 으로 세탁되어 `issue-ready` 까지 갈 수 있다. 이 `status` 필드는 직전 LIVE-1 수정으로 추가된 것이다.
- **C4 recheck 실패 뒤 이전 ready·검증 시점 유지** — `scripts/verify_candidates.py:3189-3216`. 세 실패 경로(선행 소진 단축, `except BudgetExhausted`, `observation is None`) 모두 레코드를 그대로 `output_records` 에 넣는다. 스냅숏 추가 없음, `blocking_gaps` 갱신 없음, `status`·`verified_at`·`next_recheck_required` 불변. 원인 문자열은 run 경고에 병합되지만 후보 귀속이 없다. **단순 경고 추가만으로 해결됐다고 하지 않는다** — 상태 차단 규칙이 필요하다.

## Important 13건 (분류 대상)

I1 `record` 단계가 discovery 경고를 버리고 manifest 를 `complete` 로 단정 — `:2898-2910`, `CANDIDATE_FIELDS` 에 `warnings` 없음. (`failed_scopes`·`method_limitations` 는 승계)
I2 `render` 가 알 수 없는 run 상태를 `complete` 로 기본값 — `:2582-2583`, `--manifest` 는 선택 인자.
I3 파싱 실패 응답이 `{"message": …}` 로 합성돼 실제 데이터로 소비 — `_payload_from_body:590-594`, `_decode_policy_payload:1060-1074`, `_community_profile_files:1018-1023`.
I4 `get_json` 이 `ValueError` 를 함께 잡아 허용목록 위반을 `transport-error` 로 위장 — `:671`, 가드 `run_child:403-413`.
I5 403 재시도로 예산 4배·최대 15분 대기 — `_retryable:615-616`, `MAX_RETRIES=3`, `MAX_RETRY_DELAY_SECONDS=300`(`:24-25`), 지연 `:597-613`. 계약은 code search 403 을 `available: false` 정상 경로로 규정(`references/github-verification-contract.md:42`).
I6 검색 단서가 이스케이프 없이 `q` 에 삽입 — `:1330`, `:1383`, 검증 `:812-816`.
I7 형식 어긋난 `--discovery` 가 트레이스백·종료 코드 1 — `run_record:2765-2767`, `main:3344-3346`. 계약은 2 를 잘못된 입력에 배정.
I8 `finally` 무보호 `rmtree` 가 산출물 유실 유발 — 정리 `:1875-1879`, 쓰기 `:1949-1950`, `_cleanup_clone_sessions` 에 `raise TypeError` 와 무보호 `shutil.rmtree`.
I9 미신뢰 텍스트 `sha256` 이중 의미 — `_untrusted_text:975-982` 는 `text` 해시, 정책 경로 `:1127`·`:1166` 이 전체 내용 해시로 덮어씀.
I10 문서 5곳이 C1 과 반대 보증 — `docs/development/2026-09-07-…-plan-redesign/redesign.md:24`·`:34`, `spec.md:62`·`:63`, `dot_codex/skills/…/SKILL.md:14`. Spec 본문 편집은 `report.md` 가 고정한 digest `b60eb22c…` 를 무효화하므로 개정 노트/후속 문서로 처리.
I11 `static_search` 가 읽기 실패를 `skipped_files` 로 접고 `available: true` 유지 — `:471-525`. (사전 리뷰에서 [R] 미검증)
I12 형식 어긋난 2xx 검색 payload 에도 `duplicate_search.complete: true` — `:1337`, `_recheck_duplicate_search:2989`. (미검증)
I13 clone 실패가 `clone-failed` 하나로 접히고 git stderr 폐기 — `clone_repository:453-460`, `_static_record:1617-1635`. (미검증)

## 이월 2건 재평가 (보존)

- **CODE-005** — 실재하나 차단 사유 아님. `:1135` 의 `entry_count = len(response.payload)` 가 `:1111-1115` 의 필터된 `names` 와 어긋날 수 있으나, `record` 게이트가 묶는 값은 `sha256` 뿐이라 게이트 오판은 없고 서술 필드만 부정확. `len(names)` 한 줄 수정 권장.
- **CODE-006** — 결함 아님. Spec R3.2 의 중괄호 목록은 폐쇄 집합이 아니며(같은 문장이 목록 밖에서 `keyword_hits` 를 의무화) 후보 레코드처럼 "exactly these" 로 강제하는 코드도 없음. 정확한 프레이밍은 "Spec R3.2 가 구현을 더 이상 서술하지 못함(`status`·`entry_count` 누락)" 이고 배포 계약 문서는 11 키를 정확히 문서화한다.

## 진행 로그

- 2026-09-08: 원문 보존(`pre-review-summary.md`, SHA-256 `6940af1d…`)과 이 범위 문서 작성. 다음 단계는 설치 quality-goal 버전 확인과 새 실행 개시.

## 재현 결과 (3차 실행, 오프라인·보존 fixture 만 사용)

재현 스크립트는 저장소 밖 세션 임시 경로에서 실행해 작업트리 지문을 오염시키지 않았다. GitHub 요청·`discover` 라이브 실행·대상 저장소 코드 실행·의존성 설치는 없었다. 파이썬은 `/opt/homebrew/bin/python3` (3.14.7).

### Critical 4건 — 4건 모두 재현

- **C1 재현됨.** 저장소 2개(`example-repository-completed`, `example-never-started`), 예산 24. 종료 3, `status: partial`, manifest `repositories` = `[(completed, checked), (never-started, budget-exhausted)]`. `records: []`, `failed_scopes` 는 `never-started/PAT-001` 한 건, `skipped_by_cap: []`. 즉 **완주한 저장소의 조합 `(example-repository-completed, PAT-001)` 이 세 구획 어디에도 없다.** 산출물만 보면 그 조합을 검증했는지 누락했는지 알 수 없다.
- **C2 재현됨.** (a) 테스트 그대로(`records=[]` + 최상위 `skipped` 키) → 종료 2, 사유는 `assessments[0]: combination is absent, skipped, or failed`, 그러나 `discovery.skipped_by_cap` 은 `[]` 이고 문서에 읽히지 않는 `skipped` 키만 추가돼 있다. (b) 레코드를 넣고 같은 `skipped` 키를 주면 **종료 0** — 그 키가 아무 것도 거부하지 않음을 증명한다. (c) 계약상 올바른 `skipped_by_cap` 키로 주면 종료 2. 따라서 현재 테스트는 `record is None` 분기만 밟고 `combo in forbidden_combos` 분기는 한 번도 실행되지 않는다.
- **C3 재현됨.** `policy_files[CONTRIBUTING.md].status` 를 `request-failed`(조회 실패) 로 둔 discovery 와, `policy_checks.contributing.found=false` + 12개 readiness 전부 `confirmed` + `status: pr-ready` 인 assessment → **종료 0, `pr-ready` 레코드 생성**. `status` 를 `absent`(확인된 부재) 로 바꿔도 결과가 완전히 동일하다. 게이트가 "없음" 과 "모름" 을 구분하지 못한다.
- **C4 재현됨.** `pr-ready` 후보 1건에 대해 recheck 를 두 가지 실패 응답으로 실행: `/repos/{r}/commits/main` 503, `/repos/{r}` 503. 두 경우 모두 종료 3, run `status: partial`, run 경고에 `request-failed:…:http-503` 과 `recheck-failed` 가 남지만 **후보 레코드는 바이트 동일**(`status: pr-ready`, `verified_at: 2000-01-01T00:00:00Z` 그대로, `next_recheck_required: true`, `verification_history` 길이 1 유지, `blocking_gaps: []`). 게다가 run `outcome` 은 `actionable-candidates` 로 남는다. 재검증이 전혀 성공하지 못한 실행이 "조치 가능한 후보 있음" 으로 보고된다.

### Important 13건 — 분류

판정 기준: (1) 재현 여부, (2) ready 게이트나 산출물 구획에 도달하는지, (3) Critical 과 원인 공유 여부, (4) 최소 수정 가능 여부. **"모름/실패 근거가 검증된 부정으로 세탁돼 ready 까지 도달한다"** 는 원인을 Critical 과 공유하는 항목만 이번 범위에 넣는다.

| ID | 재현 | 게이트 도달 | Critical 원인 공유 | 판정 |
|---|---|---|---|---|
| I1 record 가 discovery 경고를 버리고 manifest 를 `complete` 로 단정 | 재현(코드 `:2898-2910` 하드코딩) | 예 — 부분 실패가 산출물에서 사라짐 | C1·C4 | **포함** |
| I2 render 가 알 수 없는 run 상태를 `complete` 로 | 재현 — `status: "who-knows"` 가 `complete` 로 렌더, 원문 미표시. `--manifest` 없이도 종료 0 | 예 — 사람이 읽는 최종 산출물 | C1·C4 | **포함** |
| I3 파싱 실패 응답이 실제 내용으로 소비 | 재현 — `_payload_from_body("<html>502 Bad Gateway</html>")` → `{"message": "<html>502 Bad Gateway</html>"}`; `_decode_policy_payload` 가 이를 35바이트 내용으로 반환 | 예 — 오류 페이지가 `found: true` + sha256 로 기록돼 정책 해시 대조를 통과 | C3 | **포함**(정책 경로에서 파싱 실패를 `request-failed` 로 판정하는 최소 범위) |
| I4 허용목록 위반이 transport-error 로 위장 | 재현 — 가드 `ValueError` 가 상태 599 `{"message": "transport-error"}` 로 반환, 예산 4 소모, 대기 `[60,120,240]`=420초 | 아니오(진단) | C3 계열(실패 세탁) | **포함**(가드 예외를 재시도 대상에서 분리) |
| I5 403 재시도로 예산 4배·420초 대기 | 재현 — 403/429/503 모두 예산 4, 총 420초 대기. 계약은 403 을 `forbidden`/`http-403` 판정된 접근 실패로 규정 | 아니오 | 부분 | **보류·보고** — 재시도 대상 상태 집합 변경은 라이브 검증된 예산 계약 변경이라 승인 필요 |
| I6 검색 단서가 이스케이프 없이 `q` 에 삽입 | 재현 — 단서 `x" is:open OR repo:attacker/evil "y` 로 질의가 `repo:example-org/example-repo "x" is:open OR repo:attacker/evil "y" is:issue is:open` 이 됨 | **예 — 다른 저장소를 검색하고도 `complete: true`** | C3(모름→검증된 부정) | **포함. 심각도 상향** — 사전 리뷰의 Important 는 과소평가다. 단서는 외부 PR 텍스트에서 유래하므로 미신뢰 입력이 질의 범위를 벗어난다 |
| I7 형식 어긋난 `--discovery` 처리 | **부분 재현·주장 수정** — 사전 리뷰가 든 세 형태는 종료 2/0 이었다. 실제 재현되는 것은 (a) `repository_node_id` 없는 레코드 → `KeyError` 트레이스백·종료 1, (b) `skipped_by_cap` 이 문자열이면 **조용히 종료 0** 이며 거부 분기가 무력화 | 예 — (b) 는 C2 게이트를 통째로 무력화 | C2 | **포함**(discovery 문서 형태 검증 → 종료 2) |
| I8 `finally` 무보호 `rmtree` | 코드상 실재(`:1875-1879` 가 `:1949-1950` 쓰기보다 앞) | 아니오 | 아니오 | **보류·보고** — 독립 견고성 수정 |
| I9 미신뢰 텍스트 `sha256` 이중 의미 | 재현 — `_untrusted_text` 는 발췌 해시, 정책 경로가 전체 내용 해시로 덮어씀 | 아니오 — 게이트는 전체 내용 해시로 일관 | 아니오 | **보류·보고** — 필드 의미 문서화 문제 |
| I10 문서 5곳이 C1 과 반대 보증 | 실재 | — | C1 | **부분 포함** — 이번에 바꿀 수 있는 `SKILL.md`·`references/verification-contract.md` 만 수정. 1·2차 실행 문서는 불변 이력이라 이 문서로 처리 |
| I11 `static_search` 가 읽기 실패를 접고 `available: true` 유지 | 재현(코드 `:471-525` 가 항상 `available: True, error: None`) | 약함 — `skipped_files` 는 노출됨 | 아니오 | **보류·보고** — 정적 검색 결과에 새 한계 채널이 필요한 기능 확장 |
| I12 형식 어긋난 2xx 검색 payload 에도 `complete: true` | 재현 — 200 + 비 dict payload → `complete: True`, 경고 없음, `total_count: None`, `items: []` | **예 — `open_and_closed_searched` 확정을 뒷받침** | C3 | **포함** |
| I13 clone 실패가 `clone-failed` 하나로 접히고 git stderr 폐기 | 코드상 실재(`:451-460`) | 아니오 | 아니오 | **보류·보고** — 진단 품질 |

포함 8건(I1·I2·I3·I4·I6·I7·I10·I12) + Critical 4건, 보류·보고 5건(I5·I8·I9·I11·I13).

### 이월 2건 처리

- **CODE-005 포함** — `:1135` `entry_count = len(response.payload)` 를 필터된 `len(names)` 로. 산출 계약에 문서화된 필드의 값이 틀린 한 줄 결함이며 게이트 영향은 없다.
- **CODE-006 변경 없음** — 결함이 아니라는 재평가를 그대로 보존한다.

### 초기 dirty 경로 해석 (편차로 기록)

`capture-baseline` 이 기록한 초기 dirty 경로 4개는 모두 #79 의 미커밋 산출물이다. 이 중 `dot_codex/skills/verifying-open-source-contribution-candidates/` 는 **이번 승인 범위의 수정 대상 자체**이고 `docs/development/2026-09-08-79-pr-prereview-critical-fixes/` 는 이번 실행의 문서 디렉터리다. 따라서 "초기 dirty 경로를 바이트 동일하게 보존한다" 는 규칙은 1·2차 실행 문서 디렉터리 2개에만 적용하고(`preserved-run.sha256` 로 검증), 나머지 2개는 작업 범위로 취급한다. 이 해석을 보고서 편차 절에 남긴다.
