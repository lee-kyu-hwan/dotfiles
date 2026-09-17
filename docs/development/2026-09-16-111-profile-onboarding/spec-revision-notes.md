## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | SCOPE-001 | AC-1(일치: 기존 adapter 성공 계약 유지), AC-2(일치: schema 누락 차단), AC-4(일치: redaction 유지), AC-20(일치: 교차 차단 유지), AC-24(일치: identity_unverifiable 판정 추가) | 비공식 schema fail-closed는 기존 login·redaction 전제를 깨지 않고 identity 판정 불가를 성공에서 분리한다. | 자체 개정 |
| R1.2 | SCOPE-001 | AC-3(일치: Codex 계약 유지), AC-4(일치: redaction 유지), AC-20(일치: Codex unavailable 비승격 유지) | Claude 조직 컨텍스트 개정은 Codex unavailable branch의 전제와 판정을 바꾸지 않는다. | 치환 없음 |
| R1.3 | SCOPE-001 | AC-1(일치: six-field success 유지), AC-3(일치: Codex payload 유지), AC-4(일치: 비밀 비노출 유지), AC-16(일치: 차단 상태 command 없음), AC-23(일치: 신설 상태 비승격) | identity_unverifiable과 duplicate_mapping을 exact domain에 넣어도 six-field 형식과 blocked verifier 기본값은 유지된다. | 자체 개정 |
| R2.1 | SCOPE-001 | AC-5(일치: strict registry v2 유지), AC-20(일치: contract gate 우회 없음) | 조직 컨텍스트 의미와 중복 검사는 registry schema나 provider별 contract 조합을 변경하지 않는다. | 치환 없음 |
| R2.2 | SCOPE-001 | AC-2(일치: required field와 email 제외 유지), AC-6(일치: canonical property 유지), AC-20(일치: digest gate 우회 없음), AC-21(일치: 조직 컨텍스트 경계 실증) | 개인 의미를 제거하면서도 canonical bytes와 digest 안정성 전제를 그대로 보존한다. | 폐기된 email HMAC subject fingerprint 방향을 기존 org-context digest 무변경 재사용으로 대체한다. |
| R2.3 | SCOPE-001 | AC-7(일치: v2 형식·권한·상태 유지), AC-20(일치: enrollment gate 우회 없음), AC-21(일치: matched 의미 축소) | matched 의미를 조직 컨텍스트로 좁혀도 enrollment 형식·0700·0600·atomic replace와 stale 처리 전제는 유지된다. | 자체 개정 |
| R2.4 | SCOPE-001 | AC-8(일치: unavailable 유지), AC-10(일치: admission 순서 유지), AC-15(일치: public 상태 유지), AC-20(일치: matched 승격 금지 유지) | Claude 조직 컨텍스트 개정은 Codex unavailable의 별도 admission branch를 열거나 닫지 않는다. | 치환 없음 |
| R2.5 | SCOPE-001 | AC-9(일치: usage 이중 동의 유지), AC-10(일치: identity 우선순위 유지), AC-15(일치: usage 상태 보존), AC-20(일치: sufficient 승격 금지 유지) | 새 identity 차단 상태는 usage 이중 동의 뒤가 아니라 앞에서 판정되어 consent가 이를 덮지 못한다. | 치환 없음 |
| R2.6 | SCOPE-001 | AC-10(일치: 기존 precedence 유지), AC-20(일치: gate 우회 없음), AC-22(일치: duplicate mapping 선차단), AC-23(일치: usage consent로 identity 차단 불가) | identity_unverifiable과 duplicate_mapping을 identity 단계에 추가해 login·binding·scope·cost·usage 순서를 우회하는 경로를 만들지 않는다. | 자체 개정 |
| R3.1 | SCOPE-001 | AC-11(일치: regular-file mirror 유지), AC-20(일치: public asset 경계 유지) | identity 의미 개정은 canonical quality-goal과 profile2 mirror의 파일 집합·byte equality를 변경하지 않는다. | 치환 없음 |
| R3.2 | SCOPE-001 | AC-12(일치: denylist 유지), AC-20(일치: settings·secret 경계 유지) | 새 상태와 수동 게이트는 profile2 공용 allowlist를 넓히지 않는다. | 치환 없음 |
| R3.3 | SCOPE-001 | AC-13(일치: synthetic diff·sentinel 유지), AC-20(일치: 실제 account home 비접근 유지) | org-context fixture 추가는 rendered-home 검사의 read-only·secret-free 전제를 바꾸지 않는다. | 치환 없음 |
| R4.1 | SCOPE-001 | AC-14(일치: read-only status 유지), AC-20(일치: provider exec·write 우회 없음) | duplicate 비교와 schema 차단을 status 판정에 추가해도 status backend는 write와 provider exec를 수행하지 않는다. | 치환 없음 |
| R4.2 | SCOPE-001 | AC-15(일치: 공개 상태·exit 확장), AC-20(일치: ready 비승격), AC-22(일치: duplicate_mapping 차단), AC-23(일치: 세 상태 matched 비승격), AC-24(일치: identity_unverifiable 차단) | 두 신설 차단 상태는 ready와 분리되고 기존 launch admission 동치·exit 계약을 우회하지 않는다. | 자체 개정 |
| R4.3 | SCOPE-001 | AC-16(일치: exact command schema와 empty 차단), AC-20(일치: recovery 우회 없음), AC-22(일치: digest 비노출), AC-23(일치: 신설 상태 자동 복구 없음) | identity_unverifiable과 duplicate_mapping에 빈 commands를 요구해 불안전한 자동 복구 경로를 만들지 않는다. | 자체 개정 |
| R4.4 | SCOPE-001 | AC-17(일치: 제118호 dependency 순서 유지), AC-20(일치: ready 전 foreground action 금지 유지) | 신설 상태는 status가 ready일 때만 다음 launch를 검토하는 제118호 후순위 dependency를 강화하며 소유 경로를 바꾸지 않는다. | 치환 없음 |
| R5.1 | SCOPE-001 | AC-18(일치: 운영 계약 확장), AC-20(일치: fail-closed 문서 유지), AC-25(일치: matched 한계 명시), AC-26(일치: Keychain 수동 게이트 추가) | 운영 문서에 의미·한계·수동 게이트를 함께 요구해 구현 상태와 recovery 설명이 갈라지는 공백을 만들지 않는다. | 자체 개정 |
| R5.2 | SCOPE-001 | AC-19(일치: synthetic-only 명령 유지), AC-20(일치: 교차 회귀 확장) | 새 자동 판정은 기존 CMD-1·CMD-2와 synthetic fixture만 사용하고 실제 인증 조작 금지를 유지한다. | 치환 없음 |
| R6.1 | SCOPE-001 | AC-20(일치: 교차 gate 비우회), AC-21(일치: 같은 email·다른 조직과 같은 조직·다른 사용자 matrix), AC-25(일치: 운영 문서 한계) | 조직 컨텍스트 경계는 같은 email을 쓰는 서로 다른 두 조직 profile을 허용하면서 개인 동일성 주장을 제거한다. | 폐기된 email HMAC subject fingerprint 방향을 개인이 아닌 org-context 경계와 기존 digest 재사용으로 대체한다. |
| R6.2 | SCOPE-001 | AC-20(일치: admission 경계 유지), AC-22(일치: 중복 매핑 차단·비노출), AC-23(일치: usage consent보다 앞선 차단) | duplicate_mapping은 matched와 ready를 만들지 않고 admission 순서·usage 이중 동의·status read-only 전제를 보존한다. | 폐기된 email digest 동일 시 duplicate_account 방향을 org-context digest 동일 시 duplicate_mapping 차단으로 대체한다. |
| R6.3 | SCOPE-001 | AC-20(일치: exact-contract gate 유지), AC-23(일치: 신설 상태 matched 비승격), AC-24(일치: 비공식 schema fail-closed) | identity_unverifiable은 unavailable·duplicate_mapping과 함께 성공 승격을 금지해 다른 해소의 fail-closed 전제를 깨지 않는다. | 자체 개정 |
| R6.4 | SCOPE-001 | AC-20(일치: 자동 경계 비우회), AC-26(일치: 사람 전경 동시 실행 PASS 완료 조건) | 수동 Keychain 게이트는 자동 CMD-1·CMD-2를 대체하지 않고 시작 시점 검사와 실행 중 격리의 증거 범위를 분리한다. | 자체 개정 |
