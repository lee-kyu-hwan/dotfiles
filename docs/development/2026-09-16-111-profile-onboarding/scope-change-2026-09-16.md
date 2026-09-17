# 승인 후 범위 변경 — identity 계약의 의미 확정

- 발생: 2026-09-16, stage `IMPLEMENTING` 중
- 처리: `quality-goal` scope-change 절차. `invalidate-verification` 후
  `IMPLEMENTING → SPEC_REVIEW` 복귀. 남은 라운드 spec 2 / plan 1.
- 보존: 구현 변경 전부 보존(handoff patch 2,764줄). 커밋·푸시 없음.

## 1. 무효화된 전제와 그 정정 경위

### 1차 지적 — 승인된 Spec 의 결함

승인된 Spec 의 Claude canonical identity 는
`authMethod` + `orgId` + `subscriptionType` 을 담으면서 그 판정 결과를 `matched` 라 부르고,
`matched` 가 **개인 계정 동일성**을 증명하는 것처럼 기술했다. 이는 틀렸다.

합성 입력 실증(실제 인증 조작 없음):

```
alice@acme.test / bob@acme.test — 같은 orgId·authMethod·subscriptionType
  canonical 동일 → digest 동일 (59cfbeb90da8da81…)
```

즉 **같은 조직의 서로 다른 사용자를 구분하지 못한다**.

### 2차 — email 기반 재설계 시도와 그 폐기

오케스트레이터는 `email` HMAC 으로 개인 subject 를 식별하는 방향(D9)을 제안했고
그 방향으로 Spec 개정을 시작했다. **그 전제도 틀렸다.**

사용자의 read-only 실측(원문 값 미출력·미저장):

| 항목 | 두 Claude profile 비교 결과 |
|---|---|
| `loggedIn` | 양쪽 모두 `true` |
| `email` | **같음** |
| `orgId` | **다름** |

한 사람이 같은 이메일로 **서로 다른 두 조직**에 속해 각 profile 을 쓴다.
따라서 email-only HMAC 은 두 profile 의 지문을 같게 만들어
`duplicate_account` 로 **오판 차단**한다. 현재 사용 사례를 깨뜨린다.

**email 기반 subject fingerprint 와 email digest 동일 시 중복 차단은 폐기한다.**

## 2. 사용자 확정 결정

### D9. 선택 경계는 개인 사용자 ID 가 아니라 **조직 컨텍스트**다

이번 #111 이 구분해야 하는 단위는 사람이 아니라 profile 에 배정된 **조직 컨텍스트**다.

### D10. 기존 digest 를 그대로 재사용한다

`authMethod` + `orgId` + `subscriptionType` canonical digest 는 현재 두 조직을
실제로 구분하므로 **변경 없이 재사용**한다. email 을 canonical 에 넣지 않는다.
이메일 원문·파생 digest·HMAC 키를 만들지도, 저장하지도, 출력하지도 않는다.

### D11. `matched` 의 의미를 좁힌다

`matched` 가 **개인 동일성을 증명한다고 표현하지 않는다**. 증명하는 것은
enrollment 시점과 같은 **조직 컨텍스트**라는 사실뿐이다. 상태 이름과 문서 문언을
그 범위로 정확히 맞춘다.

### D12. 중복 매핑 차단

두 profile 의 **org-context digest 가 같으면** 중복 매핑으로 **차단·보고**한다.
비교는 내부에서만 하고 전체 digest 를 Git·상태 JSON·로그·tmux 에 출력하지 않는다.

### D13. 알려진 한계를 명시한다

**같은 조직의 서로 다른 사용자는 구분할 수 없다.** 이 한계를 Spec 과 운영 문서에
명시한다. 숨기거나 `matched` 로 덮지 않는다.

### D14. 비공식 스키마 — fail closed

`claude auth status --json` 의 필드 구성은 공식적으로 보장되지 않는다.
필요한 필드가 누락되거나 구조가 바뀌면 `matched` 로 판정하지 않고 **fail closed** 한다.
약한 판정으로 조용히 강등해 통과시키지 않는다.
근거: https://code.claude.com/docs/en/cli-usage

### D15. Keychain 동시 실행 검증은 별도 수동 게이트

시작 전 digest 검사는 프로세스 시작 시점 1회 검사이며 **실행 중 Keychain 격리를
보증하지 않는다**. `CLAUDE_CONFIG_DIR` 별 Keychain 분리는 열린 충돌 이슈가 있으므로
가정하지 않고 **사람이 전경에서 수행할 별도 수동 게이트**로 남긴다.
근거: https://github.com/anthropics/claude-code/issues/20553

자동 워크플로는 synthetic fixture 로 계약만 검증하고 실제 인증 조작을 하지 않는다.

### D16. 개정 범위 — 최소 수정

전제 오류는 **의미 규정과 중복 검사**에 국한된다. 다음은 **그대로 보존**한다.

- canonical identity 구성(`authMethod`+`orgId`+`subscriptionType`)
- strict registry v2 (`schema_version=2`, `contract_id=…-v2`)
- adapter 의 공식 필드 투영 (Claude `loggedIn`, Codex `checks["auth.credentials"]`)
- enrollment 파일 형식과 0700/0600·atomic replace
- admission 순서와 usage 이중 동의
- Codex `identity_contract="unavailable"`
- profile2 regular-file mirror
- read-only status backend
- 판정 명령 CMD-1·CMD-2 와 baseline 사실

바꾸는 것은 `matched` 의 의미 규정, 중복 매핑 차단, 알려진 한계 명시,
fail-closed 강화, 그리고 Keychain 수동 게이트를 완료 기준에 넣는 것뿐이다.

## 3. 공개 상태 어휘

| 상태 | 의미 |
|---|---|
| `matched` | enrollment 시점과 **같은 조직 컨텍스트**다. 개인 동일성은 증명하지 않는다 |
| `identity_drift` | enrollment 와 다른 조직 컨텍스트다 |
| `identity_unverifiable` | 필요한 필드 누락 또는 구조 변화로 판정 불가 — 차단 |
| `duplicate_mapping` | 다른 profile 과 같은 org-context digest — 차단 |
| `not_enrolled` / `stale_enrollment` | enrollment 없음 / v1 잔존 |
| `unavailable` | Codex 처럼 공식 subject 신호가 없는 계약 |

`unavailable`·`identity_unverifiable`·`duplicate_mapping` 은 어느 것도 `matched` 로
승격되지 않는다.

## 4. 이 실행의 금지 사항 (변경 없음)

실제 logout/login, credential 읽기·복사·rename·symlink, account 전환,
실행 중 worktree 이동을 수행하지 않는다. 검증은 synthetic fixture 와
공식 비밀 없는 상태 계약으로만 한다. 이메일 원문과 그 파생값을 만들지 않는다.
