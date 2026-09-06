# Quality Goal Report

- Task ID: 20260906T003045Z-61-quality-goal-개정-후-자기-회귀-점검-revision-r-d857b87b
- Mode: standard
- Status: COMPLETED
- Created: 2026-09-06T00:30:45Z
- Updated: 2026-09-06
- Source goal: #61 quality-goal 개정 후 자기 회귀 점검(revision regression check) 단계를 추가한다

## Classification

standard. 사용자가 명시했고 `routing-rules.md` 위험 스캔 결과와 같다.

- strict 트리거 없음 — 인증·결제·PII·DB 마이그레이션·외부 API·프로덕션 인프라 변경이 아니다. 변경 대상은 `dot_claude/skills/quality-goal/` 의 문서·상태 헬퍼·검증 스크립트다.
- standard 조건 — 여러 파일·레이어(SKILL.md, `quality_state.py`, 신규 스크립트·스키마·reference, 테스트), 상태 전이 계약 변경(`record-review` 입력), 비목표·AC 를 명시해야 하는 요구사항.
- 이슈 라벨 `quality-goal`·`enhancement`·`P2-medium` 은 standard 와 부합한다.

## Review history

| 회차 | 대상 | 행수 | 요구사항/AC | verdict | score | blocker | 게이트 |
|---|---|---|---|---|---|---|---|
| Codex 사전 점검 1 | spec.md | 448 | 30/47 | 빈 칸 53(독립 조건 단위) | — | — | 모순 4 + AC 확장 반영 |
| **공식 r1** | spec.md | 457 | 30/49 | REVISE | 78 | SPEC-01·02·03 | 실패 |
| Codex 사전 점검 2 | spec.md | 497 | 30/53 | 빈 칸 33 | — | — | 모순 5 반영, 노트 누락 행 5 검출 |
| **공식 r2** | spec.md | 499 | 30/54 | REVISE | 83 | SPEC-09(신규, 라운드 2 개정이 만든 회귀) | 실패 |
| Codex 사전 점검 3 (초점: 매핑 AC ↔ 새 문언) | spec.md | 503 | 30/54 | 매핑 AC 21 중 모순 4 | — | — | 넷 반영, 건드린 요구사항 6 → 8, 노트 재판정 0 누락 |
| **공식 r3** | spec.md | 503 | 30/54 | **PASS** | **91** | 0 (Low SPEC-13·14 잔여) | **통과**. 1차 출력은 `verified:false` 포함으로 검증 실패 → record-review-error 후 실행 증거 첨부 재기동 |
| Codex Plan 사전 점검 1 | plan.md | 230 | 태스크 8 / 추적표 54 | 빈 칸 4 | — | — | 넷 반영(T5 임시 파일 정리, AC-54 배치 문언, T7 명령 구체화, task id) |
| **Plan 공식 r1** | plan.md | 230 | 8/54 | REVISE | 83 | PLAN-01 | 실패 |
| Codex Plan 사전 점검 2 (초점: 통과 확인 성립) | plan.md | 286 | 8/54 | 54 성립, 문언 2 | — | — | CMD-4·5 문언 정정 |
| **Plan 공식 r2** | plan.md | 286 | 8/54 | **PASS** | **92** | 0 (Low PLAN-10 잔여) | **통과** |
| Codex 구현 r1~r5 | 스킬 소스 | — | — | r1 미완, r2 AC-46 모순 지목, r3·r4·r5 bounded fix | — | — | 독립 검증 310 tests OK |
| Codex 읽기 전용 diff 점검 1 | diff | — | — | 문제 6 | — | — | r5 에서 전부 반영 |
| **Code 공식 r1** | diff | 16 파일 | — | REVISE | 62 | CODE-1·2·3 (픽스처 스텁·AC 부분 단언·노트 판정 열) | 실패 |
| Codex 구현 r6·r7 | 스킬 소스 | — | — | CODE-1~6 해소, AC 54 전수 단언 대조표(저자 주장 빈 칸 0) | — | — | 독립 검증 재실행 |
| Codex 읽기 전용 diff 점검 2 (초점: AC 별 전수 단언·픽스처) | diff | — | — | 빈 칸 29 — 대조표 주장과 달리 테스트 본문에 조건 누락 | — | — | r8 로 닫음 |
| Codex 읽기 전용 diff 점검 3 | diff | — | — | 빈 칸 10 (7 테스트 + 명령 판정 2 + 편차 1) | — | — | r9 로 7 닫음 |
| Codex 읽기 전용 diff 점검 4 | diff | — | — | 빈 칸 0 | — | — | 제출 |
| **Code 공식 r2** | diff | 16 파일 | — | **PASS** | **88**(advisory) | 0 (Low CODE-7·8 잔여) | **통과** — fingerprint e4a5612778a6605e… |

## Blocking-finding resolutions

| ID | 라운드 | severity | 해소 | 확인 |
|---|---|---|---|---|
| SPEC-01 | r1 | High | R1.4(d) 정의 수 하한, R7.1 문법 고지, AC-50·51 | r2 evidence 해소 확인 |
| SPEC-02 | r1 | High | R1.4 를 문법·추출 범위·토큰 한 항으로 통합, R2.3·R2.5·R3.3·R3.4 참조, AC-16·52 | r2 evidence 해소 확인. 단 R3.4 개정이 SPEC-09 를 낳음 |
| SPEC-03 | r1 | High | `record_review(..., *, revision_check_path=None, snapshot_dir=None)` 시그니처와 § Interfaces 함수 시그니처 절, AC-27·34·53 | r2 evidence 해소 확인 |
| SPEC-09 | r2 | High | (b)안 — R3.4 만 재작성, AC-17 라운드 2 문언 유지 | r3 evidence 해소 확인 |
| PLAN-01 | Plan r1 | High | T5→T4 간선·T4 착수 조건. 같은 종류 54 AC 전수 대조로 AC-2·3·53 도 닫음 | Plan r2 evidence 해소 확인 |
| CODE-1 | Code r1 | High | 자리표시자 픽스처 3 개를 Plan T2 지정 실물로 교체, 테스트가 파일을 읽음, AC-47 가드가 내용 단언 | Code r2 evidence 해소 확인 |
| CODE-2 | Code r1 | High | AC 54 건 전수 단언 대조(독립 점검 29 → 10 → 0)로 지정 테스트 확장 | Code r2 evidence 해소 확인 |
| CODE-3 | Code r1 | High | 노트 판정 토큰 규칙을 R5.2·AC-24·Plan T4 로 한 규칙 확정 — `note_result`·policy 문서·`test_notes_table_header_and_row_coverage` 셋을 함께 수정 | Code r2 evidence 해소 확인 |

## Plan approval

- Approval timestamp: 2026-09-06T05:41:54Z
- Plan digest: a08d1c73aac096f4ed4b3f71a9ed69a9ac62d5b7231894d915fd80d6b5cd499a

## Changed files

Codex(gpt-5.6-terra, high) 구현 4 라운드. 라운드 1 은 T1~T3·T5 일부에서 `needs_plan_change` 로 끝났지만 Plan 결함을 지목하지 않아 미완 라운드로 취급하고 라운드 2 로 이어 완성했다. 라운드 2 는 실제 Spec 사실 오류(AC-46 의 "세 루브릭 Pass gate 에 85" — code-rubric Pass gate 는 base 부터 하드 조건 전용)를 지목해 `needs_plan_change` 를 냈고, 오케스트레이터는 승인 Spec 을 고치지 않고 판정 의도(임계 85 유지·Pass gate 불변)로 테스트만 보정하는 bounded fix(라운드 3)로 처리했다(Plan deviation). 라운드 4 는 오케스트레이터 독립 검증이 찾은 결함 — 태스크 절이 `## ` 헤딩에서 끝나지 않아 마지막 태스크에서 같은 행 규칙이 무력화되는 버그 — 의 bounded fix 다. 배포 스크립트가 #70 plan.md 의 PLAN-06 을 잡는 것은 라운드 4 뒤에 확인됐다.

| 경로 | 성격 |
|---|---|
| `dot_claude/skills/quality-goal/scripts/revision_check.py` | 신설. 점검 스크립트(R1~R5) |
| `dot_claude/skills/quality-goal/schemas/revision-check.schema.json` | 신설 |
| `dot_claude/skills/quality-goal/references/revision-check-policy.md` | 신설 |
| `dot_claude/skills/quality-goal/scripts/quality_state.py` | 수정. `record_review(..., *, revision_check_path=None, snapshot_dir=None)`, `revision_checks` 필드, 스냅숏, CLI `--revision-check` |
| `dot_claude/skills/quality-goal/scripts/validate_review.py` | 수정. `validate_revision_check` 추가 |
| `dot_claude/skills/quality-goal/SKILL.md` | 수정. `### Spec`·`### Plan` 절차, 참조 경로 셋, `version: 5.0.0`. 393 행 |
| `docs/quality-goal-maintenance.md` | 수정. `## 개정 후 자기 회귀 점검` 절 |
| `dot_claude/skills/quality-goal/tests/test_revision_check.py` | 신설 |
| `dot_claude/skills/quality-goal/tests/test_quality_state.py`, `test_content_contracts.py` | 수정. 신규 테스트 + 기존 11 개 본문 갱신(이름 유지) |
| `dot_claude/skills/quality-goal/tests/fixtures/revision-check/` (6 파일) | 신설 |
| `docs/development/2026-09-06-61-quality-goal-revision-regression-check/` | 워크플로 산출물(spec·plan·두 개정 노트·이 보고서) |

## Verification evidence

구현 뒤 독립 검증(`.claude/quality-state/<task-id>/verification-final.md`, 인터프리터 /opt/homebrew/bin/python3 3.14.7):

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| CMD-1 전체 스위트 | 0 | `Ran 310 tests` / `OK` (기존 240 + 신규 70) |
| CMD-3 `wc -l < SKILL.md` | 0 | 393 (< 500) |
| CMD-4 보존 절·템플릿·Pass gate | 0 | `보존 대상 절 불변` |
| CMD-5 테스트 이름 보존 | 0 | `기존 테스트 보존`(고유 239 ⊂ 현재) |
| CMD-6 자기 적용(spec·plan 독립 모드) | 0 / 0 | 빈 칸 0 |
| 배포 스크립트 on #70 plan.md | 1 | `AC 등장 행에 판정수단 동반 / AC-84 / empty / spec.md / 399` — PLAN-06 재현 |
| 배포 스크립트 on #70 spec.md | 0 | 빈 칸 0 |
| git status 대조 | — | Codex 주장 changed_files 16 = 실제 변경 16(허용 경로만), 초기 dirty 없음 |

Spec 단계의 실행 증거:

| 명령 | 종료 코드 | 증거 |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dot_claude/skills/quality-goal/tests -p 'test_*.py'` (3.14.7) | 0 | `Ran 240 tests` / `OK` |
| 같은 명령 `python3.12` 3.12.14 | 0 | `OK` |
| 같은 명령 `/usr/bin/python3` 3.9.6 | 1 | `FAILED (errors=23)` |
| `-k test_zzz_none` (3.14.7) | 5 | 매칭 0건 |
| `codex exec --sandbox read-only --ephemeral --model gpt-5.6-terra -c model_reasoning_effort="low"` | 0 | `Acknowledged.` |
| `git check-ignore -v .claude/quality-state/` | 0 | `.gitignore:25` |
| CMD-3 `wc -l < SKILL.md` | 0 | 372 |
| CMD-4 보존 절·템플릿·Pass gate 비교 | 0 | `보존 대상 절 불변` |
| CMD-5 테스트 이름 보존 | 1 → 수정 | 고유 이름 239 실측(240 아님), Spec 의 단언을 239 로 고침 |
| 프로토타입 `revision_check_proto.py plan` on #70 plan.md | 1 | 560 칸 중 빈 칸 1 = `AC-84/T17` (PLAN-06) |
| 프로토타입 spec on #70 spec.md | 0 | 599 칸, 빈 칸 0 |
| 프로토타입 spec on this spec.md (r1→r2 base) | 0 | 294 칸, 빈 칸 0, 건드린 요구사항 19, 노트 누락 행 5 검출 후 0 |
| 프로토타입 spec on this spec.md (r2→r3 base, AC 커버리지·판정 토큰 포함) | 0 | 295 칸, 빈 칸 0, 건드린 요구사항 8, 누락 행·AC·판정 0 |
| `validate_review.py validate/gate` r1·r2 | 0 / 3 | valid; gate 실패 사유 score·verdict·blockers·High |

`not configured`: lint, type check, build, E2E — 이 저장소의 스킬 디렉터리에 구성이 없다(`docs/quality-goal-maintenance.md` '결정적 테스트' 절이 `unittest` 하나만 싣는다).

## 자기 적용 결과 — 절차가 실제로 회귀를 잡았는가

- **잡았다(형식 층)**: 라운드 2 개정 중 Codex 2차 점검 반영 뒤 프로토타입의 노트 커버리지 점검이 누락 행 5 건(R1.2·R1.3·R4.1·R5.2·R5.3)을 보고했고 제출 전에 닫았다. 라운드 1 제출 전 자체 대칭 점검은 예시 식별자·타 문서 인용을 미정의 참조로 잡아(14 건) "코드 스팬 인용" 규칙을 설계에 추가하게 했다.
- **Plan 단계에서 잡았다**: 두 칸 대조 스크립트가 AC-54 의 테스트 파일 배치 불일치(Spec AC-47 vs Plan T5) 1 건을 초안에서 잡았고, PLAN-01 종류의 의존 대조 스크립트가 라운드 2 개정에서 AC-2·AC-3·AC-53 의 간선 결손 3 건을 추가로 잡았다(리뷰어는 AC-49 하나만 지적).
- **Code 단계에서 잡았다**: 오케스트레이터 독립 검증이 배포 스크립트가 #70 PLAN-06 을 못 잡는 태스크 절 경계 버그를 찾았다(픽스처는 마지막 태스크가 아니어서 통과). Codex 읽기 전용 diff 점검 1 이 부분 문자열 AC 매칭·코드 스팬 CMD 누락·검사 순서·부분 스키마 검증 등 6 건을 잡았고, 공식 Code r1 이 "AC 문언 대비 부분 단언" 형태 High 3 건을 잡아 AC 54 건 전수 단언 대조표로 닫았다.
- **Codex 자기 보고는 근거가 아니다**: 라운드 7 은 AC 54 건 대조표를 "빈 칸 0" 으로 보고했지만 독립 읽기 전용 점검이 테스트 본문에서 29 행의 누락 조건을 찾았다. 저자 주장과 독립 대조를 분리한 이 Spec 의 원칙(개정 노트는 검증 대상)이 구현 단계에서도 그대로 성립했다.
- **Codex 모델 턴 무응답 정체**: 사용자 관측으로 구현 라운드 6 의 events 가 한 항목 완료 뒤 약 80분 갱신되지 않았다(결국 완료). pid 종료만 기다리는 대기자는 이를 감지하지 못한다. 라운드 9 부터 events 10분 미갱신·총 40분 상한 감시자를 붙였다. #70 함정 목록에 추가할 사례다.
- **못 잡았다(내용 층)**: 라운드 2 의 유일한 blocker SPEC-09(R3.4 와 AC-17 의 칸 종류 모순)는 대칭 칸이 "연결" 만 보고 "같은 것을 말하는지" 는 보지 않아 통과시켰다. 원인은 개정 노트 파급 열을 저자가 기억으로 써 AC-17 을 빠뜨린 것이다. 라운드 3 부터 파급 열을 생성 목록으로 채우고 AC 마다 일치/모순을 붙이는 규칙을 D12·R5.2 에 넣었다.
- Codex 읽기 전용 사전 점검은 세 라운드 모두 공식 리뷰 전에 모순을 잡았다(1차 4, 2차 5).

## Remaining advisory findings

- CODE-7 (Low): 픽스처 `spec-revision-notes-round2.md` 의 판정 토큰이 넷째 열에 있어 확정 규칙(셋째 열)과 어긋남. 동작 테스트가 이 파일을 노트로 넘기지 않아 게이트에는 무영향. 후속에서 셋째 열로 옮기고 `--notes` 로 넘겨 `missing_rows == []` 단언.
- CODE-8 (Low): `test_last_task_section_ends_at_next_level_two_heading` 의 앞 두 `.replace` 가 픽스처 실물화 뒤 무동작. 세 번째 replace 가 경계 회귀를 여전히 잡음. 후속에서 정리.
- Spec AC-46 문언 오류(code-rubric Pass gate 에 85 없음): Plan deviation 으로 처리. Spec 문서 자체는 승인본이라 고치지 않았고, 다음 개정 시 정정 대상.
- Codex 모델 턴 무응답 정체(r6, 약 80분): 감시자(events 10분·총 40분) 도입. #70 함정 목록 후속.
- 배포(`chezmoi apply`)는 사용자가 수행. 배포 전 진행 중 goal 은 `revision_checks` 키 부재로 면제.
- SPEC-13 (Low): R7.3 판정 방법 패턴이 `range(...)` 루프·위치 인자 형태를 문자 그대로 포괄하지 않음 — Plan T5/T8 의 스캐너 규칙으로 확정.
- SPEC-14 (Low): R5.2 판정 토큰 검사 대상 한정 — Plan T4 가 `ripple[].acceptance_criteria` 로 한정.
- PLAN-10 (Low): T2 `--state` 픽스처의 스냅숏 digest 를 `reviews[artifact][-1].artifact_digest` 와 같게 만들어 T4 대조 활성화 뒤에도 유효하게 — 구현 시 반영.
- `.gitignore` 후속 없음 — `.claude/quality-state/` 는 이미 무시됨.

## Final status

- Status: completed
- Machine-readable reason: COMPLETED
- 검증 fingerprint 와 Code r2 리뷰 digest 는 같다(e4a5612778a6605e…). 그 뒤 워크스페이스에서 바뀐 파일은 이 보고서(`report.md`, 추적 안 된 docs 디렉터리) 하나뿐이며 코드 16 파일은 검증 시점과 동일하다.
