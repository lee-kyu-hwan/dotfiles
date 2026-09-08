## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.3 | PLAN-001 | AC-4 (일치 — T3가 no_changes terminal report를 직접 생성) | T3의 terminal writer가 T8의 full renderer보다 먼저 최소 보고서를 보장한다 | 소유권을 옮기지 않았다. T3의 실패 상태 보존 경계에 no_changes 보고서 작성을 추가하는 편이 더 좁다 |
| R1.4 | PLAN-001, PLAN-007 | AC-5 (일치 — T3가 prompt·started 기록·최소 sidecar·terminal report를 생성) · AC-6 (일치 — 임시 fixture root에 정확한 .gitignore를 생성) | run-directory 계약과 test-state root가 모두 T3 실행 경계에 있다 | 소유권을 옮기지 않았다. AC-5의 최소 산출물과 AC-6의 격리 root를 T3가 함께 만든다 |
| R1.1 | PLAN-001 | AC-1 (일치 — T3가 입력 고정 executor를 생성) · AC-2 (일치 — 같은 executor가 SHA와 변경 파일 경계를 생성) | terminal artifact writer는 기존 입력 경계 뒤에만 실행된다 | 소유권을 옮기지 않았다. T3의 구현 보강이 인자 계약을 바꾸지 않는다 |
| R1.2 | PLAN-001 | AC-3 (일치 — build_round_zero_prompts가 고정 prompt를 생성) | prompt 구성과 terminal report는 같은 T3 run-directory 증거를 사용한다 | 소유권을 옮기지 않았다. 기존 prompt builder의 이름과 결과를 명시했다 |
| R2.1 | PLAN-002 | AC-7 (일치 — T2가 Claude reviewer 선택 contract를 생성) · AC-8 (일치 — 같은 template이 closed severity contract를 생성) | allowlist는 reviewer template의 Codex 호출 안전성만 좁힌다 | 소유권을 옮기지 않았다. T2 정적 계약을 allowlist 방식으로 보강했다 |
| R2.2 | PLAN-002, PLAN-001 | AC-9 (일치 — T2 allowlist가 Codex 호출 template을 생성) · AC-10 (일치 — T3 executor가 schema 위반 등록 차단을 생성) | 정적 명령 contract와 실행 schema 차단은 서로 다른 T2·T3 경계다 | 소유권을 옮기지 않았다. 금지 열거를 allowlist로 치환했다 |
| R2.3 | PLAN-002, PLAN-004 | AC-11 (일치 — 전체 스킬 트리 부재 scan이 allowlist 및 placeholder 규약으로 무매치) · AC-12 (일치 — reviewer 정적 계약은 T2 schema/template가 생성) | CMD-4는 T1 이후 부재 불변식이고 T2의 allowlist가 그 불변식을 공허하지 않게 지킨다 | 소유권을 옮기지 않았다. pattern 열거 대신 허용 플래그 집합을 검사한다 |
| R2.4 | PLAN-001 | AC-13 (일치 — T3 실제 executor의 보존 prompt와 dispatch 기록을 생성) · AC-14 (일치 — 같은 executor가 양쪽 시작 뒤 판독 gate를 생성) | 임시 run root가 실제 dispatch·판독 순서의 증거를 격리한다 | 소유권을 옮기지 않았다. T3 run-state root를 명시했을 뿐 독립성 소유는 유지한다 |
| R3.1 | PLAN-003 | AC-15 (일치 — schema required 선언은 T2가 유지) · AC-16 (일치 — T4의 normalize_reviewer_findings가 실행 정규화를 생성) | 정적 schema와 실행 정규화의 경계가 함수명으로 연결된다 | 소유권을 옮기지 않았다. T4 entry point 이름만 확정했다 |
| R3.2 | PLAN-003 | AC-17 (일치 — derive_finding_id가 group과 여섯 입력으로 ID를 생성) · AC-18 (일치 — 같은 순수 ID 함수의 입력별 분리를 fixture가 검사) | T7이 group을 공급하고 T4가 ID를 파생하는 순서를 보존한다 | 소유권을 옮기지 않았다. 명시 signature로 소비자와 생산자를 고정했다 |
| R3.3 | PLAN-005 | AC-19 (일치 — finding 단위 거부는 재시도를 증가시키지 않음) · AC-20 (일치 — 거부 finding은 보정·재사용하지 않음) | record-level 거부와 source-level schema 재요청을 서로 분리한다 | 소유권을 옮기지 않았다. T4 fixture 불변식을 보강했다 |
| R3.4 | PLAN-003 | AC-71 (일치 — normalize_reviewer_findings가 공통 body 구조를 생성) | 정규화 entry point가 A/B body의 형식 누설 제거를 소유한다 | 소유권을 옮기지 않았다. T4 정규화 함수명을 확정했다 |
| R4.1 | PLAN-002 | AC-21 (일치 — T2 critique schema contract가 입력 구조를 생성) · AC-22 (일치 — 같은 contract가 reviewer 상호 비평 경계를 생성) | T2 schema 정적 계약은 T5 critique validation보다 먼저 존재한다 | 소유권을 옮기지 않았다. safety 문언은 critique schema 산출물을 바꾸지 않는다 |
| R4.2 | PLAN-002 | AC-23 (일치 — T2 critique schema contract가 fresh input 제한을 생성) | T2의 source literal 부재 규약은 critique 입력 contract와 독립이다 | 소유권을 옮기지 않았다. 정적 contract만 명확히 했다 |
| R4.3 | PLAN-003 | AC-24 (일치 — validate_and_record_critique가 근거 검증을 생성) · AC-25 (일치 — 같은 함수가 무효 반증 강등을 생성) | T5가 T3 최소 sidecar를 critique provenance로 확장한다 | 소유권을 옮기지 않았다. T5 경계 함수명을 확정했다 |
| R4.4 | PLAN-003 | AC-26 (일치 — validate_and_record_critique가 신규 finding provenance를 기록) | T4 정규화 entry point를 T5 신규 finding 경로가 소비한다 | 소유권을 옮기지 않았다. producer-consumer 함수를 명시했다 |
| R5.1 | PLAN-003 | AC-27 (일치 — advance_critique_rounds가 round 1 조건을 생성) · AC-28 (일치 — 같은 함수가 round 2 조건을 생성) · AC-29 (일치 — 같은 함수가 최대 라운드를 제한) | 라운드 상태 전이와 종료 선택자를 별도 callable로 둔다 | 소유권을 옮기지 않았다. T6 상태 전이 함수명을 확정했다 |
| R5.2 | PLAN-003 | AC-30 (일치 — select_termination_reason이 quiet 종료를 선택) · AC-31 (일치 — 같은 선택자가 요청 라운드 종료를 선택) | 종료 사유 우선순위는 T6 selector 하나에서 결정된다 | 소유권을 옮기지 않았다. selector 이름과 책임을 고정했다 |
| R5.3 | PLAN-003 | AC-32 (일치 — select_termination_reason이 신규 high 종료를 선택) | 종료 후보는 renderer 이전 T6에서 하나로 축소된다 | 소유권을 옮기지 않았다. 결정 함수명만 추가했다 |
| R5.4 | PLAN-003 | AC-33 (일치 — select_termination_reason이 priority 단일 사유를 선택) · AC-34 (일치 — advance_critique_rounds가 drift 중단을 생성) | 종료 전순서와 drift 상태 전이가 명시적으로 분리된다 | 소유권을 옮기지 않았다. T6의 두 callable을 명시했다 |
| R6.2 | PLAN-003 | AC-37 (일치 — assign_anonymous_groups가 교대 A/B 배정을 생성) · AC-38 (일치 — 같은 함수가 재현 가능한 배정을 생성) | group 공급이 ID 파생보다 먼저 일어난다 | 소유권을 옮기지 않았다. T7 group allocator 이름을 확정했다 |
| R6.3 | PLAN-003 | AC-39 (일치 — sort_and_shuffle_findings가 ASCII 정렬 뒤 셔플을 생성) · AC-40 (일치 — 같은 함수가 익명 view 마스킹을 위한 안정 순서를 제공) | group 배정 → ID 파생 → 정렬·셔플 순서가 유지된다 | 소유권을 옮기지 않았다. T7 ordering callable을 명시했다 |
| R6.1 | PLAN-002 | AC-35 (일치 — T2 synthesis schema contract가 fresh synthesizer 입력을 생성) · AC-36 (일치 — 같은 schema가 양 그룹 ID 배열 required를 생성) | T2 schema 선언은 T7 익명 view와 T8 renderer보다 먼저 존재한다 | 소유권을 옮기지 않았다. allowlist 보강은 synthesis schema 소유를 바꾸지 않는다 |
| R6.4 | PLAN-002, PLAN-003 | AC-41 (일치 — T2 schema가 양 그룹 ID required를 생성) · AC-42 (일치 — T7 group allocation과 ID derivation이 분류 입력을 생성) | schema 선언과 group 공급 실행은 T2·T7에 분리된다 | 소유권을 옮기지 않았다. named group allocator로 hand-off를 고정했다 |
| R6.5 | PLAN-002, PLAN-003 | AC-43 (일치 — T7이 불일치 synthesis 출력을 보존) · AC-44 (일치 — T2가 Codex synthesis template 부재 contract를 생성) | T7 runtime output과 T2 static no-Codex contract가 분리된다 | 소유권을 옮기지 않았다. functions와 allowlist만 명시했다 |
| R7.1 | PLAN-001, PLAN-003 | AC-45 (일치 — T8 full render_report가 정상 run report를 생성) · AC-46 (일치 — 같은 renderer가 단일 종료 사유 절을 생성) | T3의 terminal subset은 먼저 존재하고 T8이 정상 종합 절을 확장한다 | 소유권을 옮기지 않았다. terminal writer와 full renderer를 같은 callable의 단계적 확장으로 정했다 |
| R7.2 | PLAN-003 | AC-47 (일치 — full render_report가 sidecar 출처를 복원) · AC-48 (일치 — full render_report가 불일치 절을 생성) | T8만 full sidecar 복원과 불일치 출력을 소유한다 | 소유권을 옮기지 않았다. renderer interface 이름을 확정했다 |
| R7.3 | PLAN-002, PLAN-004 | AC-49 (일치 — GitHub 쓰기 부재 scan은 전체 트리에서 무매치) · AC-50 (일치 — 목적 기반 no-mutation contract가 유지) | CMD-5는 T1 이후 부재 불변식이며 T2는 pattern을 source에 쓰지 않는다 | 소유권을 옮기지 않았다. scan 범위를 줄이지 않고 source literal을 제거하는 규약을 택했다 |
| R8.1 | PLAN-001 | AC-51 (일치 — T3 terminal report가 실패 출처·원인·상태를 출력) · AC-52 (일치 — failure state가 성공 0 finding으로 변환되지 않음) | reviewer_failure terminal writer가 failure state와 report를 같은 run에 보존한다 | 소유권을 옮기지 않았다. T3가 이미 failure state를 소유한다 |
| R8.2 | PLAN-005 | AC-53 (일치 — 전체 schema 위반만 한 번 재요청하고 재위반 뒤 제외) · AC-54 (일치 — 제외 source의 원문·검증 오류가 provenance에 보존) | source-level 재요청은 T3, record-level 거부는 T4로 분리된다 | 소유권을 옮기지 않았다. 재요청 trigger를 전체 출력 schema 실패로 한정했다 |
| R8.3 | PLAN-001 | AC-55 (일치 — T3 terminal report와 sidecar가 timeout 재시도·stderr·exit를 기록) · AC-56 (일치 — 양쪽 실패가 synthesis 없이 비성공 종료) | timeout과 both-failure는 T3 terminal paths에서 완결된다 | 소유권을 옮기지 않았다. T3 failure-state 보존을 terminal output까지 확장했다 |
| R8.4 | PLAN-001 | AC-57 (일치 — T3가 single source에서 critique·양측 분류를 생략) · AC-58 (일치 — T3 terminal report가 single_reviewer 제한과 원인을 출력) | single_reviewer 상태는 full synthesis보다 앞서 T3에서 보고 가능하다 | 소유권을 옮기지 않았다. T3가 단일 출처 제어와 최소 보고를 함께 생성한다 |
| R9.2 | PLAN-006 | AC-61 (일치 — T1이 schemas와 scripts의 추적 가능한 .gitkeep을 포함한 여섯 구성 요소를 생성) · AC-62 (일치 — T1 file-map 계약이 책임 경로를 선언) | T1 pass 시점부터 checkout 재현 가능한 six-component 증거가 있다 | 소유권을 옮기지 않았다. 빈 디렉터리 대신 T1 생성 파일을 추가했다 |
| R9.1 | PLAN-006 | AC-59 (일치 — T1이 source와 target 배치 문서를 생성) · AC-60 (일치 — T1 test_contracts.py가 순수 배치 경로 함수를 생성) | tracked placeholder와 배치 path contract는 T1 골격에서 함께 재현된다 | 소유권을 옮기지 않았다. six-component 증거 보강이 배치 계약을 바꾸지 않는다 |
| R9.3 | PLAN-002, PLAN-003, PLAN-004 | AC-63 (일치 — deterministic boundary test가 SKILL.md의 오케스트레이션 전용 구조를 검사) · AC-64 (일치 — named Python boundaries가 모두 존재) · AC-65 (일치 — T2가 import 불변식을 고정하고 T3가 첫 scripts Python 비공허 검사를 제공) | 정적 import 계약은 T2, 비공허 scripts 관측은 T3, 전 경계 존재 판정은 T8에 있다 | 소유권을 옮기지 않았다. AC-65의 첫 비공허 시점과 함수 interface를 명시했다 |
| R9.4 | PLAN-002, PLAN-003 | AC-66 (일치 — T9 전체 suite가 실제 discovery를 확인) · AC-67 (일치 — 전체 트리 scan이 오류를 실패로 하고 무매치만 통과) · AC-68 (일치 — T1 verification 문서가 not configured를 선언) · AC-69 (일치 — full render_report가 입력 순서 불변 Markdown을 생성) · AC-70 (일치 — T9 spy가 외부 쓰기와 코드 수정을 0회로 보장) | T9 final scan은 T1 문서·T2 allowlist·T8 renderer를 모두 소비한다 | 소유권을 옮기지 않았다. full-tree scan의 안전 규약과 renderer 경계를 보강했다 |
