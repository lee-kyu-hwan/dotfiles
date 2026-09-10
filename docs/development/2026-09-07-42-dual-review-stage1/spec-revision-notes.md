## 라운드 2 개정

라운드 1 리뷰(65점 REVISE, blocker SPEC-001·002·003·004)의 findings 11건 전부를 이 라운드에서 반영했다. 셋째 열은 `revision_check.py` 가 생성한 파급표의 `ripple[].acceptance_criteria` 를 그대로 순회해 채웠다.

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | SPEC-009 | AC-1(일치 — 두 표기를 같은 유효 입력 집합으로 판정), AC-2(일치 — 1·2 이외 거부를 두 표기 모두에서 판정) | canonical 입력 집합이 R5.1 의 라운드 예약 조건과 같은 표기를 쓴다. | 자체 개정 |
| R1.4 | SPEC-003, SPEC-008 | AC-5(일치 — 실디스패치 프롬프트·호출 순서·sidecar·run root .gitignore 를 산출물 경로 검사에 포함), AC-6(일치 — 결정적 대상 식별자와 단조 실행 구분자의 분리를 판정) | 프롬프트 보존이 독립성 증거를 만들고, 재실행마다 새 run directory 를 만들어 R8.2 의 제외 원문 보존을 덮어쓰지 않으며, R6.3 의 실행 구분자와 같은 값을 쓴다. | 자체 개정 |
| R2.1 | SPEC-002; 독립 사전 심사 High — `code-reviewer`의 `Critical`·`Important` 원문 severity와 severity 없는 나머지 생산자의 변환 규칙 부재 | AC-7(일치 — 다섯 생산자 선택과 자유 서술 라벨 요구를 같은 계약 테스트에서 판정), AC-8(일치 — code-simplifier 배제는 변경 없이 같은 계약 테스트가 유지) | 대소문자 무시 변환표가 `Critical`→`critical`, `Important`→`high`를 덮고 severity 없는 생산자는 `medium` 기본값을 쓰며, 표 밖 명시 라벨은 R3.3 전에 거부해 Claude 출처 전체 제외를 막는다. | 활성 `pr-review-toolkit`의 `agents/code-reviewer.md:39-52` 실측 |
| R2.3 | SPEC-006 | AC-11(일치 — rg 종료 코드 구분과 대상 디렉터리 존재 확인을 CMD-4 명령 자체가 판정), AC-12(일치 — sandbox read-only 계약은 문언 변경 없이 추적표 선언만 CMD-3·CMD-4 로 정정) | CMD-4 의 종료 코드 구분은 R7.3 의 CMD-5 와 같은 형태를 쓰므로 두 금지 계약의 방어 강도가 갈리지 않는다. | 자체 개정 |
| R2.4 | SPEC-003 | AC-13(일치 — run directory 에 보존된 실제 디스패치 프롬프트를 판정 대상으로 전환), AC-14(일치 — 보존된 호출 시작 순서 기록을 판정 대상으로 전환) | Python 이 프롬프트를 구성한다는 계약이 R9.3 의 책임 목록과 같은 문언을 쓰며, 독립성이 라운드 0 한정이라는 R5.3 의 전제를 깨지 않는다. | 자체 개정 |
| R3.1 | SPEC-002; 독립 사전 심사 High — Claude 원문 severity를 정규 enum으로 변환하지 않아 `Important`가 거부됨 | AC-15(일치 — severity enum 과 finding_confidence 0–1 을 schema required 로 판정), AC-16(일치 — 대소문자 무시 `Critical`→`critical`·`Important`→`high`, 라벨 없음→`medium`, 표 밖 명시 라벨 거부를 정규 shape 변환에서 판정) | R2.1 변환 뒤에만 닫힌 enum을 검사하므로 `Important`가 유효 `high`가 되고, finding_confidence 로 개명한 경계도 R6.4 의 decision_confidence 와 섞이지 않는다. | 활성 `pr-review-toolkit`의 `agents/code-reviewer.md:39-52` 실측 |
| R3.2 | SPEC-004 | AC-17(일치 — 그룹 라벨 파생 ID 의 재실행 동일성을 판정), AC-18(일치 — 그룹 라벨이 달라진 fixture 가 다른 ID 를 냄을 판정) | 그룹 라벨 파생이 R6.2 의 실제 source 제거와 양립하고, R6.3 의 A/B 배정이 ID 네임스페이스의 유일한 입력이 된다. | 6.1.2 대칭 점검 #1 과 공식 리뷰 SPEC-004 가 독립적으로 같은 모순을 지적했고, 사용자가 익명 그룹 라벨로 확정했다 |
| R3.3 | SPEC-002; 독립 사전 심사 High — 변환 전 원문 severity와 변환 후 enum 거부 경계가 불명확함 | AC-19(일치 — R2.1 변환 뒤 enum 밖 값과 표 밖 명시 원문 severity, 0–1 밖 finding_confidence 거부를 판정), AC-20(일치 — 거부 원문의 자동 보정 금지는 변경 없이 유지) | 변환표 밖 명시 라벨은 기본값으로 보정하지 않고 거부하며, enum·범위 거부가 R8.2 의 형식 재요청 판정 기준을 정의한다. | R2.1 변환표에서 파생 |
| R3.4 | SPEC-004 | AC-71(일치 — 양 그룹 body 가 형식만으로 구별되지 않음을 판정) | 형식 정규화는 R6.2 의 A/B 관계 보존과 충돌하지 않는다. 관계는 남기고 문체만 지운다. | 사용자 익명 그룹 결정에서 파생한 신설 |
| R4.1 | SPEC-001 | AC-21(일치 — Claude 비평 입력 격리 판정. 추적표 선언을 AC 본문의 CMD-9 로 정정), AC-22(일치 — Codex 비평 입력 격리 판정. 같은 행의 두 방향 AC 가 같은 CMD-9 를 씀) | 추적표 정정만이며 R4.1 본문과 AC 본문은 바뀌지 않아 다른 해소의 전제를 건드리지 않는다. | 치환 없음 |
| R4.2 | SPEC-001 | AC-23(일치 — critique schema 의 세 판정값·근거 위치 required 판정. 추적표를 CMD-9 로 정정) | 추적표 정정만이며 critique schema 계약 자체는 그대로다. | 치환 없음 |
| R5.1 | SPEC-002, SPEC-009, SPEC-010; 독립 사전 심사 Medium — `no_new_high`와 `requested_round_limit`가 겹쳐 복수 종료 사유가 가능함 | AC-27(일치 — 한 라운드가 두 방향 호출의 묶음임을 판정), AC-28(일치 — 신규 high 이상 0 또는 rounds 1 에서 라운드 2 미예약과 겹친 후보의 단일 선택을 판정), AC-29(일치 — rounds 2 이며 신규 high 이상 1 이상일 때만 라운드 2 예약하고 이후 겹친 후보의 단일 선택을 판정) | 두 방향 합산과 high 이상 도메인이 R5.2 의 조용한 라운드 집계와 같고, 후보 충돌은 R7.1 전순서가 정확히 하나로 해소한다. | 두 독립 사전 심사 |
| R5.2 | SPEC-002, SPEC-007; 독립 사전 심사 Medium — `two_quiet_rounds`가 다른 종료 후보와 겹침 | AC-30(일치 — 단일 교차 비평의 0 이 two_quiet_rounds 를 만들지 않고 겹친 후보의 단일 선택을 판정), AC-31(일치 — 라운드 0·1 연속 0이 `two_quiet_rounds` 후보가 되고 `no_new_high`·`requested_round_limit`와 겹치면 단일 선택됨을 판정) | high 이상 집계가 R5.1 과 같은 도메인이고, R7.1 전순서가 수렴 후보와 한도 후보를 하나로 정한다. | 두 독립 사전 심사 |
| R5.3 | SPEC-007; 독립 사전 심사 Medium — `round_cap`가 drift 등 종료 후보와 겹침 | AC-32(일치 — 라운드 상한 초과와 라운드 1 이상 독립 리뷰 재호출 거부, 정상 라운드 2 완료의 겹친 후보 단일 선택을 판정) | `round_cap`은 정상 완료 후보이며 R7.1 전순서가 R5.4의 중단 후보와 함께 성립해도 하나만 고른다. | 두 독립 사전 심사 |
| R5.4 | SPEC-007; 독립 사전 심사 Medium — `abstraction_drift`가 `no_new_high`·`round_cap`과 겹침 | AC-33(일치 — 평가 시점과 0.5 초과 중단, 겹친 후보의 단일 선택을 판정), AC-34(일치 — 0.5 이하 비중단과 새 finding 0건의 비율 0, 남은 겹친 후보의 단일 선택을 판정) | 분모 0 규정과 평가 시점은 R5.1 예약 결과를 바꾸지 않고, `abstraction_drift`를 포함한 충돌은 R7.1 전순서가 하나로 정한다. | 두 독립 사전 심사 |
| R6.1 | SPEC-001 | AC-35(일치 — fresh Claude subagent 지정 판정. 추적표를 CMD-10 으로 정정), AC-36(일치 — 컨텍스트 미상속 판정. 추적표를 CMD-10 으로 정정) | 추적표 정정만이며 종합자 실행 계약 문언은 그대로다. | 치환 없음 |
| R6.2 | SPEC-004 | AC-37(일치 — 실제 source 제거와 group A·B 치환을 함께 판정), AC-38(일치 — provenance sidecar 가 종합자 입력에 없음을 판정) | group 치환은 R3.2 의 ID 파생 입력과 같은 라벨을 쓰고, sidecar 배제는 R7.2 의 복원 경로를 막지 않는다. | 6.1.2 대칭 점검 #1 과 공식 리뷰 SPEC-004 를 사용자 확정 방향으로 해소했다 |
| R6.3 | SPEC-004, SPEC-011 | AC-39(일치 — finding_id 오름차순 정규 정렬 후 같은 run ID 가 같은 순서를 냄을 판정), AC-40(일치 — A/B 배정·시드·실행 구분자가 sidecar 에 기록됨을 판정) | 정규 정렬이 AC-39·AC-69 의 집합 기준 요구를 요구사항 수준에서 충족시키고, A/B 배정 기록이 R7.2 복원의 입력이 된다. | 자체 개정 |
| R6.4 | SPEC-004 | AC-41(일치 — 세 분류 enum 과 decision_confidence·rationale·양 그룹 ID 를 required 로 판정), AC-42(일치 — 양 그룹이 같은 논점을 보고한 fixture 가 하나의 합의 항목으로 묶임을 판정) | 세 분류를 익명 관계에서 도출하도록 정의해 R6.2 의 입력만으로 판정이 성립한다. 동일 결함 판단은 종합자에게 남겨 D7 의 기각 대안과 일관된다. | 6.1.2 대칭 점검 #1 과 공식 리뷰 SPEC-004 를 사용자 확정 방향으로 해소했다 |
| R6.5 | SPEC-001 | AC-43(일치 — 불일치 fixture 보존 판정. 추적표를 CMD-10 으로 정정), AC-44(일치 — 종합자가 codex exec 를 쓰지 않음을 판정. 추적표를 CMD-10 으로 정정) | 추적표 정정만이며 불일치 보존 계약은 그대로다. | 치환 없음 |
| R7.1 | SPEC-007; 두 독립 사전 심사 Medium — 여덟 종료 조건이 겹치는데 enum 존재만 있고 승자 규칙이 없음 | AC-45(일치 — report.md 생성 판정은 변경 없이 유지), AC-46(일치 — 보고서 종료 사유가 여덟 값 enum 중 정확히 하나임을 판정) | `no_changes`부터 `round_cap`까지 R7.1에만 둔 전순서가 R5.1~R5.4·R8.3·R8.4·R1.3의 모든 종료 후보 충돌을 결정적으로 하나로 정한다. | 두 독립 사전 심사 |
| R7.3 | SPEC-006 | AC-49(일치 — CMD-5 의 rg 종료 코드 구분과 숨김·무시 파일 포함을 판정), AC-50(일치 — 자동 코드 수정 부재 판정은 CMD-6 으로 변경 없이 유지) | CMD-5 의 종료 코드 구분이 R2.3 의 CMD-4 와 같은 형태이므로 두 grep 보증의 강도가 같다. | 자체 개정 |
| R8.3 | SPEC-007 | AC-55(일치 — 타임아웃 1회 재시도와 stderr·종료 정보 기록을 판정), AC-56(일치 — 양쪽 실패가 종합 0회와 reviewer_failure 로 끝남을 판정) | reviewer_failure 가 R8.4 의 single_reviewer 와 배타적으로 정의돼 같은 상황에 두 사유가 붙지 않는다. | 자체 개정 |
| R9.1 | SPEC-001, SPEC-005 | AC-59(일치 — 배치 계약 문서의 두 경로 판정. 추적표를 CMD-11 로 정정), AC-60(일치 — chezmoi 실행 의존을 버리고 순수 배치 경로 함수로 판정) | chezmoi 실행 의존 제거로 판정이 체크아웃 위치와 무관해지고, 추적표가 그 판정 명령을 정확히 가리킨다. | 자체 개정 |
| R9.2 | SPEC-001 | AC-61(일치 — 여섯 구성 요소와 frontmatter 일곱 키 판정. 추적표를 CMD-11 로 정정), AC-62(일치 — schemas·scripts·tests 책임 경로 판정. 추적표를 CMD-11 로 정정) | 추적표 정정만이며 구성 요소·frontmatter 계약은 그대로다. | 치환 없음 |
| R9.3 | SPEC-003, SPEC-004, SPEC-011; 독립 사전 심사 Medium — 라운드 0 프롬프트 구성·실제 문자열 보존·호출/판독 순서 게이트의 Python 소유권이 AC로 판정되지 않음 | AC-63(일치 — SKILL.md 가 프롬프트 문자열을 변경하지 않고 호출만 함을 판정), AC-64(일치 — 프롬프트 구성 함수·실제 디스패치 문자열 보존·양쪽 호출 후 판독 게이트와 정규화·ID·셔플·종료·렌더링의 Python 소유권을 판정), AC-65(일치 — 외부 패키지 미import 판정은 CMD-6 으로 유지) | 세 라운드 0 책임을 Python에 모아 AC-13·AC-14의 행위 증거와 같은 구현 경계로 만들고, R2.4의 독립성과 R6.2의 익명화가 그 결정적 경계를 공유한다. | 독립 사전 심사 |
| R9.4 | SPEC-006 | AC-66(일치 — 전체 단위 테스트 종료 코드 0 판정), AC-67(일치 — CMD-4·CMD-5 두 명령으로 주장 전체를 판정하도록 판정 수단을 보강), AC-68(일치 — not configured 선언 판정. 추적표를 CMD-11 로 정정), AC-69(일치 — 입력 순서 무관 결정적 Markdown 판정), AC-70(일치 — 외부 쓰기 0회·코드 수정 0회 보장 판정) | rg 오류 구분 요구가 CMD-4·CMD-5 양쪽에 같은 형태로 적용된다. | 자체 개정 |

## 라운드 3 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.4 | SPEC-014 | AC-5(일치 — `.claude/dual-review-state/` 루트의 `.gitignore` 위치를 판정)·AC-6(일치 — run ID의 재실행 비충돌 판정은 유지) | run root를 상태 트리 루트로 고정해 실행별 디렉터리와 `.gitignore`의 소유 범위가 갈리지 않는다. | 사용자가 확정한 상태 트리 루트 |
| R2.1 | SPEC-012·SPEC-013·독립 사전 심사 Medium — 원문 ID 순번의 시작·블록 경계·거부 소비·직렬화가 미정 | AC-7(일치 — 다섯 생산자 선택과 자유 서술 라벨 계약을 유지)·AC-8(일치 — `code-simplifier` 배제 계약을 유지) | `title` 라벨 경계의 모든 블록을 검증 전에 1부터 세고 거부 블록도 소비하며 `producer=<생산자 에이전트명>;ordinal=<1부터의 10진 정수>` 하나로 직렬화해 R3.1~R3.3의 파생 사슬을 결정적으로 고정한다. | 자유 서술 출력에는 생산자별 ID 라벨이 없고 순번 규칙의 네 빈칸이 구현별 ID 차이를 만들었다 |
| R3.1 | SPEC-012·독립 사전 심사 Medium — 원문 ID canonical 직렬화가 정규 레코드 계약에 미반영 | AC-15(일치 — 열 개 필수 필드 schema를 판정)·AC-16(일치 — 선행 거부 블록 뒤 정확한 canonical 원문 ID를 가진 정규 shape를 판정) | 열 개 필수 필드의 원문 ID가 R2.1의 canonical 직렬화로 항상 공급돼 provenance 복원 사슬과 fixture의 정확값이 일치한다. | 원문 ID를 필수에서 빼면 provenance 복원 사슬이 끊어진다 |
| R3.2 | SPEC-012·독립 사전 심사 High — `finding_id`가 원문 ID를 평문으로 담아 종합자 입력에 생산자 신원을 누설할 수 있음 | AC-17(일치 — 선행 거부 뒤 정확한 원문 ID 입력의 재실행 동일성과 불투명 형식을 판정)·AC-18(일치 — 원문 ID만 다른 fixture 및 다른 입력이 서로 다른 ID를 냄을 판정) | canonical 바이트 직렬화의 SHA-256 `fid_` 식별자가 원문 ID·실제 source·reviewer명·생산자명을 평문으로 담지 않고, 실제 대응은 provenance sidecar에만 남아 R6.2의 익명 view와 양립한다. | 원문 ID 기반 결정성은 유지하면서 생산자명을 재노출하지 않는 불투명 ID 계약이 필요했다 |
| R3.3 | SPEC-013·독립 사전 심사 Medium — 거부 블록이 순번을 소비하는 시점이 불명 | AC-19(일치 — 표 밖 명시 severity의 finding 단위 거부를 판정)·AC-20(일치 — 거부 finding의 자동 보정 금지를 판정) | 검증 전 원문 ID를 부여하고 거부 뒤에도 순번을 되돌리거나 재사용하지 않아 R2.1의 fixture 순서와 R3.2 입력이 흔들리지 않는다. | 변환표 밖 명시 severity의 레코드 단위 처리와 순번 소비 경계를 함께 확정 |
| R6.2 | SPEC-012·독립 사전 심사 High — 보존된 `finding_id`가 평문 생산자명을 통해 A/B 익명화를 우회할 수 있음 | AC-37(일치 — 모든 익명 view 문자열값에서 다섯 생산자명과 원문 ID가 각각 0건임을 판정)·AC-38(일치 — `finding_id`에서 실제 source·원문 ID로의 mapping sidecar를 입력에서 배제함을 판정) | R3.2의 불투명 `finding_id`만 유지하고 모든 문자열값의 평문 누설을 금지해, A/B 관계·후보 논점·critique는 보존하면서 provenance 복원은 sidecar에 격리한다. | 원문 ID를 제거해도 파생 ID가 생산자명을 되돌려 놓을 수 있다는 독립 사전 심사 결과 |
| R6.3 | 독립 사전 심사 Medium — 불투명 ID 아래 정렬의 바이트 순서가 미정 | AC-39(일치 — 불투명 `finding_id`의 ASCII 바이트 오름차순 정렬 뒤 셔플 재현성을 판정)·AC-40(일치 — A/B 배정·시드·실행 구분자의 sidecar 기록을 유지) | 고정 ASCII 소문자 형식인 `fid_` digest를 ASCII 바이트 오름차순으로 정렬하므로 불투명성 아래에서도 셔플 입력 순서가 결정적이다. | locale 또는 구현체 기본 정렬에 맡기지 않고 R3.2 canonical ID 형식과 정렬을 결속했다 |
| R6.4 | 독립 사전 심사 High — 종합 출력의 양 그룹 finding ID가 익명 입력 계약과 연결되지 않음 | AC-41(일치 — 양 그룹의 불투명 `finding_id`를 required로 판정)·AC-42(일치 — 분류 fixture가 양 그룹의 불투명 ID를 보존함을 판정) | 종합자는 R3.2 불투명 ID만 반환하므로 required 양 그룹 ID가 출처를 밝히지 않으면서 renderer가 sidecar에서 대응을 복원할 수 있다. | finding ID를 출력에서 빼지 않고도 A/B 익명화를 유지해야 한다 |
| R8.2 | SPEC-013 | AC-53(일치 — 출력 전체 스키마 위반에만 한 번 재요청 후 출처 제외를 판정)·AC-54(일치 — 제외 출처의 원문·오류 보존을 판정) | R3.3의 finding 단위 거부와 R8.2의 출력 전체 실패를 분리해 severity 하나로 출처 전체가 탈락하지 않는다. | 출처 단위 재요청·제외의 발동 경계 확정 |
| R9.4 | SPEC-012·SPEC-013·독립 사전 심사 High·Medium — 종합자 입력 불투명성 및 순번 결정성의 산문 교차 회귀 | AC-66(일치 — 전체 단위 테스트 종료 코드 0 판정을 유지)·AC-67(일치 — CMD-4·CMD-5 두 명령 연결을 유지)·AC-68(일치 — not configured 선언을 유지)·AC-69(일치 — 불투명 ID의 ASCII 정렬을 포함한 결정적 Markdown 판정을 유지)·AC-70(일치 — 외부 쓰기 0회·코드 수정 0회 보장을 유지) | Architecture·Interfaces·Security·D2 산문이 R3.2 불투명 `finding_id`, sidecar 전용 `finding_id` 대응, R6.2 모든 문자열값의 평문 누설 금지, R6.3 ASCII 정렬을 같은 계약으로 말한다. `_requirement_for_line` 은 이를 마지막 요구사항 R9.4(spec.md:96)로 귀속하므로 해당 AC 전부와의 상호작용을 갱신했다. | 사용자 지정 귀속 규칙과 이번 교차 회귀 전수 검색 |

## 교차 회귀 전수 검색

바꾼 값·규칙·이름마다 문서 전체를 문자열로 검색해 등장 위치를 전부 맞췄다. 4차 실행이 `fp` 소비처 선언을 다섯 곳만 고치고 다섯 곳을 남겨 죽은 것을 되풀이하지 않기 위한 단계다.

| 검색어 | 확인한 절 | 결과 |
|---|---|---|
| `source`·출처·`provenance`·sidecar | R3.1, R3.2, R6.2, R6.3, R6.4, R7.2, Architecture, Interfaces, Security, D2 | 실제 `source` 는 정규 레코드와 provenance sidecar에만 남고 종합자 입력에서는 A/B와 불투명 ID로 치환되며 `finding_id` 대응은 sidecar 전용이라는 서술이 전부 일치 |
| `group`·A/B 라벨 | R3.2, R6.2, R6.3, R6.4, AC-17, AC-18, AC-37, AC-40, AC-41, AC-71 | 일치 |
| `finding_id` | R3.2, R6.3, R6.4, AC-17, AC-18, AC-39, AC-41, AC-42, Interfaces, Security, D2 | R3.2의 불투명 SHA-256 canonical ID만 종합 입력·출력에 남고 R6.3의 ASCII 정렬이 결정적이며 실제 source·원문 ID 대응은 sidecar에만 있음 |
| 원문 ID | R2.1, R3.1, R3.2, R3.3, R6.2, AC-16, AC-17, AC-18, AC-37, AC-38, Architecture, Interfaces, Security, D2 | R2.1의 canonical 직렬화와 검증 전 순번 소비가 전부의 파생 전제이고, 종합자 입력에서는 모든 평문 원문 ID와 그 mapping이 제거됨 |
| 순번·직렬화 | R2.1, R3.1, R3.2, R3.3, AC-16, AC-17, AC-18 | `title` 블록 경계·검증 전 1부터의 순번·거부 블록 소비·`producer=<생산자 에이전트명>;ordinal=<1부터의 10진 정수>` 직렬화가 하나로 고정되고 이 값만 다른 fixture도 다른 ID를 냄 |
| `confidence` | R3.1, R6.4, AC-15, AC-41, Interfaces | `finding_confidence` 와 `decision_confidence` 로 이름이 갈려 혼용 0건 |
| `severity`·`Critical`·`Important`·high·critical | R2.1, R3.1, R3.3, R8.2, AC-16, AC-19, Interfaces, Security, Test strategy | R2.1 대소문자 무시 변환표가 `Critical`→`critical`, `Important`→`high`, 라벨 없음→`medium`, 표 밖 명시 라벨→거부를 정하고 R3.1·R3.3의 닫힌 enum과 일치 |
| `--rounds` | R1.1, R5.1, AC-1, AC-2, AC-28, AC-29 | 두 표기 허용을 R1.1 이 명시하고 나머지가 그에 따름 |
| `CMD-` 각 번호 | AC 본문 71건, 추적표 36행, 판정 명령 표, 표 뒤 서술 | 추적표 선언 == AC 본문 CMD 합집합, 불일치 0행. CMD-3 봉합 문장 제거 |
| 종료 사유 우선순위 | R1.3, R5.1, R5.2, R5.3, R5.4, R7.1, R8.3, R8.4, AC-28~AC-34, AC-46, Interfaces, Decisions | 여덟 값 enum의 유일한 전순서가 R7.1에 있고, 다른 절은 그 우선순위의 정확히 하나 선택만 참조 |
| 라운드 0 Python 소유권 | R2.4, R9.3, AC-13, AC-14, AC-63, AC-64, Architecture, Decisions D5 | 프롬프트 구성 함수·실제 문자열 보존·호출/판독 순서 게이트가 Python scripts에 있고 SKILL.md는 변경 없이 호출만 함 |
| `.claude/dual-review-state` | R1.4, AC-5, AC-6, Security | 경로와 run root `.gitignore` 서술 일치 |
| `rg` 명령 문자열 | CMD-4, CMD-5, AC-11, AC-49, AC-67, R9.4 | 두 명령이 같은 종료 코드 구분 형태를 쓰고 AC-67 이 두 명령을 모두 가리킴 |

Decisions 절과 Security 절을 검색 범위에 포함했다. 4차 실행에서 `D28` 은 결정 근거 자체가 뒤집혔는데 문언이 남아 blocker 가 됐다.

## 두 심사가 독립적으로 같은 결함을 찾았다

`SPEC-004`(익명화와 종합 분류의 상호 모순)는 두 경로에서 각각 발견됐다. 6.1.2 의 Codex 대칭 점검이 발견 #1 로, Claude 공식 리뷰가 `SPEC-004` 로 지적했다. 두 심사는 서로의 결과를 보지 않았다.

이 작업이 설계하려는 구조(독립 이중 심사 → 교차 확인)가 이 작업 자신의 Spec 심사에서 값을 한 사례다.

## 규모

| 항목 | 라운드 1 | 라운드 2 | 상한 |
|---|---|---|---|
| 요구사항 | 35 | **36** | 40 |
| AC | 70 | **71** | 80 |
| 추적표 행 | 35 | 36 | 요구사항 수와 동일 |
| 결정 | 6 | 7 | — |

신설은 `R3.4`(형식 누설 차단) 하나와 `AC-71` 하나, `D7`(결정적 매칭 대안 기각) 하나다. 나머지 열 건의 finding 은 기존 문장 정정과 표 셀 수정으로 닫았다. 비목표로 옮긴 항목은 없다.
