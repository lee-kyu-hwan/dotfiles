## 라운드 2 개정

| 요구사항 | 해소 finding | 함께 바뀐 항목 | 상호작용 판정 | 치환 근거 |
|---|---|---|---|---|
| R3.2 | SPEC-002 | AC-11(일치: selectable `codex-default`와 기존 provider-default home을 고정) | 단일 selectable Codex account가 추가 account 확장성이나 no-fallback 전제를 깨지 않고 새 선택 경로도 열지 않는다. | 자체 개정; 기존 account와 home의 의미가 불명확했던 문장을 배포 가능한 exact 계약으로 치환했다. |
| R3.3 | SPEC-004 | AC-12(일치: selectable alias의 exact full-alias match를 판정) | exact-match 규칙은 `codex-default`를 허용하고 non-selectable legacy records를 검사 대상에서 제외하므로 다른 legacy 보존 해소와 충돌하지 않는다. | 자체 개정; substring 또는 component match로도 읽히던 금지 규칙을 exact match로 치환했다. |
| R3.5 | SPEC-003, SPEC-005 | AC-14(일치: directory-only domain과 non-directory registry rejection을 판정) | directory-only admission은 remote와 organization을 결정 입력에서 제거하면서 same-remote different-root 선택을 그대로 성립시키고, CMD-4에서 AC-13을 제외해 CMD-17의 home-surface 판정과 충돌하지 않는다. | 자체 개정; kind domain이 없던 allowed-scope 계약을 directory-only fail-closed 계약으로 치환하고 CMD-4의 과도한 AC 범위 주장을 제거했다. |
| R3.6 | SPEC-002 | AC-55(일치: deployed Codex legacy record와 old binding 차단을 판정) | opaque legacy record는 active parser와 모든 후보 tier 밖이라 legacy 보존이 선택 경로를 재도입하지 않고 `codex-default` 계약도 바꾸지 않는다. | 치환 없음; Codex legacy alias·home·stored binding 처리를 위한 신규 요구사항이다. |
| R6.5 | SPEC-007 | AC-30(일치: real deployed path와 synthetic fixture path를 구분) | synthetic private-child assertion 예외는 credential·identity·provider output 금지를 완화하지 않고 CMD-17의 exact env 판정과 CMD-15의 hygiene 판정을 양립시킨다. | 자체 개정; 모든 config-home-shaped test path를 금지하던 문장을 real deployed path와 파생값 금지로 치환했다. |
| R7.4 | SPEC-006 | AC-34(일치: CMD-8이 모든 required heading과 phrase를 열거해 검사) | executable documentation 판정은 운영 계약의 내용을 줄이지 않고 수동 판단 gap만 닫는다. | 자체 개정; 문서 위치만 제시하던 판정을 deterministic documentation contract로 치환했다. |
| R10.1 | SPEC-001 | AC-45(일치: shipped active declarations와 opaque Claude legacy record를 구분) | `defaults`·`scope_bindings` 제거와 opaque byte 보존을 분리해 directory-only active schema를 깨지 않고 legacy selection·admission 경로를 열지 않는다. | 자체 개정; legacy entry의 shipped registry 내 존속 방식과 active declaration의 경계가 없던 문장을 치환했다. |
| R10.2 | SPEC-001, SPEC-002 | AC-46(일치: 두 legacy record의 separate-generation zero-reference removal을 판정) | Claude와 Codex에 같은 zero-reference 제거 gate를 적용해 어느 legacy record도 구현 세대에서 제거되지 않으며 다른 migration premise를 깨지 않는다. | 자체 개정; Claude만 명시하던 제거 gate를 두 preserved legacy records에 일관되게 적용했다. |
| R11.8 | SPEC-006 | AC-54(일치: CMD-8이 exact done 의미와 status 비권한 phrase를 검사) | executable phrase check는 hook mapping이나 status surface 의미를 바꾸지 않고 issue-completion 오해 gap만 닫는다. | 자체 개정; 문서 위치 기반 판단을 exact phrase의 deterministic check로 치환했다. |
