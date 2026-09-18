## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R3.2 | SPEC-002 | AC-12(일치: dry-run 뒤 backend parent 생성 순서를 명시), AC-49(일치: missing-root 최초 생성과 rollback을 추가) | P1의 missing-root dry-run 성공을 전제로 하되 P2에 따라 apply 전 parent를 backend가 journal 기록과 함께 만들도록 고정해 handle 취득 순서와 A2를 모두 보존한다. | 자체 개정 |
| R3.3 | SPEC-006 | AC-13(일치: 대상 집합과 pattern별 positive/negative fixture를 추가) | 선생성 scanner의 범위를 구체화해도 runtime lock/journal은 R7.5의 profile tree 밖 transient state이므로 A1 판정에 새 공백을 만들지 않는다. | 자체 개정 |
| R3.4 | SPEC-001 | AC-14(일치: dry-run-derived handle과 canonical layout을 함께 판정) | handle은 dry-run 이후에만 확정하고 그 전에는 repository parent만 계산하므로 SPEC-002의 dry-run-before-mkdir 순서를 깨지 않는다. | 자체 개정 |
| R4.1 | SPEC-005 | AC-15(일치: executable backend 단일성을 유지), AC-51(일치: 양 진입점의 동일 module import와 판정 동치를 추가) | parser/path module 공유를 필수화하되 module에는 mutation entrypoint를 두지 않아 backend 계약이 한 곳뿐이라는 전제를 유지한다. | 자체 개정 |
| R4.2 | SPEC-001 | AC-16(일치: repository parent와 dry-run handle/source를 plan field로 추가) | plan이 dry-run 결과 뒤에 만들어지는 흐름을 명시해 cold-start에서도 directory mutation 전 full destination을 공개할 수 있다. | 자체 개정 |
| R4.3 | SPEC-009 | AC-17(일치: exit 1, signal 128+N, incomplete rollback 우선순위를 검증) | 기존 0과 2..7 분류를 보존하면서 빈 값이던 1과 catch 가능한 signal을 추가하고 rollback 불완전 때는 기존 exit 7을 우선해 충돌을 제거한다. | 자체 개정 |
| R5.1 | SPEC-001, SPEC-002 | AC-19(일치: Workmux 출력만 handle 권위로 사용), AC-20(일치: global config 보존 판정은 유지), AC-49(일치: 없는 parent에서 dry-run과 최초 생성을 검증) | P1에 따라 없는 parent로 dry-run한 뒤 parent/handle을 검증하고 P2에 따라 apply 전에 parent를 만들므로 순환 비교와 cold-start 교착을 함께 없앤다. | 자체 개정 |
| R5.2 | SPEC-001, SPEC-002, SPEC-008 | AC-21(일치: wrapper destination-parent와 missing-parent dry-run 계약), AC-22(일치: capability 부재와 issue/PR 자동 생성 금지를 검증), AC-49(일치: wrapper cold-start 계약을 별도 fixture로 검증) | wrapper 실측을 주장하지 않고 capability 계약으로 fail closed하며 외부 wrapper 저장소 issue/PR 생성은 non-goal과 요구사항 양쪽에서 operator follow-up으로 경계를 닫는다. | 자체 개정 |
| R7.1 | SPEC-003 | AC-29(일치: lock 뒤 durable pre-state 기록), AC-50(일치: runtime 경로·mode·stale lifecycle을 추가) | lock/journal을 dry-run 성공 뒤 runtime root에 만들도록 해 R3.2의 preflight no-mutation과 R7.2의 ownership 근거를 동시에 유지한다. | 자체 개정 |
| R7.2 | SPEC-002 | AC-30(일치: P3 잔류 component를 journal 소유권으로 역순 제거), AC-31(일치: worktree/branch 소유권 보존), AC-32(일치: window부터 역순 rollback), AC-33(일치: pre-existing artifact 불변), AC-49(일치: cold-start fault의 빈 component cleanup) | P2의 parent 선생성, A2의 exact selected chain, P3의 backend cleanup을 하나의 journal 순서로 연결해 pre-existing directory 보존과 모순되지 않는다. | 자체 개정 |
| R7.5 | SPEC-003 | AC-50(일치: exact runtime path, mode, lifetime, stale cleanup을 검증) | transient recovery state를 profile/repository tree와 binding registry 밖에 두고 plan·dry-run 전에는 만들지 않아 중복 영구 상태 금지와 A1을 모두 보존한다. | 자체 개정 |
| R8.1 | SPEC-001 | AC-16(일치: 새 repository_parent와 task_handle/source가 public allowlist에 포함), AC-36(일치: unexpected field와 raw payload 거부를 유지) | handle 출처를 공개 field로 추가해도 raw adapter output이나 command argv는 허용하지 않으므로 redaction 경계에 새 공백이 없다. | 자체 개정 |
| R9.2 | SPEC-007 | AC-40(일치: 두 문서 경로와 exact heading/phrase를 고정) | 운영 문서의 신규 경로를 구현 산출물로 명시해 기존 session-account 문서의 schema 책임과 recovery 문서 책임이 겹치지 않는다. | 자체 개정 |
| R10.1 | SPEC-004 | AC-42(일치: manifest 존재와 실제 non-skip 결과를 meta-test로 강제) | full discovery는 회귀 범위를 계속 담당하고 manifest meta-test가 기존에 놓치던 named inventory 부재·skip을 선행 차단한다. | 자체 개정 |
| R10.3 | SPEC-004 | AC-46(일치: automated mutation 금지 gate를 유지), AC-48(일치: operator deployment evidence 책임을 유지) | inventory gate 강화는 operator-only merge/apply 경계를 자동화하지 않으며 기존 Report evidence 책임도 바꾸지 않는다. | 자체 개정 |

## 라운드 3 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R3.4 | SPEC-010 | AC-14(일치: dry-run 경로 component를 `destination_basename`으로 판정) | 경로 component만 dry-run에서 얻고 registry identity는 생성 후 조회하므로 `SPEC-001`의 naming 비재구현 전제와 cold-start 순서를 모두 유지한다. | 라운드 2의 `task_handle` 단일 권위 결정을 `destination_basename`과 `workmux_handle`의 서로 다른 권위 출처로 대체한다. |
| R4.2 | SPEC-010 | AC-16(일치: create plan과 created/reused result의 식별자 시점을 구분) | 새 생성 plan에 미확정 handle을 넣지 않고 재사용만 pre-mutation 조회값을 넣어 R8.1 allowlist와 plan-before-mutation을 함께 보존한다. | 라운드 2 plan의 `task_handle` field 결정을 dry-run 경로 component와 사후 registry handle field로 분리한다. |
| R4.3 | SPEC-010 | AC-17(일치: 생성 후 매칭 실패는 exit 6/7, 재사용 매칭 실패는 exit 5로 판정) | 기존 exit taxonomy 안에서만 분류해 `SPEC-009`로 닫은 internal error·signal·rollback 우선순위를 깨지 않는다. | 치환 없음 |
| R5.1 | SPEC-010 | AC-19(일치: Q1 리터럴 override와 Q2 조건부 `Handle:`의 비권위성을 검증), AC-20(일치: global config 보존 계약은 그대로 유지), AC-49(일치: missing-parent dry-run 순서와 양립) | Q1의 byte-identical dirname 실측을 추가하면서도 P1의 dry-run-before-mkdir과 global-config merge 전제를 바꾸지 않는다. | 라운드 2의 dry-run `task_handle` 단일 권위를 `destination_basename` 권위로 한정하고 registry handle 결정은 R5.4로 이전한다. |
| R5.2 | SPEC-010 | AC-21(일치: wrapper destination과 open 뒤 handle 조회를 구분), AC-22(일치: unsupported wrapper fail-closed 유지), AC-49(일치: wrapper cold-start 계약 유지) | wrapper도 exact destination을 먼저 확정한 뒤 list 조회를 사용하므로 기존 no-fallback·missing-parent capability 전제에 새 우회가 없다. | 라운드 2 wrapper `task_handle` 결정을 destination component로 한정하고 Workmux registry identity는 open 뒤 조회하도록 대체한다. |
| R5.3 | SPEC-010 | AC-23(일치: session-state key는 exact-path 조회 `workmux_handle`만 사용) | profile/session 독립성과 stored/default 우선순위는 그대로 두고 잘못된 basename Git config section 생성만 차단한다. | 치환 없음 |
| R5.4 | SPEC-010 | AC-24(일치: Q4 exact-path list 매칭과 명시적 실패를 검증) | 생성 후에만 handle을 확정하고 실패는 rollback하므로 pre-state 시점과 exit 6/7 소유권 계약에 모순이 없다. | 라운드 2의 모호한 Workmux handle 사후 검증을 `workmux list --json`의 path/handle pair 조회로 대체한다. |
| R6.1 | SPEC-010 | AC-25(일치: 재사용은 mutation 전 exact-path handle 조회), AC-26(일치: cross-profile block은 그대로 유지) | 생성이 없는 reuse의 취득 시점을 plan 전으로 고정하되 pre-existing pair는 호출 소유로 삼지 않아 rollback 경계를 보존한다. | 치환 없음 |
| R7.1 | SPEC-010 | AC-29(일치: pre-state는 `(path, workmux_handle)` pair와 session 값을 기록), AC-50(일치: durable journal lifecycle은 유지) | pre-state에는 기존 pair set만 기록하고 새 handle은 생성 후 set difference로 추가해 생성 전 미확정 상태와 소유권 판정의 시점 충돌을 없앤다. | 라운드 2의 출처 없는 Workmux handle set을 exact path/registry handle pair set으로 대체한다. |
| R7.2 | SPEC-010 | AC-30(일치: directory rollback 유지), AC-31(일치: worktree/branch rollback 유지), AC-32(일치: window rollback에 권위 handle을 사용), AC-33(일치: pre-existing pair를 보존), AC-49(일치: cold-start owned component cleanup 유지) | Workmux pair와 handle-keyed config만 rollback inventory에 추가하며 기존 window→worktree→branch→directory 역순과 pre-existing 보존을 약화하지 않는다. | 라운드 2 rollback의 불명확한 handle 대상을 생성 후 exact-path로 확정한 `workmux_handle`로 대체한다. |
| R7.5 | SPEC-011 | AC-50(일치: lock 필드와 UUID 기반 journal 직접 조회를 단언) | PID·boot identity는 0600 runtime file에만 두고 public error에는 redacted reason만 허용해 R8.2 비밀 미노출과 충돌하지 않는다. | 자체 개정 |
| R8.1 | SPEC-010, SPEC-011 | AC-16(일치: 식별자별 plan/result 노출 시점을 고정), AC-36(일치: handle 및 stale recovery public allowlist를 판정) | 새 public field를 권위 취득 시점별로 제한하고 raw PID·boot identity·runtime path를 금지해 redaction 경계와 R7.5 recovery를 함께 만족한다. | 라운드 2의 단일 `task_handle` public field를 `destination_basename`과 시점 제한 `workmux_handle`로 대체한다. |
| R10.3 | SPEC-010, SPEC-011 | AC-46(일치: 자동화의 persistent mutation 금지는 그대로 유지), AC-48(일치: operator-only 배포 evidence 책임은 그대로 유지) | strict threat·recovery 서술만 보강했고 실제 Workmux mutation과 runtime cleanup은 격리 test 및 operator 경계 안에 남아 자동 배포 금지를 깨지 않는다. | 치환 없음 |
