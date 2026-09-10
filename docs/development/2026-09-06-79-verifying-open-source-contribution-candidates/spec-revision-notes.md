# Spec 개정 노트

## 라운드 2 개정

라운드 1 리뷰(SPEC-001~SPEC-015)를 반영한 개정이다. 아래 표의 `함께 바뀐 항목` 은 revision_check 파급표의 AC 를 모두 열거하고 각 AC 의 판정 문장이 개정된 요구사항과 일치하는지 적었다.

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | SPEC-013 | AC-1(일치), AC-43(일치) | AC-43(quick_validate) 을 R1.1 로 재매핑. 같은 사실을 말하는 두 표(추적표·AC-43)가 이제 일치한다. | 치환 없음 |
| R1.2 | SPEC-011 | AC-2(일치) | 금지 패턴 예외(docs.github.com, api-version 줄, 자리표시자)를 AC-2 에 명시. R11.2 참조 문서 작성과 충돌하지 않는다. | AC-2 의 무조건 금지를 예외 있는 금지로 치환 — 형제 스킬 관행(github-rest-contract.md 의 문서 링크·API 버전 표기)과 맞추기 위함 |
| R1.3 | SPEC-014 | AC-3(일치), AC-17(일치) | 본문 불변. AC-3 에 fixture-missing 599 판정이 추가되어 R2.4 와 함께 판정된다. 자식 프로세스 제한과 새 판정은 독립이다. | 치환 없음 |
| R1.4 | SPEC-002 | AC-4(일치), AC-20(일치) | 본문 불변. AC-20 이 스냅숏 inputs.kind/두 SHA 를 판정하도록 확장되어 revision 규칙과 함께 검사된다. | 치환 없음 |
| R2.1 | SPEC-005, SPEC-006 | AC-5(일치), AC-10(일치), AC-12(일치), AC-13(일치), AC-27(일치) | --max-clues-per-pattern(기본 5) 과 record 의 --program-rules(로컬 파일만, URL 은 2) 추가. AC-10·AC-13 은 요청 수식과, AC-27 은 program-rules 경로와 일치. | 치환 없음(옵션 추가) |
| R2.3 | SPEC-008 | AC-5(일치) | --clone-root 는 tempfile.gettempdir() 아래여야 하며 그 밖은 네트워크 전 2. 기본값 mkdtemp 는 자동 충족. strict-only 정지 조건과 일치. | 치환 없음(제약 추가) |
| R2.4 | SPEC-014 | AC-3(일치), AC-14(일치) | 본문 불변. fixture-missing 599 문장이 AC-3 으로 판정된다. | 치환 없음 |
| R3.1 | SPEC-001, SPEC-012 | AC-7(일치), AC-8(일치) | repository_checks 출력 키·타입을 명시하고, 저장소 조회 실패 시 조합을 records 가 아니라 failed_scopes 에만 두며 부분 실패는 head_sha null + unverified 고정으로 정했다. AC-7·AC-8 이 각각 판정. | '실패도 repository_checks 에 분류만 남긴다' 를 '레코드 미생성 + failed_scopes' 로 치환 — candidate_key·verified_base_sha 를 계산할 수 없는 경로를 없애기 위함(D10) |
| R3.3 | SPEC-005 | AC-10(일치) | 단서당 4 요청, 상한은 --max-clues-per-pattern, unused_clues 기록. AC-10 의 8 요청 판정과 수식이 같다. | '단서마다 검색어·저장소마다 4 조합' 의 모호한 문장을 '조합당 사용 단서 수 × 4' 수식으로 치환(D11) |
| R3.4 | SPEC-005 | AC-11(일치), AC-15(일치) | 코드 검색도 같은 단서 상한을 쓴다고 명시. AC-11·AC-15 판정은 불변. | 치환 없음 |
| R3.5 | SPEC-005 | AC-13(일치) | 본문 불변. AC-13 의 예산 픽스처를 요청 수 산식(8 요청)으로 구체화했다. | 치환 없음 |
| R3.6 | SPEC-001 | AC-12(일치), AC-18(일치) | 실패 저장소 조합은 records 가 아니라 failed_scopes 에만 있다고 명시. AC-12·AC-18 판정 불변. | 치환 없음 |
| R5.1 | SPEC-007 | AC-18(일치), AC-49(일치) | 스물아홉 필드의 출처를 discovery 복사/평가 입력/스크립트 계산 셋으로 명시하고 superseded_by 참조 규칙을 정했다. AC-49 가 참조 규칙을 판정. | 치환 없음(출처 명시 추가) |
| R5.3 | SPEC-002 | AC-20(일치), AC-30(일치) | inputs 를 {kind, discovery_sha256, assessment_sha256} 로 정하고 recheck 스냅숏의 재관측 필드와 승계 필드를 구분, validate 검사 대상으로 명시. AC-20·AC-30 이 각각 record·recheck 스냅숏을 판정. | 'inputs(두 SHA)' 를 kind 있는 객체로 치환 — recheck 가 discovery·assessment 파일 없이 스냅숏을 만들기 때문 |
| R5.4 | SPEC-001 | AC-8(일치), AC-21(일치) | verified_base_sha null 허용을 'head_sha null 인 discovery 레코드' 로 한정하고 그때 상태를 unverified/insufficient-evidence 로 고정. AC-8 이 그 경로를, AC-21 이 정상 경로를 판정. | 'discovery 자체가 없는 경우에만 null' 을 'head_sha 부분 실패에만 null' 로 치환 — R3.1 의 부분 실패 경로와 일치시키기 위함 |
| R6.4 | SPEC-014 | AC-25(일치) | 본문 불변. AC-25 에 private_evidence_reference 미반복 판정을 추가했다. | 치환 없음 |
| R6.6 | SPEC-006 | AC-27(일치) | program_rules 는 record --program-rules 가 있을 때만 found 가 bool 이고 sha256 이 파일과 같아야 하며 없으면 null 로 고정. AC-27 이 세 경로(옵션 없음·URL·로컬 파일)를 판정. | '경로나 URL 을 준 경우' 를 'record --program-rules 로컬 파일' 로 치환 — URL 취득 수단과 미신뢰 처리를 정의하지 않기 위함 |
| R6.7 | SPEC-007, SPEC-001 | AC-28(일치), AC-49(일치) | 평가 항목에 superseded_by 추가, failed_scopes 조합 평가를 2 로 명시. AC-28·AC-49 판정. | 치환 없음(항목 추가) |
| R6.8 | SPEC-006 | AC-28(일치), AC-29(일치) | record 옵션에 --program-rules 를 추가. AC-28·AC-29 판정 불변. | 치환 없음 |
| R7.1 | SPEC-002 | AC-30(일치) | 본문 불변. AC-30 이 recheck 스냅숏 inputs·승계·validate 0 을 판정한다. | 치환 없음 |
| R7.3 | SPEC-002 | AC-30(일치), AC-32(일치) | 본문 불변(구조 규칙 검사에 R5.3 승계 규칙이 포함됨). AC-32 위반 사례를 여덟으로 늘렸다. | 치환 없음 |
| R8.1 | SPEC-003 | AC-33(일치) | run 수준 outcome 과 서브커맨드별 허용 값을 추가. AC-33 이 존재·값 집합을 판정. R8.3 과 같은 값 이름을 쓴다. | 치환 없음(필드 추가) |
| R8.3 | SPEC-004 | AC-34(일치) | 'reproduced 이상' 서열을 actionable 네 상태 열거로 바꾸고 outcome 산출 기준을 R8.1 과 맞췄다. AC-34 에 stale/unverified/private-report-ready 사례 추가. | 'reproduced 이상' 을 열거 집합으로 치환 — 상태에 서열이 없기 때문 |
| R9.3 | SPEC-015, SPEC-014 | AC-38(일치) | 허용 헤더 일곱 개를 긍정형으로 열거하고 환경 변수 조항을 자격증명 변수·hosts.yml 미접근 + os.environ 단일 함수로 좁혔다. R4.1 의 clone 환경 변수 설정과 충돌하지 않는다. AC-38 이 헤더 허용 집합·소스 문자열을 판정. | '인증 관련 헤더 외' 부정형 문장을 허용 목록 긍정형으로 치환 — 반대로 읽히는 모호함 제거 |
| R10.2 | SPEC-004, SPEC-002 | AC-34(일치), AC-39(일치), AC-30(일치), AC-23(일치) | 본문 불변. 매핑된 AC-34(actionable 열거 사례)·AC-30(recheck 스냅숏 승계·validate)·AC-23 판정이 확장됐다. 픽스처 다섯 묶음 요구는 그대로다. | 치환 없음 |
| R10.3 | SPEC-011 | AC-2(일치), AC-4(일치), AC-42(일치) | 본문 불변. AC-2 의 예외 규칙이 test_skill_contract 의 금지 문자열 검사 범위를 좁히지만 실존 저장소·모델명 금지는 유지된다. | 치환 없음 |
| R10.5 | SPEC-010 | AC-47(일치) | 대상·예산 질의를 필수 절차로, 미실행은 사용자 유보 인용이 있을 때만 허용하고 남은 findings 에 남긴다. AC-47 과 strict-only E2E 절이 같은 규칙을 말한다. | '미지정 시 not executed 기록' 을 '사용자 유보 인용 필수' 로 치환 — 통과 조건 없는 생략 경로를 닫기 위함 |
| R10.6 | SPEC-009 | AC-50(일치) | 신설. 행동 평가 시나리오 문서(네 시나리오·네 항목)를 요구하고 실행은 Non-goal 8 로 #82 귀속. AC-50 이 판정. | 치환 없음(신설) |
| R11.1 | SPEC-013 | AC-47(일치), AC-51(일치) | AC-51(세 파일 존재, CMD-7) 추가로 문서 배치가 직접 판정된다. AC-47 은 report 내용 판정으로 유지. | 치환 없음 |
| R11.2 | SPEC-013 | AC-41(일치) | AC-43 매핑을 제거해 참조 문서 요구는 AC-41 만으로 판정한다. 문서 내용 요구는 불변. | 치환 없음 |

라운드 1 에서 리뷰어가 미확인으로 남긴 두 사실은 오케스트레이터가 실행으로 확인했다: `QG_PY` 에 PyYAML 6.0.3 이 설치되어 있고, `unittest discover -k` 무매칭의 종료 코드는 5 다. 두 사실은 § Test strategy 에 적었다.
