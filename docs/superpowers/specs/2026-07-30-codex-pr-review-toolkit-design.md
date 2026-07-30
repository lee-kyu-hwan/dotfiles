# Codex PR Review Toolkit 설계

## 목표

Claude Code의 공식 `pr-review-toolkit`을 Codex에서도 같은 리뷰 흐름으로 사용할 수
있게 한다. Codex에서는 종합 리뷰 스킬이 변경 범위를 파악하고, 적용 가능한 전문
리뷰어를 병렬 또는 순차 실행한 뒤 결과를 우선순위별로 합친다.

Claude 원본 리뷰 지침은 복사하지 않고 심링크를 통해 참조한다. 따라서 Claude 공식
마켓플레이스가 갱신되면 Codex도 다음 실행부터 같은 지침을 읽는다.

## 범위와 배포 방식

다음 7개 Codex 전용 개인 스킬을 기존 `dot_codex/skills` 경로로 배포한다.

- 종합 리뷰: `pr-review-toolkit`
- 전문 리뷰:
  - `pr-review-toolkit-comment-analyzer`
  - `pr-review-toolkit-pr-test-analyzer`
  - `pr-review-toolkit-silent-failure-hunter`
  - `pr-review-toolkit-type-design-analyzer`
  - `pr-review-toolkit-code-reviewer`
  - `pr-review-toolkit-code-simplifier`

`~/.codex/skills`는 Codex가 직접 읽고, 이 저장소도 `codex-import-claude-session`과
`github-work-log`를 같은 방식으로 배포한다. 래퍼는 Codex의 스킬 호출과 하위
에이전트 실행 규칙을 사용하므로 공용 `dot_agents/skills`가 아니라 Codex 전용
경로에 둔다.

MCP 서버, 훅, 앱, 별도 실행 파일이 필요하지 않으므로 Codex 플러그인과 개인
마켓플레이스는 만들지 않는다. 이 선택으로 다음을 피한다.

- `codex plugin marketplace add`와 `codex plugin add` 상태 관리
- `~/.codex/config.toml`의 marketplace/plugin 등록 드리프트
- 설치된 플러그인 캐시와 source 사이의 버전·재설치 문제
- 개인 마켓플레이스 전용 루트와 `~/plugins` 최상위 디렉터리

다음은 범위에서 제외한다.

- Claude 플러그인 원본 수정
- Claude 전용 `/pr-review-toolkit:review-pr` 문법을 Codex에 추가
- Claude의 `model`, `color`, `allowed-tools` 같은 전용 메타데이터 재현
- `README.md`나 `CLAUDE.md`에 개별 스킬 목록 추가

Codex에서는 `$pr-review-toolkit` 또는 자연어 요청으로 종합 리뷰를 호출한다.

## 저장 구조

chezmoi source에는 다음 구조를 둔다.

```text
dot_codex/
├── skills/
│   ├── pr-review-toolkit/
│   │   └── SKILL.md
│   ├── pr-review-toolkit-comment-analyzer/
│   │   └── SKILL.md
│   ├── pr-review-toolkit-pr-test-analyzer/
│   │   └── SKILL.md
│   ├── pr-review-toolkit-silent-failure-hunter/
│   │   └── SKILL.md
│   ├── pr-review-toolkit-type-design-analyzer/
│   │   └── SKILL.md
│   ├── pr-review-toolkit-code-reviewer/
│   │   └── SKILL.md
│   └── pr-review-toolkit-code-simplifier/
│       └── SKILL.md
└── symlink_pr-review-toolkit-claude.tmpl
```

`dot_codex/symlink_pr-review-toolkit-claude.tmpl`은 chezmoi의 `symlink_` 속성과 `.tmpl`
처리를 함께 사용한다. 배포 결과는 다음과 같다.

```text
~/.codex/pr-review-toolkit-claude
  -> ~/.claude/plugins/marketplaces/claude-plugins-official/plugins/pr-review-toolkit
```

템플릿 본문은 `{{ .chezmoi.homeDir }}`를 사용해 홈 디렉터리가 다른 macOS 머신에서도
동작하게 한다. 링크는 특정 캐시 버전이나 `.gcs-sha`가 아니라
`claude-plugins-official/plugins/pr-review-toolkit`이라는 안정적인 경로를
가리킨다. Claude가 마켓플레이스 디렉터리를 통째로 교체해도 같은 경로가 다시
생성되면 링크가 유효해진다.

## 머신 분기

Claude 플러그인 원본을 보장하지 않는 `server` 머신에는 7개 Codex 스킬과 심링크를
배포하지 않는다. `.chezmoiignore`에는 기존 macOS 전용 제외 블록과 분리된 server
조건 블록을 추가한다.

```text
{{ if eq .machine_type "server" }}
# server: Claude Code 공식 플러그인 의존 항목 제외
.codex/skills/pr-review-toolkit
.codex/skills/pr-review-toolkit-*
.codex/pr-review-toolkit-claude
{{ end }}
```

macOS work/personal 머신에서는 Claude 원본이 없거나 링크가 깨졌을 때 임의의 내장
프롬프트로 대체하지 않고 설치 복구 방법을 안내한다.

## Codex 호환 계층

Claude 원본은 Codex 스킬 배치 규약인 `skills/<name>/SKILL.md` 구조가 아니다.
`commands/review-pr.md`에는 필수 `name` frontmatter도 없으며, `agents/*.md`에는
Claude 전용 `model`과 `color`가 들어 있다. 따라서 원본 Markdown을 `SKILL.md`로
직접 연결하지 않고, 각 Codex 스킬을 얇은 호환 계층으로 둔다.

각 Codex 스킬은 다음 순서로 대응하는 원본을 사용한다.

1. 고정 경로 `~/.codex/pr-review-toolkit-claude` 아래의 대응 파일이 존재하는지
   확인한다.
2. 파일 전체를 읽되 Claude 전용 frontmatter는 실행 설정으로 해석하지 않는다.
3. Markdown 본문의 역할, 판단 기준, 점수 기준, 출력 형식을 따른다.
4. 원본의 `CLAUDE.md` 언급은 현재 프로젝트의 실제 지침 파일로 치환한다.
   `AGENTS.md`를 우선하고, 없으면 `CLAUDE.md` 등 실제로 존재하는 지침을 사용한다.
5. Codex 도구 이름과 하위 에이전트 호출 방식으로 실행한다.

호출 시 upstream root를 바꾸는 옵션은 제공하지 않는다. 전문 리뷰 기준의 단일
원본은 항상 고정된 Claude 공식 플러그인 경로다.

## 종합 리뷰 흐름

`pr-review-toolkit` 스킬은 Claude의 `commands/review-pr.md`를 읽은 뒤 다음 순서로
실행한다.

1. 사용자 요청에서 `comments`, `tests`, `errors`, `types`, `code`, `simplify`,
   `all`, `parallel`을 해석한다. 기본값은 `all`이다.
2. `git status`, `git diff`, 필요하면 `gh pr view`로 리뷰 범위를 결정한다.
3. 변경 내용에 따라 적용 가능한 리뷰를 고른다.
   - `code-reviewer`는 항상 적용한다.
   - 테스트 변경에는 `pr-test-analyzer`를 적용한다.
   - 주석이나 문서 변경에는 `comment-analyzer`를 적용한다.
   - 오류 처리 변경에는 `silent-failure-hunter`를 적용한다.
   - 타입 변경에는 `type-design-analyzer`를 적용한다.
4. analysis-only reviewer 실행 직전에 read-only Git 명령으로 raw `HEAD`와
   status, unstaged/staged binary diff, untracked path/content stream의 exact
   SHA-256 fingerprint를 출력한다. complete diff stdout은 review context에
   보존하지 않는다. 대신 unstaged/staged/untracked 변경을 NUL-safe Git path
   enumeration으로 읽어 status와 safely escaped path를 기록한다. 모든
   unstaged/staged tracked record에는 raw diff의 old/new Git mode를 포함한다.
   staged record는 staged object ID도 포함한다. unstaged worktree signature는
   regular file content SHA-256, newline을 추가하지 않은 exact symlink target
   digest, checked-out gitlink worktree OID 중 해당 값을 사용하고, gitlink가
   없거나 읽을 수 없으면 absent/unavailable marker를 남긴다. 나머지 상태에는
   deletion/other file-type marker를 사용한다. 이 필드만 담은 bounded path-level
   manifest는 Git이 보고한 path마다 metadata record 하나로 제한하고 diff hunk나
   파일 본문을 포함하지 않는다. fingerprint와 manifest의 before 결과를 review
   context에 label과 함께 보존한다. NUL stream은 변수나 파일에 저장하지 않고
   pipeline에서 바로 처리하며 filesystem object를 만들거나 수정하지 않는다.
5. `parallel` 요청이 있으면 독립적인 analysis-only reviewer만 하위 에이전트로 동시
   실행하고, 그렇지 않으면 순차 실행한다.
6. analysis-only reviewer 결과를 `Critical`, `Important`, `Suggestions`,
   `Strengths`로 중복 제거해 합친다. 모든 지적에는 가능한 경우 파일과 줄 번호를
   포함한다.
7. aggregate가 끝나면 같은 command set의 after fingerprint와 bounded manifest를
   review context에 보존한다. HEAD와 fingerprint를 먼저 비교하고, 불일치면
   before/after path-level manifest를 대조하여 변경 경로와 변경 종류를 보고한다.
   변경을 되돌리지 않고 mutation을 시작하지 않는다.
8. `code-simplifier`는 `simplify`가 명시됐고 사용자가 코드 수정을 요청한 경우에만,
   성공한 baseline 비교 뒤 별도 순차 mutation 단계에서 실행한다. 기본 `all`과 일반
   리뷰는 `code-simplifier`를 제외하고 읽기 전용으로 동작하며, simplifier는 어떤
   reviewer와도 병렬 실행하지 않는다.

전문 리뷰어는 동일한 diff 범위와 프로젝트 지침을 전달받는다.

## 병렬 실행과 실패 처리

- 서로 독립적인 analysis-only 전문 리뷰는 Codex 하위 에이전트로 병렬 실행할 수 있다.
- 사용할 수 있는 동시 실행 슬롯보다 리뷰어가 많으면 나머지는 다음 배치로 실행한다.
- `code-simplifier`는 parallel 요청에서도 dispatch 대상이 아니며, analysis-only
  reviewers의 완료·집계·baseline 보존 확인 뒤에만 단독 순차 mutation 단계로 실행한다.
- 한 리뷰어가 실패해도 완료된 결과는 보존하고, 실패한 리뷰 종류와 원인을 최종
  요약에 표시한다.
- Claude 원본 링크가 없거나 깨졌으면 임의의 내장 프롬프트로 대체하지 않는다.
- 7개 스킬은 동일한 복구 메시지를 사용한다.
- PR이 없으면 로컬 diff를 리뷰하며, `gh pr view` 실패 자체를 리뷰 실패로 취급하지
  않는다.

## 원본과 래퍼의 일치 규칙

현재 Claude 원본은 `commands/review-pr.md` 하나와 `agents/*.md` 여섯 개다. 검증 시
다음을 비교한다.

- 원본 command가 `review-pr.md` 하나인지 확인한다.
- 원본 agent 이름 집합이 여섯 전문 리뷰 스킬의 suffix 집합과 일치하는지 확인한다.
- 원본에 agent가 추가되거나 삭제되어 집합이 달라지면 조용히 무시하지 않고 검증을
  실패시킨다.
- 복구 메시지가 7개 `SKILL.md`에 정확히 한 번씩 존재하는지 확인한다.

## 안전한 배포

각 계획 Step은 독립 셸에서 실행된다고 가정한다. 이전 Step에서 선언한 셸 변수나
배열을 다음 Step에서 사용하지 않는다.

Task 5의 outer smoke harness는 inner Codex 밖에서 Git invariance를 독립 검증하므로
전용 temporary directory를 사용할 수 있다. 이는
`codex exec --sandbox read-only` 내부 orchestrator의 baseline 계약이 아니며,
inner skill은 review-context command output만 사용한다.

배포 미리보기와 적용 명령에는 심링크 하나와 스킬 디렉터리 7개의 절대 경로를
리터럴로 모두 적는다. 타깃이 비어 있는 `chezmoi diff`나 `chezmoi apply`는 절대
실행하지 않는다. 새 머신에서 부모 디렉터리를 만들 수 있도록 적용 명령에는
`--parent-dirs`를 사용한다.

## 검증 기준

- 7개 `SKILL.md`가 `quick_validate.py`를 통과한다.
- 배포된 `~/.codex/pr-review-toolkit-claude`가 Claude 공식 마켓플레이스의
  `pr-review-toolkit`을 가리킨다.
- Claude 원본 command/agent 파일 집합과 7개 래퍼의 대응 관계가 정확하다.
- 배포된 7개 경로와 각 `name` frontmatter가 정확하다.
- 새 Codex 프로세스의 스킬 발견 확인은 참고용 스모크 테스트로 분리한다.
- 종합 리뷰가 기본 `all`, 선택 리뷰, `parallel` 요청을 구분한다.
- 종합 리뷰가 최소 두 전문 리뷰어 결과를 하나의 우선순위 보고서로 합친다.
- 복구 메시지와 임의 프롬프트 대체 금지 규칙을 정적으로 검증한다.
- analysis-only 리뷰 전후의 raw `HEAD`와 status, unstaged/staged binary diff,
  untracked path/content stream의 exact fingerprint를 review context에 보존한다.
  complete diff stdout은 보존하지 않고, safely escaped status/path와 staged object
  ID, raw old/new Git mode, regular content SHA-256, exact symlink target digest,
  gitlink worktree OID 또는 absent/unavailable/deletion/other type marker만 가진
  bounded path-level manifest를 함께 보존한다. fingerprint가 다르면 before/after
  manifest로 변경 경로와 종류를 보고한다. NUL 데이터는 변수나 파일에 저장하지
  않고 pipeline에서 처리하며, inner baseline workflow는 filesystem write를
  수행하지 않는다.
- `simplify`를 명시하고 수정 권한을 준 실행에서만 `code-simplifier`가 변경할 수
  있으며, 이 mutation은 성공한 baseline 비교 뒤에만 순차 실행한다.

## 롤백

구현 직후 롤백할 때는 배포된 8개 타깃을 먼저 전용 백업 디렉터리로 이동해 Codex의
발견 경로에서 제거한다. 그다음 구현 커밋 3개를 최신순으로 revert해 chezmoi source와
server 제외 규칙을 되돌린다. 백업은 즉시 복구할 수 있도록 삭제하지 않는다.
