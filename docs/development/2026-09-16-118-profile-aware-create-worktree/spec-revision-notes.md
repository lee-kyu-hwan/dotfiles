## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R7.2 | SPEC-012 | AC-30(일치: journal 소유 empty parent rollback을 유지), AC-31(일치: successful identity가 있는 worktree/branch만 제거), AC-32(일치: exact window rollback 순서를 유지), AC-33(일치: pre-existing artifact 불변을 유지), AC-49(일치: cold-start owner-only cleanup을 유지), AC-54(일치: 조회 전 adapter 실패의 진단·소유·remaining 분기를 추가) | 진단 전용 조회만으로 소유권을 부여하지 않고 successful registration evidence를 계속 요구하므로 SPEC-013의 exact 실행 증명이나 SPEC-014의 tests-only gate 전제를 깨지 않는다. | 자체 개정 |
| R10.1 | SPEC-013 | AC-42(일치: 모든 `-k` 이름의 fully-qualified manifest와 direct meta-test 실행을 고정) | manifest가 module 밖 동명 테스트를 배제하고 meta-test를 direct ID로 실행하므로 SPEC-014의 기존 orchestrator 동명 gate 정정과 충돌하지 않는다. | 이전 manifest 해소가 `-k`로 meta-test 자체를 호출해 공허 통과하던 설계를 direct fully-qualified ID와 exact count 계약으로 대체한다. |
| R10.2 | SPEC-014 | AC-43(일치: 정정 전 97/3과 정정 후 두 regression module의 실패 0을 판정), AC-44(일치: 정정 후 full discovery의 수집·실행 N과 실패 0을 판정), AC-45(일치: human diff review 순서를 유지), AC-46(일치: task-owned file/prefix allowlist를 명시적으로 소비) | gate 정정을 먼저 완료한 뒤 full suite를 요구하고 두 skill을 task-owned로 허용하므로 R9.1과 모순되지 않으며 SPEC-013의 count guard를 그대로 사용한다. | 달성 불가능한 선행 red 상태의 exit 0 요구를 tests-only 정정 뒤 exact-count full-suite 성공 요구로 대체한다. |
| R10.3 | SPEC-013, SPEC-014 | AC-46(일치: #118 전용 고유 allowlist test와 자동 mutation 0을 함께 판정), AC-48(일치: operator-only merge/apply evidence 책임을 유지) | 고유 test 이름과 명시적 allowlist를 사용해 orchestrator의 동명 test와 분리하면서 operator handoff 경계를 바꾸지 않는다. | `test_changed_path_allowlist` 동명 충돌을 `test_issue_118_task_owned_path_allowlist`로 대체한다. |
| R10.4 | SPEC-013 | AC-52(일치: 0건·부분·중복 선택과 skip 계열을 runner contract로 거부) | 모든 test command가 같은 exact-selection/result-counter 규칙을 사용하므로 SPEC-014의 regression/full-suite gate도 공허 통과할 수 없다. | 자체 개정 |
| R10.5 | SPEC-014 | AC-53(일치: base·allowlist·preserved set·missing evidence 제거와 세 선행 test를 직접 판정) | 정정 diff를 두 `tests/` 파일로 제한하고 product source를 바꾸지 않아 R9.1의 의도한 skill 변경과 A1~A4 경로·backend·rollback 전제를 보존한다. | 자체 개정 |

## 라운드 3 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R4.1 | SPEC-017, SPEC-018 | AC-15(일치: mutation backend 단일성은 그대로 유지), AC-51(일치: loader의 import-only 역할과 selector 잔존 위임 함수를 함께 판정) | loader가 semantic module을 추가하지 않고 두 selector 함수도 공용 primitive에만 위임하므로 중복 구현 0건과 one-module 전제를 깨지 않는다. | SPEC-017과 SPEC-018 모두 치환 없음 |
| R10.4 | SPEC-015, SPEC-016 | AC-52(일치: 기존 exact-selection runner contract를 유지), AC-55(일치: 외부 shell이 known-bad 실행의 nonzero OS 종료 코드를 독립 판정) | 동일한 이상 관계와 runner 출력 비의존 negative gate를 사용하므로 R10.2의 regression·discovery 하한이나 R10.5의 선행 gate 전제를 깨지 않는다. | SPEC-015는 라운드 2가 도입한 `baseline 하한보다 큰지`를 실측값과 양립하는 `N이 선언한 --min-count 이상`으로 대체하며 SPEC-016은 자체 개정 |
| R10.5 | SPEC-016 | AC-53(일치: CMD-20 추가는 #103 tests-only 정정 파일·잔존 심볼·세 선행 direct ID 계약을 바꾸지 않음) | CMD-20은 temp fixture와 runner process 종료 코드만 사용하므로 SPEC-017의 selector 잔존 규정과 SPEC-018의 loader 소유권을 건드리지 않는다. | 자체 개정 |
