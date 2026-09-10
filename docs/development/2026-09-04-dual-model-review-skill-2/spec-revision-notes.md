# Spec Revision Notes

## Claude r1 반영

- 대상: `docs/development/2026-09-04-dual-model-review-skill-2/spec.md`
- 근거: `.codex-author/claude-spec-review-r1.json`
- 역할 경계: 이 문서는 Claude 공식 리뷰 결과를 반영한 author 개정 기록이며, PASS/REVISE 판정을 다시 내리지 않는다.
- 본문 크기: 개정 전 845행, 개정 후 920행으로 순증 75행이다.

### 선반영 blocker 확인과 연결 검토

- SPEC-20은 R7.6의 종결 record 탈락과 고아 marker 규칙(185~187행), R7.17의 전체 무결성 실패/record 단위 격리/고아 marker 분리(231~244행), R7.19의 GitHub source of truth(245~269행)에 반영돼 있음을 확인했다. 핵심 선택은 바꾸지 않았고, AC-65·76(400~411행)이 무효 인덱스와 정상 4-run 왕복을 서로 다른 기대값으로 판정하도록 연결했다.
- SPEC-21은 R7.6a의 여섯 번째 경로 `agent_category_unselected`(188~205행)와 R3.10의 `S(c)=∅` 술어(119~133행)에 반영돼 있음을 확인했다. AC-10·62·68·77(339, 397, 403, 412행)은 실제 선택 함수부터 lifecycle과 resolve 0건까지 같은 사건 집합을 쓴다.
- SPEC-22는 R3.5·R3.5a의 주체별 변환, 5값 outcome, Claude 전원 실패 시에만 reviewer `excluded`라는 집계(100~114행)에 반영돼 있음을 확인했다. AC-19·63·78(351, 398, 413행)이 주체 결과와 reviewer 결과를 따로 판정한다.
- 선반영 설계의 선택 자체는 재논의하지 않았다. 다섯 잔여 finding을 조합하면서 오래된 AC 문언이나 추적 연결이 그 선택과 모순되지 않도록만 맞췄다.

### Finding별 반영

#### SPEC-23 — sticky 요약 크기 상한

- Requirements의 R7.20(271~281행)에 자체 운영 상한 `SUMMARY_BODY_MAX_BYTES = 49_152`를 정의했다. 이는 GitHub 플랫폼 상한의 인용이나 추정이 아니라 48 KiB의 독립적 보수 한도이며, 최종 body 전체의 UTF-8 바이트를 센다.
- 완전한 v1 인덱스를 먼저 만든 뒤 가시 본문만 `full` → `compact` → `minimal` 순으로 줄인다. 인덱스 record·필드는 자르거나 분할하지 않는다. 인덱스 단독 또는 최소 본문도 넘으면 각각 `summary_index_oversize`·`summary_body_oversize`로 모든 GitHub 쓰기 전에 실패하고 기존 sticky를 보존한다.
- 게시 계획·상태 계약은 Interfaces의 `summary_render`(614, 623, 650행), 실행 책임은 Architecture(500, 506, 534~535행), 실패 동작은 Failure behavior(723~724행)에 연결했다.
- AC-71(406행)은 정확히 49,152/49,153바이트 경계, 두 축약 tier, 인덱스/최소 본문 초과, `apply` 재검사를 객관적으로 단정한다. 추적표의 R7.20(475행)과 판정 명령 PUB·CONTRACT(779, 781행)에 연결했다.

#### SPEC-24 — 요구사항/AC 부분 판정

- R2.3은 강화한 AC-32(367행)가 상태 쓰기 경로 제한, 정확한 `git check-ignore`, 경고 후 계속, `.gitignore` 불변을 모두 판정한다.
- R7.2에는 게시 승인 문구를 검사하는 AC-28을 AC-15와 함께 매핑했다(456행). R7.7에는 `new` inline 생성과 `persisting` 신규 댓글 금지를 판정하는 AC-8·49를 포함했다(462행).
- R7.3의 SHA-256 앞 12자 형식은 known-answer AC-72(407행), R3.3의 정확한 프리플라이트 인자는 AC-73(408행), R5.1의 기본 1라운드는 AC-74(409행)로 신설했다.
- 요구사항 추적표를 요구사항 번호 순으로 다시 만들고 66개 requirement를 모두 한 번씩 등재했다(415~486행). 488행에 각 requirement 문언의 독립 조건과 매핑 AC 합집합을 전수 대조한 방법과 결과를 기록했다. AC 정의는 AC-1~78의 번호 순이고, 메타 기준 AC-34를 제외한 77개가 적어도 한 requirement의 실제 판정 근거로 쓰인다.

#### SPEC-25 — `fp`·`run` 소비처

- v1 여덟-key 호환성을 유지하는 쪽을 택했다. R7.19 record 표의 `fp`·`run` 행(261~262행)에 진단 전용이며 lifecycle·dedup·게시·resolve 판정에는 쓰지 않는다고 명시했다.
- 새 R7.21(283행)은 두 값을 `history_diagnostics`의 `source_run_id`, `run_relation`, `fingerprint_relation`으로 실제 소비한다. 같은 anchor, 이동, 변경, 비교 불가를 닫힌 규칙으로 정의하고 판정 경계로 역류하지 못하게 했다.
- 상태 계약(648행), Architecture/data flow(506, 534~535, 695~698행), Security(743행), D28(866행)에 같은 경계를 반영했다. AC-75(410행)는 진단 네 관계와 `fp`/`run`만 바꾼 변이에서 lifecycle·summary tier·쓰기 집합이 불변임을 단정한다.

#### SPEC-26 — 리뷰어 실패 세 행의 비대칭

- R7.6a(190~203행)에 `SRC_HAS(codex, src)`와 `SRC_HAS(claude, src)`를 닫힌 술어로 정의했다. 세 행을 모두 `reviewers[r].failure_type == <type> ∧ SRC_HAS(r, record.src)` 꼴로 통일하고, 표의 공통 전제 때문에 항상 참이던 “현재 다른 출처가 다시 내지 않음” 절은 제거했다.
- 조합 검토 표(823행)에도 같은 술어를 적어 요구사항과 회귀 점검의 표현을 일치시켰다.

#### SPEC-27 — 추상화 이탈 등호 경계

- R5.4(147행)의 두 번째 조건을 `current_critique_count >= previous_critique_count`로 직접 적고, count가 스키마와 R5.2 검증을 통과한 반박 항목 수임을 고정했다.
- AC-22(354행)에 `==`이면 첫 조건과 함께 true, `<`이면 false, 직전 라운드가 없는 첫 라운드는 false인 경계 픽스처를 추가했다. 조합 검토 표(824행)도 같은 부등식을 쓴다.

### 신설 요구사항과 AC

- 요구사항: R7.20(요약 UTF-8 48 KiB 상한·결정적 축약·쓰기 전 실패), R7.21(`fp`·`run` 진단 소비와 판정 비간섭).
- AC-71: 요약 크기 경계와 안전 실패.
- AC-72: `finding_id` 12자리 SHA-256 known-answer.
- AC-73: 프리플라이트 정확한 argv·한 줄 프롬프트·대체 금지.
- AC-74: 기본/명시 `--rounds` 호출 횟수.
- AC-75: `fp`·`run` 진단 관계와 판정 비간섭.
- AC-76: SPEC-20의 resolved 후 두 후속 실행까지 4-run 왕복.
- AC-77: SPEC-21의 담당 category 미선택 통합 경로.
- AC-78: SPEC-22의 주체별 변환·5값 outcome·reviewer 집계.

### 판단이 갈린 지점

- GitHub의 미문서 상한을 사실처럼 정하지 않고, 스킬 운영 한도를 48 KiB로 정했다. overflow에서 여러 sticky로 분할하거나 인덱스를 자르는 대신 전체 쓰기 전 명시적으로 실패한다. 단일 sticky와 다음 실행의 완전한 판정 입력을 우선한 선택이다.
- `fp`·`run`을 v1에서 제거하지 않았다. 이미 정한 여덟-key 왕복 계약을 유지하되 실제 소비를 진단으로 한정하고, AC-75로 lifecycle에 영향을 주지 않음을 고정했다.
- SPEC-26의 Claude 출처 판정은 특정 agent 하나가 아니라 `claude:` prefix 원소의 존재로 정의했다. reviewer 전체 실패와 agent 일부 실패의 판정 단위를 섞지 않기 위한 선택이다.

### 조합 검토

- 본문의 `## 개정 조합 검토`(802~828행)에서 선행 다섯 결손 경로에 SPEC-21의 미선택 경로를 더한 여섯 경로, R3.10 coverage, R7.19 인덱스, R7.17 record 격리, R7.20 크기 guard, R7.21 진단을 함께 대조했다.
- 크기 축약은 가시 표현만 바꾸고 인덱스의 `cat`·`src`·`fp`·`run`을 바꾸지 않는다. `fp`·`run` 진단은 lifecycle 입력이 아니다. 인덱스/최소 본문 초과는 inline·resolve만 따로 진행하지 않고 모든 쓰기 전에 중단한다.
- 결손 reason은 여섯 경로와 `history_unavailable`로 닫혀 있고, `S(c)=∅`인 미선택과 `S(c)≠∅ ∧ OK(c)=∅`인 선택자 전원 실패는 배타적이다. 유효 인덱스의 종결 고아 marker는 전체 복원을 실패시키지 않는다.
- API 인터페이스는 읽기 여섯·쓰기 네 메서드 그대로이며, 새 요구사항은 외부 쓰기 surface를 늘리지 않는다.

## readiness READY-01 반영

- 근거: `.codex-readiness/result-attempt3.json`의 READY-01 finding 본문과 `required_resolution`만 사용했다. 도구 문제로 손상됐다고 안내된 score와 evidence 필드는 판단 근거에서 제외했다.
- 범위: `spec.md` 920행에서 936행으로 순증 16행이다. 기존 requirement 66개는 유지하고 AC-79만 기존 번호 뒤에 신설했다.

### 선택한 해소

- R7.12의 요약 → inline → resolve 순서는 유지했다. 순서를 바꾸면 반대 실패 경계에서 marker만 있고 완전한 index가 없는 상태가 먼저 생기므로, GitHub v1 record에 필수 `placement`를 추가하는 대안을 택했다(D29, 882행).
- `placement=inline`은 1단계가 지속하는 게시 의도이고, R7.9 marker와 REST review 연결은 2단계 완료 증거다. 둘을 조합해 `summary_only`, `inline_pending`, `inline_posted`, `linkage_invalid`를 결정적으로 복원한다.
- 출시 전 계약 교정이므로 marker version은 v1을 유지하되 record는 아홉 key로 확정했다. 이전 여덟-key 초안이나 `placement` 누락 record는 값을 추정하지 않고 전체 인덱스 `invalid` 안전 경로로 보낸다(Migration, 905행). 앞 절의 “여덟-key 유지” 기록은 이 절의 출시 전 교정으로 대체된다.

### 본문 반영 위치

- R7.12·R7.13(222~226행): 요약 단계가 `placement`를 먼저 지속하고 inline marker가 완료를 증명한다. 로컬 상태가 없을 때 pending인 현재 finding만 정확히 한 번 복구하며, 현재 finding 부재·inline 불가는 격리한다.
- R7.17(231~253행): record별 `delivery_states={finding_id, placement, status, action, reason}`와 네 상태의 닫힌 판정표를 추가했다. marker 0개 pending과 marker 불일치/중복을 구분해 SPEC-20의 record 단위 격리를 보존했다.
- R7.19(254~279행): v1 persisted record를 `placement` 포함 아홉 key로 확장하고, `new`의 placement 산출 및 `persisting`·`resolved`·`not_re_reviewed`의 carry-forward 규칙을 고정했다.
- Interfaces/Architecture/data flow(511~545, 626~662, 689~708행): `publish_findings.py`, plan/state의 `history_restore.delivery_states`, GitHub durable 경계를 같은 계약에 연결했다.
- Failure behavior(716~747행): 2단계 실패 뒤 같은 로컬 상태 재시도와 로컬 상태 소실 뒤 다음 head 복구/격리를 각각 명시했다.
- Migration/rollback(905~915행): 배포 전 v1 교정, 여덟-key 초안의 안전 처리, 로컬 bookkeeping 소실 시 GitHub 복구를 명시했다.

### 수용 기준과 조합 검토

- AC-79(424행): head A에서 요약 성공 → inline 원자 호출 실패 → 로컬 상태 전체 제거 → head B에서 같은 finding 복구 → 다시 로컬 상태 제거 → `inline_posted` 확인까지 fake GitHub 다중 실행 왕복으로 판정한다. `summary_only`, 현재 finding 부재/inline 불가 격리, marker 불일치·중복 대조 fixture도 포함한다.
- 기존 AC-8·47·64·65·67은 placement와 pending/posted/summary-only 구분에 맞게 좁게 보강했고, AC-79를 R7.6·7.7·7.12·7.13·7.17·7.19·R8.2·R8.5 추적 행과 PUB 판정 명령에 연결했다.
- 조합 검토(815~842행)에서 `inline_pending`은 `history_restore.status=ok`인 delivery 중간 상태, marker 불일치는 record 단위 `linkage_invalid`, 인덱스 자체 손상은 전체 invalid라는 세 경계를 분리했다. 여섯 coverage 결손, `fp`/`run` 진단, 48 KiB 불가분 인덱스, 쓰기 메서드 네 개는 바꾸지 않았다.

## readiness READY-01(2차) 반영

- 근거: `.codex-readiness/result-attempt4.json`의 READY-01(Medium) 본문과 `required_resolution`을 기준으로 삼았다. 개정 전 `spec.md` 936행에서 개정 후 959행으로 순증 23행이며, 기존 requirement 66개와 AC-1~79의 번호는 유지했다.
- 방법: 66개 requirement 문언을 열거값, 경계·오류, 상태 변화, 실제 사용자 출력 위치, 금지 동작으로 분해한 뒤 각 추적 행의 AC 합집합이 그 조건을 직접 단정하는지 전수 대조했다. 같은 파일·기능을 언급하기만 한 AC는 판정 근거로 세지 않았다.

### READY-01의 네 결손

- R1.4(62행): AC-74의 기본/명시 라운드 수 판정에 더해 AC-80(425행)을 신설했다. 파서는 lexical token `0`·`1`·`2`만 수락하고 `-1`·`3`·`01`·`1.0`·`foo`·값 누락 및 미지원 `--resume`을 상태·리뷰어·GitHub 접근 전에 거부한다. R1.4 추적 행(439행)에 AC-74·80을 함께 연결했다.
- R2.5(71행): AC-81(426행)에 owner/repo/PR/full SHA 고정값을 넣은 exact known-answer `octo-org-widget-kit-pr42-0123456789ab`를 신설했다. 13번째 이후만 다른 full SHA의 candidate ID 충돌은 AC-61의 `run_id_prefix_collision` 안전 중단으로 연결했고, R2.5 추적 행(445행)에 AC-80·81을 추가했다.
- R6.4(162행): `review_state.py`의 production `render_report(state, synthesis)`를 실제 사용자 리포트의 유일한 판정 경로로 Architecture·Interfaces·data flow(511~523, 551, 623~627, 730행)에 명시했다. AC-82(427행)는 반환 Markdown과 `SKILL.md`의 verbatim 전달을 실행해 두 잔존 한계와 advisory/non-blocking 문구를 단정하며, 정적 참조 문서나 report 전용 golden만으로 통과하지 못한다. R6.4 추적 행(468행)에 연결했다.
- R9.2(323행): 유지보수 문서의 별도 `후속 작업` 절에 SARIF의 현재 미지원 상태와 착수 조건 또는 호환성 범위를 비어 있지 않은 record로 요구했다. AC-83(428행)은 Markdown heading 경계를 파싱하며, R9.2 추적 행(498행)에 연결했다.

### 신설·보강한 AC와 추적표

- 신설: AC-80(`--rounds` 닫힌 허용 집합과 조기 거부), AC-81(exact `run_id` known-answer와 prefix collision 연결), AC-82(production 사용자 리포트 및 같은 상태의 게시 요약), AC-83(heading-scoped 유지보수 후속 작업).
- 기존 AC 보강: AC-3~8, AC-12, AC-17, AC-19, AC-21, AC-25~26, AC-36, AC-40~41, AC-44~46, AC-48, AC-51, AC-54~56, AC-61, AC-65, AC-73~74, AC-78. 고정 SHA/dirty worktree, 병합·게시 단계·sticky marker, 병렬 dispatch, 주체별 retry, evidence 정규화, 크기 경계, 닫힌 스키마·path regex, 실제 리포트, exact CLI, target/base 고정, 재개 순서·충돌, strict index, 프리플라이트·rounds, 주체 outcome을 각각 문언의 입력·출력·금지 동작까지 직접 관측하게 했다.
- 추적표(434~501행)는 66개 requirement를 정확히 한 번씩 등재한다. AC-34는 전체 테스트 통과를 묶는 메타 기준이라 특정 requirement에 배정하지 않았고, 나머지 AC 82개는 모두 적어도 한 requirement의 실제 판정 근거로 등장한다. AC 83개 전부가 Test strategy의 판정 명령(808~829행)에 배정됐으며 AC 정의는 AC-1부터 AC-83까지 단조 증가한다.

### 전수 대조에서 추가로 발견해 고친 항목

- 실제 출력 조건: R2.1a·R3.7·R3.9·R6.3·R10.3의 리포트/게시 요약 조건도 AC-82로 연결했다. R10.1~R10.3의 100/20,000 등호 경계, 101/20,001 초과 경계와 묵시적 추가 절단 금지는 AC-25에 직접 적었다.
- 대상·입력 계약: R2.1a가 요청 ref를 실제 `base_sha..head_sha` 계산에 쓰는지 AC-54로, R2.2가 INTAKE 뒤 branch/worktree 변이에도 전 단계에서 고정 대상을 쓰는지 AC-51로, R2.5의 조회→ID→상태 디렉터리 순서와 완료 기록 재개를 AC-61로 보강했다. R2.4의 exact `.gitignore` entry는 AC-36이 `git check-ignore -v`의 source와 match pattern까지 대조한다.
- 리뷰 파이프라인 계약: 고정 SHA의 `anchor_fingerprint`(AC-3), 주체별 검증 오류만 포함한 retry 입력(AC-19), 다섯 Claude agent 각각의 schema 우선 문구(AC-45), `abstraction_drift` 사용자 안내와 전이 정지(AC-56)를 추가로 직접 판정한다.
- 게시 계약: R7.5의 모든 위치 표시는 `full` tier에만 적용하고 compact/minimal 축약은 R7.20을 우선하게 해 상한 계약과의 모순을 없앴다. R7.7의 어느 lifecycle에서도 스레드 답글을 만들지 않는 조건은 reply endpoint가 없는 화이트리스트를 검사하는 AC-14에 연결했다.

### 조합 검토와 판단이 갈린 지점

- 본문의 조합 검토(833~863행)에서 새 parser/run ID/report/follow-up 판정과 기존 여섯 coverage 결손, 아홉-key v1 인덱스, `placement` 복구, `fp`/`run` 진단, 48 KiB guard를 함께 대조했다. 새 AC는 lifecycle 입력·GitHub source of truth·쓰기 메서드 네 개를 바꾸지 않는다.
- run ID는 요구된 12자 형식을 유지하되 full SHA를 상태 고정값으로 대조한다. 같은 prefix의 다른 SHA를 기존 상태로 재개하는 대신 쓰기 전 명시적으로 중단하는 쪽을 택했다.
- 실제 리포트 조건은 오케스트레이터 자유형식에 맡기지 않고 production renderer로 고정했다. 이 renderer는 기존 state/synthesis만 읽으므로 R7.19 복원이나 게시 계획을 변경하지 않는다.
