# Spec revision notes

## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | SPEC-005, SPEC-009 | AC-1(일치: 두 module-import process의 barrier overlap과 exact-root 생존·제거 observable 추가), AC-2(일치: repository state root 아래 `watchdog-test-<uuid>` namespace로 경로 구체화) | process별 UUID 1회 생성은 R1.2의 exact cleanup 소유권을 강화하며 deterministic clock 또는 stdin 계약의 전제를 바꾸지 않는다. | 자체 개정 — 기존 `<suite-uuid>` 표현을 live task와 구별되는 `watchdog-test-<uuid>` 및 process 생성 시점으로 구체화했다. |
| R1.2 | SPEC-005, SPEC-009 | AC-2(일치: fixture 하위 경계 유지), AC-3(일치: exact owned root만 cleanup·residue 검사하고 shipped bytes·보존 checkout 검증 유지) | broad prefix glob 제거는 병렬 suite를 보호하며 기존 preservation 검증 범위를 축소하지 않는다. | 자체 개정 — UUID-scoped라는 추상 문구를 저장된 exact path 삭제·부재 확인 계약으로 치환했다. |
| R2.1 | SPEC-001, SPEC-006, SPEC-007 | AC-4(일치: pinned Python 3.12 module invocation으로 deterministic clock 판정 실행), AC-5(일치: baseline·단일-line mutation·복원 control과 식별 가능한 race assertion 추가) | race negative control은 R4.1의 다섯 파일 allowlist 안에서만 overlay하므로 scope·보존 해소와 모순되지 않는다. | 자체 개정 — 시간·경합 기능 계약은 유지하고 실행되지 않던 direct-file command와 불명확한 mutation 절차를 runnable harness로 교체했다. |
| R3.1 | SPEC-004, SPEC-008 | AC-7(일치: 3:1 wrapper/content 계약과 별도 실제 Sol/low argv smoke 연결) | wrapper 문서 계약을 stdin validation 및 stalled record와 분리해 각 실패가 다른 해소를 가리지 않는다. | 자체 개정 — 기존 복합 R3.1에서 wrapper·문서 책임만 남기고 독립 계약을 R3.2와 R3.3으로 분리했다. |
| R3.2 | SPEC-008 | AC-8(일치: empty·missing·directory explicit stdin의 pre-launch exit 2와 생략 preflight 허용) | production 변경을 stdin validation에 한정해 R3.1의 3:1 transport와 R3.3의 기존 record shape에 새 변경을 만들지 않는다. | 치환 없음 — R3.1에서 분리해 추가한 새 요구사항이다. |
| R3.3 | SPEC-008 | AC-6(일치: preflight termination과 top-level record/report payload residual PID 복사를 명시) | 새 nested residual field를 금지해 기존 record/report interface 및 stdin-only production scope와 모순되지 않는다. | 치환 없음 — R3.1에서 분리해 추가한 새 요구사항이다. |
| R4.1 | SPEC-002, SPEC-003 | AC-9(일치: e3df177 scope, 두 9ff32a30 preservation guard, e3df177 watchdog AST name guard, 실제 signal-order tests와 full suite를 모두 인용) | watchdog 전용 name guard를 inline evidence로 두어 기존 generic checker 파일을 수정하지 않고 다섯 구현 파일 범위를 유지한다. | 자체 개정 — CMD-5/CMD-6만으로 판정하던 불완전한 보존 근거를 CMD-7/CMD-9/CMD-10까지 포함한 완전한 gate로 치환했다. |
| R5.1 | SPEC-004, SPEC-005, SPEC-007, SPEC-008 | AC-1(일치: focused overlap proof와 두 background full-module status await), AC-5(일치: task-state disposable checkout mutation), AC-10(일치: version-first pinned interpreter와 named Sol/low smoke outputs·completed record semantics) | process requirement로 명시해 implementation 동작 요구사항과 검증 거버넌스를 구분하며 다른 resolution의 파일 범위나 모델 전제를 넓히지 않는다. | 자체 개정 — author 주장 중심의 포괄 문구를 orchestrator CODE gate와 사용자 model override를 명시한 재현 가능한 명령 집합으로 치환했다. |

변경되지 않은 R2.1의 production 시간 주입 계약, R4.1의 실제 signal 알고리즘 비변경 원칙, 기존 AC 식별자 AC-1부터 AC-10까지는 유지했다. 새 명령은 proposed tests의 결함 검출 가능성을 Spec에서 판단하게 하되, 동시 full suite와 real-model smoke의 실제 성공은 구현 뒤 CODE gate에서만 요구한다.

## 라운드 3 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.2 | SPEC-010 | AC-2(일치: fixture 경계와 기존 비-위험 selector는 유지), AC-3(일치: 보존 test selector를 실제 정의 class인 `WatchdogAbortAndReapTestCase`로 수정하고 loader error를 실패로 명시) | selector의 소유 class만 바로잡아 exact cleanup·preservation 요구와 production 범위를 바꾸지 않는다. | 자체 개정 — `snapshots/spec-r2.md`의 잘못된 parent-class selector를 읽기 전용 class 정의 증거에 따라 교체했다. |
| R2.1 | SPEC-012 | AC-4(일치: deterministic clock 판정은 변경 없음), AC-5(일치: 첨부 base evidence가 e3df177 resolve·branch 포함·watchdog test file 존재를 증명해 mutation checkout 전제를 닫음) | base revision의 실재·도달 가능성 증거만 추가하며 race mutation 절차나 시간 계약을 변경하지 않는다. | 자체 개정 — `snapshots/spec-r2.md`에서 미검증이던 e3df177 전제를 첨부 `spec-r3-base-evidence.json`으로 치환했다. |
| R3.1 | SPEC-011 | AC-7(일치: CMD-11에서 `--output-last-message`와 reply file을 제거하고 documented argv prompt·stdout events·stderr·record만 판정) | 실제 smoke가 기존 3:1 content contract와 동일한 preflight template을 사용하므로 stdin validation 또는 stalled termination 계약에 새 경로를 만들지 않는다. | 자체 개정 — `snapshots/spec-r2.md`의 문서와 어긋난 reply-file smoke를 reply/result-schema 없는 documented preflight 호출로 교체했다. |
| R4.1 | SPEC-010, SPEC-012 | AC-9(일치: CMD-7의 다섯 signal test selector를 실제 정의 class로 수정하고 첨부 evidence로 e3df177 watchdog AST guard 전제를 확인) | class qualification과 base evidence만 교정해 실제 process 행동, signal 알고리즘, 다섯 구현 파일 allowlist를 그대로 보존한다. | 자체 개정 — `snapshots/spec-r2.md`의 loader-error selector와 미입증 base 전제를 실제 class 정의 및 첨부 evidence로 치환했다. |
| R5.1 | SPEC-010, SPEC-011, SPEC-012 | AC-1(일치: 동시 suite 검증은 변경 없음), AC-5(일치: controlled mutation의 e3df177 전제를 첨부 evidence로 확인), AC-10(일치: CMD-1/CMD-7 selector를 실행 가능하게 하고 CMD-11을 reply file·result schema 없는 documented preflight transport로 제한) | 세 수정은 검증 명령의 실행 가능성과 계약 일치만 회복하며 production 동작·파일 범위·Codex Sol/low 및 Claude Opus 정책을 넓히지 않는다. | 자체 개정 — `snapshots/spec-r2.md`의 잘못된 class selector, reply-file smoke, 미입증 base 전제를 각각 실제 정의·문서화된 argv·첨부 evidence로 교체했다. |

라운드 2까지의 개정 기록은 보존했다. R/AC 식별자와 기존 요구사항은 삭제·재번호화하지 않았고, 라운드 3은 CMD selector, preflight smoke 입력·산출물 계약, base evidence 인용만 제한적으로 교정했다.
