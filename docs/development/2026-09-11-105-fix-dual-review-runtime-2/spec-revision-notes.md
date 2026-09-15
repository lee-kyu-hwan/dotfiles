## 실행 1 라운드 2 개정 (보존)

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

## 실행 2 라운드 0 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | SPEC-009 | AC-1(일치: `unrecognized_model`·`PROBE_OK` 원시 전사와 slash 실행 가능성 근거 연결) | 모델 식별자 근거를 보존 evidence에 연결할 뿐 production/harness flag 분리나 run-id 판정의 전제를 바꾸지 않는다. | 치환 없음 |
| R6.1 | SPEC-009 | AC-1(일치: command·사용 스킬·stdout/stderr·exit·run 목록·provenance·report·snapshot 인용) | CMD-6의 선행 실행 가능성을 원시 전사로 고정하며 SPEC-010의 하니스 전용 권한 경계와 모순되지 않는다. | 치환 없음 |
| R1.3 | SPEC-010 | AC-3(일치: 확인된 CLI 기능, production emit, CMD-6 하니스 목록 분리) | 세 목록의 문서·assertion 경계를 분리해 SPEC-009의 P3 명령을 production 계약으로 오독하는 새 공백을 막는다. | 앞선 SPEC-001 해소의 단일 전체 flag 목록이 production emit 목록으로 읽힐 수 있어 기능 존재 목록과 실제 emit 목록으로 치환했다. |
| R6.2 | SPEC-011 | AC-16(일치: 기존 phase·source 판정 유지), AC-17(일치: 선관측 최댓값 기본값 0에 정확히 1을 더함) | 빈 접두사 집합도 `000001`로 결정하면서 기존 phase 조건과 보존 run 요구를 그대로 유지한다. | 앞선 SPEC-007 해소의 “기존 최댓값보다 큰 번호”를 `max(existing, default=0) + 1`의 정확한 판정으로 치환했다. |
| R6.5 | SPEC-011 | AC-16(일치: E2E phase 판정 유지), AC-17(일치: 모델 호출 전 번호 기준선 관측), AC-20(일치: helper의 동적 run-id 사후 판정 인터페이스) | helper의 선검사와 사후 판정이 같은 기본값 0 기준을 공유해 빈 집합에서 새 판정 공백을 만들지 않는다. | 앞선 SPEC-007 해소에 누락된 빈 집합 분기를 helper 계약까지 확장해 치환했다. |

## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.2 | SPEC-001 | AC-2(일치: 마지막 argv의 단일 `-`와 위치 prompt 부재), AC-9(일치: live Codex 명령과 EOF stdin) | 명시적 표시자와 EOF 생명주기를 분리해 P7의 근거를 보존하면서 producer 유효성 판정에 새 교착 공백을 만들지 않는다. | 앞선 “현행 argv 그대로” 해소를 P7이 확인한 EOF 본질과 사용자가 허용한 명시적 `-` 최소 변경으로 치환했다. |
| R2.1 | SPEC-001 | AC-4(일치: start 시점 prompt와 EOF 관측), AC-5(일치: 대용량 prompt의 무교착·무절단) | start-before-read 독립성과 EOF 보장이 함께 성립해 대용량 입력 해소의 전제를 깨지 않는다. | P7에 따라 표시자 유무와 독립적인 EOF 계약을 추가한 자체 개정이다. |
| R3.1 | SPEC-003, SPEC-004 | AC-7(일치: `minItems` 부재와 빈 배열 수용), AC-9(일치: canonical schema live 수용) | strict 폐쇄를 유지하면서 빈 배열을 허용하므로 Claude 호환 분기와 여섯 producer 유효성 요구 모두와 양립한다. | 앞선 `minItems: 1` 해소는 공급자 수용 가능성과 목적 적합성을 혼동했으므로 허위 finding을 유도하지 않는 계약으로 치환했다. |
| R3.2 | SPEC-003 | AC-8(일치: critique finding object의 strict 폐쇄 유지), AC-9(일치: critique schema의 Claude/Codex live 수용) | 호환 진단은 critique의 필수 필드 폐쇄를 약화하지 않고 shared schema 원칙을 유지한다. | R3.3의 거부 분기가 공유 critique AC에 미치는 파급을 명시한 자체 개정이다. |
| R3.3 | SPEC-003 | AC-9(일치: `$schema`-only 진단 재시도와 `NEEDS_REDESIGN` 중단), AC-15(일치: 기본 discover의 live skip 유지), AC-19(일치: opt-in helper의 evidence 계약) | 진단 재시도가 strict keyword나 provider별 계약을 조용히 약화하지 않아 Codex 400 해소를 되돌리지 않는다. | rollback으로 기존 schema를 복원하던 방식을 shared schema fix-forward 또는 명시적 중단으로 치환했다. |
| R4.1 | SPEC-006 | AC-10(일치: `.gitkeep` 특수 분기 제거와 일반 fixture 대체), AC-11(일치: archive에서 `.gitkeep` 0건) | 죽은 scanner 분기 제거가 binary cache 제외와 필수 packaging 경로 검사를 약화하지 않는다. | 유지·제거가 미결정이던 분기를 실제 패키지 구조에 맞춰 제거하기로 한 자체 개정이다. |
| R4.2 | SPEC-002, SPEC-006 | AC-10(일치: source 이름과 scanner 일반 계약), AC-11(일치: cache 제외 source/archive 동등성) | source scanner 정리와 cache fixture 제외가 같은 상대 경로 비교에서 충돌하지 않는다. | 공유 packaging AC 변경의 파급을 명시한 자체 개정이다. |
| R4.3 | SPEC-002 | AC-11(일치: source cache 실재 선단정과 archive 0건 및 cleanup) | cache fixture를 CMD-5 안에서 만들고 정리해 Python 버전 판정과 후속 live 명령에 상태 누수를 만들지 않는다. | `PYTHONDONTWRITEBYTECODE=1` 실행의 우연한 cache 부재에 기대던 공허한 판정을 실재 fixture 기반 판정으로 치환했다. |
| R5.1 | SPEC-004, SPEC-005 | AC-12(일치: structured 빈 배열·명시적 Claude 무소견과 ingestion 실패 구분) | 무소견을 완료로 인정하면서 표지 없는 0블록은 실패로 유지해 여섯 producer 전원 조건에 우회로를 만들지 않는다. | 앞선 모든 빈 findings를 실패로 보던 해소를 유효 응답과 findings 수를 분리하는 계약으로 치환했다. |
| R5.2 | SPEC-005 | AC-13(일치: production producer 하나의 실패도 `reviewer_failure`) | source별 축약 성공을 없애 R5.1의 명시적 무소견과 실패 구분을 그대로 producer 전원 gate에 전달한다. | 앞선 source별 최소 한 유효 producer 완화를 되돌려 이슈 #105 완료 조건 2와 다시 일치시켰다. |
| R6.2 | SPEC-005 | AC-16(일치: 여섯 producer 전부 유효 응답), AC-17(일치: 기존 run과 제품 상태 보존) | producer 전원 gate는 run-id와 무변경 판정을 바꾸지 않고 E2E 완료 기준만 원래 이슈 수준으로 복원한다. | 앞선 실행에서 AC-16을 source별 최소 한 유효 producer로 완화했던 것을 되돌렸다. |
| R6.3 | SPEC-007 | AC-15(일치: Python 3.14.7 단정과 `python3 -VV` evidence), AC-18(일치: verification 문서와 판정 환경 일치) | 버전 evidence 추가는 기본 suite의 live skip과 독립적이며 archive cache fixture 생성 조건도 바꾸지 않는다. | 암묵적 PATH 선택을 명시적 버전 단정과 보존 전사로 강화한 자체 개정이다. |
| R6.4 | SPEC-003, SPEC-007 | AC-9(일치: live schema 진단과 원시 evidence), AC-15(일치: 환경변수 부재 시 live skip), AC-19(일치: helper 환경 인터페이스와 evidence 계약) | opt-in helper만 진단 재시도를 수행하므로 기본 suite의 무비용 실행과 Python version 판정을 깨지 않는다. | provider 거부 시 행동이 없던 live helper 계약을 진단·중단 가능한 계약으로 치환했다. |
| R6.5 | SPEC-005 | AC-16(일치: 여섯 producer 전원과 phase 사후 판정), AC-17(일치: 선관측 run-id와 무변경), AC-20(일치: E2E helper 인터페이스) | helper가 producer별 유효 상태를 검사해 source 축약 성공을 막으면서 기존 run-id와 무변경 사후 판정을 유지한다. | 앞선 AC-16 완화를 E2E helper 경계에서도 되돌린 자체 개정이다. |
