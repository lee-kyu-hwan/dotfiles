## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R1.1 | SCOPE-001 | AC-1(일치: official projection 보존) AC-2(일치: 판정 불가 분리) AC-4(일치: redaction 유지) AC-20(일치: 비승격 교차 회귀) AC-24(일치: schema drift fail closed) | 조직 컨텍스트 의미 변경은 기존 official field projection과 redaction 전제를 깨지 않고 판정 불가 상태만 구체화한다. | 자체 개정; 치환 없음 |
| R1.2 | SCOPE-001 | AC-3(일치: Codex 계약 보존) AC-4(일치: redaction 유지) AC-20(일치: unavailable 비승격) | Claude 전용 중복 입력은 Codex unavailable 경로에 주입되지 않아 기존 Codex 계약과 충돌하지 않는다. | 자체 개정; 치환 없음 |
| R1.3 | SCOPE-001 | AC-1(일치: six-field 유지) AC-3(일치: Codex payload 유지) AC-4(일치: 공개 비노출) AC-16(일치: commands 경계) AC-23(일치: identity 상태 비승격) | 신설 identity 상태는 exact six-field와 public redaction을 유지하며 matched 승격 경로를 만들지 않는다. | 자체 개정; 치환 없음 |
| R2.1 | SCOPE-001 | AC-5(일치: registry v2 보존) AC-20(일치: exact contract 유지) | active profile 열거는 이미 검증된 strict registry만 사용해 implicit default나 legacy 활성화를 만들지 않는다. | 자체 개정; 치환 없음 |
| R2.2 | SCOPE-001 | AC-2(일치: required field 엄격성) AC-6(일치: canonical 불변) AC-20(일치: identity 비승격) AC-21(일치: 조직 컨텍스트 경계) | canonical 3-field와 v2 digest를 변경하지 않아 email 기반 폐기 결정 및 기존 normalization과 일치한다. | email HMAC 재설계를 폐기하고 기존 canonical 재사용으로 치환 |
| R2.3 | SCOPE-001 | AC-7(일치: v1/v2 경계 보존) AC-20(일치: enrollment 비우회) AC-21(일치: matched 의미 축소) | v1·v2 파일 형식과 permission을 유지하고 matched의 문서 의미만 조직 컨텍스트로 좁힌다. | 개인 동일성 표현을 조직 컨텍스트 표현으로 치환 |
| R2.4 | SCOPE-001 | AC-8(일치: unavailable 보존) AC-10(일치: precedence 유지) AC-15(일치: ready 하위 상태 유지) AC-20(일치: 비승격) | Claude 중복 비교가 Codex digest I/O 0회와 unavailable 상태를 우회하거나 matched로 바꾸지 않는다. | 자체 개정; 치환 없음 |
| R2.5 | PLAN-002 | AC-9(일치: launch/status 양쪽 2×2) AC-10(일치: 앞선 identity 우선) AC-15(일치: status-launch 동치) AC-20(일치: sufficient 비승격) | launch parser의 flag 전달을 명시해 status와 같은 이중 동의 규칙을 공유하며 identity 차단보다 앞서지 않는다. | status 전용 서술을 launch와 status 양쪽 서술로 치환 |
| R2.6 | SPEC-004, PLAN-002 | AC-10(일치: admission 순서) AC-20(일치: gate 비우회) AC-22(일치: duplicate 차단) AC-23(일치: identity 우선) | registry 기반 duplicate 입력과 launch consent 전달은 shared classifier의 기존 login→identity→cost→usage 순서를 유지한다. | 입력 경로 부재를 verifier 전용 registry 열거 계약으로 치환 |
| R3.1 | PLAN-003 | AC-11(일치: mirror equality) AC-20(일치: public/private 경계) | 복사 기반 render simulation은 기존 45-file regular mirror의 set·bytes 검증을 그대로 사용한다. | 불명확한 render를 기존 복사 기반 fixture로 치환 |
| R3.2 | PLAN-003 | AC-12(일치: denylist 유지) AC-20(일치: private ingress 차단) | 실제 chezmoi를 호출하지 않아 denylist 검증이나 untrusted account-home 경계를 넓히지 않는다. | 불명확한 render를 기존 복사 기반 fixture로 치환 |
| R3.3 | PLAN-003 | AC-13(일치: isolated diff와 live-action sentinel) AC-20(일치: secret 경계 유지) | copy render와 chezmoi sentinel을 함께 고정해 synthetic diff 증거와 production mutation 금지를 동시에 유지한다. | 실제 바이너리 가능성을 복사 기반 simulation으로 치환 |
| R4.1 | PLAN-002, SPEC-004 | AC-14(일치: read-only status) AC-20(일치: side-effect 0회) | status와 launch가 같은 registry-derived verifier 입력을 쓰되 status는 여전히 exec/write path를 갖지 않는다. | status 입력 공백을 shared verifier-only 주입으로 치환 |
| R4.2 | SPEC-004 | AC-15(일치: 신설 exact status/exit) AC-20(일치: ready 비우회) AC-22(일치: duplicate 결과) AC-23(일치: 비승격) AC-24(일치: unverifiable 결과) | 두 신설 상태를 status-launch 1:1 표와 단일 decision 변환에 추가해 별도 우회 classifier를 만들지 않는다. | 상태 누락을 exact `identity_unverifiable`·`duplicate_mapping` 행으로 치환 |
| R4.3 | SPEC-004 | AC-16(일치: empty commands/redaction) AC-20(일치: 공개 경계) AC-22(일치: digest 비노출) AC-23(일치: identity 차단) | duplicate/unverifiable commands를 비워 복구 자동화나 digest 노출 경로를 만들지 않는다. | 신설 차단 상태의 command 공백을 명시하는 것으로 치환 |
| R4.4 | SCOPE-001 | AC-17(일치: #118 dependency 보존) AC-20(일치: owned path 경계) | 조직 컨텍스트 변경은 #118 결과 schema나 소유 경로를 수정하지 않고 네 공유 파일 rebase 계약을 유지한다. | 자체 개정; 치환 없음 |
| R5.1 | SCOPE-001 | AC-18(일치: 운영 계약 문서화) AC-20(일치: 교차 경계) AC-25(일치: 개인 식별 한계) AC-26(일치: 수동 게이트) | 문서 delta가 matched 의미·폐기된 email 방향·Keychain 한계를 함께 기록해 자동 검증의 보증 범위를 과장하지 않는다. | 개인 동일성 문언을 조직 컨텍스트와 수동 게이트 문언으로 치환 |
| R5.2 | SCOPE-001, PLAN-003 | AC-19(일치: synthetic-only 명령) AC-20(일치: production 경계) | copy render와 새 identity fixture 모두 temp synthetic 입력만 사용해 실제 account/network/chezmoi 접근을 추가하지 않는다. | 불명확한 render를 기존 synthetic copy fixture로 치환 |
| R6.1 | SCOPE-001 | AC-20(일치: 좁아진 matched 의미) AC-21(일치: org-context 경계) AC-25(일치: 한계 문서화) | unchanged canonical과 same-email/different-org 허용을 함께 고정해 폐기된 email 식별 방향을 되살리지 않는다. | email HMAC 방향을 기존 org-context digest 재사용으로 치환 |
| R6.2 | SPEC-004 | AC-20(일치: gate 비우회) AC-22(일치: duplicate 입력·결과) AC-23(일치: 비승격) | verifier child의 registry-derived valid-v2 비교가 차단·exit 3·empty commands·digest 비노출을 만들고 다른 admission gate를 건너뛰지 않는다. | 입력 경로 부재를 `AI_OTHER_ACTIVE_CLAUDE_IDENTITY_DIGEST_FILES` 주입으로 치환 |
| R6.3 | SCOPE-001 | AC-20(일치: fail closed) AC-23(일치: 상태 비승격) AC-24(일치: schema 변화 차단) | required field 실패를 identity unverifiable로 분리해 email·fallback·이전 digest로 matched를 합성하지 않는다. | unknown 압축을 명시적 identity unverifiable 차단으로 치환 |
| R6.4 | SCOPE-001 | AC-20(일치: 자동 경계 비우회) AC-26(일치: 별도 사람 수동 게이트) | 자동 CMD 성공과 사람의 동시 실행 PASS를 분리해 시작 전 digest 검사를 실행 중 격리 보증으로 오해하지 않는다. | 자동 완료만으로 충분하다는 전제를 별도 수동 게이트로 치환 |
