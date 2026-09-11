## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | SPEC-001, SPEC-004, SPEC-008 | AC-1(일치: 기존 예산 소진 귀속), AC-2(일치: 분할 불변식 단정 보강), AC-3(일치: 종료 코드 우선순위 유지) | 분할 위반만 무출력 종료 2이고 완전 분할된 예산 소진은 종료 3이어서 R1.3의 입력 오류 종료 2 및 기존 예산 우선순위와 충돌하거나 새 공백을 만들지 않는다. | 자체 개정 |
| R1.2 | SPEC-004 | AC-4(일치: skipped 분기), AC-5(일치: 두 금지 구획 직접 단정) | 실제 record와 겹치는 두 금지 구획을 직접 단정하므로 존재하지 않는 record 분기로 우회하는 공백을 닫고 R1.1의 상호 배타성 요구를 약화하지 않는다. | 자체 개정 |
| R2.1 | SPEC-003, SPEC-006 | AC-8(일치: record 매핑·무출력), AC-9(일치: recheck 매핑·차단) | 정확한 10경로 매핑은 매핑 밖 대조군과 구분되고 record 종료 2의 무출력 계약은 recheck의 R3.1 차단 전제를 깨지 않는다. | 자체 개정 |
| R2.2 | ORCH-2 | AC-10(일치: policy), AC-11(일치: duplicate search), AC-23(일치: community profile 기본값·미완료 stage) | community profile은 기존 policy·duplicate 판정과 같은 malformed-2xx 원칙을 쓰되 기본값과 `stages_completed`만 보존하므로 기존 판정과 겹치거나 새 상태 공백을 만들지 않는다. | 자체 개정 |
| R2.3 | SPEC-006 | AC-12(일치: guard 무출력) | allowlist 위반의 무출력 종료 2는 transport 재시도 경로와 분리되어 기존 OSError·HTTP 실패 계약을 깨지 않는다. | 자체 개정 |
| R3.1 | SPEC-002 | AC-15(일치: 8키·승계 4필드), AC-16(일치: snapshot·top-level 불변식) | 실패 snapshot은 정확한 8키, 승계 4필드 동일성, top-level/latest 일치를 함께 만족하고 top-level 변경도 기존 9개 가변 필드 안이어서 evidence 세탁이나 default-deny 공백을 만들지 않는다. | 자체 개정 |
| R4.1 | SPEC-005, SPEC-007, ORCH-1 | AC-19(일치: 정확 문장 단정), AC-21(일치: 폐쇄 계약·동적 revision), AC-22(일치: 전체 스위트) | 문서 substring 검사·날짜 literal 제약·실행 가능한 전체 discover 명령은 같은 계약 스위트 안에서 독립적으로 판정되며 폐쇄 상수 집합이나 미검증 라이브 경로 주장을 바꾸지 않는다. | 자체 개정 |
| R4.2 | CODE-005 | AC-20(일치: filtered names 기반 count·hash) | entry_count와 canonical content hash가 같은 정규화 names를 기준으로 하므로 R2.2의 malformed payload 판정과 충돌하거나 새 공백을 만들지 않는다. | 자체 개정 |
