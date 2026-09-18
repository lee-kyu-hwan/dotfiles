## 라운드 2 개정

라운드 1 공식 리뷰의 `PLAN-001`~`PLAN-006`과, `revision_check.py`가 결정적으로 잡아낸 `AC 등장 행에 판정수단 동반` 결함(모든 태스크의 `대상 AC:` 줄이 추적행의 판정 명령·테스트 이름을 동반하지 않아 열여덟 칸이 전부 `empty`였다)을 함께 해소했다. 후자는 태스크 본문의 AC 표기만 정규화하므로 모든 요구사항이 touched로 잡힌다.

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | revision-check 결함(AC 등장 행 판정수단 누락) | AC-1(일치: T2 대상 AC 줄이 CMD-2와 test_settings_compat_verifier_argv를 동반), AC-2(일치: 같은 줄이 test_settings_compat_enrollment_argv를 동반) | 표기 정규화만 수행해 T2의 argv 하드닝 내용과 판정 대상을 바꾸지 않으므로 다른 해소의 전제를 깨지 않는다. | 자체 개정 |
| R1.2 | PLAN-001, PLAN-002, PLAN-005 | AC-3(일치: role 최종 argv 하드닝 전제가 계약 확장 뒤에 성립), AC-17(일치: 네 계약 상수 동기화와 fixture override 기반 미광고 두 경우를 T1 안에서 판정) | 공용 fixture helper 기본 광고 목록을 먼저 올리고 네 계약 상수를 한 묶음으로 바꾸므로 중간 Red 구간이 전체 suite 판정에 노출되지 않으며 다른 해소의 전제를 깨지 않는다. | 자체 개정 |
| R1.3 | PLAN-004 | AC-4(일치: positive control이 구현 전 확정적으로 실패하고 negative control은 전후 모두 통과), AC-16(일치: 같은 우회 분기가 교차 회귀의 호환성 축을 성립시킴) | T4의 Red를 관측 가능한 positive control로 바꿔 G3을 충족시키며 negative control을 유지해 미하드닝 경로의 fail-closed 판정을 약화하지 않는다. | 라운드 1의 기대("분기 구분 assert에서 실패")에 대응하는 assert가 테스트 서술에 없어 positive control 서술로 치환했다. |
| R1.4 | revision-check 결함(AC 등장 행 판정수단 누락) | AC-5(일치: T9 대상 AC 줄이 CMD-4와 test_settings_compat_live_identity_projection을 동반) | live projection 판정 내용과 opt-in 경계를 바꾸지 않는 표기 정규화이며 새 공백을 만들지 않는다. | 자체 개정 |
| R2.1 | revision-check 결함(AC 등장 행 판정수단 누락) | AC-6(일치: T6 대상 AC 줄이 CMD-1과 test_settings_compat_profile1_status를 동반) | 16키 fixture 계약과 `ready`/exit 0 판정은 그대로이므로 R1.3의 우회 분기 해소와 모순되지 않는다. | 자체 개정 |
| R2.2 | revision-check 결함(AC 등장 행 판정수단 누락) | AC-7(일치: T6 대상 AC 줄이 CMD-2와 test_settings_compat_profile1_launch_e2e를 동반) | role launch E2E의 판정 대상과 session exec 1회 기대를 바꾸지 않는다. | 자체 개정 |
| R2.3 | revision-check 결함(AC 등장 행 판정수단 누락) | AC-8(일치: T6 대상 AC 줄이 test_settings_compat_profile2_enrollment_to_ready를 동반), AC-9(일치: T7 대상 AC 줄이 test_settings_compat_documentation_contract를 동반) | profile2 전경 enrollment 금지 전제와 세 단계 lifecycle 순서를 그대로 두므로 자동 실행 금지 제약을 깨지 않는다. | 자체 개정 |
| R3.1 | revision-check 결함(AC 등장 행 판정수단 누락) | AC-10(일치: T5 대상 AC 줄이 test_settings_compat_auth_status_sentinel을 동반), AC-11(일치: 같은 줄이 test_settings_compat_role_launch_sentinel을 동반) | sentinel negative control 선행 증명 절차를 바꾸지 않으므로 보안 판정 강도가 유지된다. | 자체 개정 |
| R3.2 | PLAN-001, PLAN-002 | AC-12(일치: 신규 test_settings_compat_*는 기본 격리 모드 유지), AC-13(일치: 기존 29개 본문 불변), AC-14(일치: fixture helper와 test_portable_cli_contract 상수 동기화 뒤에도 기존 92개 통과) | 기존 테스트 편집을 fixture helper 1곳과 계약 상수 1곳으로 명시 한정(G12)해 "기존 121개 보존" 제약과 T1이 더는 모순되지 않는다. | 라운드 1의 "기존 92개 테스트는 변경하지 않는다" 선언이 T1과 실행 불가능한 모순을 만들어 G12의 한정 허용으로 치환했다. |
| R3.3 | PLAN-003, PLAN-006 | AC-9(일치: 두 문서의 profile2 block 판정 내용 불변), AC-15(일치: 허용 집합은 그대로 10개 파일이며 frozen evidence 문서는 여전히 범위 밖), AC-18(일치: 설정 격리 block 판정 내용 불변) | 설치 계약 checker를 배포 게이트에서 빼고 CMD-4·CMD-2로 대체해 G7 허용 집합을 넓히지 않고도 배포 전 호환성 확인이 실제로 통과 가능해지며, 행 범위 정정은 참조 정확도만 바꾼다. | 라운드 1이 게이트로 지정한 checker가 이번 변경 이전에 이미 exit 1로 실패함을 실측해 대체 확인과 후속 작업 분리로 치환했다. |
