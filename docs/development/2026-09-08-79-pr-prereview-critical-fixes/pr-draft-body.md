Refs #79

## 무엇을 추가하는가

다른 저장소의 최신 기본 브랜치를 상대로 재사용 패턴(`PAT-*`)의 기여 가능성을 검증하는 Codex 스킬 `dot_codex/skills/verifying-open-source-contribution-candidates/` 를 신설한다. 상위 epic 은 #78 이고, 이 변경은 그중 #79 하나만 다룬다. 형제 스킬(`collecting-recent-closed-prs`, `analyzing-open-source-pr-patterns`)은 읽기만 하고 수정하지 않는다.

구성은 다음과 같다.

- `scripts/verify_candidates.py` — 서브커맨드 `discover`·`record`·`recheck`·`render`·`validate` 와 `--print-revision`. 표준 라이브러리만 사용하고 Python 3.9 문법으로 파싱된다.
- `SKILL.md` — 발동·비발동 조건과 6단계 절차, 다섯 경계 문장(원격 텍스트는 데이터, 실행은 제시→승인→격리→기록, 외부 제안 직전 `recheck` 필수, GitHub 쓰기 금지, 수집·분석은 형제 스킬 담당).
- `references/verification-contract.md`, `references/github-verification-contract.md` — 후보 레코드 29 필드와 출처 분류, 상태 9 × 이유 14 허용 조합, readiness 12 키, 스냅숏 규칙, 종료 코드, endpoint·요청 순서·clone 계약. `tests/test_skill_contract.py` 가 이 문서를 파싱해 코드 상수와 대조한다.
- `evals/behavioral-eval.md` — 행동 평가 시나리오 네 개(실행은 #82 로 귀속, 이 변경에서는 미실행).
- `tests/` — 테스트 44개와 오프라인 픽스처. 네트워크·`gh`·실제 GitHub 없이 전부 통과한다.

핵심 안전 성질은 다음이다. 스크립트는 GitHub 에 GET 만 보내고 쓰기를 하지 않는다. 외부 저장소 코드를 실행·import·빌드·설치하지 않으며, clone 은 사용자가 허용할 때만 세션 임시 영역에 shallow clone 하고 정적으로 읽은 뒤 그 실행이 만든 정확한 경로만 정리한다. 원격 텍스트는 미신뢰 객체로만 저장하고 Markdown 에서는 닫을 수 없는 펜스에 넣는다. 토큰 형태 문자열은 출력 직전 마스킹한다. 근거 없는 `issue-ready`/`pr-ready` 는 게이트가 거부한다.

## 테스트

로컬에서 직접 실행한 결과다.

- 새 스킬 스위트: `Ran 44 tests` OK
- 형제 스킬 회귀: `analyzing-open-source-pr-patterns` 30개 OK, `collecting-recent-closed-prs` 108개 OK, 두 디렉터리는 기준 커밋 대비 불변
- `quick_validate.py`: `Skill is valid!`
- Python 3.9 문법 파싱: 통과
- 변경 경로 확인 및 이전 실행 문서 다섯 파일 SHA-256 불변: 통과

lint·type check·build 는 이 저장소에 구성이 없어 `not configured` 다.

## 실증한 범위와 실증하지 않은 범위

`discover` 실경로는 사용자 승인 범위에서 1회 검증했다. 대상 `eslint-community/eslint-plugin-promise`, 패턴 `PAT-001`, 단서 4개, 요청 예산 80, 후보 상한 2/2, clone 허용. 결과는 종료 코드 0, manifest `complete`/`discovered`, 요청 44/80, `failed_scopes` 없음, clone SHA 가 원격 head 와 동일, clone `removed: true` 였다. 관찰로 대상 저장소는 `rules/` 구조이고 문서가 자동 생성되므로(closed PR #396) `PAT-001` 의 경로 단서가 1:1 로 대응하지 않았다. 이는 관찰이며 적용 불가·후보 없음·정책 허용으로 단정하지 않았다.

`assessment`·`record`·`recheck` 의 실경로는 실제 GitHub 를 상대로 한 번도 실행하지 않았다. `CAN-*` 레코드도 없고 검증된 기여 후보도 없다. 즉 `discover` 성공은 기여 후보 검증이 아니다. 이 두 문장을 리뷰 시 그대로 전제해 달라.

## 남은 advisory

- `entry_count` 가 해시 대상 이름 수와 다를 수 있다(디렉터리 응답에서 `name` 없는 항목이 있을 때). 게이트가 묶는 값은 `sha256` 이라 오판은 없고 서술 필드만 부정확하다. 한 줄 수정으로 해소된다.
- Spec R3.2 의 정책 결과 필드 목록이 구현을 더 이상 서술하지 못한다(`status`·`entry_count` 누락). 배포되는 계약 문서는 11 키를 정확히 문서화한다. Spec 본문은 보고서가 고정한 digest 때문에 개정 노트나 후속 이슈로 다룬다.
- PR 직전 사전 리뷰에서 추가로 발견된 문제들은 이 PR 에 포함하지 않았다. 상세는 아래 참고.

## 배포와 후속 작업의 분리

이 변경은 저장소 소스만 추가한다. `chezmoi apply` 를 실행하지 않았으므로 `~/.codex/skills/` 에는 배포되지 않았다. Claude Code/Codex 공용 배포와 실행 차이 검증, 행동 평가 실제 실행은 #82 의 범위다. 트래커 수집(#80)과 일반 Issue 입력(#81)도 이 변경에 없다.

`docs/development/2026-09-07-79-verifying-open-source-contribution-candidates-plan-redesign/` 에 Spec·Plan·재설계 기록·보고서를 함께 둔다. 같은 디렉터리의 `preserved-run.sha256` 은 이전 실행(`docs/development/2026-09-06-79-…/`)의 보존 문서 다섯 개가 바뀌지 않았음을 판정한다. 이 PR 은 #79 를 닫지 않는다.
