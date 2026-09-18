## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | PLAN-002 파급 | AC-1(일치: T2 package와 sibling load 책임 안에서 기존 routing 검사를 유지) | 비-root 로드 회귀는 스킬 routing 범위를 넓히지 않아 다른 해소의 전제나 경계를 깨지 않는다. | 치환 없음 |
| R3.2 | PLAN-001 | AC-13(일치: `run_id`를 provenance 키로 고정하고 댓글·Issue 본문 필드 이름을 T4에 열거) | 필드 고정은 T3의 provenance 산출물을 구체화하며 다른 해소의 전제를 깨거나 새 공백을 만들지 않는다. | 자체 개정 |
| R3.5 | PLAN-001 | AC-17(일치: curated pre-merge content dedup과 RED probe를 배치), AC-18(일치: 편집 append와 analyzer prefix 판정을 유지) | run-independent 선행 dedup은 형제 policy plumbing과 양립하고 기존 prefix 및 편집 append 계약에 새 공백을 만들지 않는다. | 자체 개정 |
| R1.2 | PLAN-002 | AC-2(일치: 비-root `cwd` 실행과 sibling 부재 exit 2를 T2 계약 검사에 포함) | `__file__` 앵커는 caller 입력 검증 순서를 보존하며 fixture 소유권이나 merger 전제를 바꾸지 않는다. | 자체 개정 |
| R1.3 | PLAN-002 파급 | AC-3(일치: sibling loader를 기존 단일 script 안에 두고 CMD-5를 유지) | 로드 규칙은 신규 파일을 추가하지 않아 package allowlist와 다른 해소 사이에 새 공백을 만들지 않는다. | 치환 없음 |
| R2.2 | PLAN-001 파급 | AC-5(일치: T5의 reference 정규화 뒤 tracker observation 선행 dedup 순서를 유지) | content dedup은 같은 content version만 제거하고 서로 다른 origin 관측은 보존하므로 reference 계약을 깨지 않는다. | 치환 없음 |
| R2.4 | PLAN-004 파급 | AC-8(일치: hydration 결과를 curated envelope record로 전달) | incoming envelope 형태는 authoritative identity와 state를 바꾸지 않아 hydration 계약에 새 공백을 만들지 않는다. | 치환 없음 |
| R2.6 | PLAN-004 파급 | AC-10(일치: envelope와 dedup 제어값은 caller와 로컬 코드에서만 결정) | 원격 본문은 content hash 입력으로만 남아 generated_by나 identity 정책을 제어하지 못하므로 다른 해소와 모순되지 않는다. | 치환 없음 |
| R3.1 | PLAN-003 | AC-11(일치: T5만 expected bytes를 쓰고 CMD-6을 판정), AC-12(일치: T5 end-to-end corpus oracle 유지), AC-37(일치: fresh generator oracle 유지), AC-38(일치: T4의 existing generator 검사는 별도 유지) | T4와 T5의 쓰기 경계를 분리해 CMD-6 시점을 명확히 하며 incoming envelope 해소와 충돌하지 않는다. | 자체 개정 |
| R3.1 | PLAN-004 | AC-11(일치: analyzer 입력은 corpus envelope), AC-12(일치: bare list 금지), AC-37(일치: fresh curated name·revision 보존), AC-38(일치: existing envelope generator 보존) | incoming envelope 명시는 T5의 fixture 소유권을 보강하고 형제 기본 generator에 의존하는 새 공백을 닫는다. | 자체 개정 |
| R3.3 | PLAN-001 파급 | AC-14(일치: existing 관측 집합 탐색을 같은 global PR node identity record로 제한) | 선행 dedup의 탐색 키를 기존 global identity와 일치시켜 alias 병합이나 ID 보존 계약을 깨지 않는다. | 자체 개정 |
| R3.4 | PLAN-005 | AC-15(일치: default 경로의 동작 보존), AC-16(일치: explicit-only가 모든 merge 경로로 전달) | 실제 다섯 호출 지점과 세 pass-through 함수의 무동작 변경 경계를 명시해 curated dedup 전제를 깨지 않는다. | 자체 개정 |
| R3.4 | PLAN-006 | AC-15(일치: characterization과 수정 전 RED를 구분), AC-16(일치: explicit-only RED의 unexpected-keyword 양상을 고정) | 테스트별 사전 상태를 구분해 plumbing 범위를 넓히지 않으며 PLAN-005의 호출 경로 판정과 모순되지 않는다. | 자체 개정 |
| R3.6 | PLAN-001 파급 | AC-19(일치: content dedup 뒤 authoritative projection 및 unknown-value 검사를 유지) | tracker 관측 필터는 authoritative PR state 계산을 바꾸지 않아 projection 계약에 새 공백을 만들지 않는다. | 치환 없음 |
| R4.1 | PLAN-004 파급 | AC-20(일치: curated corpus envelope와 별개로 manifest run의 name·revision을 계속 기록) | corpus 전달 형태를 명시해도 run/page/gap provenance는 manifest에 남으므로 두 provenance 경계가 모순되지 않는다. | 치환 없음 |
| R5.1 | PLAN-003 파급 | AC-26(일치: T5가 쓰는 expected bytes도 합성 CLI output으로 제한) | fixture 소유권을 T5로 단일화해 private runtime 입력이 committed oracle에 섞이는 새 공백을 만들지 않는다. | 자체 개정 |
| R5.2 | PLAN-002 파급 | AC-27(일치: sibling 부재와 비-root 실행에서도 GitHub write 및 추가 network는 0회) | 로드 preflight는 GET runner 이전에 끝나므로 read-only 정책이나 외부 부작용 경계를 깨지 않는다. | 치환 없음 |
| R6.3 | PLAN-001 및 PLAN-003 파급 | AC-30(일치: T7은 확정 fixture와 revision만 사용), AC-31(일치: unchanged/edited 재수집 GREEN 판정 유지), AC-32(일치: 기존 안전 행동 회귀 유지) | dedup RED와 fixture 작성 시점을 명확히 해 독립 평가가 미확정 oracle을 소비하는 공백을 만들지 않는다. | 자체 개정 |
