# #82 1단계 — 검증 스킬을 손으로 한 번 통과시킨 기록

- 작성: 2026-09-19
- 범위: #82 완료 기준 11개 중 하나만 다룬다. `verifying-open-source-contribution-candidates` 를 실제 패턴 후보로 한 번 돌리고, 수집 → 분석 → 검증 사이에서 손으로 옮긴 것을 적는다
- 하지 않은 것: 전체 워크플로 자동 연결, Claude·Codex 공용 배포, 분석 스킬 수정(#183), curated 스킬 수정(#184), 검증 스킬 코드 수정
- 안전 제약 준수: eslint 쪽 저장소(`eslint-learning-lab` 포함)에 쓴 파일 0개. GitHub 쓰기 0회. upstream 코드 실행 0회. clone 0회. 의존성 설치 0회. 네트워크는 `gh api` GET 과 공개 문서 조회뿐이다

## 0. 결론

**돌았다. `CAN-*` 3건이 근거 링크와 함께 나왔다.** 다만 검증 스킬만으로는 판정이 나오지 않았다. 세 가지를 스킬 밖에서 손으로 채워야 했다.

1. **입력 변환.** #169 후보 C1~C7 은 `PAT-*` 형식이 아니다. C1 을 `PAT-002` 로 손으로 옮겼다. 필드 12개 중 11개를 새로 채웠고, 그중 검증 결과를 좌우하는 `search_clues` 는 전부 새로 지었다
2. **정책 확인.** 스킬의 정책 조회가 ESLint 의 CONTRIBUTING·CLA·SECURITY·CoC·PR 템플릿을 **모두 `absent` 로 기록했다.** 원인은 조직 `.github` 저장소 조회에 대상 저장소의 기본 브랜치를 `ref` 로 넘기는 계약 결함이다(§ 5.1). AI 정책은 조회 범위 밖(`eslint/eslint` docs)에 있다. 손으로 읽어 확인했지만, 게이트가 discovery 에 없는 정책 해시를 거부해서 **후보 기록에 `found: true` 로 적을 수 없다.** 반대로 정책을 전혀 보지 않고도 readiness 만 `confirmed` 로 적으면 `issue-ready` 가 통과된다(§ 5.2, 로컬 실험으로 확인)
3. **중복 확인.** discover 의 중복 검색은 `complete: true` 였지만 실제 중복(이슈 #710, PR #720)을 찾지 못했다. locus 를 정한 뒤 손으로 다시 검색해서 찾았다

C1 패턴 자체는 다른 저장소에서도 성립했다. `eslint/markdown` 메인테이너가 PR #433 에서 같은 결정을 내렸고, 같은 종류의 결함이 `accepted` 이슈로 열려 있다. 하지만 둘 다 이미 처리 중이어서 **새로 제출할 기여 후보는 0건** 이다.

### 이전 실행과의 관계

과제 설명과 #183 본문은 이 스킬이 한 번도 실행되지 않았다고 적었지만 정확하지 않다. #79 가 2026-09-10 에 제한된 라이브 검증을 한 번 했다(`eslint-community/eslint-plugin-promise` × `PAT-001`, `CAN-001` `unverified`, 기록은 `docs/development/2026-09-10-79-live-verification-proposal/`). 그때는 회귀 확인이 목적이었고, 대상 저장소가 소스 corpus 안에 있었다. #79 완료 기준 7("실제 저장소 근거에 연결된 후보 판정")은 미충족으로 #82 에 넘어왔다.

이번 실행에서 처음 확인된 것은 다음 네 가지다.

- 분석 스킬 밖에서 나온 결함 종류 패턴(C1)
- 소스 corpus 밖의 대상 저장소
- 근거에 연결된 서로 다른 판정 3건(`duplicate-open`, `already-fixed`, `reproduction-failed`)
- search API 403 rate-limit 재시도 경로의 라이브 관측. #79 문서가 라이브에서 재현할 수 없다고 적은 경로다

## 1. 입력 계약 — `PAT-*` 는 어떤 형식이어야 하나

근거: `scripts/verify_candidates.py` 의 `validate_analysis_envelope`, `ANALYSIS_ENVELOPE_FIELDS`, `PATTERN_FIELDS`

| 층 | 요구 |
| --- | --- |
| envelope | 정확히 6필드 `schema_version`("1.0.0"), `generated_by`(객체), `analysis_generated_by`(객체), `records`(배열), `patterns`(배열), `limitations`(문자열 배열). 추가 필드 거부 |
| pattern | 12필드 필수: `pattern_id`(`PAT-<n>`, 중복 금지), `description`, `search_clues`·`applicability`·`counterconditions`·`expected_tests`·`maintainer_judgment_required`(문자열 배열), `provenance_mode`(문자열), `source_licenses`(배열), `confidence`(객체), `superseded_by`(null 또는 `PAT-<n>`), `pattern_history`(1개 이상, 마지막 항목 `revision` 이 `sha256:<64hex>`). 추가 필드는 허용(`evidence_pr_ids`, `generated_by` 등) |
| `records` | 배열인지만 본다. 검증 스킬은 PR 레코드 내용을 쓰지 않는다 |

검증 스킬이 실제로 **쓰는** 패턴 필드는 셋뿐이다.

- `pattern_id`
- `pattern_history[-1].revision` 은 후보의 `pattern_revisions` 로 간다
- `search_clues` 는 앞에서부터 최대 5개를 쓴다. 단서 하나마다 이슈·PR 검색 4회(open/closed × issue/pr)와 코드 검색 1회를 한다. 큰따옴표·역슬래시·제어문자가 든 단서는 거부된다

나머지 9필드는 계약 검사만 통과하면 된다. assessment 를 쓰는 AI 가 판단 재료로 읽는다.

| 입력 | 계약 통과 | 비고 |
| --- | --- | --- |
| `runs/2026-09-06-four-repositories/analysis.json` | 통과 | `patterns` 0건. discover 에 줄 것이 없다 |
| `runs/2026-09-06-four-repositories/supplement-analysis.json` | **그대로 통과** | `PAT-001` 1건 |
| #169 `candidates.json`(C1~C7) | **통과 불가** | 항목이 `{id, statement, cited_prs, found_by}` 뿐이다. `PAT-<n>` ID, 12필드 중 11필드, `pattern_history` 가 없다 |

## 2. C1~C7 변환 — 필요한가, 어디에 두어야 하나

**필요하다.** 형식만의 문제가 아니다. 옮기면서 새로 정해야 했던 값은 다음과 같다.

| 필드 | C1 에서 가져온 것 | 새로 정한 것 |
| --- | --- | --- |
| `description` | 반박 검증 워커의 `revised_statement` | — |
| `evidence_pr_ids` | `cited_prs` 3개 | `n#553`·`n#554`·`promise#637` 를 corpus 로컬 ID `PR-002`·`PR-004`·`PR-008` 로 바꿨다. 매핑은 #169 의 `keymap.json` 에만 있다. corpus 마다 `PR-*` 를 따로 매기므로 두 corpus 에 걸친 패턴은 한 envelope 의 ID 공간으로 표현할 수 없다. C1 은 세 PR 이 모두 supplement 쪽이라 가능했다 |
| `source_licenses` | — | supplement 레코드의 `license.spdx_id` 에서 찾아 넣었다(MIT·MIT·ISC) |
| `applicability`·`counterconditions`·`expected_tests`·`maintainer_judgment_required` | — | 새로 썼다 |
| **`search_clues`** | — | **전부 새로 지었다.** 검증 결과를 좌우하는 필드다(§ 5.3) |
| `confidence` | 반박 검증 `confidence: medium` | 한계 2개를 적었다 |
| `pattern_history[].revision` | — | 분석 스킬이 만든 값이 아니므로 분석 스킬의 revision 을 빌려 쓰지 않았다. 생산자를 `manual-bridge-from-agy-candidates` 로, revision 을 변환 입력 두 파일(`candidates.json`, `verify_C1.result.json`)의 바이트 해시로 두었다 |

C2~C7 은 옮기지 않았다. C3 은 `PAT-001` 과 같다. C4·C5·C7 은 반박 검증에서 `actionable: false` 였다. C2·C6 은 `weak · low` 다.

**두어야 할 곳: 분석 스킬(`analyzing-open-source-pr-patterns`) 의 출력이다. 검증 스킬 쪽이 아니다.**

- 계약상 `PAT-*` 도출은 분석 스킬의 책임이다. 검증 스킬은 "공급된 패턴을 검증만 한다"(`SKILL.md` Boundaries). 검증 스킬에 변환기를 두면 이 경계가 깨진다
- 변환에 필요한 재료(PR 키 → `PR-*` 매핑, 레코드의 라이선스)는 분석 스킬의 입력인 corpus 에 있다
- `search_clues` 는 검증 스킬이 소비하는 방식에 맞춰 설계해야 하는데, 지금 분석 계약에는 그 규칙이 없다(§ 5.3). #183 에 넘길 입력이다
- 그래서 이번에는 코드로 두지 않았다. scratchpad 의 1회용 스크립트로만 옮겼다

## 3. 실행

| 항목 | 값 |
| --- | --- |
| 스킬 | 이 워크트리의 `dot_codex/skills/verifying-open-source-contribution-candidates` (main `ff976bc` 과 같다). 실행 전 오프라인 테스트 `Ran 62 tests OK` |
| analysis | 브리지 envelope. supplement 원본의 envelope·레코드 10건·`PAT-001` 을 그대로 두고 `PAT-002`(C1)를 더했다. 계약 검사 위반 0 |
| 대상 저장소 | `eslint/markdown` 1개. 조정자에게 선택을 물었지만 20분 동안 답이 없었다. 부작용 없는 읽기 전용 실행이라 질문에 적은 권고안으로 진행했다. 이유: 소스 corpus 4개 저장소 밖이다. fixable 규칙과 규칙 레지스트리·문서·테스트 묶음이 있어 두 패턴을 모두 적용할 수 있다 |
| 옵션 | `--request-budget 120`, `--allow-clone` 없음(clone 은 허용 네트워크 범위 밖), `--program-rules` 없음, 캡 기본값(5/20), 단서 상한 기본값 5 |
| discover | **exit 0, `complete`**, 조합 2개, 요청 **70/120**, 77초. 구성은 저장소 단계 24(저장소·head·community profile·PVR 4 + 정책 20) + 이슈 검색 36 + 코드 검색 9 + 재시도 1. 재시도는 31번째 이슈 검색이 분당 한도 30을 넘어 403 `X-RateLimit-Remaining: 0` 을 받은 것이고, `remaining-zero-and-reset` 으로 45초 대기 뒤 성공했다 |
| assessment | AI(이 워커)가 작성했다. 3건: `PAT-001` 1건, `PAT-002` 2건(locus 가 다르다) |
| record | **exit 0**, `CAN-001`~`CAN-003` |
| validate / render | exit 0 / exit 0 |
| 실험 1 | 손으로 읽은 조직 CONTRIBUTING 을 `policy_checks.contributing.found: true` 로 적은 변형으로 record 를 돌렸다. **exit 2** `policy_checks.contributing.sha256` 로 거부됐다(§ 5.2) |
| 실험 2 | 정책 항목을 모두 `found: null` 로 둔 채 readiness 12개를 `confirmed` 로 적고 `issue-ready` 로 record 를 돌렸다. **exit 0** 으로 기록됐다(§ 5.2). 실험 산출물은 지웠다 |

산출물(`discovery.json`, `assessment.json`, `candidates.json`, `manifest.json`, `report.md`, 변환·assessment 생성 스크립트)은 세션 scratchpad 에만 있다. `bridge-analysis.json` 은 로컬 전용 원본(`supplement-analysis.json`) 레코드를 담고 있어서 공개 저장소인 dotfiles 에 넣지 않았다.

### 예산 밖 요청

assessment 를 쓰려고 `gh api` 로 한 읽기는 **약 50회** 다. 규칙 소스 21개, 디렉터리 목록, 정책 파일, AI 정책 문서, 이슈·PR 본문, locus 별 중복 검색이 여기에 들어간다. 이 요청은 스킬의 요청 예산과 manifest 에 **잡히지 않는다.** 실제 사용량은 manifest 의 70회보다 많다.

## 4. 결과 — `CAN-*` 3건

| 후보 | 패턴 | locus | 상태 / 이유 | 핵심 근거 |
| --- | --- | --- | --- | --- |
| `CAN-001` | `PAT-001` 규칙 구현·등록·문서·테스트 묶음 | `src/rules` + `docs/rules` + `tests/rules` | `not-applicable` / `reproduction-failed` | head `4cc3873` 에서 규칙 21 · 문서 21 · 테스트 21 이 이름으로 모두 짝지어진다. 레지스트리(`src/build/rules.js`)와 README 목록은 빌드 생성이다(반대조건 해당). 관례 패턴이라 결함을 가리키지 않는다 |
| `CAN-002` | `PAT-002` 의미를 보존하지 못하는 fixer | `src/rules/no-bare-urls.js` www 자동 링크 fix | `duplicate` / `duplicate-open` | `` url === `http://${text}` `` 는 GFM `www.` 자동 링크를 잡는데 fix 결과 `<www.example.com>` 은 스킴이 없어 autolink 가 아니다(정적 추론, 실행 안 함). 이슈 [#710](https://github.com/eslint/markdown/issues/710)(bug·accepted·repro:yes) open, 수정 PR [#720](https://github.com/eslint/markdown/pull/720) open(CHANGES_REQUESTED) |
| `CAN-003` | `PAT-002` | `src/rules/no-reference-like-urls.js` title 있는 링크 fix | `not-applicable` / `already-fixed` | 원 PR [#433](https://github.com/eslint/markdown/pull/433#discussion_r2168971520) 리뷰에서 title 손실을 지적받고 "정보를 잃지 않고는 고칠 수 없으면 보고만 한다" 로 바꿨다. head 에 `if (title) return null` 이 있다 |

세 후보 모두 다음 값이 같다.

- `ai_policy_status: allowed-with-disclosure`, `disclosure_required: true`
- 12개 readiness 중 `policy_files_reviewed` 는 `not-confirmed` 다. 정책은 손으로 읽었지만 게이트가 인정하는 해시가 없다
- run outcome 은 `no-actionable-candidates` / `complete` 다

과제에서 확인하라고 한 세 가지에 대한 답은 다음과 같다.

| 확인 항목 | 결과 |
| --- | --- |
| CAN-* 가 나오는가 | 나온다. 조합 2개에서 locus 3개. 한 조합에 locus 를 여러 개 둘 수 있다 |
| 근거가 붙는가 | 붙는다. `evidence_links` 와 readiness `evidence_links` 가 head SHA 고정 blob URL, 이슈·PR·리뷰 코멘트를 가리킨다. `verified_at`·`verified_base_sha` 가 기록된다. 다만 근거는 전부 assessment 작성자가 스킬 밖에서 모은 것이고, 스킬의 discover 산출물에서 온 근거는 `PAT-001` 의 코드 검색 hit 뿐이다 |
| 정책 확인이 되는가 | **스킬로는 안 된다.** 발견 20경로 중 found 1(`eslint/markdown/.github/ISSUE_TEMPLATE`), absent 19. 실제로는 CONTRIBUTING(CLA 요구 포함)·SECURITY·CoC·PR 템플릿(AI acknowledgment 포함)이 조직 `.github` 에 있다. AI 정책은 [`eslint/eslint` docs/src/contribute/ai-policy.md](https://github.com/eslint/eslint/blob/a0d1a3772679d3d74bb860fc65b5b58678acd452/docs/src/contribute/ai-policy.md) 에 있다: AI 사용 공개 의무, AI 생성 PR 은 `accepted` 이슈에만. 손으로 확인했다 |

## 5. 막힌 곳과 틀린 곳

### 5.1 조직 `.github` 정책을 놓친다 — 계약 결함 (높음)

`discover_policy_files` 는 대상 저장소와 `{owner}/.github` 두 곳 모두에 `ref={대상 저장소 기본 브랜치}` 를 붙인다. 계약 `references/github-verification-contract.md` R3.2 가 그렇게 적혀 있어서 구현은 계약대로다.

- `eslint/markdown` 의 기본 브랜치는 `main`, `eslint/.github` 의 기본 브랜치는 `master` 다
- `GET /repos/eslint/.github/contents/CONTRIBUTING.md?ref=main` → 404 `No commit found for the ref main`. 스킬은 이 404 를 진짜 부재(`absent`)로 기록한다. `request-failed` 가 아니다
- 결과적으로 CONTRIBUTING·SECURITY·CODE_OF_CONDUCT 가 모두 absent 가 된다. 같은 run 의 community profile 응답은 `contributing: true`, `code_of_conduct: true`, `pull_request_template: true` 라고 답했는데 스킬은 이 불일치를 경고하지 않는다
- 게이트의 "`request-failed` 정책은 ready 를 막는다" 보호도 우회된다. 404 가 absent 로 분류되기 때문이다
- #79 라이브(`eslint-community/.github`, 기본 브랜치 `main`)에서는 브랜치가 우연히 같아 드러나지 않았다

같은 조회에서 확인된 빈틈이 하나 더 있다. 조직 `.github` 저장소는 **루트** `PULL_REQUEST_TEMPLATE.md` 를 쓰는데 조회 경로 10개에는 `.github/PULL_REQUEST_TEMPLATE.md` 만 있다. ESLint 의 PR 템플릿에는 AI acknowledgment 체크 항목이 있어서 정책 판단에 직접 쓰인다.

### 5.2 손으로 읽은 정책은 기록할 수 없고, 정책을 안 봐도 ready 가 된다 (높음)

AI 정책처럼 대상 저장소와 조직 `.github` 밖(다른 저장소의 docs, 웹사이트)에 있는 정책은 discover 가 원리적으로 찾지 못한다. 손으로 읽어도 기록할 곳이 없다. assessment 의 `policy_checks.<key>.found: true` 는 discovery 가 관측한 정책 해시와 일치해야 하기 때문이다. 이번 실험에서 exit 2 로 거부됐다. 그래서 `found: null` 과 서술형 `assessment` 로만 남겼고, `policy_files_reviewed` 는 `not-confirmed` 로 두었다.

반대 방향은 막히지 않는다. **게이트는 readiness `policy_files_reviewed` 와 `policy_checks.*.found` 를 서로 대조하지 않는다.** 로컬 실험에서 이번 discovery 를 그대로 쓰고, 정책 항목을 모두 `found: null`(CONTRIBUTING·CLA·AI 정책 미관측)로 둔 채 readiness 만 `confirmed` 로 적었다. 그러자 `issue-ready` 후보가 exit 0 으로 기록됐다. § 5.1 때문에 404 가 `absent` 로 분류되므로 "`request-failed` 정책은 ready 를 막는다" 보호도 걸리지 않는다.

정리하면 다음과 같다.

- 정책을 제대로 읽은 작성자는 그 사실을 기록할 수 없다
- 정책을 읽지 않은 작성자는 ready 를 적을 수 있다
- ESLint 의 경우 CLA 서명과 "AI 생성 PR 은 `accepted` 이슈에만" 규칙이 이 틈으로 빠진다

### 5.3 `search_clues` 하나로 두 가지 검색을 한다 (중간)

같은 단서가 이슈·PR 중복 검색과 코드 검색에 함께 쓰인다.

| 단서 | 이슈·PR 검색(4회 합) | 코드 검색 | 관찰 |
| --- | --- | --- | --- |
| `lib/all-rules.js` | 0 | 0 | 소스 저장소 전용 경로다 |
| `docs/rules` | 47 | 29 | 규칙 문서 링크라서 관련 없는 항목까지 넓게 걸린다 |
| `tests/lib/rules` | 2 | 0 | |
| `README 규칙 목록` | 0 | 0 | **한국어 단서.** 영어 저장소에서는 항상 0이다 |
| `unsafe autofix`·`autofix breaks`·`remove autofix` | 0·0·2 | 0·0·0 | 자연어 단서는 코드에 안 걸린다 |
| `fixer.replaceText` | 0 | 3 | 코드 토큰은 이슈에 안 걸린다. fixable 규칙 5개 중 3개만 잡았다(whitespace fixer 2개 누락) |
| `hasSuggestions` | 0 | 0 | |

- 큰따옴표가 금지라서 `fixable: "code"` 같은 가장 정확한 코드 단서를 쓸 수 없다
- 분석 계약에는 단서를 대상 저장소의 언어와 코드 토큰에 맞추라는 규칙이 없다. `PAT-001` 의 단서는 소스 저장소의 경로를 그대로 적었다

### 5.4 중복 검색은 locus 가 정해지기 전에 끝난다 (높음)

discover 의 중복 검색은 (패턴, 저장소) 조합 단위로 패턴 단서만 쓴다. `PAT-002` 조합의 20개 질의는 모두 성공해 `duplicate_search.complete: true` 였다. 그런데 locus 가 `no-bare-urls` 로 정해진 뒤의 실제 중복 #710·#720 은 찾지 못했다.

- `complete` 는 "질의가 모두 성공했다" 는 뜻이지 "관련 중복이 없다" 는 뜻이 아니다. 게이트는 `complete: true` 이면 `open_and_closed_searched: confirmed` 를 허용한다. assessment 작성자가 이 차이를 모르면 중복을 놓친 채 ready 로 갈 수 있다
- locus 별 재검색을 할 CLI 단계가 없다. 이번에는 손으로 `gh api search/issues` 를 돌렸고, 그 요청과 결과는 스킬 산출물에 남지 않는다. 링크만 assessment 에 적었다
- 후보는 locus 단위인데 `duplicate_search` 증거는 조합 단위다. `CAN-002` 와 `CAN-003` 이 같은 `duplicate_search` 를 가진다

### 5.5 Markdown 보고서가 후보가 무엇인지 보여 주지 않는다 (중간)

`render` 결과에는 상태·SHA·시각·근거 링크·blocking gap·미확인 readiness 는 있다. 하지만 다음 항목이 없다.

- `locus`·`summary`·`impact`·`pattern_ids`
- `ai_policy_status`·`policy_checks` 판정
- `duplicate_verdict`

대신 조합 단위 중복 검색 제목 49개가 "untrusted excerpt" 로 나열된다. `CAN-002` 절에는 #710·#720 이 아니라 관련 없는 PR 제목 2개가 나온다. nvim 에서 읽는 사람은 `CAN-002` 가 `no-bare-urls` 이야기라는 것을 근거 URL 로만 짐작할 수 있다. #82 의 "nvim용 Markdown 에 실제 검증 후보, 증거, 검증 SHA/시각, 남은 판단을 구분" 기준과 직접 관련된다.

### 5.6 잘 작동한 것

- 계약 검사: 브리지 envelope 의 형식 위반을 0으로 확인한 뒤에야 discover 가 돌았다. 틀린 assessment(§ 5.2 실험)는 exit 2 로 거부됐다
- 403 rate-limit 재시도: 이슈 검색 한도(분당 30회)에 걸린 뒤 `X-RateLimit-Reset` 까지 기다렸다가 성공했다. 재시도 이벤트에는 허용 헤더만 남았다
- 부분 결과 표현: 정책을 확인하지 못한 사실이 `not-confirmed` 와 `found: null` 로 드러났다. 다만 ready 로 올라가지 않은 것은 작성자의 선택이고 게이트가 강제한 것이 아니다(§ 5.2)
- 원격 텍스트는 모두 `untrusted: true` 객체로 저장됐다

## 6. 연결 지점 — 단계 사이에서 손으로 옮긴 것

```
수집(corpus.json · supplement-corpus.json)
  │  ① corpus 가 둘로 나뉘고 PR-* 번호가 corpus 마다 따로다
  ▼
분석(analysis.json: PAT 0 · supplement-analysis.json: PAT-001)
  │  ② 분석 스킬은 패턴을 1개만 냈다(#183)
  │  ③ #169 agy 추출·반박 검증이 C1~C7 을 냈지만 PAT 형식이 아니다
  ▼
[손] 브리지: C1 → PAT-002, PR 키 매핑, 라이선스, search_clues 설계, revision
  ▼
[손] 대상 저장소·예산·clone 허용 결정 (어느 산출물에도 없다)
  ▼
검증 discover (스킬, 70 요청)
  ▼
[손] locus 찾기: 대상 저장소 소스를 gh api 로 읽고 정적 추론 (~28 요청, 예산 밖)
[손] locus 별 중복 재검색 (~11 요청, 예산 밖)
[손] 정책 읽기: 조직 .github(master), eslint/eslint AI 정책 (~12 요청, 예산 밖)
[손/AI] assessment.json 작성: 3건 × readiness 12 · policy 8
  ▼
검증 record · validate · render (스킬)
```

| # | 경계 | 손으로 한 일 | 지금 이 일을 맡는 곳 | 맡아야 할 곳(제안) |
| --- | --- | --- | --- | --- |
| 1 | 수집 → 분석 | 두 corpus 를 하나의 다이제스트로 합치고 PR 키(`n#553`)를 붙였다(#169) | 없음(#169 스크립트) | #183 |
| 2 | 분석 → 검증 | agy 후보 → `PAT-*` 12필드. ID 매핑, 라이선스, 단서 설계, revision | 없음 | 분석 스킬(#183). 단서 규칙은 두 스킬 계약 모두에 |
| 3 | 분석 → 검증 | `records` 는 supplement 10건만 실었다. `analysis.json` 쪽 3건은 빠졌다 | 없음 | #183 corpus 분할·통합 |
| 4 | 사용자 → 검증 | 대상 저장소·예산·clone 허용 | 사용자(SKILL 1단계) | #82 통합 요청의 입력 |
| 5 | 검증 내부 | locus 확정, 정적 확인 | assessment 작성자(AI) | 그대로 AI 역할. 다만 쓴 요청과 읽은 파일을 manifest 에 남길 경로가 필요 |
| 6 | 검증 내부 | locus 별 중복 재검색 | 없음 | 검증 스킬 새 단계(§ 7 초안 B) |
| 7 | 검증 내부 | 조직·외부 정책 읽기 | 없음(스킬은 놓침) | 검증 스킬 정책 조회 수정(§ 7 초안 A) + 외부 정책 입력(초안 B) |
| 8 | 검증 → 사용자 | 후보가 무엇인지 설명 | 없음(render 에 locus 없음) | render 개선(§ 7 초안 C) |

## 7. 후속 이슈 초안

아래는 초안이다. 이슈는 만들지 않았다.

### 초안 A — fix(skills): 검증 스킬이 조직 `.github` 정책을 대상 저장소 브랜치로 조회해 놓친다

- 문제: § 5.1. `{owner}/.github` 조회에 대상 저장소의 `default_branch` 를 `ref` 로 준다. 브랜치가 다르면 404 가 나고 그것을 `absent` 로 기록한다. 루트 `PULL_REQUEST_TEMPLATE.md` 는 경로 목록에 없다
- 제안
  - `.github` 저장소 조회에서는 `ref` 를 빼서 그 저장소의 기본 브랜치를 쓴다. 요청 수는 늘지 않는다
  - 404 본문이 ref 부재(`No commit found for the ref`)이면 `request-failed` 로 분류한다
  - `.github` 저장소에는 루트 경로(`CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `PULL_REQUEST_TEMPLATE.md`)를 조회한다
  - community profile 이 파일이 있다고 답했는데 정책 결과가 전부 absent 이면 경고한다
  - ready 게이트가 readiness `policy_files_reviewed: confirmed` 와 `policy_checks.*.found` 를 대조하게 한다(§ 5.2 실험 2). 외부 정책을 인정할 경로(초안 B 의 `--policy-url`)와 함께 설계해야 ESLint 같은 저장소가 영구히 막히지 않는다
  - R3.2 계약과 fixture 테스트를 고친다
- 재현: `eslint/markdown` discover → 정책 20경로 중 found 1. `gh api 'repos/eslint/.github/contents/CONTRIBUTING.md?ref=main'` → 404
- 크기: 조회 수정은 작다. 요청 순서·예산 계약이 바뀌므로 계약 테스트 갱신이 필요하다. 게이트 대조는 초안 B 와 묶이면 중간이다

### 초안 B — feat(skills): 검증 스킬에 locus 확정 뒤의 근거 수집 단계를 둔다

- 문제: § 5.2·§ 5.4. locus 별 중복 재검색과 저장소 밖 정책 문서가 스킬 산출물에 들어갈 길이 없다. 예산 밖 요청 약 50회가 manifest 에 남지 않는다
- 제안(택일 또는 조합)
  - `research` 서브커맨드: `--candidate-locus <pattern>:<repo>:<locus> --clue ...` 로 locus 전용 중복 검색을 하고 discovery 에 덧붙인다(요청 예산·manifest 포함)
  - `--policy-url`: 사용자가 지정한 외부 정책 문서(예: 다른 저장소의 docs 경로)를 스크립트가 GET 하고 해시를 남긴다. 그러면 assessment 가 `found: true` 로 인용할 수 있다
  - 게이트: `open_and_closed_searched: confirmed` 에 locus 전용 검색 근거를 요구할지 결정한다
- 크기: 중간. 계약(필드·스냅숏·recheck 가변 필드)을 건드린다. quality-goal 흐름으로 설계부터 하는 편이 맞다

### 초안 C — feat(skills): 검증 보고서 Markdown 에 후보 내용과 정책·중복 판정을 싣는다

- 문제: § 5.5. nvim 보고서에서 후보가 무엇인지(locus·summary), 정책 판정, 중복 판정이 보이지 않는다. 관련 없는 중복 검색 제목이 가장 많은 분량을 차지한다
- 제안: 후보 절에 `pattern_ids`·`locus`·`summary`·`impact`·`ai_policy_status`/`disclosure_required`·`duplicate_verdict` 를 넣는다. untrusted excerpt 는 개수만 적고 본문은 접거나 `duplicate_verdict.matched_items` 에 든 것만 보인다
- #82 기준 "nvim용 Markdown" 에 속한다. #82 안에서 처리해도 된다

### #183 에 넘길 입력 (새 이슈 아님)

- `PAT-*` 는 검증 스킬의 입력 계약(§ 1)을 만족해야 하고, 그중 `search_clues` 가 검증 품질을 결정한다
- 단서 규칙 제안
  - 대상 저장소의 언어(대개 영어)와 코드 토큰으로 쓴다
  - 소스 저장소 전용 경로를 피한다
  - 큰따옴표를 쓰지 않는다
  - 이슈 검색용과 코드 검색용을 구분한다. 계약을 나눌지(`issue_clues`·`code_clues`)는 두 스킬 공동 결정이다
- agy 후보(C1)를 `PAT` 로 올릴 때 필요한 매핑은 § 2 표다. PR 키 → corpus 로컬 `PR-*` 매핑은 corpus 가 나뉘어 있으면 표현할 수 없다

## 8. 한계

- 대상 저장소 1개, 패턴 2개, 1회 실행이다. 음성·양성의 독립 사례가 충분하다고 주장하지 않는다. 다만 `CAN-002`(근거에 연결된 중복)와 `CAN-001`(빈틈 없음)은 locus 와 근거가 서로 다른 독립 판정이다
- `CAN-002` 의 결함은 정적 추론이다. 코드를 실행하지 않았다. 이슈 #710 의 재현 보고와 메인테이너의 `repro:yes` 라벨이 결함을 뒷받침한다
- fixable 규칙 5개 중 whitespace fixer 2개(`no-missing-atx-heading-space`, `no-space-in-emphasis`)와 `no-reversed-media-syntax` 는 assessment 하지 않았다
- `recheck` 는 돌리지 않았다. ready 후보가 없어서 계약상 필요하지 않다
- 대상 저장소는 조정자 답을 받지 못한 채 워커가 골랐다(§ 3)
