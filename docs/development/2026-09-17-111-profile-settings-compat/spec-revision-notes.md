## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | SPEC-004, SPEC-005 | AC-1(일치: exact argv 계약 유지), AC-2(일치: 합성 분기를 끄고 실제 fake Claude argv 캡처) | argv 순서의 live 판정과 enrollment subprocess 판정이 같은 exact 명령을 공유해 다른 해소의 전제를 깨거나 새 공백을 만들지 않는다. | 자체 개정 |
| R1.2 | SPEC-003 | AC-3(일치: 최종 role argv 하드닝 유지), AC-17(일치: manifest·런타임·설치 checker required-option 동기화와 미광고 실패 고정) | CLI 계약 확대가 role argv의 exact-one 검사와 결합되며 R3.3 변경 범위 및 scope 검사에도 함께 반영되어 새 공백을 만들지 않는다. | 자체 개정 |
| R1.3 | SPEC-006 | AC-4(일치: 미하드닝 경로 fail-closed 유지), AC-16(일치: trusted verifier 위임과 role 경계를 한 시나리오에서 확인) | status의 trusted verifier 위임 조건을 본문에 고정해 prescan 예외가 임의 direct 경로로 넓어지지 않으며 다른 보안 해소를 깨지 않는다. | 자체 개정 |
| R1.4 | SPEC-004 | AC-5(일치: baseline과 exact-order 하드닝 argv 및 canonical projection을 함께 판정) | argv 순서 검증을 canonical identity 비교와 같은 read-only probe에 추가해 값 비노출 전제를 유지하고 새 공백을 만들지 않는다. | 자체 개정 |
| R2.1 | SPEC-001 | AC-6(일치: 16개 키 이름·JSON 타입 표를 그대로 참조) | 실제 값을 기록하지 않은 단일 fixture 계약이 status 판정을 고정하고 AC-7·AC-16과 같은 입력을 공유하므로 다른 해소를 깨지 않는다. | 자체 개정 |
| R2.2 | SPEC-001 | AC-7(일치: 16개 키 표의 exact 키 집합·JSON 타입을 직접 참조) | role launch가 status와 같은 16개 키 입력을 사용해 호환성 판정이 갈라지지 않으며 CLI required-option 해소와도 모순되지 않는다. | 자체 개정 |
| R2.3 | SPEC-002 | AC-8(일치: 합성 lifecycle 순서 유지), AC-9(일치: 두 문서의 exact 명령·status·exit·순서·경계 문구를 문자 단위로 고정) | profile2 lifecycle의 실행 결과와 문서 block이 같은 세 단계 계약을 사용해 자동 enrollment 금지 전제를 깨거나 새 공백을 만들지 않는다. | 자체 개정 |
| R3.2 | SPEC-002, SPEC-003, SPEC-005 | AC-12(일치: 새 회귀도 기본 격리를 유지), AC-13(일치: account suite 전체 회귀 유지), AC-14(일치: orchestrator suite 전체 회귀와 live opt-in 유지) | enrollment argv의 비합성 예외, CLI option 검사, 문서 검사를 fake executable·임시 경로 안에 두어 기존 전체 suite와 live probe 경계를 깨지 않는다. | 자체 개정 |
| R3.3 | SPEC-002, SPEC-003 | AC-9(일치: exact profile2 문서 block), AC-15(일치: roles.toml과 설치 계약 checker를 허용 범위에 포함), AC-18(일치: 설정 격리·profile1 호환성 문구와 profile2 block을 회귀 검사) | 문서 객관화와 CLI 계약 파일 확대를 exact 범위·scope 검사·문서 검사에 동시에 반영해 서로의 전제를 깨거나 새 공백을 만들지 않는다. | 자체 개정 |
