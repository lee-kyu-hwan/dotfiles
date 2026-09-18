## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | PLAN-011 | AC-1(일치: T5의 입력 계약은 그대로이고 chezmoi scanner 근거만 보강됨) | PLAN-011 실측 근거는 다른 해소의 runner·harness 전제를 바꾸지 않는다. | 라운드 1의 미확인 플래그 우려를 chezmoi v2.70.0 실측이 반증해 근거 인용으로 대체함 |
| R1.2 | PLAN-011 | AC-2(일치: session/profile 독립성 유지), AC-3(일치: profile 추론 계약 유지) | T5의 실측 인용은 profile 선택과 network sentinel 해소에 새 의존성을 만들지 않는다. | 라운드 1의 미확인 플래그 우려를 chezmoi v2.70.0 실측이 반증해 근거 인용으로 대체함 |
| R1.3 | PLAN-013 | AC-4(일치: branch E2E를 변수 없이도 실행), AC-5(일치: PR E2E를 변수 없이도 실행) | deny 강화 mode와 변수 없는 실행을 함께 고정해 CMD-13의 no-skip 전제를 보존한다. | 자체 개정 |
| R10.1 | PLAN-012 | AC-42(일치: discovery ID에 결정적으로 tests. 접두를 붙여 manifest와 대조) | 정규화는 기존 60-ID manifest와 unique -k 등식을 바꾸지 않는다. | 자체 개정 |
| R10.2 | PLAN-009, PLAN-012, PLAN-013, PLAN-014, PLAN-015 | AC-43(일치: CMD-12 정본 유지), AC-44(일치: CMD-13 discovery 정규화와 no-skip 적용), AC-45(일치: diff review 순서 유지), AC-46(일치: allowlist 밖 경로 0건의 subset 판정) | CMD-28 추가, runner 정규화, network 변수 계약, portable checker 정정과 subset scope gate가 서로의 통과 조건을 깨지 않는다. | 치환 없음 |
| R10.3 | PLAN-009, PLAN-013, PLAN-015 | AC-46(일치: pre-existing dirty prefix 면제 뒤 allowlist 밖 변경 0건), AC-48(일치: operator handoff 계약 유지) | final gate에 CMD-28을 넣어도 operator-only merge/apply와 source scope 전제는 그대로다. | 자체 개정 |
| R10.4 | PLAN-012 | AC-52(일치: root 선삽입으로 exact module/direct ID load 성립), AC-55(일치: temp PYTHONPATH module과 runner nonzero 교차검사 유지) | root 선삽입은 CMD-20/CMD-21의 temp module entry를 제거하지 않아 negative gate를 깨지 않는다. | 자체 개정 |
| R10.5 | PLAN-014 | AC-53(일치: portable fake가 정상 version/help와 네 줄 probe log를 제공하고 변경은 두 tests 파일에 한정) | 정상 shim은 실제 installed-CLI help-only probe를 우회하지 않고 PLAN-016 예외 범위와도 일치한다. | 자체 개정 |
| R2.1 | PLAN-009 | AC-6(일치: 세 ai-session 회귀 case 존재를 CMD-28 N≥22로 구속) | 수집 하한만 추가하며 workspace profile schema 판정 이름과 60-ID manifest를 바꾸지 않는다. | 자체 개정 |
| R2.2 | PLAN-009 | AC-7(일치: 세 ai-session 회귀 case 존재를 CMD-28 N≥22로 구속) | 신규 command에 -k를 추가하지 않아 canonical repository mapping의 command-table 등식을 보존한다. | 자체 개정 |
| R2.3 | PLAN-009 | AC-8(일치: mixed-deployment 회귀 case를 포함한 module 수집 N≥22) | CMD-12 정본 문자열은 유지되고 CMD-28만 Plan 보조 gate로 추가된다. | 자체 개정 |
| R3.1 | PLAN-011 | AC-10(일치: containment test 계약 유지), AC-11(일치: TOCTOU test 계약 유지) | chezmoi flag 실측 인용은 path containment나 rollback 순서를 바꾸지 않는다. | 라운드 1의 미확인 플래그 우려를 chezmoi v2.70.0 실측이 반증해 근거 인용으로 대체함 |
| R3.2 | PLAN-013 | AC-12(일치: lazy creation E2E를 변수 없이도 실행), AC-49(일치: cold-start case를 deny mode와 기본 mode 모두 실행) | unset 환경에서도 skip을 금지해 CMD-16과 CMD-13의 실행 결과가 모순되지 않는다. | 자체 개정 |
| R3.3 | PLAN-011 | AC-13(일치: v2.70.0에서 다섯 global flag와 두 execute-template flag 실재를 근거로 고정) | 실측된 기존 격리 수단을 유지하므로 대체 수단이 다른 scanner 전제를 만들지 않는다. | 라운드 1의 PLAN-011 우려가 chezmoi v2.70.0 실측으로 반증되어 대체 설계 없이 근거 인용으로 치환됨 |
| R3.4 | PLAN-013 | AC-14(일치: canonical layout case가 deny 강화 mode와 변수 없는 discovery에서 모두 실행) | network mode는 destination_basename과 workmux_handle의 출처를 바꾸지 않는다. | 자체 개정 |
| R4.1 | PLAN-011 | AC-15(일치: single backend 계약 유지), AC-51(일치: shared module identity 계약 유지) | scanner flag 근거는 backend와 loader 소유권 경계를 변경하지 않는다. | 라운드 1의 미확인 플래그 우려를 chezmoi v2.70.0 실측이 반증해 근거 인용으로 대체함 |
| R5.1 | PLAN-013 | AC-19(일치: real Workmux dry-run 계약 유지), AC-20(일치: global config E2E를 두 mode에서 실행), AC-49(일치: cold-start E2E를 두 mode에서 실행) | 강화 sentinel은 Workmux dry-run/apply 의미를 바꾸지 않고 network hit만 fail closed한다. | 자체 개정 |
| R5.3 | PLAN-013 | AC-23(일치: session 선택 E2E가 환경변수 유무로 skip되지 않음) | 변수 계약은 session 이름과 profile 독립성에 새 입력을 추가하지 않는다. | 자체 개정 |
| R9.3 | PLAN-013, PLAN-016 | AC-41(일치: create-worktree harness는 기본·deny mode 모두 actual access 0건이고 CMD-12 help-only probe는 sentinel 밖의 명시적 예외) | help-only 예외는 인증·network·mutation이 없고 E2E sentinel을 우회하지 않아 PLAN-013의 zero-hit 전제를 깨지 않는다. | 자체 개정 |
