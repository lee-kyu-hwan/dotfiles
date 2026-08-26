# quality-goal 구현 — Plan 편차·결정 기록

- Task: quality-goal 스킬 구현 (Plan: `docs/superpowers/plans/2026-08-25-quality-goal.md`)
- 목적: Plan 대비 편차와 사용자 결정을 한곳에 기록한다. Task 9의 `report.md`가 이 문서를 인용한다.

## D-1. 경로 매핑: 프로젝트 로컬 `.claude/` → chezmoi `dot_claude/`

사용자 결정(2026-08-25): 스킬을 프로젝트 로컬이 아니라 **dotfiles(chezmoi)로 관리**한다.
Plan의 모든 `.claude/` 경로는 아래 매핑으로 치환해 구현한다. Task 2~9의 Files 항목과
커밋 체크포인트 경로에 동일하게 적용된다.

| Plan 경로 | 저장소 경로 (source) | 배포 경로 (chezmoi apply 후) |
|---|---|---|
| `.claude/skills/quality-goal/**` | `dot_claude/skills/quality-goal/**` | `~/.claude/skills/quality-goal/**` |
| `.claude/agents/quality-reviewer.md` | `dot_claude/agents/quality-reviewer.md` | `~/.claude/agents/quality-reviewer.md` |
| `.claude/quality-state/` (런타임) | 저장소에 두지 않음 | 스킬을 **사용하는 각 프로젝트**의 `.claude/quality-state/` |

Task 7의 `.gitignore` 단계는 "스킬을 사용하는 프로젝트"의 ignore 문제이므로 구현 시
SKILL.md 런타임 지시(대상 프로젝트에서 ignore 확인/안내)로 적용 방식을 판단한다.

## D-2. 평가 기간 중 배포 금지 제약

`chezmoi apply`를 실행하면 `dot_claude/skills/quality-goal/`이 `~/.claude/skills/`로
배포되어 **baseline의 "스킬 부재" 전제가 깨진다.**

- Task 9의 with-skill 평가가 끝날 때까지 `chezmoi apply`(또는 이 스킬을 `~/.claude`로
  배포하는 어떤 행위)를 하지 않는다.
- Task 9 with-skill 평가는 Plan대로 **일회용 fixture 저장소 안에 프로젝트 로컬
  `.claude/` 번들을 복사**해 실행한다 (dot_claude → .claude 역매핑). 사용자 스코프
  `~/.claude`는 평가 동안 깨끗하게 유지된다.
- 2026-08-25 확인: `~/.claude/skills/quality-goal`, `~/.agents/skills/quality-goal` 미존재.

## D-3. baseline 실행 방법 편차

- Plan Task 1 Step 3의 `--settings '{"skillOverrides":{"quality-goal":"off"}}'`는 생략했다.
  스킬이 어디에도 배포되지 않아 "부재" 조건이 자연 충족되기 때문(위 D-2 확인 참조).
- baseline 원본과 요약은 저장소 밖(`scratchpad/baseline/`)에 보존한다 (Plan 요구).
- 사용자 환경의 superpowers 플러그인 5.0.7이 로드된 상태가 이 사용자의 실제 baseline이다.

## D-4. Codex 모델 라우팅 변경 (사용자 승인, 2026-08-25)

- 원래 /goal 지시: 구현 Codex `gpt-5.6-sol` / effort `high` 고정.
- 변경: 구현은 `gpt-5.6-luna`, effort **유동 운용** — 복잡 Task(2·3·7)는 `max`,
  문서·템플릿 Task(4·5·6)는 `high`, 수정 라운드는 원 Task와 동일 effort.
- 리뷰는 변경 없음: fresh-context Claude Opus / high (Task 6 이후 `quality-reviewer.md`).
- 변경 전 산출물: `evals.json`은 `gpt-5.6-sol`/high로 작성됨.
- 가용성 preflight: sol·luna 모두 `MODEL_OK` 응답(exit 0), effort `max`는 서버 수용
  확인(무효값은 `invalid_request_error`로 거부됨을 실측). 증거: `scratchpad/baseline/preflight.txt`.
- 주의: 이 변경은 **구현 메타 작업**의 라우팅이다. 스킬 자체의 런타임 라우팅
  (light/standard=Terra, strict=Sol)은 Spec §14 그대로 구현한다.

## D-5. evals.json 문구·assertion 기록 (Task 1 리뷰 TASK1-005/006)

- `routing-standard` goal은 Plan Task 1 표(238행)의 "across selector, ..." 대신
  "across **the** selector, ..."를 사용한다. Plan 내부적으로도 Task 9 Step 1(1012행)의
  실제 실행 명령이 "the"를 포함해 서로 불일치하며, **Task 9의 실행 명령과 바이트 일치**
  하는 쪽을 불변 식별 문구로 채택했다.
- `routing-strict`에 Plan 표가 요구하지 않은 `prints_selected_mode_and_reasons`를
  의도적으로 추가했다(상위집합 강화). 라우팅 근거 출력은 모든 모드의 공통 계약이기 때문.

## D-6. Task 1 baseline 재실행 (Task 1 리뷰 TASK1-001/002)

- 1차 baseline은 7/9 시나리오가 빈 저장소 fixture에서 실행되어 "코드베이스 부재"가
  교란 요인이었고, pressure-resume은 재개할 산출물이 seed되지 않았다.
- 조치: 최소 소스 fixture(package.json + selector/session-state/api-client + node --test
  테스트 1개)로 `routing-standard`, `routing-strict`, `pressure-approval`을 재실행하고,
  `pressure-resume`은 "리뷰 통과한 spec.md"를 seed한 fixture로 재실행했다.
  결과는 `scratchpad/baseline/v2/`에 보존, 판정은 summary.md v2 매트릭스가 대체한다.
- 재실행하지 않은 pressure-blocker/loop/malformed-review는 판정 대상이 정책 결정
  (점수 vs finding, 3차 라운드, JSON 실패 처리)이라 빈 저장소 교란이 핵심 판정을
  바꾸지 않음을 근거로 유지하되, summary.md에 교란 사실을 명시한다.

## D-7. Task 1 리뷰 결과와 잔여 advisory finding

- round 1 (fresh Opus): REVISE — High 2, Medium 2, Low 4 → 전부 수정.
- round 2 (fresh Opus, 신규 컨텍스트): **PASS** — 8건 resolved 확인, 신규 Critical/High 없음.
  리뷰 루프는 2라운드로 종결(한도 2 준수).
- 잔여 advisory (Task 9 report.md에 승계):
  - **TASK1-009 (Medium)**: pressure-resume seed spec.md의 "Next stage: implementation
    plan" 문구가 재개 지점을 힌트해 resumes_at_plan_stage/does_not_recreate_spec의
    판별력을 낮춤. **Task 8 전 조치**: with-skill 비교 시 힌트 문구를 제거한 seed를
    사용하거나 해당 assertion을 상태머신 단위 테스트로 판정.
  - TASK1-010 (Low): summary v1을 덮어써 v1→v2 델타 감사 추적이 약함 (v1 원본 JSON은 보존).
  - TASK1-011 (Low): pressure-resume baseline이 승인 없이 7커밋 구현을 완주했으나
    이를 잡는 assertion이 없음 — 평가 보정 후보.
  - TASK1-012 (Low): summary.md 31·37행 근거 문구가 v2 원본과 불일치 — 리뷰어 세부
    회신 확인 후 두 행 모두 정정 완료. TASK1-010의 델타 불일치도 특정됨
    (does_not_recreate_spec은 v1에서도 공허한 P) — 집계 서술 정정 완료.
- unittest 명령 적응: 경로에 하이픈(`quality-goal`)이 포함돼 Plan의
  `python3 -m unittest <파일경로>` 형태 대신 `python3 -m unittest discover -s <tests dir>
  -p '<pattern>'`을 focused/full 공통으로 사용한다.

## D-8. Task 2 계약 결정과 잔여 advisory

- **PASS+blockers 처리**: Plan의 canonical 게이트 테스트(PASS verdict + High blocker를
  evaluate_gate에 직접 투입)에 맞춰, "PASS ⇒ blockers 없음"은 검증 오류가 아니라
  게이트 실패(`blockers_present`)로 처리한다. 초기 구현의 오류 문자열 매칭 예외는
  제거했다. "PASS ⇒ required_next_action null"은 Plan 명시라 검증 오류로 유지.
- **round >= 2는 prior 필수**: prior 생략을 빈 open-finding 목록으로 간주하면 호출자
  실수가 리뷰어 JSON 불량으로 오귀속되므로(리뷰 TASK2-003), 명시적 검증 오류로
  fail-closed 한다. 빈 목록은 `{"open_finding_ids": []}`로 명시 전달.
- **TASK2-009 (Low, 기록만)**: REVISE/BLOCKED verdict에서 required_next_action null을
  허용하는 것은 Plan 공유 계약(PASS만 제약)을 그대로 따른 것이다. 규칙 추가는
  Plan 편차라 하지 않고, 리뷰어 프롬프트(Task 6)에서 행동 지침으로 다룬다.
- **__pycache__ 오염 방지**: .gitignore에 `__pycache__/`·`*.pyc` 추가, .chezmoiignore에
  `.claude/skills/quality-goal/**/__pycache__` 추가, 테스트 실행은
  `PYTHONDONTWRITEBYTECODE=1`로 표준화 (리뷰 TASK2-006).
- **인터페이스 상위집합 확장 (TASK2-010 기록)**: Plan 명시 계약은
  `evaluate_gate(payload, checks)`·`gate --input --checks`이나, High finding 해소를 위해
  `expected_artifact`/`prior` 키워드 인자와 gate CLI `--artifact`/`--prior`를 추가했다.
  2-positional 호출 하위 호환은 테스트로 고정됨. Plan 대비 상위집합 편차.
- **round 2 신규 advisory (Low 2건, report 승계)**:
  - TASK2-011: `required_next_action`이 빈 문자열이어도 검증 통과(스키마 minLength 없음,
    Python도 타입만 검사). 게이트는 fail-closed 유지되므로 위험 낮음. validate 서브커맨드가
    검증 오류 시 stderr에 진단을 쓰지 않는 점도 함께 기록 — 오류는 stdout JSON errors에 포함.

## D-9. Task 3 상태 머신 설계 결정 (round 1 리뷰 반영)

- **IMPLEMENTING 가드는 모든 진입 경로에 적용**: Plan 문구 "cannot reach IMPLEMENTING
  without a current approved Plan digest"를 수정 루프 재진입(CODE_REVIEW→IMPLEMENTING)에도
  강제. RED 검토 단계에서 오케스트레이터가 직접 보강 지시.
- **base_revision·initial_dirty_paths는 `capture_workspace_baseline(state)`가 채운다**
  (TASK3-007): `new_state`를 git에 결합시키지 않기 위해 별도 함수 + CLI
  `capture-baseline`으로 분리. 오케스트레이터는 INTAKE에서 호출한다.
- **전이 전제조건을 Plan 표보다 강화** (TASK3-010): Plan의 전이 표는 모드 무관이지만,
  light만 CLASSIFIED→AWAITING_PLAN_APPROVAL, standard/strict만 CLASSIFIED→SPEC_REVIEW,
  CODE_REVIEW→COMPLETED는 code 리뷰 1회 이상 + 마지막 리뷰 PASS·blocker 없음 +
  open finding 없음 + verification.valid를 요구한다. 상태 머신 수준의 게이트 우회
  차단(defense in depth)이 Plan의 의도("하드 게이트")에 부합한다고 판단.
- **task_id 형식 확장** (TASK3-009): `<timestamp>-<유니코드 slug>-<goal_key 8자>`로
  충돌·한국어 goal 식별성 해결. CLI `init --task-id` 선택 인자 추가(상위집합),
  기존 state.json 존재 시 exit 4로 거부.
- **fingerprint 프레이밍** (TASK3-005): 성분별 `label:length:` 프레이밍으로 경계 모호성
  제거. 중첩 repo·symlink는 lstat 기반으로 안전 처리 (TASK3-004).
- **Plan 초과 추가 API** (round 2 TASK3-020 기록): `record_verification`,
  `invalidate_stale_verification`, `set_artifact`은 Plan의 Produces 목록에 없는 추가
  함수다. 도입 이유: 워크스페이스 변경 시 검증 무효화(설계 §10)와 CODE_REVIEW→COMPLETED
  하드 게이트, artifact 경로 등록을 CLI로 수행하기 위함. CLI에도
  `record-verification`/`invalidate-verification`/`set-artifact`로 노출한다 (TASK3-017).
- **불일치 강등의 영속 계약** (round 2 TASK3-018 기록): 승인 digest/경로 불일치 강등은
  `ApprovalMismatchError`(exit 3)와 함께 디스크에 영속된다. 그 외 오류는 무변이.
- **중첩 repo 해싱의 보수적 선택** (round 2 TASK3-021 기록): untracked 중첩 git repo는
  `.git` 내부까지 해시한다. 중첩 repo의 commit/gc가 fingerprint를 바꿔 검증을 무효화할
  수 있으나 fail-closed 방향이라 의도적으로 유지한다.
- **round 3 잔여 advisory (Low 2건, report 승계)**: Task 3 리뷰는 3라운드 만에 PASS 종결.
  - TASK3-022: artifact/승인 경로를 원문 그대로 저장하고 비교는 resolve로 수행 —
    상대 경로 등록 시 cwd에 따라 강등될 수 있음(fail-closed). SKILL.md에서 절대 경로
    사용을 지시할 것 (Task 7에서 반영).
  - TASK3-023: 승인 이후 set-artifact로 포인터 변경 가능하나 IMPLEMENTING 진입 가드가
    차단함을 재현 확인. COMPLETED 게이트에 가드 재확인 추가는 선택 강화로 보류.

## D-10. Task 4 리뷰 결과와 잔여 advisory

- round 1 REVISE(High 1·Medium 5·Low 3) → 수정 → round 2 **PASS** (2라운드 종결).
- High 1건: plan-rubric의 `required_sections` 하드 체크 누락 — 세 루브릭 모두 gate-check
  JSON 키를 백틱으로 명시해 해소.
- 잔여 advisory (Low 3건, report 승계):
  - TASK4-010: planning-policy가 마커 토큰을 우회 표현("two common all-caps markers")으로
    지칭 — 마커 금지 테스트가 references/*.md의 리터럴을 막기 때문. 오해 위험 낮음.
  - TASK4-011: routing-rules의 "async or asynchronous" 중복 표현.
  - TASK4-012: 루브릭 문서의 게이트 키와 validate_review.REQUIRED_CHECKS 간 드리프트
    가드 없음(현재 값은 정확히 일치, 포함 단정만 존재).

## D-11. Task 5 리뷰 결과와 사후 advisory 수정

- round 1 **PASS** (Medium 1·Low 3, blocking 없음). 게이트 통과 후 의존 Task(7·8)가
  생기기 전에 advisory 4건을 즉시 수정하는 쪽을 선택 — 재리뷰 없이 테스트로 검증.
- 수정 내역: strict 블록 테스트를 마커 구간 실추출 방식으로 교체(변형 검증 수행),
  plan 전용 strict 토큰 `PLAN_` 접두사 부여 + 추적성 표 행 반복 지시 추가,
  설계 §7의 6번째 항목(프로덕션 변경 부재 확인) 서브섹션을 양 템플릿에 추가,
  changed_files 패턴이 `../`·`./`·`~`·절대경로를 거부하도록 강화.
- 판단 근거: Medium/Low는 advisory지만 테스트 공허함(TASK5-001)은 Task 8의 회귀
  기반을 약화시키고, 토큰 충돌(TASK5-004)은 Task 7 렌더링 버그의 씨앗이라 선제 수정.

## D-12. Task 6 확인 사항 (리뷰 TASK6-004·005)

- **agent frontmatter 키 유효성**: Claude Code 하니스 문서가 agent 정의 frontmatter에서
  model·reasoning effort·tools를 읽는다고 명시하므로 `effort: high`는 유효. `maxTurns: 12`는
  Plan 명시 계약이라 유지하되, 하니스가 무시해도 리뷰 품질에는 영향 없음(호출 시
  오케스트레이터가 범위를 좁게 유지).
- **ignore 파일 편차 귀속**: Plan상 `.gitignore`는 Task 7 소관이나, `__pycache__` 규칙은
  Task 2 리뷰 TASK2-006 해소를 위해 선행 적용했다(D-8 기록). Task 7에서는
  `.claude/quality-state/` 항목만 추가하면 된다.
- **Task 6 round 2 PASS + Task 7 인계 사항 (Low 2건)**:
  - TASK6-006: round 2 이상의 리뷰 검증 시 오케스트레이터가 **항상 `--prior`를 공급**
    해야 함(빈 목록도 명시 전달) — SKILL.md 리뷰 절차에 명시할 것.
  - TASK6-007: BLOCKED payload 세부 규칙 고정 테스트 부재 — 선택 사항, Task 8 후보.
  - TASK3-022 인계: SKILL.md가 artifact/승인 경로를 **절대 경로**로 등록하도록 지시할 것.

## D-13. Task 7 리뷰 결과

- round 1 REVISE(**Critical 1**·High 1·Medium 4·Low 3) → 수정 → round 2 **PASS**.
- Critical: light 모드가 PLAN_REVIEW/PLAN_PASSED를 경유하도록 지시해 상태 머신과 모순
  (오케스트레이터가 정독 중 선발견, 리뷰어가 CLI 재현으로 확정) → CLASSIFIED→
  AWAITING_PLAN_APPROVAL 직행 + rework 경로(IMPLEMENTING→PLAN_REVIEW→PLAN_PASSED→
  재승인)로 재작성. light 12단계 CLI 완주를 오케스트레이터가 독립 재현.
- High: Report를 터미널 전이 후 등록하라는 지시(터미널 불변과 충돌) → 전이 전 등록으로 수정.
- round 2 신규 Low 2건(record-review digest 명시, "revise at most twice" 표현)은
  post-PASS 마이크로 수정으로 즉시 해소(160개 테스트 검증).
- 리뷰어 참고사항: .chezmoiignore 구조상 스킬의 tests/ 디렉토리는 $HOME에 배포됨 —
  의도된 선택(테스트 동반 배포, D-1 참조).

## D-14. Task 8 리뷰 결과

- round 1 **PASS** (Low 5건, blocking 없음). 리뷰어가 신규 테스트 4개를 변이 검증
  (사본 변이 → FAILED 확인)으로 비공허성까지 입증. Plan의 8개 회귀 불릿은
  기존 4 + 신규 4로 전부 커버, advisory 백로그 2건(TASK4-012·TASK6-007) 해소.
- 잔여 advisory (Low 5건, report 승계): dirty 보존 테스트의 지문 비교 미사용,
  make_git_repo의 전역 gpgsign 상속 가능성, code round 4 거부가 stage 가드 경유,
  BLOCKED payload 정규식의 줄바꿈 민감성, Plan Files 목록이 실제(2개 파일)보다 넓음.
- Task 8은 test_quality_state.py·test_content_contracts.py 2개 파일만 수정
  (test_validate_review.py는 기존 테스트가 요구를 이미 커버).

## D-15. Task 9 에서 발견한 Task 5 산출물 결함과 수정

- **발견 경로**: 인증된 end-to-end 실행. `codex exec --output-schema` 가 HTTP 400 으로
  거부되어 오케스트레이터가 Codex 를 호출할 수 없었다. 결정적 테스트·CLI 워크스루로는
  드러나지 않는 계층(외부 API 계약)의 결함이었다.
- **원인 2건** (`gpt-5.6-terra` 로 실측):
  - `codex-result.schema.json` 의 `"uniqueItems": true` → `'uniqueItems' is not permitted`
  - 같은 파일의 `changed_files.items.pattern` `^(?!\.\.?/)[^/~].*` →
    `regex lookaround is not supported`. 이 lookaround 는 Task 5 리뷰 TASK5-002 의
    "경로 탈출 차단 강화" 조치가 도입한 것으로, 강화가 곧 비호환을 만든 사례다.
- **수정**: `uniqueItems` 제거, 패턴을 lookaround 없는 `^([^/~.].*|\.[^/.].*)$` 로 교체.
  로컬 9개 경로로 동등성을 확인하고 API 가 실제로 수락해 유효한 결과 객체를 반환하는
  것까지 검증했다. 계약 테스트는 이제 패턴을 문자열이 아니라 **행동**으로 단정하고,
  lookaround 와 `uniqueItems` 재도입을 금지한다.
- **`review.schema.json` 은 그대로 둔다**: 로컬 `validate_review.py` 전용이라 API 로
  전송되지 않으므로 `uniqueItems` 가 유효하다.
- **스킬 자체의 행동은 정확했다**: 스테이지를 유지한 채 문의했고(성급한 BLOCKED 없음),
  모델 무단 대체를 거부하며 "모델 교체는 이 400 을 해결하지 못한다"고 진단했고,
  승인 범위 밖 파일 수정을 거부했으며 워크트리를 건드리지 않았다.
- **교훈**: 외부 API 계약은 `structurally validated`·`fixture tested` 수준에서 검증되지
  않는다. 스키마를 API 로 보내는 코드 경로가 있으면 최소 1회 실제 호출로 확인해야 한다.
