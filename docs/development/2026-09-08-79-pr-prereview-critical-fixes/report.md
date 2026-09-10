# Quality Goal Report

- Task ID: 20260908T011803Z-79-사전-리뷰-critical-4건-최소-수정-예산-소진-시-조합-누락-2b100e8c
- Mode: strict
- Status: CODE_REVIEW → COMPLETED
- Created: 2026-09-08T01:18:03Z
- Updated: 2026-09-08T10:55:00Z
- Source goal: #79 사전 리뷰 Critical 4건 최소 수정 — 예산 소진 시 조합 누락, skipped_by_cap/failed_scopes 거부 분기 미검증 테스트, 정책 request-failed 가 ready 를 차단하지 않음, recheck 실패 후 이전 ready·검증 시점 유지

## 실행 연결

이 실행은 #79 의 세 번째 quality-goal 실행이다. 1차(`20260906T125225Z-…-ec840cba`)는 Plan 한도 소진으로 `NEEDS_REDESIGN`, 2차(`20260906T194200Z-…-f0ac72ad`)는 `COMPLETED`(spec 2 / plan 2 / code 3, 마지막 코드 리뷰 PASS 91)로 끝났고 `discover` 실경로를 1회 라이브 검증했다. 그 뒤 읽기 전용 PR 사전 리뷰가 **PR 준비 차단** 으로 판정해 Critical 4건과 Important 13건, 이월 2건을 남겼다. 이 실행은 그 판정을 입력으로 받는다. 1·2차 실행의 문서와 상태는 불변 이력이며 이 실행에서 수정하지 않았다(§ 검증 근거의 CMD-16·CMD-17).

입력 문서는 같은 디렉터리의 `pre-review-summary.md`(사전 리뷰 원문, SHA-256 `6940af1d…`)와 `followup-scope.md`(확정 범위·재현 결과·포함/보류 분류)다.

## Classification

`quality_state.py classify` 로 `strict` 를 기록했다. 근거는 다음 7건이다.

1. **공개·외부 API 호환성/멱등성** — `CANDIDATE_FIELDS`(29), `RECHECK_MUTABLE_FIELDS`(9, 여집합 default-deny), `STATUS_REASON_TABLE`, `READINESS_KEYS`(12), 종료 코드 0/1/2/3/4 구획은 `#80`~`#82` 후속 스킬이 소비하는 출력 계약이다. C1·C3·C4 는 이 계약의 status/ready/종료 코드 의미를 직접 바꾼다.
2. **보안 통제** — 이 스킬의 안전 통제는 정책 게이트와 untrusted-text 처리다. C3 은 정책 문서 조회가 실패해도 readiness 가 통과하는 정책 게이트 실패다.
3. **되돌리기 어려운 결과** — `CAN-*` 의 `ready`·`verified_at`·`verified_base_sha` 는 실제 PR 제안 직전 재검증의 근거다. C4 처럼 낡은 ready 가 유효해 보이면 잘못된 외부 제안으로 이어진다.
4. **구획 correctness** — C1 은 저장소 단계 예산 소진이 조합 단계를 통째로 건너뛰어 누락을 산출물에 표시하지 않는다. 예산 소진(3) 대 접근 실패(4) 구획 규칙과 맞물린다.
5. **standard 조건 동시 충족** — 스크립트·테스트·계약 문서 등 다수 파일과 계층이 함께 바뀐다.
6. **이슈 라벨** — `#79` 라벨에 위험을 낮출 근거가 없어 위험 스캔 결과가 그대로 유지된다.
7. **불확실 시 상위 모드** — 사전 리뷰가 PR 준비 차단으로 판정한 상태이므로 상위 모드를 선택한다.

## 사전 리뷰 지적의 재현과 분류

모든 재현은 저장소 밖 세션 임시 경로에서 오프라인으로 실행했다. GitHub 요청·라이브 `discover`·대상 저장소 코드 실행·의존성 설치는 없었다. 재현 스크립트와 출력은 `.claude/quality-state/<task-id>/repro/` 에 보존했다.

**Critical 4건 전부 재현됐다.** 상세는 `followup-scope.md` § 재현 결과에 있다. 요약하면 (C1) 완주 저장소의 조합이 `records`·`skipped_by_cap`·`failed_scopes` 어디에도 없었고, (C2) 금지 조합 분기가 `record is None` 분기에 가려 한 번도 실행되지 않았으며, (C3) `request-failed` 가 확인된 `absent` 와 동일하게 `pr-ready` 를 통과했고, (C4) recheck 실패 세 경로 모두 후보 레코드를 바이트 동일하게 통과시키면서 run outcome 은 `actionable-candidates` 로 남았다.

**Important 13건은 재현 결과로 분류했다.** 심각도를 무비판적으로 수용하지 않았다.

- **포함 8건** — I1·I2·I3·I4·I6·I7·I10·I12. 모두 "모름/실패 근거가 검증된 부정으로 세탁돼 산출물이나 ready 게이트에 도달한다" 는 원인을 Critical 과 공유한다.
- **심각도 상향 1건** — **I6** 은 사전 리뷰의 Important 가 과소평가다. 단서 `x" is:open OR repo:attacker/evil "y` 로 질의가 **다른 저장소를 검색하면서도 `complete: true`** 가 된다. 단서는 외부 PR 텍스트에서 유래하는 미신뢰 입력이다.
- **주장 정정 1건** — **I7** 은 사전 리뷰가 든 세 형태가 재현되지 않았다(종료 2/0). 실제로 재현되는 것은 `repository_node_id` 누락 레코드의 `KeyError` 트레이스백·종료 1과, `skipped_by_cap` 이 문자열일 때 조용히 종료 0 이 되어 C2 게이트가 무력화되는 것이다.
- **보류·보고 5건** — I5(403/429/5xx 재시도 대상 집합 변경은 라이브 검증된 예산 계약 변경), I8(`finally` 무보호 `rmtree`), I9(미신뢰 텍스트 `sha256` 이중 의미, 게이트 영향 없음), I11(`static_search.available` 고정, 새 한계 채널이 필요한 기능 확장), I13(clone 실패 진단). 모두 Spec Non-goals 1~5 에 근거와 함께 명시했다.
- **이월 2건** — CODE-005 는 포함(한 줄 수정), CODE-006 은 결함이 아니라는 재평가를 유지하고 변경하지 않았다.

## Review history

설치 quality-goal 은 **v5.1.0** 이다. 이 버전은 standard·strict SPEC_REVIEW 에서 별도 Codex Spec author 가 초안과 모든 개정을 쓰고, 그 뒤 advisory readiness 심사를 거치도록 요구한다. 오케스트레이터는 Spec 본문을 직접 쓰지 않았다.

| 산출물 | 라운드 | 모델·effort | 판정 | 점수 | blocker | 라운드 사이의 변화 |
|---|---|---|---|---|---|---|
| readiness (advisory) | spec r1 attempt 1 | Codex `gpt-5.6-sol` / high | READY | 100 | 없음 | 체크리스트 C1~C8 전부 pass |
| spec | 1 | 리뷰어 opus / high | REVISE | 79 | `SPEC-001`, `SPEC-002` | finding 8건. 첫 응답은 스키마 검증 실패로 폐기(INC-1) |
| readiness (advisory) | spec r2 attempt 1 | Codex `gpt-5.6-sol` / high | READY | 100 | 없음 | supplied target 10건 전부 `resolved` |
| spec | 2 | 리뷰어 opus / high | **PASS** | 96 | 없음 | 8건 해소 + 오케스트레이터 발행 `ORCH-1`·`ORCH-2` 해소. AC 22 → 23. 첫 호출은 턴 예산 초과로 폐기(INC-2) |
| plan | 1 | 리뷰어 opus / high | PASS | 88 | 없음 | finding 6건(Medium 3 + Low 3) |
| plan | 2 | 리뷰어 opus / high | **PASS** | 93 | 없음 | 6건 전부 resolved. 새 Low 2건(`PLAN-007`·`PLAN-008`) |
| code | 1 | 리뷰어 opus / high | **PASS** | 93 | 없음 | Low 2건(`CODE-001`·`CODE-002`) |

구현 라운드는 Codex `gpt-5.6-sol` / high 1회다(strict 라우트). 라운드 사용량은 spec 2/3, plan 2/2, code 1/3 이다.

Spec 라운드 2 의 결정적 검사는 `revision_check.py --artifact spec` 종료 0(`passed: true`, `empty_cells: 0`, `missing_rows: []`)이고, 개정 노트는 `spec-revision-notes.md` 다. Plan 라운드 2 도 `revision_check.py --artifact plan` 종료 0 이며 개정 노트는 `plan-revision-notes.md` 다.

## Blocking-finding resolutions

| finding | 심각도 | 해소 | 검증 근거 |
|---|---|---|---|
| `SPEC-001` | High | R1.1 과 Failure behavior 절에 분할 불변식 위반의 종료 코드 2, redaction 을 거친 정확히 한 줄의 stderr `error: discover partition invariant violated`, traceback 없음, 출력·manifest·Markdown 파일의 생성·수정 없음을 못박고 AC-2 와 CMD-1 통과 조건을 그에 맞게 재서술 | Spec 라운드 2 리뷰어가 `spec.md:53`·`:78`·`:170` 에서 확인. 구현 후 `_validate_discover_partition` 이 그대로 구현됐고 CMD-1 이 종료 0 |
| `SPEC-002` | High | R3.1 에 실패 snapshot 8개 evidence 필드 값을 전부 고정(승계 4필드는 직전 값 깊은 복사, 미관측 4필드는 `repository_checks: null`·`observed_head_sha: null`·8키 null 정책 객체·빈 queries `complete: false`)하고 실패 후 top-level 값까지 명시. 직전 성공 관찰을 복사하는 구현이 AC-15·AC-16 에서 실패하도록 보강 | Spec 라운드 2 리뷰어가 `spec.md:66`·`:91`·`:92` 에서 확인. 구현 후 `_block_failed_recheck` 가 그 값을 그대로 쓰고 CMD-9 종료 0, 변이 M4 로 커버리지 확인 |

Plan 라운드 1 의 finding 6건은 blocker 가 아니었지만 사용자가 승인 게이트에서 문서 해소를 선택해 라운드 2 에서 전부 해소했다. 상세는 `plan-revision-notes.md` 와 위 Review history 에 있다.

오케스트레이터가 직접 발행한 결정적 finding 3건도 기록한다.

| finding | 내용 | 처리 |
|---|---|---|
| `ORCH-1` | Spec 의 CMD-14 표기 `-m unittest discover -s tests -t .` 가 `ImportError: Start directory is not importable` 로 실행되지 않아 AC-22 의 유일한 판정 수단이 실행 불가였다. 실측으로 확인했다 | Spec 라운드 2 에서 절대 경로 `-s`/`-t` + `-p 'test_*.py'` 형태로 정정. 정정된 형태로 `Ran 55 tests / OK` |
| `ORCH-2` | 확정 범위가 I3 의 증거로 든 `_community_profile_files` 가 어떤 AC 로도 판정되지 않았다. 2xx 형식 불일치가 6개 키를 모두 `false`(확인된 부재)로 만들고 `stages_completed` 에 `community_profile` 을 붙인다 | Spec 라운드 2 에서 R2.2 확장 + AC-23 신설. 구현 후 CMD-6 종료 0, 변이 M5 로 커버리지 확인 |
| `ORCH-3` | 분할 불변식의 "구획 내부 중복" 분기가 어떤 테스트도 밟지 않는다 | 코드 리뷰가 `CODE-001`(Low, 비차단)로 판정. 아래 § Remaining advisory findings |

## Plan approval

- Approval timestamp: 2026-09-08T04:20:00Z
- Plan digest: `994a9d527d831d496a6b8cf988f3c5b42f21d7833140a42ce35f5c38f22be29b`

승인 게이트는 두 번 제시됐다. 첫 제시(Plan 라운드 1, digest `4c354b4a…`)에서 사용자는 advisory finding 6건을 문서에서 해소하도록 선택해 `AWAITING_PLAN_APPROVAL → PLAN_REVIEW` 로 되돌렸다. 두 번째 제시에서 개정된 Plan(digest `994a9d52…`, PASS 93)에 대해 구현을 승인했다. `approve-plan` 은 승인 직전에 파일의 현재 SHA-256 이 Plan 리뷰가 기록한 digest 와 같음을 확인한 뒤 기록했다.

## Changed files

구현 라운드가 신고한 9개 파일이 구현 창 동안 실제로 수정된 9개와 정확히 일치한다. 모두 `dot_codex/skills/verifying-open-source-contribution-candidates/` 하위다.

| 파일 | 종류 | 의도된 변경 |
|---|---|---|
| `scripts/verify_candidates.py` | update | 분할 불변식 검사(`_validate_discover_partition`), discovery 형태 검증(`_validate_discovery_document`), 파싱 실패 sentinel, allowlist 전용 예외(`ChildCommandError`), 정책 3상태 소비와 `request-failed` ready 차단, community profile 형태 가드, 미신뢰 단서·저장 query 거부, recheck 실패 상태 차단(`_block_failed_recheck`), record manifest 상태 전파, render `unknown` 기본값, `entry_count` 정정 |
| `tests/test_verify_candidates.py` | update | 신설 테스트 11개, 기존 금지 조합 절의 잘못된 키 사용 정정 |
| `tests/test_skill_contract.py` | update | 계약 문서 네 문장 단정에 `SKILL.md` 추가 |
| `tests/fixtures/budget/partition-violation/case.json` | **add** | 중복·누락 주입 모드와 기대 종료 코드·stderr |
| `tests/fixtures/mixed/case.json` | update | 분할·전파 시나리오 갱신 |
| `tests/fixtures/injection/responses.json` | update | 정책 본문을 실제 contents API 형태(base64)로 정규화 |
| `tests/fixtures/redaction/responses.json` | update | 같은 정규화 |
| `SKILL.md` | update | R4.1 의 네 문장 반영 |
| `references/verification-contract.md` | update | R4.1 의 네 문장 반영 |

`compute_revision()` 이 해시하는 6개 경로 중 다수가 바뀌어 리비전 값이 달라졌다. 이는 계약된 동작이며 `test_print_revision_matches_recomputation` 이 재계산값과 비교해 통과한다.

## Verification evidence

python `/opt/homebrew/bin/python3` 3.14.7, `PYTHONDONTWRITEBYTECODE=1`, 네트워크 없음. 기준 커밋 `6d60011cbdaead7946b191d3f12029eef5c141c8`. 변경 전 기준선은 대상 스킬 44 tests OK, 형제 스킬 30 tests OK 와 108 tests OK 다.

| ID | 대상 | 종료 코드 | 결과 |
|---|---|---|---|
| CMD-1 | `test_budget_exhaustion_partitions_all_selected_combinations` | 0 | Ran 1 test OK |
| CMD-2 | `test_exit_code_matrix` | 0 | Ran 1 test OK |
| CMD-3 | `test_record_rejects_present_forbidden_combinations` + `test_assessment_binding_and_missing_assessments` | 0 | Ran 2 tests OK |
| CMD-4 | `test_record_rejects_malformed_discovery_shapes` | 0 | Ran 1 test OK |
| CMD-5 | `test_policy_request_failure_blocks_ready` | 0 | Ran 1 test OK |
| CMD-6 | `test_malformed_success_payloads_remain_incomplete` | 0 | Ran 1 test OK |
| CMD-7 | `test_allowlist_violation_fails_without_retry` | 0 | Ran 1 test OK |
| CMD-8 | `test_untrusted_search_clues_cannot_escape_repository_scope` | 0 | Ran 1 test OK |
| CMD-9 | `test_recheck_failure_blocks_actionable_candidate` | 0 | Ran 1 test OK |
| CMD-10 | `test_record_manifest_preserves_discovery_failure_state` | 0 | Ran 1 test OK |
| CMD-11 | `test_render_never_defaults_unknown_status_to_complete` | 0 | Ran 1 test OK |
| CMD-12 | `test_policy_directory_entry_count_uses_filtered_names` | 0 | Ran 1 test OK |
| CMD-13 | `test_reference_documents_cover_contract` + `test_print_revision_matches_recomputation` | 0 | Ran 2 tests OK |
| CMD-14 | 전체 오프라인 스위트 | 0 | **Ran 55 tests OK** (기준선 44 + 신설 11) |
| CMD-15 | 형제 스킬 두 스위트 | 0 | Ran 30 OK, Ran 108 OK — 기준선과 동일 |
| CMD-16 | 1차 실행 문서 불변성 | 0 | 5/5 `OK` |
| CMD-17 | 2차 실행 문서 불변성 | 0 | 7/7 checksum `OK`, `git status` 단일 미추적 항목 유지, `-uall` 정확히 7개 |

초기 dirty 경로 보존을 함께 확인했다. 1차 문서 5/5, 2차 문서 7/7, 형제 스킬 디렉터리는 구현 창 동안 수정된 파일 0개다.

### 미구성 범주 (통과로 적지 않는다)

| 범주 | 확인한 저장소 근거 | 기록 |
|---|---|---|
| lint | 스킬 디렉터리에 `ruff.toml`·`.flake8`·`setup.cfg`·`tox.ini`·`package.json` 없음. 항목은 `agents`·`evals`·`references`·`scripts`·`SKILL.md`·`tests` 뿐 | not configured |
| type check | `mypy.ini`·`pyproject.toml`·`py.typed` 없음 | not configured |
| build | 빌드 시스템·`Makefile` 없음. 표준 라이브러리 스크립트 트리 | not configured |
| E2E / 라이브 | 승인 범위가 추가 GitHub 요청·라이브 `discover`·`recheck`·대상 저장소 코드 실행·의존성 설치를 금지 | 승인에 의한 범위 밖. 통과로 적지 않는다 |

### Critical 4건의 실제 차단 확인

구현 전에 작성한 재현 스크립트를 **그대로** 다시 실행했다.

| | 결과 |
|---|---|
| C1 | 완주 저장소의 조합이 `failed_scopes/budget-exhausted` 에 귀속. 유실 집합 공집합(이전 1건) |
| C2 | 게이트 분기가 이제 테스트로 실행된다. 변이 M1 로 확인(아래) |
| C3 | `request-failed` → 종료 2 `error: assessments[0].policy_files_reviewed: request-failed policy observation`. 확인된 `absent` 는 여전히 종료 0 으로 `pr-ready` 도달 |
| C4 | `pr-ready` → `unverified`/`insufficient-evidence`, `next_recheck_required: false`, `blocking_gaps: ["recheck-failed"]`, history 1→2 실패 snapshot, `verified_at` 보존, run outcome `actionable-candidates` → `no-actionable-candidates`, 경고 `recheck-failed:CAN-001:example-org/example-repo:transport-or-5xx`. 레코드가 더 이상 바이트 동일하지 않다 |

**경고만 추가해 ready 를 유지한 것이 아니다.** C3 은 종료 2 로 후보 생성을 막고 C4 는 상태 자체를 `unverified` 로 내린다.

### 변이 테스트 (테스트가 실제로 결함을 잡는지 확인)

스킬 트리를 세션 임시 경로에 복사해 사본에서만 변이했다. **작업트리는 변경하지 않았으므로 지문에 영향이 없다.**

| 변이 | 결과 |
|---|---|
| M1 `or combo in forbidden_combos` 제거 | CMD-3 FAILED(3건), 전체 스위트 FAILED — C2 커버 확인 |
| M2 분할 불변식 "구획 내부 중복" raise 제거 | CMD-1 여전히 OK — `CODE-001` 근거 |
| M2b 분할 불변식 disjointness·universe raise 제거 | CMD-1 FAILED(2건) — 주입 두 모드가 여기서 잡힌다 |
| M3 `request-failed` 정책 게이트 제거 | CMD-5 FAILED(2건) — C3 커버 확인 |
| M4 `recheck-failed` gap 제거 | CMD-9 FAILED(1건) — C4 커버 확인 |
| M5 community profile 형태 가드 제거 | CMD-6 FAILED(2건) — AC-23 커버 확인 |
| M6 render `unknown` 을 `complete` 로 되돌림 | CMD-11 FAILED(3건) — AC-18 커버 확인 |
| M7 record manifest status 를 `complete` 로 하드코딩 | CMD-10 FAILED(1건) — AC-17 커버 확인 |
| M8 M2 를 전체 스위트로 확대 | Ran 55 tests OK — `CODE-001` 확정 |
| 복원 | pristine 사본 재검증 Ran 55 tests OK |

사전 리뷰의 Critical 2 는 "게이트를 지워도 44개가 전부 통과한다" 는 것이었다. 이제 그 절을 지우면 3건이 실패한다.

### 구현자 편차 2건 검토

1. **injection·redaction fixture 의 정책 본문을 직접 UTF-8 에서 base64 로 정규화** — 수용. R2.2 의 강화된 정책 payload 검증이 실제 GitHub contents API 형태를 요구한다. 주입 payload 자체는 그대로다. 디코드해 확인한 결과 `CONTRIBUTING.md` 는 여전히 프롬프트 주입 문구와 중첩 펜스를 담고 있고 `test_injection_fixture_is_inert` 도 그 문구가 미신뢰 발췌에 나타나며 후보가 `unverified` 로 남는 것을 그대로 단정한다. 어떤 단정도 약화되지 않았다.
2. **all-404 사례를 실제 discover 시나리오로도 실행** — 수용. 종료 4 의 다섯 번째 분할 시나리오를 더한 강화이며 기대 결과를 바꾸지 않는다.

### 지문

검증 시점 작업트리 지문은 `89c9b8bffd98ddcca9dcbefb4ec6d40b55fc2dc88bcc2ad4efa5843fa26725c9` 이고 코드 리뷰 라운드 1 의 심사 대상 digest 와 같다. 종결 가드는 기록된 검증 지문과 마지막 통과 리뷰의 digest 를 대조하며 두 값이 일치한다. 이 보고서 파일은 종결 직전에 등록되므로 **종결 후 작업트리의 실시간 지문은 이 문서만큼 심사 시점과 다르다.** 이는 절차상 의도된 순서이며, 종결 후 이 보고서를 다시 편집해 지문을 재불일치시키지 않는다.

## Remaining advisory findings

blocker 는 없다. 남은 것은 Low 4건이다.

| finding | 출처 | 내용 | 영향 | 후속 |
|---|---|---|---|---|
| `SPEC-009` | Spec 라운드 2 | AC-8 의 "매핑 밖 경로" 대조군은 생산 코드가 만들 수 없는 값이다. `discover_policy_files` 는 정확히 10개 `POLICY_PATHS` 만 순회하고 `cla_or_dco`·`ai_policy` 가 그 10개 전부에 매핑되므로 실제 수집 결과에 매핑 밖 항목이 없다 | 없음. 대조군은 fixture 전용 합성 경로로 만들면 된다 | Plan 전역 제약과 구현 프롬프트에 fixture 전용임을 명시해 반영 완료 |
| `PLAN-007` | Plan 라운드 2 | T3 step 3 의 CMD-3 전체 형태가 그 시점에 없는 테스트를 참조한다 | 없음. 실측으로 축약 형태(`Ran 1 test / OK`)와 전체 형태(`FAILED (errors=1)`)를 확인했다 | Plan 라운드 한도(2/2) 소진으로 문서 수정 불가. 구현 프롬프트에 축약 형태를 구속 지시로 실어 구현자가 그대로 따랐다 |
| `PLAN-008` | Plan 라운드 2 | CMD-17 의 `git status` 기대값이 문서에 근거로 기록되지 않았다 | 없음. `git ls-files` 가 0줄이라 그 디렉터리는 미추적이고 기대값 자체는 사실과 맞다 | 같은 이유로 문서 수정 불가. 구현 프롬프트에 baseline 근거와 `-uall` 7개 파일 집합 대조를 추가로 실었다 |
| `CODE-001` | 코드 리뷰 라운드 1 | 분할 불변식의 "구획 내부 중복" raise 분기(`scripts/verify_candidates.py:1634`)를 어떤 테스트도 밟지 않는다. AC-2 의 `duplicate` 주입은 교차 구획 중복이라 인접 분기가 잡는다 | 유지보수성만. 리뷰어와 오케스트레이터 모두 AC-2 는 충족이고 남은 분기는 기준을 넘는 올바른 방어 코드라고 판정 | `partition-violation` fixture 에 구획 내부 중복 사례를 추가하거나, 이 분기가 의도적으로 미커버 방어 코드임을 계약 문서에 기록 |
| `CODE-002` | 코드 리뷰 라운드 1 | 2xx payload 형태 검증이 두 검색 소비자 사이에 비대칭이다. `discover_duplicate_search` 는 `_valid_search_payload` 로 성공을 게이트하지만 `discover_code_search`(`scripts/verify_candidates.py:1483`)는 HTTP 상태만 보므로 2xx 형식 불일치 code-search 본문이 `available` 을 유지하며 조용히 빈 hits 와 경고 없음이 된다 | **승인 범위 밖.** R2.2 와 AC-11 은 issue/PR 중복 검색·정책 경로·community profile 만 지목하고 Non-goals 는 기능 확장을 금지한다. 오케스트레이터도 코드로 직접 확인했다 | **후속 범위 항목으로 보고한다.** 같은 원인 계열(모름을 검증된 부정으로 세탁)이므로 `discover_code_search` 와 그 recheck 대응부에 같은 형태 게이트를 적용하는 별도 승인이 필요하다 |

## 편차와 사건

상세는 `.claude/quality-state/<task-id>/orchestrator-deviations.md` 에 있다.

- **DEV-1** 초기 dirty 경로 4개는 모두 #79 의 미커밋 산출물이다. 그중 대상 스킬 디렉터리는 이번 승인 범위의 수정 대상 자체이고 2026-09-08 문서 디렉터리는 이번 실행의 문서 위치다. 따라서 "초기 dirty 경로 바이트 동일 보존" 규칙을 1·2차 실행 문서 디렉터리 2개에만 적용했고 CMD-16·CMD-17 로 검증했다.
- **DEV-2** `init` 이 기록한 문서 디렉터리에 사전 리뷰 입력이 이미 있었다. 파일명이 겹치지 않으므로 숫자 접미사 디렉터리를 새로 만들지 않고 같은 디렉터리를 썼다.
- **DEV-3** Spec 라운드 2 리뷰어 재시도 프롬프트에 10개 target 의 해소 주장과 줄 번호 색인을 인라인했다. 원인이 판정 내용이 아니라 읽기 예산이었기 때문이다. 심사 범위·rubric·근거 경로·판정 기준은 바꾸지 않았고 특정 판정이나 결정적 점검의 waive 를 요청하지 않았다.
- **DEV-4** Plan 라운드 한도 소진으로 `PLAN-007`·`PLAN-008` 을 문서에서 고치지 못했다. 사실을 직접 확인해 구현 프롬프트에 구속력 있는 정정으로 실었다.
- **DEV-5** 코드 리뷰에 unified diff 를 싣지 못했다. 대상 디렉터리가 착수 전부터 전체 미추적이었고 구현 전 내용 스냅숏을 뜨지 않았으며 Codex 이벤트 로그도 패치 본문을 남기지 않는다. 대체 근거로 변경 파일 목록과 종류, 요구사항별 현재 코드 줄 범위 색인, 검증 JSON, 심사 대상 지문을 실었고 이 한계를 리뷰 프롬프트에 명시했다. 다음 실행에서는 IMPLEMENTING 진입 직전에 대상 디렉터리의 파일별 SHA-256 과 사본을 상태 디렉터리에 남긴다.
- **INC-1** Spec 라운드 1 리뷰어 첫 응답이 `new_blocker_evidence` 누락 3건으로 스키마 검증에 실패했다. 원문을 보존하고 `record-review-error` 기록 후 계약이 허용하는 1회 재시도를 같은 라운드로 실행했다.
- **INC-2** Spec 라운드 2 리뷰어 첫 호출이 도구 35회·24턴 한도에서 결과 JSON 없이 멈췄다. 계약이 리뷰어 문맥 재개를 금지하므로 재개하지 않고 새 호출로 재시도했다.
- **INC-3** 구현 직전 preflight 가 200초 감시 창을 넘겼다. 사후 확인 결과 preflight 자체는 성공했다(모델이 비어 있지 않은 한 줄을 응답). 모델 부재가 아니므로 `BLOCKED_MODEL_UNAVAILABLE` 복구 경로를 발동하지 않았고 모델을 임의로 대체하지 않았다.
- **편차 1건(readiness)** readiness 라운드 2 리뷰어가 `prior_findings[].id` 에서 `ORCH-1`·`ORCH-2` 를 `SPEC-009`·`SPEC-010` 으로 재명명했다. 정책은 참조 ID 의 원 접두 유지를 요구한다. `evidence` 본문에 원 ID 를 명시했으므로 대응은 추적 가능하다. readiness 는 advisory 이므로 상태를 바꾸지 않고 기록만 했다.

## 유지되는 한계 주장

- **`discover` 실경로만 1회 라이브 검증됐다.** 그 근거는 2차 실행의 읽기 전용 이력이며 이번 변경의 검증으로 재사용하지 않았다.
- **`assessment`·`record`·`recheck` 실경로는 라이브 미검증이고 실제 `CAN-*` 산출물은 없다.** 이번 모든 판정은 보존 fixture 와 주입 transport 로 오프라인 실행했다.
- **`#79` 전체 완료를 주장하지 않는다.** 이번 실행의 범위는 사전 리뷰가 차단한 결함의 최소 수정이다.
- **배포하지 않았다.** commit·push·PR 생성·merge·`chezmoi apply`·배포·GitHub 이슈·댓글 작성을 수행하지 않았고 `main`·다른 워크트리·전역 설치본·`$HOME` 설정을 수정하지 않았다.
- **보류 5건(I5·I8·I9·I11·I13)과 `CODE-002` 는 미해결이다.** 각각 별도 승인이 필요한 후속 범위다.

## Final status

- Status: `completed`
- Machine-readable reason: `null` (정상 종결. spec 2/3, plan 2/2, code 1/3 라운드, 마지막 코드 리뷰 PASS 93, blocker 0, 미해소 advisory Low 5건)
