# Spec 라운드 1 실행 전사 — 오케스트레이터 독립 검증

리뷰어는 명령을 실행할 수 없다. 아래는 오케스트레이터가 직접 실행한 명령과 그 출력이다.
모든 실행은 스크래치 공유 클론 또는 이 워크트리에서 이루어졌고, `$HOME` 의 배포본과
실제 GitHub 는 건드리지 않았다.

- 대상 Spec: `/Users/lee-kyu-hwan/code/dotfiles__worktrees/107-feat-dual-review-shared-entrypoint/docs/development/2026-09-17-107-dual-review-shared-entrypoint/spec.md`
- Spec SHA-256: `26d4f15bb3fd0405f454e5c92969504e3812c604d97723b69f5f993cc7727f87`
- 프로젝트 루트: `/Users/lee-kyu-hwan/code/dotfiles__worktrees/107-feat-dual-review-shared-entrypoint`
- base revision: `3c68f33ee687e900a6349731f1e4a38a124e326c`
- mode: strict

---

## V1. baseline — 기존 스위트는 그린이다

```
$ cd dot_claude/skills/dual-review && python3 -m unittest discover -s tests
{"run_dir": "/tmp/run", "termination_reason": "single_reviewer"}
{"run_dir": "/tmp/run", "termination_reason": "pipeline_failure"}
{"run_dir": "/tmp/run", "termination_reason": "no_changes"}
{"run_dir": "/tmp/run", "termination_reason": "requested_round_limit"}
```

skip 1 건은 `test_live_api.ProductionSchemaLiveTests.test_production_structured_output_schemas`
로 `DUAL_REVIEW_LIVE_API=1` 환경변수 게이트다.

## V2. 스킬 트리 밖에서 dual-review 를 참조하는 테스트는 없다

```
$ grep -rln 'dual-review\|dual_review' . --exclude-dir=.git | grep -v '^./dot_claude/skills/dual-review/' | grep -v '^./docs/'
.chezmoiignore
.git
docs/development/2026-09-11-105-fix-dual-review-runtime-2/report.md
docs/development/2026-09-11-105-fix-dual-review-runtime-2/spec.md
docs/development/2026-09-04-dual-model-review-skill/report.md
docs/development/2026-09-11-105-fix-dual-review-runtime-2/plan.md
docs/development/2026-09-04-dual-model-review-skill/spec.md
docs/development/2026-09-04-dual-model-review-skill/plan.md
docs/development/2026-09-17-107-dual-review-shared-entrypoint/spec.md
docs/development/2026-08-28-dual-model-review-skill-2/report.md
docs/development/2026-08-28-dual-model-review-skill-2/plan.md
docs/development/2026-09-07-42-dual-review-stage1/report.md
docs/development/2026-09-07-42-dual-review-stage1/verification-r6.md
docs/development/2026-09-07-42-dual-review-stage1/plan.md
docs/development/2026-08-28-dual-model-review-skill-2/spec.md
docs/development/2026-09-07-42-dual-review-stage1/spec.md
docs/development/2026-09-07-42-dual-review-stage1/command-transcript-r3.txt
docs/development/2026-09-07-42-dual-review-stage1/spec-revision-notes.md
docs/development/2026-09-07-42-dual-review-stage1/verification-r10.md
docs/development/2026-09-07-42-dual-review-stage1/verification-r8.md
docs/development/2026-08-28-dual-model-review-skill/report.md
docs/development/2026-08-28-dual-model-review-skill/spec.md
docs/development/2026-09-04-dual-model-review-skill-2/report.md
docs/development/2026-09-04-dual-model-review-skill-2/plan.md
docs/development/2026-09-04-dual-model-review-skill-2/spec.md
docs/development/2026-09-16-111-profile-onboarding/baseline-verification.md
docs/development/2026-09-11-105-fix-dual-review-runtime/report.md
docs/development/2026-09-11-105-fix-dual-review-runtime/spec.md
dot_claude/skills/dual-review/references/operation.md
dot_claude/skills/dual-review/tests/test_live_api.py
dot_claude/skills/dual-review/tests/test_contracts.py
dot_claude/skills/dual-review/tests/test_execution.py
dot_claude/skills/dual-review/tests/live_e2e.py
dot_claude/skills/dual-review/scripts/review_state.py
dot_claude/skills/dual-review/SKILL.md
dot_claude/skills/dual-review/tests/test_synthesis.py
dot_claude/skills/dual-review/tests/test_rounds.py
```

`.chezmoiignore` 한 줄뿐이다. 따라서 회귀 신호는 전부 스킬 트리 안의 122 개에 있다.

## V3. producer 수 — Spec 의 "여섯" 주장 대조

```
$ python3 -c "import sys; sys.path.insert(0,'scripts'); import review_state as r; print(len(r.CLAUDE_PRODUCERS)); [print(' -',p) for p in r.CLAUDE_PRODUCERS]"
5
 - pr-review-toolkit:code-reviewer
 - pr-test-analyzer
 - comment-analyzer
 - silent-failure-hunter
 - type-design-analyzer
```

저장소 용어 대조:

```
$ grep -n 'five\|six' SKILL.md references/operation.md
SKILL.md:15:five Claude producers and the read-only Codex process before reading any result,
SKILL.md:19:Use these five Claude finding producers only: `pr-review-toolkit:code-reviewer`,
references/operation.md:7:starts all five Claude producer processes and the Codex process before reading any
references/operation.md:8:response. Claude uses only the five finding-producing review
references/operation.md:68:Anonymous-view masking removes the five Claude producer names and original finding
```

즉 코드의 `CLAUDE_PRODUCERS` 는 **5 개**이고, 저장소 문서는 일관되게
"five Claude producer processes **and** the Codex process" 로 쓴다.
`review_state.py:149` 의 `get_source` 도 `codex` 를 producer 집합과 분리해 취급한다.
Spec 의 R2.2·AC-10 이 쓴 "여섯 producer" 가 이 용어와 일치하는지는 리뷰어가 판정할 사항이다.

## V4. 경로 해석 지점 — parents[1] 의 실제 사용 위치

```
$ grep -n 'parents\[1\]' scripts/review_state.py
76:    schema = Path(__file__).resolve().parents[1] / "schemas" / schema_name
89:        schema = (Path(__file__).resolve().parents[1] / "schemas" / schema_name).read_text(encoding="utf-8")
524:    template = (Path(__file__).resolve().parents[1] / "templates" / "report.md").read_text(encoding="utf-8")
```

## V5. 목표 배치는 기존 스위트에 무신호다 (probe A)

스크래치 공유 클론에서 payload 를 `dot_claude` 밖으로 옮기고 얇은 진입점을 둔 뒤 재실행:

```
# probe A: payload 를 dot_codex/skills/dual-review 로 이동, dot_claude 는 얇은 SKILL.md + symlink_*.tmpl
# base 3c68f33
test_arguments (test_contracts.PackagingContractTests.test_arguments) ... ok
Ran 122 tests in 1.652s
OK (skipped=1)
```

공허해진 단언 5 곳의 실측 출력:

```
# probe A 상태에서 계약 단언이 공허해졌는지 실측 (SKILL_ROOT 는 테스트와 동일한 식으로 계산)
# base 3c68f33, payload = dot_codex/skills/dual-review
SKILL_ROOT = /private/tmp/claude-501/-Users-lee-kyu-hwan-code-dotfiles--worktrees-42-feat-dual-model-review-skill/ee01a496-e529-42c1-beb4-debfe19c52ca/scratchpad/107-measure/dot_codex/skills/dual-review

[1] .chezmoiignore 단언 블록 (test_contracts.py:167-170)
    조건: 'dot_claude' in SKILL_ROOT.parts -> False
    결과: 조건 False 이므로 블록 전체가 건너뛰어진다. 실패가 아니라 침묵.

[2] chezmoi 접두사/.tmpl 금지 단언 (test_contracts.py:176-185)
    repo root = /private/tmp/claude-501/-Users-lee-kyu-hwan-code-dotfiles--worktrees-42-feat-dual-model-review-skill/ee01a496-e529-42c1-beb4-debfe19c52ca/scratchpad/107-measure
    얇은 진입점 트리 존재: True
    그 안의 파일: ['SKILL.md', 'symlink_references.tmpl', 'symlink_schemas.tmpl', 'symlink_scripts.tmpl', 'symlink_templates.tmpl']
    순회 대상은 SKILL_ROOT.rglob('*') 뿐 -> 위 파일들은 한 번도 검사되지 않는다.

[3] managed_target (test_contracts.py:15-19, 호출부 203-206)
    호출부는 리터럴 'dot_claude/skills/dual-review/SKILL.md' 를 넘긴다 -> 이동을 감지할 수 없다.
    실제 원본 경로로 호출하면 ValueError: skill source required

[4] Codex 배포 대상을 단언하는 테스트
    grep 'codex/skills/dual-review' tests/ -> (없음)

[5] operation.md 문자열 단언 (test_contracts.py:256)
    'dot_claude/skills/dual-review/SKILL.md' 가 문서에 남아 있는가: True
    -> 원본이 옮겨졌는데도 문서의 낡은 경로 주장이 단언을 통과시킨다.
```

## V6. 현재 계약 테스트가 이 작업을 물리적으로 막는다 (probe B)

`dot_claude/skills/dual-review/scripts/symlink_review_state.py.tmpl` 한 개만 추가:

```
FAIL: test_packaging_contract (test_contracts.PackagingContractTests.test_packaging_contract)
Ran 122 tests in 1.647s
FAILED (failures=1, skipped=1)

FAIL: test_packaging_contract (test_contracts.PackagingContractTests.test_packaging_contract)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/claude-501/-Users-lee-kyu-hwan-code-dotfiles--worktrees-42-feat-dual-model-review-skill/ee01a496-e529-42c1-beb4-debfe19c52ca/scratchpad/107-measure/dot_claude/skills/dual-review/tests/test_contracts.py", line 183, in test_packaging_contract
    self.assertFalse(component.endswith(".tmpl"), relative)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: True is not false : scripts/symlink_review_state.py.tmpl
```

이 메서드는 단일 거대 테스트라 첫 위반 단언에서 멈춘다. 같은 루프의 `symlink_` 접두사
금지(`test_contracts.py:185`)는 평가되지 않았다.

## V7. chezmoi 는 디렉터리 단위 심링크를 지원하고, __pycache__ 가 새 경로로 샌다

```
## 1. 디렉터리 단위 symlink 가 성립하는가 -> 성립한다
$ chezmoi -S $S -D $DEST managed | grep dual-review
.claude/skills/dual-review
.claude/skills/dual-review/SKILL.md
.claude/skills/dual-review/references
.claude/skills/dual-review/schemas
.claude/skills/dual-review/scripts
.claude/skills/dual-review/templates
.codex/skills/dual-review
.codex/skills/dual-review/SKILL.md
.codex/skills/dual-review/references
.codex/skills/dual-review/references/operation.md
.codex/skills/dual-review/references/verification.md
.codex/skills/dual-review/schemas
.codex/skills/dual-review/schemas/critique.schema.json
.codex/skills/dual-review/schemas/reviewer.schema.json
.codex/skills/dual-review/schemas/synthesis.schema.json
.codex/skills/dual-review/scripts
.codex/skills/dual-review/scripts/__pycache__
.codex/skills/dual-review/scripts/__pycache__/review_state.cpython-314.pyc
.codex/skills/dual-review/scripts/review_state.py
.codex/skills/dual-review/templates
.codex/skills/dual-review/templates/report.md
.codex/skills/dual-review/tests
.codex/skills/dual-review/tests/__pycache__
.codex/skills/dual-review/tests/__pycache__/test_contracts.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__/test_critique.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__/test_execution.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__/test_live_api.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__/test_normalization.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__/test_reporting.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__/test_rounds.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__/test_synthesis.cpython-314.pyc
.codex/skills/dual-review/tests/live_e2e.py
.codex/skills/dual-review/tests/test_contracts.py
.codex/skills/dual-review/tests/test_critique.py
.codex/skills/dual-review/tests/test_execution.py
.codex/skills/dual-review/tests/test_live_api.py
.codex/skills/dual-review/tests/test_normalization.py
.codex/skills/dual-review/tests/test_reporting.py
.codex/skills/dual-review/tests/test_rounds.py
.codex/skills/dual-review/tests/test_synthesis.py

얇은 진입점 쪽 .claude/skills/dual-review 아래 references/schemas/scripts/templates 가
각각 '항목 1건'으로만 관리된다 (하위 파일이 나열되지 않는다) -> 디렉터리 심링크로 해석됐다.
반면 .codex/skills/dual-review 쪽은 하위 파일이 전부 나열된다 -> 실디렉터리(단일 원본).

## 2. 그러나 __pycache__ 가 새 경로로 새어 나간다
$ grep -n 'dual-review' $S/.chezmoiignore
13:.claude/skills/dual-review/**/__pycache__
-> .claude 경로만 제외한다. .codex 경로는 제외 규칙이 없다.
$ chezmoi managed | grep __pycache__
.codex/skills/dual-review/scripts/__pycache__
.codex/skills/dual-review/scripts/__pycache__/review_state.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__
.codex/skills/dual-review/tests/__pycache__/test_contracts.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__/test_critique.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__/test_execution.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__/test_live_api.cpython-314.pyc
.codex/skills/dual-review/tests/__pycache__/test_normalization.cpython-314.pyc
```

## V8. 디렉터리 심링크를 지나도 parents[1] 이 공용 원본을 가리킨다

```
심링크 경유 __file__      : /private/tmp/claude-501/-Users-lee-kyu-hwan-code-dotfiles--worktrees-42-feat-dual-model-review-skill/ee01a496-e529-42c1-beb4-debfe19c52ca/scratchpad/107-symlink-probe/claude/dual-review/scripts/review_state.py
  .resolve()             : /private/tmp/claude-501/-Users-lee-kyu-hwan-code-dotfiles--worktrees-42-feat-dual-model-review-skill/ee01a496-e529-42c1-beb4-debfe19c52ca/scratchpad/107-symlink-probe/shared/dual-review/scripts/review_state.py
  .resolve().parents[1]  : /private/tmp/claude-501/-Users-lee-kyu-hwan-code-dotfiles--worktrees-42-feat-dual-model-review-skill/ee01a496-e529-42c1-beb4-debfe19c52ca/scratchpad/107-symlink-probe/shared/dual-review
  schemas/reviewer.schema.json       존재: True
  templates/report.md                존재: True

판정: parents[1] 이 공용 원본 디렉터리로 해석되므로 schemas/templates 를 정상적으로 찾는다.

# 실제 실행으로도 확인 — 심링크 경유 스크립트를 import 해 렌더 헬퍼가 템플릿을 읽는지 본다
템플릿 읽기 성공, 길이: 193 바이트
첫 줄: # Dual review report
```

따라서 "payload 디렉터리를 통째로 심링크한다"(Spec R1.3, D3)는 성립하고,
"스크립트 파일 하나만 심링크한다"는 배치는 깨진다.

## V9. 저장소 관례 — 공용 스킬 원본 위치

```
$ grep -n 'dot_agents' CLAUDE.md
44:- `dot_agents/skills/` → `~/.agents/skills/` — 에이전트 공용 스킬 (Claude Code 외 도구도 읽음)

$ find dot_agents/skills -type f | sort
dot_agents/skills/create-worktree/agents/openai.yaml
dot_agents/skills/create-worktree/SKILL.md
dot_agents/skills/deep-research/SKILL.md
dot_agents/skills/move-window-to-session/SKILL.md
dot_agents/skills/remove-worktree/agents/openai.yaml
dot_agents/skills/remove-worktree/SKILL.md

$ ls -1 dot_codex/skills/ | head -20
analyzing-open-source-pr-patterns
codex-import-claude-session
collecting-recent-closed-prs
deep-research
github-work-log
pr-review-toolkit
pr-review-toolkit-code-reviewer
pr-review-toolkit-code-simplifier
pr-review-toolkit-comment-analyzer
pr-review-toolkit-pr-test-analyzer
pr-review-toolkit-silent-failure-hunter
pr-review-toolkit-type-design-analyzer
verifying-open-source-contribution-candidates
```

github-work-log 선례 — 본체는 하나, Claude 쪽은 chezmoi 심링크 템플릿:

```
$ cat dot_claude/skills/github-work-log/scripts/symlink_collect-github-activity.sh.tmpl
{{ .chezmoi.homeDir }}/.codex/skills/github-work-log/scripts/collect-github-activity.sh

$ ls -la ~/.claude/skills/github-work-log/scripts/
lrwxr-xr-x@ - lee-kyu-hwan  6 Jul 10:24 collect-github-activity.sh -> /Users/lee-kyu-hwan/.codex/skills/github-work-log/scripts/collect-github-activity.sh
```

단 `github-work-log` 의 `SKILL.md` 자체는 두 트리에 복제되어 있고 본문이 서로 다르다.

## V10. Codex 발견 루트는 저장소 설정만으로 확정되지 않는다

```
$ ls -1 ~/.agents/skills/
create-worktree
deep-research
github-work-log
move-window-to-session
quality-goal
remove-worktree
superpowers -> /Users/lee-kyu-hwan/.codex/superpowers/skills

$ ls -1 ~/.codex/skills/
analyzing-open-source-pr-patterns
codex-import-claude-session
collecting-recent-closed-prs
deep-research
github-work-log
pr-review-toolkit
pr-review-toolkit-code-reviewer
pr-review-toolkit-code-simplifier
pr-review-toolkit-comment-analyzer
pr-review-toolkit-pr-test-analyzer
pr-review-toolkit-silent-failure-hunter
pr-review-toolkit-type-design-analyzer
vercel-composition-patterns -> /Users/lee-kyu-hwan/code/kh-dev-blog/.agents/skills/vercel-composition-patterns
vercel-react-best-practices -> /Users/lee-kyu-hwan/code/kh-dev-blog/.agents/skills/vercel-react-best-practices
verifying-open-source-contribution-candidates
web-design-guidelines -> /Users/lee-kyu-hwan/code/kh-dev-blog/.agents/skills/web-design-guidelines

$ grep -rn -i 'skill' docs/codex-config-reference.toml dot_codex/*.toml 2>/dev/null | head

```

탐색 루트를 정하는 설정 키가 저장소에도 `~/.codex/config.toml` 에도 없다.
`~/.codex/config.toml` 에는 `[[skills.config]]` 항목이 SKILL.md 절대 경로 단위로만 존재한다.
Spec 의 R1.1 이 이것을 live probe 로 확정하도록 요구하는 근거가 여기다.

## V11. Codex CLI preflight — 선택 모델이 응답한다

```
$ codex --version
codex-cli 0.154.0

preflight (gpt-5.6-sol, read-only, effort low): PREFLIGHT_EXIT=0
모델 응답: Understood.
```

## V12. Spec author 의 쓰기 범위 준수

```
$ git status --porcelain
?? docs/development/2026-09-17-107-dual-review-shared-entrypoint/
```

author 결과의 `changed_files` 는 `["docs/development/2026-09-17-107-dual-review-shared-entrypoint/spec.md"]`
하나였고 실제 작업 트리와 일치한다. 허용 밖 파일 수정은 없다.
