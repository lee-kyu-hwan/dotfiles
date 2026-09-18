## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | SPEC-02 | AC-1 (일치 — 보호 대상 `### Plan` 밖의 새 author 절로 작성 주체 계약을 고정) | 외부 절 선택이 이름 규약이나 공통 기준선 결정을 깨뜨리지 않고 기존 Plan bytes 보호 공백도 만들지 않는다. | 자체 개정 |
| R3.5 | SPEC-05 | AC-17 (일치 — expected artifact 기본값과 단일 인자 회귀를 함께 판정) | 선택적 매개변수는 artifact mismatch 검증을 유지하면서 기존 호출 호환성 공백을 닫는다. | 자체 개정 |
| R4.3 | SPEC-04 | AC-21 (일치 — 정책 문언과 validator 판정 가능 범위를 분리) | supplied target 집합은 content contract에, payload 내부 규칙은 validator에 배정해 다른 해소의 테스트 규약을 깨뜨리지 않는다. | 자체 개정 |
| R7.1 | SPEC-03 | AC-31 (일치 — 다섯 파일 기준선과 maintenance 실행을 함께 고정) | 갱신된 기준선을 테스트 보존과 절 보존 양쪽에 동일하게 적용해 fifth-file 실패와 보존 기준 발산을 동시에 막는다. | 자체 개정 |
| R7.2 | SPEC-01, SPEC-04 | AC-32 (일치 — `plan_author` 또는 `plan_readiness` 공통 규약과 validator 범위를 반영) | 하나의 이름 규약을 content·validator·state 가드가 공유하므로 공허 통과 해소 사이에 새 모순이 없다. | 자체 개정 |
| R7.3 | SPEC-01, SPEC-04 | AC-32 (일치 — state 판정을 CMD-3 양수 선택 실행으로 추가) | state 사례를 CMD-2에서 분리해 CMD-3에 배정하면서 R7.2의 동일 이름 규약을 재사용하므로 판정 공백이 없다. | 자체 개정 |
| R7.4 | SPEC-04 | AC-33 (일치 — 복수 판정 명령을 식별자 문법에 맞게 모두 인식시킴), AC-34 (일치 — 기존 byte 불변 판정은 변경하지 않음) | 복수 CMD 구분을 공백으로 통일해 기존 전체 suite와 보존 판정의 의미를 바꾸지 않고 유령 판정 수단 가능성을 없앤다. | 자체 개정 |
| R7.5 | SPEC-01, SPEC-02, SPEC-03 | AC-1 (일치 — 새 `### Plan author` 절과 보존 명령을 요구), AC-35 (일치 — 정확한 version 단언과 동일 `QG_BASE`의 두 helper 실행을 요구) | 외부 절 결정, 정확한 version 판정, 공통 기준선 이동을 한 계약으로 묶어 어느 해소도 다른 해소의 전제를 깨뜨리지 않는다. | 자체 개정 |
