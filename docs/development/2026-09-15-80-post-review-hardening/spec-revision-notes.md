## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R3.1 | SPEC-001 | AC-4(일치: 승인된 한국어 첫-token 및 delimiter 문법과 보존 case를 판정) | D1 승인 확정은 R3.2~R3.4의 label 문법 전제를 깨지 않고 승인 대기 공백을 닫는다. | 자체 개정 |
| R3.2 | SPEC-001 | AC-5(일치: 영어 example 복수형·경계·설명형 보존을 판정) | ASCII 글자 경계 확정은 R3.1의 한국어 경계와 R3.4의 URL 제거 전제를 바꾸지 않고 새 분류 공백을 만들지 않는다. | 자체 개정 |
| R3.3 | SPEC-001 | AC-6(일치: 영어 notice 복수형·announcement·경계를 판정) | notice 계열의 확정 문법은 R3.2와 같은 경계를 사용해 다른 해소의 전제를 깨거나 새 CLI 표면을 만들지 않는다. | 자체 개정 |
| R3.4 | SPEC-001 | AC-7(일치: URL span 제거 뒤 F3d가 submission임을 판정) | URL 제거 우선순위는 R3.1~R3.3의 keyword 입력을 한정하므로 다른 해소와 모순되지 않고 URL 유래 오탐 공백을 닫는다. | 자체 개정 |
| R6.1 | SPEC-003 | AC-13(일치: 재현된 두 번째 temporary write 실패만 새 계약으로 판정) | 검증 범위를 재현 경로로 한정해 Non-goal의 미재현 restore 실패 전제를 깨지 않고 미검증 단계의 신규 보장 공백을 제거한다. | 자체 개정 |
| R7.1 | SPEC-005 | AC-14(일치: 이번 run의 usable 수확으로 failed/partial을 판정) | #80의 complete/partial 오보고 방지 의도를 명시해 다른 해소를 축소하지 않고 원 계약과의 해석 공백을 닫는다. | 자체 개정 |
| R8.1 | SPEC-004 | AC-15(일치: 추가 인자와 접두 축약의 기존 거부 결과를 판정) | 부정 단언은 argparse 등록 해소를 유지하면서 다른 요구사항의 전제를 깨지 않고 신규 CLI 표면 공백을 닫는다. | 자체 개정 |
| R9.1 | SPEC-002 | AC-17(일치: 두 절대 경로를 `<worktree>` 하나로만 치환함을 판정) | placeholder 어휘를 CMD-8과 일치시켜 다른 해소의 전제를 깨지 않고 도달 불가 placeholder 공백을 제거한다. | 자체 개정 |
| R11.2 | 다른 해소의 파급으로 touched 판정(공식 finding 해소 아님) | AC-22 (일치: CMD-2 CMD-5 test_ac_22_contract_stdlib_synthetic_packaging 판정이 그대로다), AC-23 (일치: CMD-1 CMD-2 CMD-3 CMD-4 CMD-6 회귀 suite 판정이 그대로다) | 이 파급 행은 다른 해소의 전제를 깨지 않고 새 공백을 만들지 않는다. | 치환 없음 |
