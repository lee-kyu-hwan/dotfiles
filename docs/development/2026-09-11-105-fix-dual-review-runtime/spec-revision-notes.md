## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.2 | SPEC-002 | AC-2(일치: Codex 모델·stdin 계약), AC-9(일치: live stdin 판정) | stdin 고정은 strict schema live 검증을 교착 없이 수행하게 하며 다른 해소의 전제를 깨지 않는다. | 자체 개정 |
| R1.3 | SPEC-001 | AC-3(일치: 확인 flag와 가변 인자 문서화) | 확인된 flag 집합과 stdin 규칙이 CMD-6의 실행 가능성을 뒷받침하며 production allowlist와 충돌하지 않는다. | 자체 개정 |
| R3.1 | SPEC-002 | AC-7(일치: 재귀 폐쇄와 keyword 보존), AC-9(일치: 미실증 provider 경로 검증) | Codex에서 수용된 keyword를 보존하면서 Claude·critique·synthesis의 공백은 live probe로 닫는다. | 자체 개정 |
| R3.2 | SPEC-002 | AC-8(일치: critique 항목 폐쇄), AC-9(일치: critique provider 수용 판정) | critique의 결정론적 구조 검사와 실제 provider 검사를 분리해 새 호환성 공백을 만들지 않는다. | 자체 개정 |
| R3.3 | SPEC-002, SPEC-008 | AC-9(일치: opt-in provider 판정), AC-15(일치: 기본 skip 판정), AC-19(일치: live probe 산출물 계약) | opt-in일 때만 실제 API를 호출하므로 provider 검증과 기본 suite의 무비용 실행이 양립한다. | 자체 개정 |
| R4.1 | SPEC-004 | AC-10(일치: 두 helper required paths), AC-11(일치: archive 포함 판정) | live helper를 명시적 배포 산출물로 추가해 packaging 목록과 archive 동등성 사이의 공백을 제거한다. | 자체 개정 |
| R4.2 | SPEC-004 | AC-10(일치: source 경로 판정), AC-11(일치: source/archive 동등성) | 두 helper를 source와 archive 양쪽에서 같은 상대 경로로 검사하므로 배포 경계가 일관된다. | 자체 개정 |
| R4.3 | SPEC-004 | AC-11(일치: helper 포함과 cache 제외를 함께 판정) | helper 포함 요구는 기존 runtime cache 제외 규칙을 약화하지 않고 동일 archive 판정에서 공존한다. | 자체 개정 |
| R5.1 | SPEC-003, SPEC-005 | AC-12(일치: 전부 거부 재시도와 일부 거부 무재시도) | group-independent 판정이 기존 일부 항목 거부 계약을 보존하면서 빈 리뷰의 보수적 실패 의미를 명확히 한다. | 자체 개정 |
| R6.1 | SPEC-001 | AC-1(일치: project 스킬·Python 진입점·no_changes 산출물) | 검증 전용 Python allowlist는 slash 실행을 가능하게 하지만 reviewer 생성 명령의 읽기 전용 계약은 바꾸지 않는다. | 자체 개정 |
| R6.2 | SPEC-005, SPEC-007 | AC-16(일치: source별 유효 producer와 phase 횟수), AC-17(일치: 계산된 접두사의 증가 run) | producer 기준과 동적 run-id 기준을 실제 파이프라인에 맞춰 고정해 서로 거짓 실패를 만들지 않는다. | 자체 개정 |
| R6.3 | SPEC-006, SPEC-008 | AC-15(일치: 기본 discover의 live skip), AC-18(일치: DRV와 Spec CMD 분리) | 번호 체계 분리는 기본 suite 판정 문구와 독립적이며 문서 참조 충돌을 제거한다. | 자체 개정 |
| R6.4 | SPEC-002, SPEC-004, SPEC-008 | AC-9(일치: 실제 provider 조합), AC-15(일치: 환경변수 부재 시 skip), AC-19(일치: 파일·인터페이스·evidence 계약) | 새 opt-in 산출물은 기본 실행을 네트워크에서 격리하면서 미실증 schema 경로를 검증한다. | 자체 개정 |
| R6.5 | SPEC-004, SPEC-005, SPEC-007 | AC-16(일치: E2E phase와 source 기준), AC-17(일치: 동적 run-id와 무변경), AC-20(일치: helper CLI 산출물 계약) | E2E helper의 정적 계약과 live 판정을 함께 묶어 producer·run-id 해소 사이에 새 자동화 공백을 만들지 않는다. | 자체 개정 |
