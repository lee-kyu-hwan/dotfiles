# PR Review Summary

리뷰 대상: `79-feat/contribution-candidate-verifier` 워크트리의 미추적 44개 파일(신규 스킬 32 + 이번 실행 문서 7 + 이전 실행 보존 문서 5). `git diff`·`git diff --cached` 는 비어 있고 PR 은 아직 없다. 절차는 `~/.codex/skills/pr-review-toolkit/SKILL.md`, upstream 은 `~/.codex/pr-review-toolkit-claude` 만 사용했다. 분석 역할 다섯(code, tests, comments, errors, types)을 순차 실행했고 `simplify` 는 제외했다. `[V]` 는 오케스트레이터가 코드에서 직접 재확인한 항목, `[R]` 은 리뷰어 보고만 있는 항목이다.

## Critical Issues

- **[code-reviewer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer] [V] 예산 소진 시 먼저 완주한 저장소의 조합이 세 목록 어디에도 남지 않는다** — `dot_codex/skills/verifying-open-source-contribution-candidates/scripts/verify_candidates.py:1758` (저장소 단계 `except BudgetExhausted` 가 자기 저장소 패턴만 `failed_scopes` 에 넣음), `:1786` (`if not exhausted:` 로 조합 단계 전체 건너뜀). 저장소 A 완주 후 B 가 소진되면 A 의 조합은 `records`·`failed_scopes`·`skipped_by_cap` 어디에도 없고, A 는 manifest 에 `outcome: checked, reason: null` 로 남는다. 종료 코드는 B 때문에 3 이라 겉보기 신호만 맞고 무엇이 유실됐는지 열거할 수 없다. Spec R3.5·R3.6 와 SKILL.md 의 "부재 증거를 부정 결론으로 바꾸지 않는다" 를 정면으로 어긴다. 저장소의 자체 픽스처 `tests/fixtures/budget/unstarted/case.json` 이 이 상황을 결정적으로 재현한다(저장소 단계 비용 4 + 정책 20 = 24, 예산 24).
- **[pr-test-analyzer] [V] `skipped_by_cap`/`failed_scopes` 조합 거부 게이트가 한 번도 실행되지 않는다** — 게이트는 `scripts/verify_candidates.py:2794` (`if record is None or combo in forbidden_combos`). 테스트 `tests/test_verify_candidates.py:1762` 는 `write_record_inputs(..., **discovery_changes)` 로 최상위 `"skipped"`·`"failed"` 키를 넣지만 실제 필드명은 `skipped_by_cap`·`failed_scopes` 이고(`tests/test_verify_candidates.py:362-379` 의 헬퍼가 그 이름을 씀), 동시에 `records=[]` 를 넘기므로 거부는 `record is None` 분기에서 발생한다. `forbidden_combos` 블록을 삭제해도 44개 테스트가 모두 통과한다. Spec AC-28 의 두 문구("`skipped_by_cap` 조합 평가는 `2`", "`failed_scopes` 조합 평가는 `2`")가 실질적으로 미충족이며, 위 항목과 겹치면 "선언적으로 거부한 조합에 후보를 만드는" 정확한 실패 경로가 열린다.
- **[silent-failure-hunter, type-design-analyzer] [V] 정책 결과의 `status` 3-상태가 기록만 되고 읽히지 않아 조회 실패가 부재로 세탁된다** — 생산자 `scripts/verify_candidates.py:1101,1148`, 소비자는 `_policy_sha_values:2042` 와 `_reobserved_policy_checks` 뿐이며 둘 다 `found` 만 본다. 파일 전체에 `status == "request-failed"` 를 읽는 코드가 없다. 따라서 CONTRIBUTING.md 가 503 으로 실패해도 평가자가 `policy_checks.contributing.found = false` + `readiness_checks.policy_files_reviewed = confirmed` 를 주장하면 게이트를 통과해 `issue-ready` 가 된다(해시 대조는 `found: true` 주장에만 발동, `:2185-2191`). 이 `status` 필드는 직전 LIVE-1 수정으로 추가된 것이다.
- **[silent-failure-hunter] [V] `recheck` 실패 후에도 후보가 이전 ready 상태를 그대로 주장한다** — `scripts/verify_candidates.py:3189-3216`. 세 실패 경로(선행 소진 단축, `except BudgetExhausted`, `observation is None`) 모두 `output_records.append(record)` 로 레코드를 **그대로** 내보낸다. 스냅숏 추가 없음, `blocking_gaps` 갱신 없음, `status`·`verified_at`·`next_recheck_required` 불변. `recheck` 는 SKILL.md 6단계가 외부 제안 직전 필수로 규정한 게이트이므로, 재확인되지 않은 근거 위에서 후보가 계속 ready 로 보인다. (정정: 원인 문자열은 run 경고에 병합된다. 빠지는 것은 후보 귀속과 레코드 갱신이다.)

## Important Issues

- **[silent-failure-hunter] [V] `record` 단계가 discovery 실패 근거를 버리고 manifest 를 `complete` 로 단정한다** — `scripts/verify_candidates.py:2898-2910` 이 `"warnings": []`, `"status": "complete"` 를 하드코딩하고 모든 저장소를 `{outcome: "checked", reason: None}` 으로 적는다. `CANDIDATE_FIELDS` 에 `warnings` 가 없어 후보 레코드로도 넘어가지 않는다. (완화: `failed_scopes`·`method_limitations` 는 discovery 에서 승계한다.)
- **[silent-failure-hunter] [V] `render` 가 알 수 없는 run 상태를 `complete` 로 기본값 처리한다** — `scripts/verify_candidates.py:2582-2583`. `--manifest` 는 `render` 의 선택 인자이므로 manifest 없이 렌더하면 사람이 읽는 보고서가 근거 없이 `Run status: complete` + `Warnings: none` 을 단정한다. (`outcome` 은 레코드로 재계산하는데 `status` 만 낙관적 기본값.)
- **[silent-failure-hunter, type-design-analyzer] [V] 파싱 실패 응답이 그럴듯한 payload 로 합성돼 실제 데이터로 소비된다** — `_payload_from_body:590-594` 가 `{"message": ...}` 를 반환하고, 모든 소비자 가드는 `isinstance(payload, dict)` 다. `_decode_policy_payload:1060-1074` 는 base64 `content` 가 없으면 payload 를 JSON 직렬화해 "내용" 으로 삼으므로 정책 파일이 `status: found` + 그 합성물의 해시로 기록된다. `_community_profile_files:1018-1023` 은 여섯 키를 모두 `False` 로 만들고 `stages_completed` 에 `community_profile` 을 추가한다.
- **[silent-failure-hunter] [V] `get_json` 이 `ValueError` 를 함께 잡아 실행 파일·GET 허용 목록 위반을 `transport-error` 로 위장한다** — `scripts/verify_candidates.py:671` 의 `except (OSError, subprocess.SubprocessError, ValueError)`; `run_child:403-413` 은 그 세 위반에 평범한 `ValueError` 를 쓴다. 보안 가드의 실패가 네트워크 오류처럼 보이고 재시도로 예산까지 소비한다.
- **[code-reviewer, silent-failure-hunter] [V] 403 이 재시도 대상이라 예상된 code search 실패가 예산 4배·최대 15분 대기를 유발한다** — `_retryable:615-616`, `MAX_RETRIES = 3`, `MAX_RETRY_DELAY_SECONDS = 300.0`(`:24-25`), 지연 우선순위 `:597-613`. `references/github-verification-contract.md:42` 는 code search 403 을 `available: false` 로 끝나는 정상 경로로 규정한다.
- **[code-reviewer] [V] 검색 단서가 이스케이프 없이 `q` 에 삽입된다** — `scripts/verify_candidates.py:1330`, `:1383`. `search_clues` 는 문자열 배열 여부만 검증되고(`:812-816`) 원격 PR 텍스트에서 파생한 값이다. 큰따옴표를 포함한 단서는 인용을 깨고 추가 `repo:` 한정자를 주입할 수 있어, 계약이 금지한 "원격 텍스트가 option 이 되는" 상태가 된다.
- **[code-reviewer, silent-failure-hunter] [V] 형식이 어긋난 `--discovery` 가 트레이스백과 종료 코드 1 로 끝난다** — `run_record:2765-2767` 은 `schema_version` 과 `records` 배열만 확인한 뒤 필수 키를 첨자 접근하고, `main:3344-3346` 은 `CliInputError` 만 잡는다. 계약은 1 을 검증 실패, 2 를 잘못된 입력에 배정한다. 트레이스백은 `_write_stderr` 의 레댁션 지점도 우회한다.
- **[silent-failure-hunter] [V] `finally` 의 무보호 `rmtree` 가 실행 전체의 감사 기록을 날릴 수 있다** — 정리는 `scripts/verify_candidates.py:1875-1879` 의 `finally` 에서, 출력 쓰기는 그 뒤 `:1949-1950` 에서 일어난다. `_cleanup_clone_sessions` 는 `TypeError` 를 던지고 `shutil.rmtree` 를 감싸지 않는다. 삭제 실패 시 예산을 다 쓴 성공적 discovery 가 산출물 없이 끝난다.
- **[type-design-analyzer, comment-analyzer] [V] 미신뢰 텍스트 객체의 `sha256` 이 두 가지 뜻을 갖는다** — `_untrusted_text:975-982` 는 저장된 `text` 를 해시하지만 정책 경로는 `:1127`, `:1166` 에서 전체 내용 해시로 덮어쓴다. `truncated: true` 일 때 `sha256` 이 옆의 `text` 를 인증하지 못한다. 계약 문서는 어느 쪽인지 말하지 않는다.
- **[comment-analyzer] [V] 문서 다섯 곳이 위 Critical 1 과 반대되는 보증을 한다** — `docs/development/2026-09-07-…-plan-redesign/redesign.md:24`(규칙 5)·`:34`(사례 B′), `spec.md:62`(R3.5)·`:63`(R3.6), `dot_codex/skills/…/SKILL.md:14`(5단계의 네 버킷). Spec 본문 편집은 `report.md` 가 고정한 digest `b60eb22c…` 를 무효화하므로 개정 노트나 후속 이슈로 남기는 것이 옳다.
- **[silent-failure-hunter] [R] `static_search` 가 읽기 실패를 `skipped_files` 하나로 접고 `available: true` 를 유지한다** — `scripts/verify_candidates.py:471-525`. 클론 전체가 읽히지 않아도 "단서 없음" 과 같은 근거 상태가 된다.
- **[silent-failure-hunter] [R] 형식이 어긋난 2xx 검색 payload 에도 `duplicate_search.complete: true` 가 유지된다** — `scripts/verify_candidates.py:1337`(및 `_recheck_duplicate_search:2989`). `complete` 는 `open_and_closed_searched` readiness 주장의 유일한 가드다.
- **[silent-failure-hunter] [R] clone 실패가 맥락 없는 `clone-failed` 하나로 접히고 git stderr 는 버려진다** — `clone_repository:453-460`, `_static_record:1617-1635`.

## Suggestions

- **[code-reviewer] CODE-005 는 결함이나 차단 사유가 아니다** — `scripts/verify_candidates.py:1135` 의 `entry_count = len(response.payload)` 가 `:1111-1115` 의 필터된 `names` 와 어긋날 수 있다. 소비 측을 전수 확인하면 `record` 게이트가 묶는 값은 `sha256` 뿐이므로 게이트 오판은 없고 서술 필드만 부정확하다. `len(names)` 한 줄 수정 권장.
- **[code-reviewer, comment-analyzer] CODE-006 은 결함이 아니다** — Spec R3.2 의 중괄호 목록은 폐쇄 집합이 아니며(같은 문장이 목록 밖에서 `keyword_hits` 를 의무화한다) 후보 레코드처럼 "exactly these" 로 강제하는 코드도 없다. 다만 프레이밍은 "문서 대 문서" 가 아니라 "Spec R3.2 가 구현을 더 이상 서술하지 못함(`status` 누락)" 이 정확하다. `report.md:209` 문구 조정 권장.
- **[type-design-analyzer] 세 목록 분할을 실행 가능한 불변식으로 만들 것** — discovery 딕셔너리 조립 직전에 `records ⊎ skipped_by_cap ⊎ failed_scopes == selected_combinations` 를 검사해 위반 시 즉시 실패. `run_discover` 의 열 몇 개 `continue`/`break` 경로에서 *다음* 결함을 잡는 값이 크다.
- **[type-design-analyzer] 중복 표현을 하나로 줄일 것** — 정책 결과에서 `found` 를 `status` 의 파생으로 만들고(단일 출구에서 `found = status == "found"`), 미신뢰 텍스트 `sha256` 은 항상 `text` 를 해시하도록 두 덮어쓰기 줄을 삭제.
- **[type-design-analyzer] `_missing_assessment` 의 `locus: ""` 자리표시자가 영구 중복을 만든다** — 나중에 실제 locus 로 평가되면 다른 `candidate_key`·새 `CAN-` id 가 되어 자리표시자가 superseded 되지 않는다.
- **[type-design-analyzer] `candidate_key` 의 빈 `node_id` 는 discovery 경계에서 실패시켜야 한다** — 현재는 `validate_candidates_document:2360` 이 `record` 시점에 거부하므로 디스크에는 남지 않지만, 사용자는 이미 평가 한 사이클을 낭비한다. `head_sha` 는 같은 함수에서 모델링된 상태로 잘 처리된다.
- **[comment-analyzer] 삭제 함정 두 곳** — `scripts/verify_candidates.py:23` 의 `# api_version default` 주석은 `tests/test_skill_contract.py:64` 의 날짜 스캔 예외를 만드는 유일한 장치다(3,350행 중 유일한 인라인 주석). `SKILL.md:19-23` 의 경계 문장은 `tests/test_skill_contract.py:80-88` 이 정확한 부분 문자열로 단정하므로 중복처럼 보여도 지울 수 없다. 두 곳에 이유를 적는 주석 권장.
- **[comment-analyzer] 계약 문서 정밀화** — 종료 코드 3 트리거 목록에 `head_sha` 부재와 `request-failed:`/`fixture-missing:` 경고를 추가(`references/verification-contract.md:128`), 검색 hit 의 `clue` 키와 `line: 0`(경로 일치) 센티널 문서화(`references/github-verification-contract.md:42`), Issue `title` 이 미신뢰 텍스트 객체임을 명시(`:38`), "public ready states" 를 `issue-ready`/`pr-ready` 로 명시(`references/verification-contract.md:81`).
- **[comment-analyzer] `evals/behavioral-eval.md:12-17` 의 `## Negative` 제목이 실제로는 보안 민감 시나리오다** — 네 제목은 `tests/test_skill_contract.py:150-151` 이 그대로 단정하므로 개명은 테스트와 같은 변경에 포함해야 한다.
- **[comment-analyzer] `discover_exit_code:1452-1457` 에 docstring 필요** — `del records` 와 호출부(`:1881`)가 `records` 를 두 번 넘기는 구조가 의도인지 알 수 없다. 이 함수가 바로 예산 결함의 분기점이다.
- **[orchestrator] `dot_codex/skills/…/scripts/__pycache__/` 가 분석 단계 중(2026-09-07 21:09) 생성됐다** — `.gitignore:21-22` 대상이라 커밋되지 않고 baseline 다섯 지문에도 영향이 없다. 패키징 전 삭제하면 깔끔하다.

## Strengths

- 오프라인 보장이 구조적으로 강제된다 — `tests/test_verify_candidates.py:507-509` 의 기본 runner 가 자식 프로세스 호출 시 `AssertionError` 를 던지고, 네트워크를 타는 모든 테스트는 `--fixture-dir` 또는 명시적 기록 runner 를 쓴다. clone 테스트는 `tempfile` 아래 실제 로컬 git 저장소를 만든다.
- 보안 동작이 구조가 아니라 행동으로 검증된다 — 펜스 불가침(`tests/test_verify_candidates.py:2452-2484`, 중첩 백틱 삽입 후 확장된 펜스가 정확히 두 번), 레댁션이 stderr 를 포함한 다섯 산출물과 소스 문자열까지(`:2486-2545`), 정적 탐색의 읽기 전용성을 전후 파일 해시로(`:1332-1360`), clone 정리를 예외 경로까지(`:1444-1471`).
- 직전 LIVE-1·LIVE-2 회귀가 실제로 덮여 있다 — 정책 탐색의 발견/부재/조회 실패 3-상태와 디렉터리 목록의 정규 JSON 해시, 키워드 양성 7·음성 8 경계 사례(`tests/test_verify_candidates.py:747-951`).
- 후보 문서 불변식이 모든 쓰기 경계에서 강제된다 — `run_record:2884` 와 `run_recheck:3261` 이 쓰기 전에 `validate_candidates_document` 를 호출하고 읽기 시에도 검증한다. recheck 불변성은 `CANDIDATE_FIELDS − RECHECK_MUTABLE_FIELDS` 여집합으로 표현돼 새로 추가되는 필드가 기본적으로 불변이다(default-deny).
- `RequestBudget:255-275` 는 불법 상태를 표현 불가능하게 만든 잘 설계된 타입이다 — bool-as-int 거부, 양수 상한 강제, `remaining` 파생, `consume()` 이 초과 *전에* 예외.
- 계약 문서가 코드 상수에 묶여 있다 — `tests/test_skill_contract.py` 가 `RECHECK_MUTABLE_FIELDS`·`FAILED_SCOPE_REASONS`·허용 헤더·상태×이유 표를 문서에서 파싱해 `ast.literal_eval` 결과와 비교하므로 문서 드리프트가 테스트 실패가 된다.
- 이전 실행 보존 증거가 무결하다 — `preserved-run.sha256` 다섯 항목 모두 `shasum -a 256 -c` 통과, 매니페스트가 `docs/development/2026-09-06-…/` 다섯 파일과 1:1 대응.
- 종료 코드 단일 규칙(전부 접근 실패만 4, 예산 소진은 항상 3)이 `discover_exit_code:1458-1479` 에서 정확히 구현되고 계약 문서 한 문장과 일치한다 — 이전 실행의 blocker PLAN-012 가 다룬 지점이다.

## Recommended Action

1. **PR 준비 차단.** 아래 네 Critical 을 먼저 처리한다. 모두 `scripts/verify_candidates.py` 국소 수정 + 테스트 단정 추가이며 새 설계가 필요하지 않다.
2. Critical 1 최소 수정: 저장소 루프의 `except BudgetExhausted` 와 `if exhausted:` 단축 경로가 *아직 처리되지 않은 모든* 선택 조합을 `budget-exhausted` 로 `failed_scopes` 에 넣도록 하고(조합 루프의 `selected_combinations[combination_index:]` 처리와 같은 형태), 그 저장소들의 `reason` 을 `budget-exhausted` 로 표시한다. 이어서 discovery 조립 직전에 세 목록의 완전 분할을 검사하는 함수를 추가한다.
3. Critical 2 최소 수정: `tests/test_verify_candidates.py:1762` 가 헬퍼의 `skipped=`/`failed=` 매개변수(또는 실제 필드명)를 쓰고 `records` 에 해당 조합을 포함하도록 고치며, 종료 코드만이 아니라 stderr 의 `combination is absent, skipped, or failed` 를 단정한다.
4. Critical 3 최소 수정: `_policy_sha_values` 와 `_reobserved_policy_checks` 를 `status` 기준으로 바꾸고, 게이트에 "해당 정책 경로가 `request-failed` 인데 평가가 `found: false` 를 주장하고 상태가 `issue-ready`/`pr-ready` 면 위반" 규칙을 추가한다(약 10행).
5. Critical 4 최소 수정: `recheck` 의 세 실패 경로에서 `blocking_gaps` 에 `recheck-failed` 를 추가하고(이미 `RECHECK_MUTABLE_FIELDS` 에 포함된 필드) 경고에 `candidate_id`·저장소·원인을 담는다.
6. 같은 PR 권장: Important 의 `record` 단계 경고 승계와 `render` 기본값(둘 다 사람이 읽는 산출물의 정직성), 403 재시도 정책, 단서 이스케이프.
7. 후속 PR 가능: 나머지 Important 와 Suggestions. Spec R3.2·R3.5·R3.6 문언은 digest 가 고정돼 있으므로 본문 편집 대신 개정 노트 또는 후속 이슈로 남긴다.
8. 재수정 후 `CMD-1`~`CMD-8` 전체와 표적 회귀를 다시 돌리고, quality-goal 계약에 따르려면 코드 리뷰 라운드가 소진된 상태이므로 새 실행에서 검증해야 한다(기존 COMPLETED 를 새 변경의 검증으로 재사용하지 않는다).

---

## Appendix A — baseline 기록 (파일 쓰기 없이 수집)

| 항목 | before | after | 판정 |
|---|---|---|---|
| HEAD | `6d60011cbdaead7946b191d3f12029eef5c141c8` | 동일 | 일치 |
| status 지문 | `34f9b0a246a94a029b0f5f2dfa61634b43967a36ac65733264cd558f19057bf6` | 동일 | 일치 |
| unstaged diff 지문 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`(빈 diff) | 동일 | 일치 |
| staged diff 지문 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`(빈 diff) | 동일 | 일치 |
| untracked 지문 | `28b45dc890e32d83345a4ef475d8ccaa66ab7ee89385bdf72ed023b5f4e750ca` | 동일 | 일치 |
| 경로 매니페스트 | unstaged 0행 / staged 0행 / untracked 44경로 | 동일 | 일치 |

한도 중단 후 재개 시점에도 위 다섯 지문을 먼저 재확인해 동일함을 확인했으므로, 중단 전에 완료된 code·tests 결과를 현재 상태에 유효한 것으로 보존했고 재실행하지 않았다. `gh pr view` 는 사용자의 네트워크 금지 지시에 따라 실행하지 않고 로컬 Git 범위로 진행했다(스킬의 fallback 절 준수).

## Appendix B — quality-goal 지문 불일치 (사용자 요청 확인 항목)

- 저장된 지문(`state.verification.workspace_fingerprint`) = 마지막 통과 코드 리뷰 digest = `f07741b419fca7f227af3a7c2521482f1f7d2bc6475d84430236284feb4889e1`
- 현재 워크스페이스 지문 = `c4c29870ae2d13d224551e9498f4a69be057432cbd877e2b706033c12ab7a05b` → **불일치**
- 원인: 코드 리뷰 라운드 3 기록 이후 변경된 경로는 `docs/development/2026-09-07-79-…-plan-redesign/report.md` **하나뿐**이다(전체 미추적 파일 mtime 스캔과 스킬 디렉터리 대상 `find -newer` 두 방법으로 확인). 스킬의 코드·테스트·픽스처·참조 문서는 리뷰 시점과 동일하다.
- 결론: 코드는 리뷰된 상태 그대로이지만 보고서의 전이 후 편집분은 정식 리뷰를 받지 않았다. "현재 상태 전체가 리뷰됨" 으로 단정하지 않는다.

## Appendix C — 이번 단계에서 실제 실행한 검증 (별도 테스트 단계)

| 명령 | 결과 |
|---|---|
| 새 스킬 전체 스위트 | `Ran 44 tests` OK |
| 형제 `analyzing-open-source-pr-patterns` | `Ran 30 tests` OK |
| 형제 `collecting-recent-closed-prs` | `Ran 108 tests` OK |
| `git diff --quiet <base> -- 형제 두 디렉터리` | 종료 0(불변) |
| `quick_validate.py <skill>` | `Skill is valid!` 종료 0 |
| 3.9 문법 파싱 | 종료 0 |
| `shasum -a 256 -c preserved-run.sha256` | 5/5 OK |
| 테스트 후 status 지문 | `34f9b0a2…`(변동 없음) |

네트워크 조사·추가 `discover`·대상 저장소 코드 실행·의존성 설치는 하지 않았다. 코드·기존 보고서·quality-goal 상태 파일은 수정하지 않았다(상태는 여전히 `COMPLETED`, 라운드 spec 2 / plan 2 / code 3).
