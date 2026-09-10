# Spec Revision Notes

## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.2 | SPEC-002 | AC-2(일치: 기존 CODE-002 partial·clone 대조 유지), AC-3(일치: `spec.md`의 code-search 경계를 명시적 문서 판정 대상으로 지정) | 문서 판정 대상만 명시해 CODE-002의 `available: false` 경로와 두 새 warning의 additive partial 조건 또는 종료 우선순위를 바꾸지 않는다. | 자체 개정 |
| R3.2 | SPEC-002 | AC-7(일치: cleanup warning·removed 사실성과 discovery/manifest partial·종료 3을 함께 단정), AC-9(일치: 기존 clone 다섯 필드와 실제 removed 값 보존) | cleanup warning을 additive partial 조건으로 넣어도 선행 종료 4와 예산 소진 종료 3을 깨지 않고 CODE-002의 기존 unavailable OR와 겹치면 동일한 종료 3으로 수렴하므로 새 공백이 없다. | 자체 개정 |
| R4.1 | SPEC-004 | AC-10(일치: additive shape의 정상 exclusion 대조 유지), AC-11(일치: additive `complete: false`가 partial 상태·종료 3과 연결됨) | R4.1의 필드 범위는 바꾸지 않고 AC-11의 상태 판정을 보강해 cleanup·static warning의 일관된 partial 처리와 CODE-002 경로를 침범하지 않는다. | 자체 개정 |
| R4.2 | SPEC-004 | AC-10(일치: intentional exclusion은 warning과 partial을 만들지 않음), AC-11(일치: read failure warning·complete false와 discovery/manifest partial·종료 3을 함께 단정) | static warning을 cleanup과 같은 additive partial 조건으로 처리해 종료 4 우선순위와 예산 소진 종료 3을 유지하고 CODE-002 unavailable 경로와 중복되어도 상태는 한 번의 partial이므로 다른 해소의 전제를 깨지 않는다. | 자체 개정 |
| R5.2 | SPEC-003 | AC-15(일치: `spec.md`의 I13 문서 전용 경계를 명시적 문서 판정 대상으로 지정) | 판정 대상 파일만 보강하므로 I13을 후속 문서화로만 남기는 승인 범위를 넓히지 않고 다른 해소와 충돌하지 않는다. | 자체 개정 |
| R6.1 | SPEC-003 | AC-16(일치: 전용 계약 테스트가 모든 폐쇄 집합·schema·clone shape·종료 집합과 우선순위를 직접 단정) | AC-16을 좁히지 않고 CMD-5의 독립 표적 테스트를 늘려 R6.1의 증명 범위를 유지했으며, 고친 전체 discovery 명령에 의존하지 않아 SPEC-001 해소와 새 검증 공백 없이 공존한다. | 자체 개정 |
| R6.2 | SPEC-001 | AC-17(일치: 대상 tests 디렉터리를 start/top-level로 함께 사용), AC-18(일치: 형제 tests 디렉터리를 start/top-level로 함께 사용), AC-19(일치: 형제 tests 디렉터리를 start/top-level로 함께 사용) | 세 명령의 import 가능성만 바로잡아 폐쇄 집합·종료 우선순위·CODE-002 및 두 새 warning의 partial 의미를 바꾸지 않고 전체 회귀 증거를 복원한다. | 자체 개정 |
| R6.3 | SPEC-003 | AC-20(일치: `spec.md`의 범위 무결성 절을 명시적 문서 판정 대상으로 지정) | 범위 증명의 문서 위치만 명시해 승인 파일 범위와 1·2·3차 문서·루트 `AGENTS.md` 불변 요구를 유지하며 다른 해소가 범위를 넓히지 못하게 한다. | 자체 개정 |
