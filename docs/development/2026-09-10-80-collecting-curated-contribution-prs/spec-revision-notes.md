## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | SPEC-003 | AC-1 (일치: CMD-2 exact contract test ID를 판정 수단에 추가) | 테스트 이름 강화는 routing 경계나 다른 finding 해소의 전제를 깨지 않고 공백을 만들지 않는다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R1.2 | SPEC-003 | AC-2 (일치: CLI 사전 검증을 전담하는 exact contract test ID를 추가) | 필터 선택 강화는 network 전 입력 거부 계약과 일치하며 다른 해소와 충돌하지 않는다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R1.3 | SPEC-003, SPEC-004 | AC-3 (일치: fixture·eval 허용 집합과 exact packaging test ID를 함께 판정) | fixture와 eval을 허용해 CMD-6·CMD-7의 입력을 합법화하되 six-file revision 범위는 넓히지 않는다. | 허용 범위의 모순을 제거하고 필터 판정을 exact ID로 치환 |
| R2.1 | SPEC-001, SPEC-003 | AC-4 (일치: Link 신호·page 검증·adapter page 요청·partial을 exact collection test로 판정) | page 요청은 R2.3 budget을 소비하고 provenance와 실패는 R4.1·R4.3 및 AC-23에 같은 의미로 연결되어 새 공백이 없다. | 구현 불가능한 exact absolute URL 추적을 검증된 page 전달 결정으로 치환 |
| R2.2 | SPEC-003 | AC-5 (일치: reference 정규화를 전담하는 exact end-to-end test ID를 추가) | test ID 강화만 수행해 origin 관측과 cap 의미를 바꾸지 않는다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R2.3 | SPEC-001, SPEC-003 | AC-6 (일치: cap count exact test를 지정), AC-7 (일치: Link 검증 후 page 요청만 shared budget에 계상) | 잘못된 Link에서 추측 요청을 금지해 R2.1 partial 판정과 request provenance가 서로 모순되지 않는다. | exact URL 직접 추적 전제를 adapter page 요청과 exact test 증거로 치환 |
| R2.4 | SPEC-003 | AC-8 (일치: authoritative hydration exact end-to-end test ID를 추가) | 형제 hydration 재사용과 transport 결정은 분리되어 다른 해소의 전제를 깨지 않는다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R2.5 | SPEC-003 | AC-9 (일치: role separation exact collection test ID를 추가) | test ID 강화는 tracker와 upstream association 분리 의미를 바꾸지 않는다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R2.6 | SPEC-003 | AC-10 (일치: injection 불활성 exact end-to-end test ID를 추가) | 원격 텍스트 비신뢰 경계는 Link URL을 provenance로만 쓰는 R2.1 결정과 일치한다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R3.1 | SPEC-002, SPEC-003 | AC-11 (일치: analyzer 호환성 판정을 유지), AC-12 (일치: schema 불변식 exact test를 지정), AC-37 (일치: fresh envelope의 curated generator를 판정), AC-38 (일치: merged envelope 보존과 curated provenance 위치를 판정) | fresh와 merge 정책을 분리해 기존 생성자 오기 없이 manifest·source provenance를 보존하며 다른 해소와 충돌하지 않는다. | 모든 corpus가 curated generator를 가진다는 모호한 문언을 fresh/merge 이원 정책으로 치환 |
| R3.2 | SPEC-003 | AC-13 (일치: 관측 provenance exact collection test ID를 추가) | page provenance는 manifest에, comment edit provenance는 source observation에 남아 역할 중복이나 공백이 없다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R3.3 | SPEC-003 | AC-14 (일치: global identity exact merge test ID를 추가) | 생성자 envelope 보존은 record identity 병합 불변식에 영향을 주지 않는다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R3.4 | SPEC-003 | AC-15 (일치: 형제 unfiltered 전체 suite 판정을 유지), AC-16 (일치: explicit-only exact merge test ID를 추가) | 형제 transport를 그대로 두고 source_policy 세 파일만 바꾸므로 SPEC-001 해소와 상충하지 않는다. | 필터 대상 AC만 exact ID 판정으로 치환 |
| R3.5 | SPEC-003 | AC-17 (일치: recollection idempotency exact merge test ID를 추가), AC-18 (일치: analyzer append-only 판정을 유지) | comment ID 순서 이상을 partial로 처리해 관측 prefix를 complete로 오보고하는 새 경로가 없다. | 필터 대상 AC만 exact ID 판정으로 치환 |
| R3.6 | SPEC-003 | AC-19 (일치: projection과 history exact merge test ID를 추가) | transport gap의 partial 판정은 authoritative state 합성 금지와 독립이며 충돌하지 않는다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R4.1 | SPEC-001, SPEC-002, SPEC-003, SPEC-006 | AC-20 (일치: next URL·parsed page·validation·generator·method provenance exact test를 지정) | page provenance는 R2.3 budget event와 R4.3 partial 사유를 연결하고 curated revision 위치도 명확히 해 다른 해소를 깨지 않는다. | 추상적 comment page provenance를 관측·검증 필드와 exact test로 구체화 |
| R4.2 | SPEC-003, SPEC-006 | AC-21 (일치: same-tracker resume·append exact test를 지정), AC-22 (일치: fingerprint mismatch exact test를 지정) | R4.5 discriminator가 먼저 foreign manifest를 거부하고 같은 tracker만 기존 fingerprint 규칙으로 넘겨 공백이 없다. | 필터 판정을 exact ID로 치환하고 foreign manifest 사전 조건을 분리 |
| R4.3 | SPEC-001, SPEC-003, SPEC-005, SPEC-006 | AC-23 (일치: Link·comment order gap을 partial로 판정), AC-24 (일치: complete 0과 input 2·partial 3·failed 4를 모두 판정) | 0·2·3·4 행렬은 R2.1의 비추측 pagination과 R4.5 discriminator 거부를 같은 실패 의미로 연결한다. | 누락된 complete 종료 코드와 구현 불가 pagination 전제를 명시적 상태 행렬로 치환 |
| R4.4 | SPEC-003 | AC-25 (일치: atomic output exact collection test ID를 추가) | foreign manifest와 Link 검증은 쓰기 전에 실패하므로 기존 destination 보존과 충돌하지 않는다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R4.5 | SPEC-006 | AC-39 (일치: 형제 manifest와 다른 tracker manifest를 network·write 전에 거부) | R4.2 resume/fingerprint보다 먼저 discriminator를 확인해 foreign run 혼합 공백을 닫고 같은 tracker resume은 유지한다. | 자체 개정 |
| R5.1 | SPEC-003 | AC-26 (일치: public synthetic fixture exact contract test ID를 추가) | fixture 허용 범위 확대는 합성 데이터 제한 안에서만 이뤄져 private 원문 노출 공백이 없다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R5.2 | SPEC-003 | AC-27 (일치: read-only runner exact end-to-end test ID를 추가) | Link URL은 실행 argv의 절대 endpoint로 전달되지 않아 GET allowlist와 형제 adapter 계약을 유지한다. | 라운드 1의 모호한 실제 선택 서술을 exact ID 증거로 치환 |
| R6.1 | SPEC-004 | AC-28 (일치: fixtures·evals를 허용하되 canonical six-path revision 판정을 유지) | R1.3 파일 집합 확대가 revision 입력을 암묵적으로 늘리지 않아 형제와 신규 digest 계약 모두 유지된다. | 허용 파일과 revision 대상 파일을 동일시하던 공백을 명시적 분리로 치환 |
| R6.3 | SPEC-003 | AC-30 (일치: 행동 평가 문서 판정을 유지), AC-31 (일치: RED exact end-to-end test ID를 추가), AC-32 (일치: safety exact end-to-end test ID를 추가) | exact test ID 증거와 별도 행동 평가 문서는 상호 보완하며 독립 평가를 unit test로 대체하지 않는다. | 필터 대상 AC만 exact ID 판정으로 치환 |
| R6.4 | 공식 finding이 아니라 base commit `067923b` fast-forward 반영에 따른 회귀 baseline 사실 정정 | AC-33 (일치: collector 110개·갱신 revision baseline), AC-34 (일치: analyzer 30개·revision 불변 baseline), AC-35 (일치: candidate verifier 62개 baseline) | 회귀 baseline 수치만 현행화하고 전체 suite 종료 코드 0 판정은 유지하므로 다른 해소의 전제를 깨거나 새 공백을 만들지 않는다. | fast-forward 전 collector 108개·이전 revision 근거를 병합 후 재측정한 110개·현재 revision 근거로 치환 |
| R6.5 | SPEC-003 | AC-40 (일치: AC→exact unittest method→filter 매핑 meta-test와 verbose 증거를 판정) | 종료 코드 5인 무매칭과 종료 코드 0인 무관 substring 매칭을 모두 배제하며 모든 CMD의 기존 판정 의미를 바꾸지 않는다. | 무매칭이 종료 코드 0이라는 잘못된 전제를 실측 5로 정정하고 잔여 substring 위험만 exact ID 규약으로 치환 |
