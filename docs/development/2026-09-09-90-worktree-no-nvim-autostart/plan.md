# Quality Goal Implementation Plan

- Task ID: 90-worktree-no-nvim-autostart
- Mode: standard
- Status: Draft — plan review round 2
- Created: 2026-09-09
- Updated: 2026-09-09
- Source goal: #90 — 새 worktree 창의 0번 페인에서 nvim 자동 실행을 없앤다.

## Spec link

승인 정본은 [spec.md](/Users/lee-kyu-hwan/code/dotfiles__worktrees/90-fix-worktree-no-nvim-autostart/docs/development/2026-09-09-90-worktree-no-nvim-autostart/spec.md)이며 SHA-256은 `002800664d0451feabeead8b6118acb229317d215de03643dc1f46bccac59825`이다. 판정 명령과 기대 결과는 이 Spec의 `판정 명령 표`를 정본으로 한다.

## Global constraints

- 구현은 이 Plan이 검토·승인된 뒤에만 시작한다. 이 Plan 작성 단계에서는 source 파일을 수정하지 않는다.
- 변경 허용 대상은 `dot_config/workmux/config.yaml`, `dot_claude/skills/create-worktree/SKILL.md`, `dot_agents/skills/create-worktree/SKILL.md`, `dot_local/bin/executable_tmux-stack-layout`의 지정 문언뿐이다. `status_format`, `base_branch`, `nerdfont`, pane 수·split·focus, 스크립트 실행 코드는 범위 밖이다.
- 판정은 worktree 루트 `/Users/lee-kyu-hwan/code/dotfiles__worktrees/90-fix-worktree-no-nvim-autostart`에서 한다. Python 명령은 `/opt/homebrew/bin/python3`와 `PYTHONDONTWRITEBYTECODE=1`을 사용한다.
- 배포본 `~/.config/workmux/config.yaml`, 다른 worktree(`#42`, `#85`, `#79`), main 브랜치는 읽거나 수정하지 않는다. `chezmoi apply`, 머지, 실제 창 생성은 이 워크플로우의 범위 밖이다.
- `workmux add`는 Spec의 `CMD-2`에 있는 `--dry-run --config` 형태만 사용한다. dry-run 없는 `workmux add` 및 `workmux open`은 어떤 태스크에도 사용하지 않는다.
- initial dirty path인 `docs/development/2026-09-09-90-worktree-no-nvim-autostart/`는 보존한다. baseline은 `9ff32a30c9498df007ec5dfa558a442cc7841be1`이며, staged·committed·untracked 상태를 모두 포함하는 `CMD-8`로 범위를 판정한다.
- 이 브랜치 `90-fix/worktree-no-nvim-autostart`에 커밋하는 것은 허용하지만, 이 Plan 자체는 commit·add·checkout·stash·restore를 실행하지 않는다.

## File map

| File | Responsibility and exact interface change |
|---|---|
| `dot_config/workmux/config.yaml` | `# 레이아웃: 좌측 pane(세로 전체) / 우측 상단 pane / 우측 하단 pane`, `# 어떤 프로그램도 자동 실행하지 않는다. 모든 pane은 빈 셸로 열리며,`, `# 필요할 때 사용자가 직접 시작한다 — 에이전트는 개당 400MB/55MB를 쓰므로`, `# worktree를 만들 때마다 띄우지 않는다.` 및 첫 pane `- {}`로 바꾼다. 나머지 두 pane과 `status_format: false`, `base_branch: auto`, `nerdfont: true`는 그대로 둔다. |
| `dot_claude/skills/create-worktree/SKILL.md` | `## 주의사항` 첫 항목을 `- 에이전트(Claude·Codex)를 포함해 어떤 프로그램도 자동 실행하지 않는다. 레이아웃의 세` 및 `  pane은 모두 빈 셸이므로 필요할 때 사용자가 직접 시작한다.`로 바꾼다. Claude 전용 frontmatter와 나머지 두 주의사항 항목은 보존한다. |
| `dot_agents/skills/create-worktree/SKILL.md` | Claude 스킬과 바이트 단위로 같은 `- 에이전트(Claude·Codex)를 포함해 어떤 프로그램도 자동 실행하지 않는다. 레이아웃의 세` 및 `  pane은 모두 빈 셸이므로 필요할 때 사용자가 직접 시작한다.`를 같은 본문 위치에 적용한다. agents frontmatter에는 Claude 전용 세 줄을 추가하지 않는다. |
| `dot_local/bin/executable_tmux-stack-layout` | 3-pane 분기의 주석 세 줄을 `#       workmux 기본 배치(좌 1개(세로 전체) + 우 2개(상하))와 같다.`, `#       행 단위로 쌓으면 좌측 패인의 높이가 절반으로 줄어드므로,`, `#       이 개수에서는 열 단위로 배치한다.`로 바꾼다. 13행 `#       결과적으로 이 키가 workmux 레이아웃을 복구하는 역할을 한다.` 및 모든 실행 코드는 그대로 둔다. |
| `docs/development/2026-09-09-90-worktree-no-nvim-autostart/plan.md` | 현재 계획 산출물이다. 구현 시 source 변경 증거와 음성 대조 전사는 Git-ignored quality-state 경로에 기록하며, 이 Plan의 source 파일 목록을 넓히지 않는다. |

## Task dependencies

T1, T2, T3은 각각 config·스킬 쌍·layout 주석이라는 독립 편집 경계를 가진다. 다만 `CMD-3`은 네 source 파일 전체를 검사하므로 각 태스크는 자기 변경 전의 실패를 기록하고, T3 완료 뒤의 최종 `CMD-3` 통과를 공동 완료 조건으로 사용한다. `CMD-8`의 baseline 실패 기록은 어떤 source 편집보다 먼저 T4의 사전 단계로 남기며, T4의 통과 검사는 T1~T3 뒤에 실행한다. T1의 `- {}`가 `CMD-2` 파싱과 `CMD-7` 보존 키 검사의 입력을 만들고, T2는 `CMD-4`의 본문 동일성 계약을, T3는 `CMD-5`·`CMD-6`의 주석 전용 계약을 완결한다.

## Tasks

### T1. workmux source config를 첫 pane 빈 매핑과 빈 셸 정책으로 교체

대상 AC: AC-1 (CMD-1), AC-2 (CMD-2), AC-3 (CMD-3), AC-7 (CMD-7)

1. 실패 기록: source를 고치기 전에 Spec 정본의 `CMD-1`, `CMD-3`, `CMD-7`을 실행하고 각각 종료 코드 1을 기록한다. baseline 전사에서 확인된 실패값도 각각 1이다. `CMD-2`는 불변식이므로 같은 시점에 종료 코드 0을 기록한다. `CMD-2`의 판별력은 저장소 파일을 건드리지 않는 다음 음성 대조로 재실행한다. 먼저 변형하지 않은 최소 config 복제본에서 같은 dry-run 하네스가 종료 코드 0인 양성 대조를 기록한다. 그 뒤 그 복제본에 `    split: BROKEN` 한 줄만 추가해 음성 대조를 만든다. 이 세 줄짜리 최소 config에서 실제 `Failed to parse config ... panes[0].split: unknown variant \`BROKEN\``가 난다는 근거는 `cmd-transcript-spec-r3-negative-control.md`의 CMD-2 출력 꼬리이다. 양성·음성 출력과 음성의 실제 오류 문언을 quality-state 전사에 보존한 뒤에만 임시 경로를 삭제한다.

```sh
set -euo pipefail
scratch=/private/tmp/workmux-config-parse-negative-90
test ! -e "$scratch"
mkdir "$scratch" "$scratch/data" "$scratch/state" "$scratch/cache"
trap 'rm -rf "$scratch"' EXIT
printf '%s\n' 'panes:' '  - command: nvim' > "$scratch/config.yaml"
git -C "$scratch" init -q -b main
git -C "$scratch" config user.email spec@example.invalid
git -C "$scratch" config user.name spec
git -C "$scratch" commit --allow-empty -qm baseline
(cd "$scratch" && XDG_DATA_HOME="$scratch/data" XDG_STATE_HOME="$scratch/state" XDG_CACHE_HOME="$scratch/cache" workmux add --dry-run --config "$scratch/config.yaml" workmux-config-parse-negative-90) > "$scratch/positive.out" 2>&1
printf '%s\n' '    split: BROKEN' >> "$scratch/config.yaml"
if (cd "$scratch" && XDG_DATA_HOME="$scratch/data" XDG_STATE_HOME="$scratch/state" XDG_CACHE_HOME="$scratch/cache" workmux add --dry-run --config "$scratch/config.yaml" workmux-config-parse-negative-90) > "$scratch/negative.out" 2>&1; then
  printf '%s\n' 'CMD-2 negative control unexpectedly passed' >&2
  exit 1
else
  control_code=$?
  test "$control_code" -eq 1
fi
grep -F 'panes[0].split: unknown variant `BROKEN`' "$scratch/negative.out"
cat "$scratch/positive.out" "$scratch/negative.out"
```
2. 최소 변경: `dot_config/workmux/config.yaml`에 아래 diff의 추가 행을 문자 단위로 적용한다. 첫 pane 외의 두 선언, `status_format: false`, `base_branch: auto`, `nerdfont: true` 및 파일의 다른 행은 바꾸지 않는다.

```diff
-# 레이아웃: 좌 nvim(세로 전체) / 우상 claude / 우하 codex
+# 레이아웃: 좌측 pane(세로 전체) / 우측 상단 pane / 우측 하단 pane
 #
 # split 방향은 tmux와 같다 (horizontal=좌우, vertical=위아래).
 # Orca는 반대이므로 혼동하지 않도록 주의.
 #
-# nvim만 자동 실행한다. command를 생략한 pane은 빈 셸로 열리며,
-# claude·codex는 필요할 때 직접 시작한다 — 에이전트가 개당 400MB/55MB를
-# 쓰므로 worktree를 만들 때마다 띄우지 않는다.
+# 어떤 프로그램도 자동 실행하지 않는다. 모든 pane은 빈 셸로 열리며,
+# 필요할 때 사용자가 직접 시작한다 — 에이전트는 개당 400MB/55MB를 쓰므로
+# worktree를 만들 때마다 띄우지 않는다.
 panes:
-  - command: nvim
+  - {}
```

3. 통과 기록: 같은 `CMD-1`, `CMD-2`, `CMD-7`을 다시 실행해 각각 종료 코드 0을 기록한다. `CMD-3`은 아직 종료 코드 1이어야 한다. 두 스킬의 `nvim만 실행`과 layout의 `좌 nvim`·`nvim이 상단` 금지어가 남아 있기 때문이다. `CMD-2`의 dry-run 성공은 YAML 파싱 증거일 뿐 pane 동작 증거로 해석하지 않는다. 네 파일 전체 상태에서 `CMD-3`이 처음 종료 코드 0이 되는 기록은 T3의 통과 기록에 귀속한다. 어느 판정 명령도 이 기대 종료 코드와 다르면 다음 태스크로 진행하지 않고, 명령·stdout·stderr·실제 종료 코드를 전사와 함께 기록해 중단한다. 원인이 T1 변경으로 한정되고 복원이 필요하면 이 태스크의 config 파일만 baseline으로 복원한 뒤 재검토하며, 다른 태스크 파일은 건드리지 않는다.

### T2. create-worktree 스킬 두 본문의 첫 주의사항 항목을 동기화

대상 AC: AC-3 (CMD-3), AC-4 (CMD-4)

1. 실패 기록: T2의 편집 전 `CMD-3`을 실행해 종료 코드 1을 기록한다. `CMD-4`는 불변식이므로 종료 코드 0을 기록한다. 저장소 파일을 건드리지 않고 다음 명령으로 임시 복제본에서 먼저 변형하지 않은 복제본의 같은 CMD-4 하네스가 종료 코드 0인 양성 대조를 기록한다. 이어 CMD-4가 검증하는 네 고의 위반을 각각 만든다: (A) agents 본문 끝 한 줄 추가, (B) Claude frontmatter 세 줄 삭제, (C) agents에 그 세 줄 추가, (D) Claude 세 줄 순서 변경. `run_cmd4`의 Python 프로그램은 아래 `### CMD-4` 코드 블록의 프로그램 텍스트와 같다. 각 변형 직후 변형 확인 단언도 실행하고, 각 사례의 CMD-4 종료 코드 1, 실제 `AssertionError` 출력, 주입한 위반에 대응한 CMD-4 단언 문언(A: `cb == ab`, B: `extra in cf`, C: `all(not any(line.startswith(key) for line in af.splitlines()) for key in keys)`, D: `extra in cf`)을 quality-state 전사에 함께 보존한다. 전사를 보존한 뒤에만 임시 경로를 삭제한다.

```sh
set -euo pipefail
scratch=/private/tmp/create-worktree-skill-negative-90
base="$scratch/base"
case_dir="$scratch/case"
test ! -e "$scratch"
mkdir -p "$base/dot_claude/skills/create-worktree" "$base/dot_agents/skills/create-worktree"
trap 'rm -rf "$scratch"' EXIT
cp dot_claude/skills/create-worktree/SKILL.md "$base/dot_claude/skills/create-worktree/SKILL.md"
cp dot_agents/skills/create-worktree/SKILL.md "$base/dot_agents/skills/create-worktree/SKILL.md"
reset_case() { rm -rf "$case_dir"; cp -R "$base" "$case_dir"; }
run_cmd4() {
  (cd "$case_dir" && PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; c = Path("dot_claude/skills/create-worktree/SKILL.md").read_bytes(); a = Path("dot_agents/skills/create-worktree/SKILL.md").read_bytes(); assert c.startswith(b"---\n") and a.startswith(b"---\n"); cf, cb = c.split(b"---\n", 2)[1:]; af, ab = a.split(b"---\n", 2)[1:]; description = b"description: Use when creating a git worktree for a branch or a pull request (PR) review, optionally opening it in a named tmux session\n"; extra = b"argument-hint: <branch-name" + bytes([124]) + b"pr-ref> [target-session]\nuser-invocable: true\nallowed-tools: Bash\n"; keys = (b"argument-hint:", b"user-invocable:", b"allowed-tools:"); assert cb == ab; assert description in cf and description in af; assert extra in cf; assert all(not any(line.startswith(key) for line in af.splitlines()) for key in keys); assert cf == af.replace(description, description + extra)')
}
expect_cmd4_failure() { case_name=$1; if run_cmd4 > "$scratch/$case_name.stdout" 2> "$scratch/$case_name.stderr"; then return 1; else control_code=$?; test "$control_code" -eq 1; cat "$scratch/$case_name.stderr"; fi; }
reset_case
run_cmd4 > "$scratch/positive.stdout" 2> "$scratch/positive.stderr"
cat "$scratch/positive.stdout" "$scratch/positive.stderr"
reset_case
printf '\n- negative-control-extra\n' >> "$case_dir/dot_agents/skills/create-worktree/SKILL.md"
test "$(tail -n 1 "$case_dir/dot_agents/skills/create-worktree/SKILL.md")" = '- negative-control-extra'
expect_cmd4_failure A
reset_case
/opt/homebrew/bin/python3 -c 'from pathlib import Path; p = Path("'"$case_dir"'/dot_claude/skills/create-worktree/SKILL.md"); t = p.read_text(); lines = ("argument-hint: <branch-name|pr-ref> [target-session]\n", "user-invocable: true\n", "allowed-tools: Bash\n"); u = "".join(part for part in t.splitlines(keepends=True) if part not in lines); assert u != t; p.write_text(u)'
expect_cmd4_failure B
reset_case
/opt/homebrew/bin/python3 -c 'from pathlib import Path; p = Path("'"$case_dir"'/dot_agents/skills/create-worktree/SKILL.md"); t = p.read_text(); marker = "description: Use when creating a git worktree for a branch or a pull request (PR) review, optionally opening it in a named tmux session\n"; extra = "argument-hint: <branch-name|pr-ref> [target-session]\nuser-invocable: true\nallowed-tools: Bash\n"; u = t.replace(marker, marker + extra, 1); assert u != t; p.write_text(u)'
expect_cmd4_failure C
reset_case
/opt/homebrew/bin/python3 -c 'from pathlib import Path; p = Path("'"$case_dir"'/dot_claude/skills/create-worktree/SKILL.md"); t = p.read_text(); old = "argument-hint: <branch-name|pr-ref> [target-session]\nuser-invocable: true\nallowed-tools: Bash\n"; new = "allowed-tools: Bash\nuser-invocable: true\nargument-hint: <branch-name|pr-ref> [target-session]\n"; u = t.replace(old, new, 1); assert u != t; p.write_text(u)'
expect_cmd4_failure D
```
2. 최소 변경: 두 파일의 `## 주의사항` 첫 항목을 아래 두 줄로 완전히 같게 바꾼다. 둘째·셋째 목록 항목, Claude frontmatter의 `argument-hint`, `user-invocable`, `allowed-tools` 세 줄, agents frontmatter의 부재 상태를 바꾸지 않는다.

```markdown
- 에이전트(Claude·Codex)를 포함해 어떤 프로그램도 자동 실행하지 않는다. 레이아웃의 세
  pane은 모두 빈 셸이므로 필요할 때 사용자가 직접 시작한다.
```

3. 통과 기록: `CMD-4`를 다시 실행해 종료 코드 0을 기록한다. `CMD-3`은 아직 종료 코드 1이어야 한다. layout의 `좌 nvim`·`nvim이 상단` 금지어가 남아 있기 때문이다. SPEC-015 권고를 구현 증거로 반영해 두 `## 주의사항` 절이 각각 세 목록 항목을 그대로 유지함을 함께 기록한다. SPEC-016 권고도 반영해 AC-3 산문의 여섯 표현보다 엄격한 `CMD-3`의 `banned` 일곱 리터럴 전체를 정본으로 검사한다. Spec은 수정하지 않는다. 어느 판정 명령도 이 기대 종료 코드와 다르면 다음 태스크로 진행하지 않고, 명령·stdout·stderr·실제 종료 코드와 음성 대조의 사례별 변형 확인·`AssertionError` 전사를 기록해 중단한다. 원인이 T2 변경으로 한정되고 복원이 필요하면 이 태스크의 두 스킬 파일만 baseline으로 복원한 뒤 재검토하며, T1·T3 파일은 건드리지 않는다.

### T3. 3-pane layout 설명을 확인된 기하학으로만 교체

대상 AC: AC-3 (CMD-3), AC-5 (CMD-5), AC-6 (CMD-6)

1. 실패 기록: T3의 주석을 고치기 전에 `CMD-3`, `CMD-5`, `CMD-6`을 실행하고 각각 종료 코드 1을 기록한다. `CMD-6`의 baseline 실패는 대상 파일 diff가 비어 있기 때문이어야 한다.
2. 최소 변경: `dot_local/bin/executable_tmux-stack-layout`의 3-pane 분기에서 아래 세 주석 행만 교체한다. 바로 다음의 복구 역할 주석은 그대로 두고, shebang·조건문·tmux 호출 등 실행 코드는 한 글자도 바꾸지 않는다.

```diff
-#       workmux 기본 배치(좌 nvim / 우상 claude / 우하 codex)와 같다.
-#       행 단위로 쌓으면 nvim이 상단 가로 전체가 되어 높이가 절반으로 줄어
-#       편집에 불리하므로, 이 개수에서는 열 단위로 배치한다.
+#       workmux 기본 배치(좌 1개(세로 전체) + 우 2개(상하))와 같다.
+#       행 단위로 쌓으면 좌측 패인의 높이가 절반으로 줄어드므로,
+#       이 개수에서는 열 단위로 배치한다.
 #       결과적으로 이 키가 workmux 레이아웃을 복구하는 역할을 한다.
```

3. 통과 기록: 같은 `CMD-3`, `CMD-5`, `CMD-6`을 다시 실행해 모두 종료 코드 0을 기록한다. 이 시점의 `CMD-3` 종료 코드 0이 네 source 파일 전체에서 처음 얻는 통과 기록이다. `CMD-5`는 시작 주석부터 다음 `#   - 패인 ` 경계까지의 내용만 검사하고, `CMD-6`은 baseline 대비 추가·삭제 행이 모두 `#`로 시작함을 확인해야 한다. 어느 판정 명령도 이 기대 종료 코드와 다르면 다음 태스크로 진행하지 않고, 명령·stdout·stderr·실제 종료 코드를 전사와 함께 기록해 중단한다. 원인이 T3 변경으로 한정되고 복원이 필요하면 이 태스크의 layout 파일만 baseline으로 복원한 뒤 재검토하며, T1·T2 파일은 건드리지 않는다.

### T4. baseline 기준 변경 범위와 전체 판정 결과를 마감

대상 AC: AC-8 (CMD-8)

1. 실패 기록: T1~T3 시작 전에 Spec baseline 전사와 같은 `CMD-8`을 실행해 종료 코드 1을 기록한다. 실패 원인은 네 source 파일이 아직 변경 집합에 없다는 것이어야 하며, initial dirty 문서 디렉터리는 보존한다.
2. 최소 변경: 이 태스크는 source를 추가 편집하지 않는다. T1~T3이 검증된 네 source 변경만 남겼는지 확인하고, 실행 중 생긴 추적되지 않은 파일이 있으면 삭제나 복구를 임의로 수행하지 말고 허용 범위를 벗어난 경로로 기록하여 구현을 중단한다.
3. 통과 기록: T1~T3 뒤 `CMD-8`을 실행해 종료 코드 0을 기록한다. staged·committed·untracked를 합친 변경 집합은 네 source 파일을 모두 포함하고, 그 밖의 경로는 `docs/development/2026-09-09-90-worktree-no-nvim-autostart/` 아래 문서 산출물만 허용된다. 이어서 `CMD-1`부터 `CMD-8`까지 Spec 순서대로 실행해 모든 최종 종료 코드가 0인지 기록한다. `CMD-2`·`CMD-4`의 음성 대조 전사도 이번 구현 결과와 함께 다시 첨부한다.

## Verification commands

아래는 Spec 정본의 `판정 명령 표`를 그대로 옮긴 실행 순서다. 각 명령은 worktree 루트에서 실행한다.

| ID | Exact command | Expected successful outcome |
|---|---|---|
| CMD-1 | 아래 `CMD-1` 코드 블록 | `panes`가 빈 첫 매핑과 기존 3-pane 계약에 정확히 일치하여 종료 코드 0 |
| CMD-2 | 아래 `CMD-2` 코드 블록 | 임시 git 저장소에서 source YAML을 dry-run 파싱하고 EXIT에서 임시 경로를 제거하며 종료 코드 0 |
| CMD-3 | 아래 `CMD-3` 코드 블록 | 네 파일의 금지 전제 부재 및 config·두 스킬 기대 문언 등가로 종료 코드 0 |
| CMD-4 | 아래 `CMD-4` 코드 블록 | 두 본문 동일 및 허용된 Claude 전용 frontmatter 차이만 남아 종료 코드 0 |
| CMD-5 | 아래 `CMD-5` 코드 블록 | 3-pane 주석이 배치·기하학·복구 역할을 보이고 nvim을 언급하지 않아 종료 코드 0 |
| CMD-6 | 아래 `CMD-6` 코드 블록 | baseline 대비 script diff가 존재하고 모든 변경 행이 주석이라 종료 코드 0 |
| CMD-7 | 아래 `CMD-7` 코드 블록 | 첫 pane 빈 매핑 및 세 보존 키가 정확하여 종료 코드 0 |
| CMD-8 | 아래 `CMD-8` 코드 블록 | 네 source 파일과 허용 문서 경로만 변경 집합에 있어 종료 코드 0 |

### CMD-1

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; import yaml; panes = yaml.safe_load(Path("dot_config/workmux/config.yaml").read_text())["panes"]; assert panes == [{}, {"split": "horizontal", "focus": True}, {"split": "vertical"}], panes'
```

### CMD-2

```sh
set -euo pipefail; scratch=/private/tmp/workmux-config-parse-90; test ! -e "$scratch"; mkdir "$scratch"; trap 'rm -rf "$scratch"' EXIT; git -C "$scratch" init -q -b main; git -C "$scratch" config user.email spec@example.invalid; git -C "$scratch" config user.name spec; git -C "$scratch" commit --allow-empty -qm baseline; (cd "$scratch" && workmux add --dry-run --config /Users/lee-kyu-hwan/code/dotfiles__worktrees/90-fix-worktree-no-nvim-autostart/dot_config/workmux/config.yaml workmux-config-parse-90)
```

### CMD-3

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; paths = [Path("dot_config/workmux/config.yaml"), Path("dot_claude/skills/create-worktree/SKILL.md"), Path("dot_agents/skills/create-worktree/SKILL.md"), Path("dot_local/bin/executable_tmux-stack-layout")]; config = paths[0].read_text(); skills = [p.read_text() for p in paths[1:3]]; text = "\n".join(p.read_text() for p in paths); banned = ("command: nvim", "nvim만 자동 실행", "nvim만 실행", "좌 nvim", "우상 claude", "우하 codex", "nvim이 상단"); assert not [s for s in banned if s in text]; config_expected = "# workmux 전역 설정\n# https://workmux.raine.dev\n#\n# 레이아웃: 좌측 pane(세로 전체) / 우측 상단 pane / 우측 하단 pane\n#\n# split 방향은 tmux와 같다 (horizontal=좌우, vertical=위아래).\n# Orca는 반대이므로 혼동하지 않도록 주의.\n#\n# 어떤 프로그램도 자동 실행하지 않는다. 모든 pane은 빈 셸로 열리며,\n# 필요할 때 사용자가 직접 시작한다 — 에이전트는 개당 400MB/55MB를 쓰므로\n# worktree를 만들 때마다 띄우지 않는다."; assert config[:config.index("panes:")].rstrip("\n") == config_expected; expected = "- 에이전트(Claude·Codex)를 포함해 어떤 프로그램도 자동 실행하지 않는다. 레이아웃의 세 pane은 모두 빈 셸이므로 필요할 때 사용자가 직접 시작한다."; normalize = lambda value: " ".join(value.split()); first_item = lambda skill: (lambda notice: notice[notice.index("- "):notice.index("\n- ", notice.index("- ") + 1)])(skill.split("## 주의사항\n", 1)[1]); assert all(normalize(first_item(skill)) == expected for skill in skills)'
```

### CMD-4

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; c = Path("dot_claude/skills/create-worktree/SKILL.md").read_bytes(); a = Path("dot_agents/skills/create-worktree/SKILL.md").read_bytes(); assert c.startswith(b"---\n") and a.startswith(b"---\n"); cf, cb = c.split(b"---\n", 2)[1:]; af, ab = a.split(b"---\n", 2)[1:]; description = b"description: Use when creating a git worktree for a branch or a pull request (PR) review, optionally opening it in a named tmux session\n"; extra = b"argument-hint: <branch-name" + bytes([124]) + b"pr-ref> [target-session]\nuser-invocable: true\nallowed-tools: Bash\n"; keys = (b"argument-hint:", b"user-invocable:", b"allowed-tools:"); assert cb == ab; assert description in cf and description in af; assert extra in cf; assert all(not any(line.startswith(key) for line in af.splitlines()) for key in keys); assert cf == af.replace(description, description + extra)'
```

### CMD-5

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; lines = Path("dot_local/bin/executable_tmux-stack-layout").read_text().splitlines(); start = next(i for i, line in enumerate(lines) if line == "#   - 패인 3개: 좌 1개(세로 전체) + 우 2개(상하)"); end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("#   - 패인 ")); block = "\n".join(lines[start:end]); required = ("#       workmux 기본 배치(좌 1개(세로 전체) + 우 2개(상하))와 같다.", "#       행 단위로 쌓으면 좌측 패인의 높이가 절반으로 줄어드므로,", "#       이 개수에서는 열 단위로 배치한다.", "#       결과적으로 이 키가 workmux 레이아웃을 복구하는 역할을 한다."); assert all(line in block for line in required); assert "nvim" not in block'
```

### CMD-6

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'import subprocess; baseline = "9ff32a30c9498df007ec5dfa558a442cc7841be1"; target = "dot_local/bin/executable_tmux-stack-layout"; diff = subprocess.run(["git", "diff", "--unified=0", baseline, "--", target], check=True, capture_output=True, text=True).stdout; changed = [line for line in diff.splitlines() if line[:1] in ("+", "-") and not line.startswith(("+++", "---"))]; assert changed and all(line[1:].startswith("#") for line in changed), changed'
```

### CMD-7

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; import yaml; data = yaml.safe_load(Path("dot_config/workmux/config.yaml").read_text()); assert data["panes"][0] == {}, data["panes"]; assert {key: data[key] for key in ("status_format", "base_branch", "nerdfont")} == {"status_format": False, "base_branch": "auto", "nerdfont": True}'
```

### CMD-8

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'import subprocess; baseline = "9ff32a30c9498df007ec5dfa558a442cc7841be1"; sources = {"dot_config/workmux/config.yaml", "dot_claude/skills/create-worktree/SKILL.md", "dot_agents/skills/create-worktree/SKILL.md", "dot_local/bin/executable_tmux-stack-layout"}; docs_prefix = "docs/development/2026-09-09-90-worktree-no-nvim-autostart/"; run = lambda args: subprocess.run(args, check=True, capture_output=True, text=True).stdout.splitlines(); tracked = set(run(["git", "-c", "core.quotePath=false", "diff", "--name-only", baseline])); status = run(["git", "-c", "core.quotePath=false", "status", "--porcelain=v1", "--untracked-files=all"]); untracked = {line[3:] for line in status if line.startswith("?? ")}; changed = tracked.union(untracked); allowed = sources.union({path for path in changed if path.startswith(docs_prefix)}); assert sources <= changed, sorted(sources - changed); assert changed <= allowed, sorted(changed - allowed)'
```

## Rollout and rollback

이 변경은 chezmoi source만 고친다. 이 워크플로우는 `chezmoi apply`를 실행하지 않으며, 사용자가 승인 후 별도로 실행할 때에만 배포본에 반영된다. 반영 효과는 앞으로 만드는 창에만 적용되고, 이미 열린 창·pane·프로세스는 건드리지 않는다. 실제 창 동작은 배포 후 사용자가 다음 worktree를 만들 때 확인한다.

롤백 트리거는 workmux가 변경 YAML을 파싱하지 못하는 경우 또는 배포 후 첫 worktree 생성에서 pane이 세 개로 열리지 않는 경우다. source를 baseline으로 되돌리는 구체적 명령은 다음과 같다.

```sh
git restore --source=9ff32a30c9498df007ec5dfa558a442cc7841be1 -- dot_config/workmux/config.yaml dot_claude/skills/create-worktree/SKILL.md dot_agents/skills/create-worktree/SKILL.md dot_local/bin/executable_tmux-stack-layout
```

그 뒤 네 source 파일이 baseline과 동일해졌는지 다음 명령으로 직접 확인한다. 이 명령의 stdout을 캡처하고 **네 source diff 출력이 빈 문자열인지**만으로 판정한다. `git diff --name-only`의 종료 코드는 출력이 있어도 0일 수 있으므로 롤백 완료의 판정 근거로 쓰지 않는다.

```sh
git diff --name-only 9ff32a30c9498df007ec5dfa558a442cc7841be1 -- dot_config/workmux/config.yaml dot_claude/skills/create-worktree/SKILL.md dot_agents/skills/create-worktree/SKILL.md dot_local/bin/executable_tmux-stack-layout
```

또한 다음 읽기 전용 검사는 staged·committed·untracked를 합친 남은 변경 경로가 `docs/development/2026-09-09-90-worktree-no-nvim-autostart/` 아래에만 있는지 확인한다. 기대 결과는 stdout이 비어 있고 `unexpected` 단언이 통과하는 것이다.

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'import subprocess; baseline = "9ff32a30c9498df007ec5dfa558a442cc7841be1"; docs_prefix = "docs/development/2026-09-09-90-worktree-no-nvim-autostart/"; run = lambda args: subprocess.run(args, check=True, capture_output=True, text=True).stdout.splitlines(); tracked = set(run(["git", "-c", "core.quotePath=false", "diff", "--name-only", baseline])); status_lines = run(["git", "-c", "core.quotePath=false", "status", "--porcelain=v1", "--untracked-files=all"]); untracked = {line[3:] for line in status_lines if line.startswith("?? ")}; unexpected = sorted(path for path in tracked.union(untracked) if not path.startswith(docs_prefix)); assert not unexpected, unexpected'
```

롤백 후 `CMD-8`이 종료 코드 1을 내는 것은 정상이다. 그 명령의 계약은 네 source가 변경 집합에 모두 있어야 한다는 것이므로, baseline과 같게 되돌린 뒤에는 그 계약의 반대 상태가 된다. 배포본을 이미 갱신했다면, 되돌린 source를 사용자가 다시 `chezmoi apply`하여 배포본도 되돌려야 한다. 이 Plan의 자동화·구현 단계는 그 apply를 실행하지 않는다.

## Acceptance-criteria traceability

| Criterion | Task | Verification command | Expected outcome |
|---|---|---|---|
| AC-1 | T1 | CMD-1 | `panes` 정확한 목록, 첫 항목에 `command`·`split` 없음, 종료 코드 0 |
| AC-2 | T1 | CMD-2 | `--dry-run --config` source 파싱 성공, 종료 코드 0 |
| AC-3 | T1 | CMD-3 | config 주석 블록 등가, 종료 코드 0 (T3 완료 후) |
| AC-3 | T2 | CMD-3 | 두 스킬 주의사항 첫 항목 등가, 종료 코드 0 (T3 완료 후) |
| AC-3 | T3 | CMD-3 | layout 금지어 부재로 네 파일 전체 통과, 종료 코드 0 |
| AC-4 | T2 | CMD-4 | 본문 바이트 동일과 Claude 전용 세 frontmatter 줄만 확인, 종료 코드 0 |
| AC-5 | T3 | CMD-5 | 3-pane 주석 경계 블록의 배치·기하학·복구 역할 및 nvim 부재, 종료 코드 0 |
| AC-6 | T3 | CMD-6 | baseline script diff의 변경 행이 존재하고 모두 주석, 종료 코드 0 |
| AC-7 | T1 | CMD-7 | 첫 pane 빈 매핑 및 `status_format`·`base_branch`·`nerdfont` 보존, 종료 코드 0 |
| AC-8 | T4 | CMD-8 | 네 source 모두 포함, 문서 디렉터리 외 허용 범위 이탈 없음, 종료 코드 0 |
