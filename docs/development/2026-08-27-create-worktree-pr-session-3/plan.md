# Quality Goal Implementation Plan

- Task ID: 20260827T120102Z-28-35-create-worktree-스킬-3차-실행-pr-링크-입력-a16ed82b
- Mode: standard
- Status: PLAN_REVIEW (round 2)
- Created: 2026-08-28
- Updated: 2026-08-28
- Source goal: #28 #35 create-worktree 스킬 3차 실행 — PR 링크 입력 시 2-review 세션에 PR 번호 윈도우를 생성하고 대상 세션을 직접 지정하도록 확장한다. SPEC-009(AC-9 판별력)과 SPEC-010(--pr 정규화)를 선반영하고, 휘발성 식별자를 증거에서 제거한다

## Spec link

- 경로: `docs/development/2026-08-27-create-worktree-pr-session-3/spec.md`
- SHA-256: `5c742d283a2e042b97f81239c5dd7e836a3b1b9bb7c9c822e7476a5c597408f9`
- 게이트: 라운드 2에서 90점 PASS, 블로커 0, Critical/High 0
- 이 Plan은 위 digest의 Spec만을 근거로 한다. Spec이 바뀌면 이 Plan을 무효로 본다.

### Spec 잔여 권고 사항의 처리

Spec 게이트 통과 후에도 Medium 1건·Low 4건이 남았다. 통과 시점 digest를 깨지 않기 위해
Spec 본문은 수정하지 않았고, **이 Plan이 각각의 해소 방침을 확정한다.** 구현은 Spec이
아니라 아래 확정안을 따른다.

| ID | 심각도 | 내용 | 이 Plan의 확정 |
|---|---|---|---|
| SPEC-018 | Medium | R8.2("실제 세션 ≠ 선택 세션이면 정리")가 R2.6 3행("창이 열려 있고 옮기지 않으면 실제 세션으로 갱신")과 충돌 | **분기별로 나눈다** — ① 생성·오픈 분기: R8.2 그대로 적용 ② 이동 분기(R7.5): 이동 후 최종 위치가 선택 세션과 다르면 **보고하고 config에 잘못된 값을 쓰지 않는다** ③ 옮기지 않는 분기(R7.3·R7.4): 불일치가 정상이므로 R8.2를 적용하지 않고 R2.6이 관장한다. 세 갈래를 SKILL.md 사후 검증 절에 모두 적는다 |
| SPEC-019 | Low | AC-9b의 "실행된 `git config` 명령 기록"에 캡처 방법이 없다 | **아래 "스모크 실행 하네스"의 명령 로그**를 캡처 수단으로 확정. 로그가 비었거나 하네스를 우회한 흔적이 있으면 통과가 아니라 **"검증 불가"**로 보고 |
| SPEC-020 | Low | AC-56 정규식이 줄 끝 `PR`을 놓친다 | 앵커 추가 — `'pull request\|(^\|[^a-z])PR([^a-z]\|$)'` |
| SPEC-021 | Low | Spec 헤더가 "round 1"로 남아 있다 | **수정하지 않는다.** 통과 시점 digest 보존. 보고서에 알려진 표기 오류로 기록 |
| SPEC-022 | Low | R7.5가 `move-window-to-session`의 `{worktree명}`을 handle과 무조건 등치. 그 스킬은 PATH basename으로 정의 | **분기 규칙까지 확정한다** — handle과 경로를 함께 넘기고, 이동 후 `workmux.worktree.{handle}.window-session`을 읽어 대상 세션과 다르면(그 스킬이 basename 키에 썼다는 뜻) **스킬이 handle 키를 직접 갱신하고 그 사실을 보고한다.** 갱신도 실패하면 중단한다. 이 분기는 스모크로 덮이지 않는다(아래 한계 참조) |

**SPEC-022의 검증 한계.** 이 저장소의 기본 명명에서는 PR #31 worktree의 handle과 PATH
basename이 같아 분기가 발동하지 않는다. 스모크로 확인할 수 없으므로 문서 검토로만
판정하고 보고서에 잔여 격차로 기록한다. 억지로 조건을 만들려면 `--name`으로 handle을
바꾼 worktree를 옮겨야 하는데, 그것은 T8 픽스처와 T9~T12 상태 전이를 뒤섞어 다른 기준의
판정을 흐린다.

## Global constraints

### 변경 허용 경로 (이 셋 외 어떤 파일도 수정하지 않는다)

1. `dot_claude/skills/create-worktree/SKILL.md`
2. `dot_agents/skills/create-worktree/SKILL.md`
3. `dot_agents/skills/create-worktree/agents/openai.yaml`

### 보존 대상 (baseline의 initial dirty path — 바이트 단위 보존)

- `docs/development/2026-08-27-create-worktree-pr-session/`
- `docs/development/2026-08-27-create-worktree-pr-session-2/`

이번 실행 산출물인 `-3/` 디렉터리는 오케스트레이터만 쓴다. Codex는 수정하지 않는다.

### 저장소 관례

- **홈의 적용본을 직접 수정하지 않는다.** 소스만 고치고 chezmoi가 생성한다(CLAUDE.md).
- 두 SKILL.md 본문은 Claude 전용 frontmatter 3줄을 제외하고 동일해야 한다.

### 안전 제약

- **커밋·푸시·머지 금지.**
- **`chezmoi apply`를 인자 없이 실행하지 않는다.** `dot_claude/skills/quality-goal`이
  chezmoi 소스에 있어(실측) 전체 apply는 다른 세션이 실행 중인 quality-goal 배포본
  **23개 파일**을 덮는다. 반드시 경로를 한정한다.
- 다른 세션의 worktree·창(`workmux list`에 이미 있는 항목)을 건드리지 않는다.
- Codex 호출에 `--skip-git-repo-check`, `--full-auto`, `--yolo`를 쓰지 않는다.

### 구현 규칙

- **test-first**: 검증 명령을 먼저 실행해 실패를 기록(T1) → 최소 변경(T2~T4) → 같은
  명령으로 통과 기록(T5).
- Spec의 요구사항 번호를 SKILL.md 본문에 노출하지 않는다. 절 제목과 서술로 옮긴다.
- Spec R9.6의 보존 규칙 18개는 문구가 바뀌어도 규칙 자체가 남아야 한다.

## 스모크 실행 하네스 (PLAN-001·PLAN-002 해소의 핵심)

### 문제

라운드 1 Plan은 스킬이 **파생해야 할 값**(대상 세션, 창 이름, `--pr` 인자 형태)을
오케스트레이터가 직접 타이핑한 뒤 그 값을 검증했다. 그러면 SKILL.md가 틀리게 적혀 있어도
통과한다 — Spec D19가 AC-9b를 만든 이유와 정확히 같은 결함이다.

### 원칙

1. **입력에 정답을 넣지 않는다.** 각 스모크 단계의 호출 프롬프트에는 그 단계가 검증하려는
   값을 넣지 않는다. 세션 선택을 검증하는 단계에는 세션명을 주지 않고, 창 이름 파생을
   검증하는 단계에는 이름을 주지 않는다.
2. **배포본이 절차를 결정한다.** 호출 주체는 `~/.claude/skills/create-worktree/SKILL.md`
   를 읽고 스스로 명령을 만든다.
3. **실제 실행된 명령줄을 기계적으로 남긴다.** 자기 보고가 아니라 로그로 남긴다.

### 하네스 구성 (T7 직후, T8 시작 전에 준비)

```bash
HARNESS=/tmp/qg-harness
mkdir -p "$HARNESS/shim"
LOG="$HARNESS/cmd.log"; : > "$LOG"

# workmux·git·tmux 실행을 argv 그대로 기록하는 shim
# tmux를 포함하는 이유(PLAN-013): 창 이동은 tmux move-window·display-message로 일어나므로
# tmux를 빼면 T11의 "이동 경로를 탔다"는 증거를 만들 수 없다.
for real in /opt/homebrew/bin/workmux /opt/homebrew/bin/git /opt/homebrew/bin/tmux; do
  name=$(basename "$real")
  cat > "$HARNESS/shim/$name" <<EOF
#!/bin/sh
printf '%s' "$name" >> "$LOG"
for a in "\$@"; do printf ' %s' "\$a" >> "$LOG"; done
printf '\n' >> "$LOG"
exec "$real" "\$@"
EOF
  chmod +x "$HARNESS/shim/$name"
done

# 모든 셸 명령을 이 스크립트로 통과시킨다
cat > "$HARNESS/run.sh" <<EOF
#!/bin/bash
export PATH="$HARNESS/shim:\$PATH"
eval "\$@"
EOF
chmod +x "$HARNESS/run.sh"
```

`workmux`와 `git`의 실경로는 실측했다(`/opt/homebrew/bin/workmux`,
`/opt/homebrew/bin/git`). shim은 argv를 로그에 붙인 뒤 실물을 `exec`하므로 동작을 바꾸지
않는다.

### 호출 방식 (PLAN-018)

각 스모크 단계는 **Agent 도구로 `general-purpose` 하위 에이전트 하나**를 띄워 수행한다
(Bash 권한이 있어야 하므로 읽기 전용 에이전트는 쓰지 않는다). 오케스트레이터가 그
에이전트에게 주는 것은 (a) 그 단계의 입력, (b) 하네스 사용 지시뿐이다. 하네스 지시는
검증 대상 값과 무관하므로 정답을 흘리지 않는다.

프롬프트 형식은 다음과 같고, `{단계별 입력}`만 단계마다 달라진다. 각 단계의 실제 문구는
해당 태스크에 그대로 적어 두었다.

> 모든 셸 명령을 `/tmp/qg-harness/run.sh "<명령>"` 형태로 실행해라. 명령에 작은따옴표가
> 들어가면 바깥은 큰따옴표로 감싼다.
> `~/.claude/skills/create-worktree/SKILL.md`의 절차를 따라라.
> 작업: {단계별 입력}

### 단계별 로그 분리 (PLAN-012)

`cmd.log`는 누적되므로 "그 단계의 호출"을 기계적으로 판정하려면 경계를 나눠야 한다.
**각 단계 시작 직전에 로그를 그 단계 파일로 옮기고 비운다.**

```bash
newphase() {            # 사용: newphase T9
  mv "$LOG" "/tmp/qg-harness/cmd-$1-prev.log" 2>/dev/null || :
  : > "$LOG"
  echo "### phase $1" >> "$LOG"
}
```

단계가 끝나면 `cp "$LOG" "/tmp/qg-harness/cmd-<단계>.log"`로 보존한다. 이후 모든
per-phase grep은 그 단계 파일만 읽는다.

### 판정과 폴백

**우회 판정은 단계마다 기대 명령이 다르다.** `add`/`open`은 생성 단계에서만 나온다 —
T10·T11·T12는 올바르게 동작해도 `add`/`open`을 부르지 않으므로, 그것을 기준으로 삼으면
정상 실행이 "검증 불가"로 오판된다(PLAN-012).

| 단계 | 로그에 반드시 있어야 하는 것 | 없으면 |
|---|---|---|
| T8 B부 | `workmux list` ≥1 **그리고** `git config` ≥1 | 검증 불가 |
| T9 | `workmux add` ≥1 | 검증 불가 |
| T10 | `workmux list` ≥1 (기존 창 판정을 했다는 증거) | 검증 불가 |
| T11 | `workmux list` ≥1 **그리고** `tmux move-window` 또는 `git config ... window-session` ≥1 | 검증 불가 |
| T12 | `workmux list` ≥1 **그리고** `git config ... window-session` ≥1 | 검증 불가 |

- 하네스 구성 자체가 실패하면(shim 생성 불가 등) 실행 기준을 문서 검토로 강등하고 사유를
  보고서에 남긴다(Spec 폴백 b).
- **관찰 가능한 종국 상태도 함께 증거로 쓴다.** 세션·창 이름·브랜치·HEAD는 로그와 독립적
  으로 확인되며, 입력에 그 값을 주지 않았으므로 스킬이 파생한 결과다.

### 잔여 한계 (PLAN-017 — 명시적으로 기록한다)

- 음성 단언(`$SLUG`·`$W` 조회 0건)은 **하네스를 완전히 지켰을 때만** 성립한다. 에이전트가
  일부 명령을 `run.sh` 밖에서 실행하면 그 호출은 로그에 남지 않는다. 위 표는 **전면**
  우회만 잡고 **부분** 우회는 잡지 못한다. 따라서 음성 단언은 "그 단계의 명령 시퀀스가
  로그에 온전히 있다는 전제 아래"로만 해석하고, 보고서에 그 전제를 명시한다.
- **인용 부호 주의**: 절차의 명령에는 작은따옴표가 들어간다(`-F '#{window_id} …'`).
  래퍼에 넘길 때는 **큰따옴표로 감싼다** — `run.sh "tmux list-panes -a -F '#{window_id}'"`.
  이 안내가 없으면 에이전트가 래퍼를 버리기 쉽다.

### 하네스 정리 (T13)

```bash
rm -rf /tmp/qg-harness
```

## File map

| 파일 | 책임 | 이번 변경 |
|---|---|---|
| `dot_claude/skills/create-worktree/SKILL.md` | Claude Code가 읽는 절차 + Claude 전용 frontmatter | 본문 전면 확장, `argument-hint`·`description` 갱신 |
| `dot_agents/skills/create-worktree/SKILL.md` | Codex·공용 에이전트가 읽는 절차 | **동일 본문**, `description` 갱신. Claude 전용 3줄 없음 |
| `dot_agents/skills/create-worktree/agents/openai.yaml` | Codex UI 메타데이터 | `default_prompt`에 세션 또는 PR 사례 추가 |
| `~/.claude/skills/create-worktree/`, `~/.agents/skills/create-worktree/` | 위의 적용본 | 직접 수정 금지. 경로 한정 `chezmoi apply`가 생성 |
| `dot_claude/skills/move-window-to-session/SKILL.md` | 창 이동 절차 | **읽기만.** 입력 계약(21행)과 `{worktree명}` 정의(104행)·config 쓰기(114행) |
| `dot_claude/skills/remove-worktree/SKILL.md` | worktree 제거 | **읽기만.** `remove`가 브랜치까지 지움(26행), `-k`로 보존(36행) |
| `dot_config/workmux/config.yaml` | pane 레이아웃 | **읽기만.** |
| `/Users/lee-kyu-hwan/code/zambaguni-front/scripts/create-worktree.sh` | git-crypt 래퍼 | **읽기만. 이 저장소 밖의 절대경로다.** Codex 샌드박스에서 읽히지 않을 수 있으며, 그때는 Spec이 인용한 82–98행 서술을 근거로 쓴다 |

## Task dependencies

```
T1 (기준선 캡처, red)
  ↓
T2 (dot_claude SKILL.md 재작성 — 정본) → T3 (dot_agents 복제) → T4 (openai.yaml)
  ↓
T5 (1층 결정적 검사, green)  →  T6 (2층 문서 검토)
  ↓
T7 (경로 한정 chezmoi apply + 무영향 검증)   ← 스모크는 배포본을 실행하므로 선행 필수
  ↓
T7.5 (스모크 하네스 준비)
  ↓
T8 (0차: A부 환경 전제 + B부 산출물)  ← T9와 같은 브랜치. 완전 정리 후 진행
  ↓
T9 (1차: 신규 생성, 입력은 PR URL만)
  ↓
T10 (2차: 같은 세션 재호출)   ← T9의 창이 살아 있어야 성립
  ↓
T11 (3차: 다른 세션 명시 이동)
  ↓
T12 (4차: 레거시 값 + 세션 미명시)
  ↓
T13 (정리·하네스 제거·최종 확인)
```

**셸 연속성 규칙 (PLAN-004).** T9~T12의 `$WT`·`$H`·`$WID` 같은 값은 셸을 넘어 유지되지
않는다. **각 단계는 시작할 때 `workmux list --json`에서 다시 파생한다.** 아래 공통 프리앰블을
매 단계 앞에 붙인다.

```bash
BR=30-enhancement/tmux-open-pr-shortcut
WT=$(workmux list --json | python3 -c "import json,sys;r=[w['path'] for w in json.load(sys.stdin) if w['branch']=='$BR'];print(r[0] if r else '')")
H=$(workmux list --json  | python3 -c "import json,sys;r=[w['handle'] for w in json.load(sys.stdin) if w['branch']=='$BR'];print(r[0] if r else '')")
[ -n "$WT" ] || { echo "FAIL: worktree 없음"; exit 1; }
[ -n "$H" ]  || { echo "FAIL: handle 없음"; exit 1; }
wids() { tmux list-panes -a -F '#{window_id} #{pane_current_path}' \
  | awk -v wt="$WT" '$2==wt||index($2,wt"/")==1{print $1}' | sort -u; }
```

**빈 값 방어 (PLAN-004).** 창 개수는 `wids | grep -c .`로 센다 — `wc -l`은 빈 문자열에도
1을 준다. 비교 전에 `[ -n ... ]`로 비어 있지 않음을 먼저 단언한다.

**적용 범위 (PLAN-014).** 이 프리앰블은 **T9~T13 전부**에 적용한다. T13도 `$H`를 쓰며,
정의되지 않은 `$H`로 `workmux remove "" -k`를 실행하면 파괴적 명령이 빈 인자로 나가고
`git config --get-regexp "^workmux\.worktree\.\."`가 모든 키에 매칭되어 잔여물 검사가
거짓 실패를 낸다.

### `workmux remove`의 확인 프롬프트 처리 (PLAN-016)

`workmux remove`는 **기본적으로 확인 프롬프트를 띄우고**, 이 저장소의 `remove-worktree`
스킬은 그것을 `-f`로 우회하지 말라고 명시한다(`remove-worktree/SKILL.md:29-30`).
비대화형 Bash 호출에서 프롬프트가 뜨면 명령이 정지한다.

**처리 방침**: 정리 단계의 `workmux remove`는 자동 실행하지 않는다. 오케스트레이터가
명령을 만들어 **사용자에게 제시하고, 사용자가 `! workmux remove …` 형태로 직접 실행**한다.
`-f`를 쓰지 않으므로 스킬의 금지 규칙을 지키고, 미커밋 변경 경고도 사용자가 본다.

제시할 명령을 만들 때는 `$H`가 비어 있지 않음을 먼저 확인한다. 정지·타임아웃이 발생하면
아래 롤백 트리거 표의 해당 행을 따른다.

## Tasks

### T1. 기준선 캡처 (red 기록)

```bash
cd /Users/lee-kyu-hwan/code/dotfiles
B=.claude/quality-state/20260827T120102Z-28-35-create-worktree-스킬-3차-실행-pr-링크-입력-a16ed82b/baseline
mkdir -p "$B"
QV=/Users/lee-kyu-hwan/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/scripts/quick_validate.py

# 1) argument-hint (실패 기대)
grep -q 'argument-hint: <branch-name|pr-ref> \[target-session\]' \
  dot_claude/skills/create-worktree/SKILL.md; echo "argument-hint: $?" | tee "$B/red.txt"

# 2) description (양쪽 실패 기대)
for f in dot_agents/skills/create-worktree/SKILL.md dot_claude/skills/create-worktree/SKILL.md; do
  sed -n '3p' "$f" | grep -qiE 'pull request|(^|[^a-z])PR([^a-z]|$)'; echo "desc-PR $f: $?" | tee -a "$B/red.txt"
  sed -n '3p' "$f" | grep -qi 'session'; echo "desc-session $f: $?" | tee -a "$B/red.txt"
done

# 3) openai.yaml (실패 기대)
grep -qE '2-review|pull/' dot_agents/skills/create-worktree/agents/openai.yaml
echo "openai: $?" | tee -a "$B/red.txt"

# 4) 두 본문 diff
diff dot_agents/skills/create-worktree/SKILL.md \
     dot_claude/skills/create-worktree/SKILL.md > "$B/diff-before.txt"; echo "diff: $?" | tee -a "$B/red.txt"

# 5) 1-main 잔존
grep -c -- '1-main' dot_agents/skills/create-worktree/SKILL.md \
                    dot_claude/skills/create-worktree/SKILL.md | tee -a "$B/red.txt"

# 6) quick_validate 기준선 (PLAN-009 — T5가 대조할 좌변)
python3 "$QV" dot_claude/skills/create-worktree > "$B/qv-claude-before.txt" 2>&1; echo "qv-claude: $?" | tee -a "$B/red.txt"
python3 "$QV" dot_agents/skills/create-worktree > "$B/qv-agents-before.txt" 2>&1; echo "qv-agents: $?" | tee -a "$B/red.txt"
```

**기대(red)**: 1·2·3번 exit 1, 4번은 frontmatter 3줄 + 버전 문구 1줄, 5번은 `1-main`
다수, 6번은 둘 다 exit 0이되 `dot_claude`에 Claude 전용 키 안내가 있다.

**실패 처리**: 1·2·3번이 이미 exit 0이면 소스가 예상과 다르므로 중단·보고.

> **workmux 키 기준선은 여기서 잡지 않는다(PLAN-010).** 정리 검증의 기준점은 T8이 잡는
> `$HARNESS/wm-keys-before.txt` 하나이며, T8·T13이 모두 그것과 대조한다. 기준선을 둘
> 두면 어느 쪽이 권위인지 모호해진다.

---

### T2. `dot_claude/skills/create-worktree/SKILL.md` 재작성 (정본)

**frontmatter**

```yaml
---
name: create-worktree
description: <아래 제약을 만족하는 한 줄>
argument-hint: <branch-name|pr-ref> [target-session]
user-invocable: true
allowed-tools: Bash
---
```

`description` 제약: 한 줄, 양쪽 파일 문자열까지 동일, `pull request` 또는 단어 경계의
`PR` 포함, `session` 포함. 예: `Use when creating a git worktree for a branch or a pull
request (PR) review, optionally opening it in a named tmux session`.

**본문에 옮길 절과 Spec 대응**

| SKILL.md 절 | Spec 근거 | 핵심 |
|---|---|---|
| 파라미터 | R1.1–R1.7 | 입력 계약, PR 트리거 3종, 표지 없는 맨 숫자 금지, 자연어 2-튜플 환원, 추측 금지, 3개 이상 중단 |
| 워크트리 식별자 | R2.0 | `handle` 정의, 브랜치·창 이름 유추 금지 근거, 기본 설정에서만 basename과 일치, 4개 하위 키 |
| 세션 선택 | R2.1–R2.6 | 4단계 우선순위, 레거시 정규식, **영속 변경 명령 열거 + 읽기 전용·dry-run 예외**, 명시값 덮어쓰기, 사라진 세션 복구, **갱신 대상 3행 표** |
| 세션 검증 | R3.1–R3.6 | **서버 부재와 세션 부재 구분**, `grep -qxF`, **`has-session` 금지 근거**, **자동 생성 금지** |
| PR 해석 | R4.0–R4.8 | 저장소 확정, 조회 필드, 불일치 중단, 기존 worktree는 생성만 건너뜀, OID 비교, head 확보, 상태 4요소, **`--pr` 정규화** |
| 이름 파생 | R5.1–R5.6 | 짧은 이름, 이슈 번호, PR 번호 우선, 생략, 소문자, 모드별 충돌 재시도 |
| 생성·오픈 경로 | R6.1–R6.10 | 루트 기준 분기, git-crypt add 금지, positional·`--name` 생략, 래퍼 순서, 실패 중단, 세션 변수화, 미지원 조합, HEAD 검증, 경로·handle 확보와 폴백, git-crypt 필터만 있는 경우 |
| 기존 worktree 처리 | R7.0–R7.6 | 존재·경로 판정, 창 탐지 4단계와 저장값 부재·스테일 처리, 분기 4종, `move-window-to-session` 호출 |
| 사후 검증 | R8.1–R8.3 | 실제 창 확인, **분기별 불일치 규칙(아래)**, 보고 항목 |
| 주의사항 | R9.6의 14–16 | 에이전트 자동 실행 안 함, 개발 서버 분리, 레이아웃 위치 |

**SPEC-018 확정 — 사후 검증 절에 세 갈래를 모두 적는다.**

> 실제 창 위치를 확인한 뒤의 처리는 이번 호출이 무엇을 했는지에 따라 다르다.
> - **창을 새로 만들거나 열었으면**: 실제 세션이 선택 세션과 다르면 잘못 만들어진
>   세션과 git config를 함께 정리한다.
> - **창을 옮겼으면**: 최종 위치가 선택 세션과 다르면 이동이 완결되지 않은 것이다.
>   그 사실을 보고하고, config에 잘못된 값을 쓰지 않는다.
> - **창을 옮기지 않았으면**: 실제 세션이 선택 세션과 다른 것이 정상이다. 정리하지
>   않는다. 이때의 `window-session` 갱신은 "세션 선택"의 갱신 대상 표가 관장한다.

**SPEC-022 확정 — 이동 절에 분기 규칙까지 적는다.**

> `move-window-to-session`에 handle과 worktree 경로를 함께 넘긴다. 그 스킬은
> `workmux list`의 PATH basename에서 이름을 파생하므로, 기본 명명이 아니면 handle과
> 어긋날 수 있다. 이동이 끝나면 `workmux.worktree.{handle}.window-session`을 읽는다.
> - 대상 세션과 같으면 정상이다.
> - 다르면 그 스킬이 basename 키에 쓴 것이다. **handle 키를 직접 대상 세션으로 갱신하고
>   그 사실을 보고한다.** 갱신도 실패하면 중단한다.

**`1-main` 사용 제한**: Spec의 허용 3용례만. 금지 5용례는 0건.

**검증(태스크 직후)**

```bash
grep -q 'argument-hint: <branch-name|pr-ref> \[target-session\]' dot_claude/skills/create-worktree/SKILL.md && echo OK-hint
sed -n '3p' dot_claude/skills/create-worktree/SKILL.md | grep -qiE 'pull request|(^|[^a-z])PR([^a-z]|$)' && echo OK-desc-PR
sed -n '3p' dot_claude/skills/create-worktree/SKILL.md | grep -qi 'session' && echo OK-desc-session
```

세 줄이 모두 출력되어야 한다.

---

### T3. `dot_agents/skills/create-worktree/SKILL.md` 동기화

T2의 본문을 그대로 복제, frontmatter는 `name`·`description` 2줄만.

```bash
diff dot_agents/skills/create-worktree/SKILL.md \
     dot_claude/skills/create-worktree/SKILL.md
```

**기대**: `3a4,6`과 뒤따르는 `>` 3줄만. 다른 hunk가 있으면 실패. **인자 순서를 바꾸지
않는다** — 바꾸면 정상 상태가 `4,6d3`으로 나와 기대값과 어긋난다.

---

### T4. `dot_agents/skills/create-worktree/agents/openai.yaml`

```yaml
interface:
  display_name: "Create Worktree"
  short_description: "브랜치 또는 PR용 Git worktree 생성 및 Workmux 윈도우 구성"
  default_prompt: "Use $create-worktree to open https://github.com/owner/repo/pull/1247 in the 2-review session."
```

```bash
grep -qE '2-review|pull/' dot_agents/skills/create-worktree/agents/openai.yaml && echo OK
```

---

### T5. 1층 결정적 검사 (green 기록)

```bash
cd /Users/lee-kyu-hwan/code/dotfiles
B=.claude/quality-state/20260827T120102Z-28-35-create-worktree-스킬-3차-실행-pr-링크-입력-a16ed82b/baseline
QV=/Users/lee-kyu-hwan/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/scripts/quick_validate.py

# AC-59 — T1이 잡은 기준선과 대조 (PLAN-009)
python3 "$QV" dot_claude/skills/create-worktree > /tmp/qv-claude-after.txt 2>&1; echo "qv-claude: $?"
python3 "$QV" dot_agents/skills/create-worktree > /tmp/qv-agents-after.txt 2>&1; echo "qv-agents: $?"
diff "$B/qv-claude-before.txt" /tmp/qv-claude-after.txt; echo "qv-claude diff: $?"
diff "$B/qv-agents-before.txt" /tmp/qv-agents-after.txt; echo "qv-agents diff: $?"

# AC-7
grep -q 'argument-hint: <branch-name|pr-ref> \[target-session\]' dot_claude/skills/create-worktree/SKILL.md; echo "AC-7: $?"

# AC-56 (SPEC-020 확정 정규식)
for f in dot_agents/skills/create-worktree/SKILL.md dot_claude/skills/create-worktree/SKILL.md; do
  sed -n '3p' "$f" | grep -qiE 'pull request|(^|[^a-z])PR([^a-z]|$)' || echo "FAIL PR: $f"
  sed -n '3p' "$f" | grep -qi 'session' || echo "FAIL session: $f"
done
[ "$(sed -n '3p' dot_agents/skills/create-worktree/SKILL.md)" \
  = "$(sed -n '3p' dot_claude/skills/create-worktree/SKILL.md)" ] || echo "FAIL desc 불일치"

# AC-53 / AC-54 / AC-18
diff dot_agents/skills/create-worktree/SKILL.md dot_claude/skills/create-worktree/SKILL.md
grep -qE '2-review|pull/' dot_agents/skills/create-worktree/agents/openai.yaml; echo "AC-54: $?"
grep -n -- '1-main' dot_agents/skills/create-worktree/SKILL.md dot_claude/skills/create-worktree/SKILL.md

# AC-15/16/17 실행 절반 — 부작용 없는 tmux 프로브
tmux -L quality-goal-nonexistent-socket list-sessions; echo "server-absent: $?"          # 1
tmux list-sessions -F '#{session_name}' | grep -qxF -- 'definitely-not-a-session'; echo "no-session: $?"  # 1
tmux has-session -t 2; echo "prefix-2: $?"                                               # 0
tmux has-session -t 2-rev; echo "prefix-2-rev: $?"                                       # 0
tmux list-sessions -F '#{session_name}' | grep -qxF -- '2-rev'; echo "grep-2-rev: $?"     # 1

# AC-60
git diff --check; echo "whitespace: $?"
pre-commit run --all-files; echo "gitleaks: $?"
```

**기대**: `qv-*-after`가 기준선과 **동일**(경고 증가 없음), AC-7·53·54·56 통과, tmux 프로브
5개 종료 코드가 주석과 일치, AC-60 둘 다 통과.

**실패 처리**: 어떤 항목이든 어긋나면 T2~T4로 돌아가 고치고 T5 전체를 다시 실행한다.

---

### T6. 2층 문서 검토

Spec이 `[문서]`로 표시한 기준을 두 SKILL.md에서 확인한다.

| 확인 항목 | 대상 AC | 근거 위치 기록 |
|---|---|---|
| 입력 계약·PR 트리거·맨 숫자 금지·자연어 환원·추측 금지·3개 이상 중단 | AC-1~6 | |
| handle 정의·유추 금지 근거·4개 키 네임스페이스 | AC-8 | |
| 우선순위 4단계(저장값 > 모드 기본값) | AC-10 | |
| 레거시 정규식 판정과 glob 반례 | AC-11 | |
| 영속 변경 명령 열거 + 읽기 전용·dry-run 예외 | AC-12 | |
| 갱신 대상 3행 표 | AC-12b(문서) | |
| 사라진 세션 복구 4단계 | AC-14 | |
| **tmux 서버 부재와 세션 부재 구분 서술** | AC-15(문서) | **PLAN-006** |
| **선택 세션 부재 시 자동 생성 금지 서술** | AC-16(문서) | **PLAN-006** |
| **`has-session` 접두사 함정 근거 서술** | AC-17(문서) | **PLAN-006** |
| `1-main` 허용 3용례만, 금지 5용례 0건 | AC-18 | T5의 grep 출력과 대조 |
| 저장소 확정·조회 필드·불일치 중단·기존 worktree 분기·OID 비교·gh 실패 중단·head 확보 | AC-19~25 | |
| CLOSED·MERGED 4요소 | AC-26 | |
| `--pr {PR번호}` 표기 | AC-27(문서) | |
| 짧은 이름·이슈 번호·생략·소문자·충돌 재시도 | AC-28·29·31·32·33 | |
| 루트 기준 분기·git-crypt add 금지·래퍼 순서·실패 중단·미지원 조합 | AC-34·35·37·38·39 | |
| 경로·handle 확보와 폴백 | AC-41(문서) | |
| git-crypt 필터만 있는 경우 | AC-42 | |
| 흐름에서 worktree 판정이 세션 선택보다 앞 | AC-43 | |
| 창 탐지 4단계와 파생 이름 금지 근거 | AC-44(문서) | |
| 매칭 0건·2건 이상·공백·`cd`·저장값 부재·스테일 | AC-45 | |
| 창 닫힘 시 직접 열기 | AC-46 | |
| 미명시 시 존중(경로 1·2) | AC-48(문서) | |
| 이동 호출 형식 + **SPEC-022 분기 규칙** | AC-49(문서) | |
| **사후 검증 세 갈래**(생성·이동·미이동) | AC-51 | **SPEC-018 확정** |
| 보존 규칙 18개 | AC-57 | 18개 개별 |

**판정**: 각 항목이 두 파일 모두에 있어야 한다. AC-57은 18개를 개별로 세어 누락 0건.

---

### T7. 경로 한정 `chezmoi apply` + 무영향 검증

```bash
cd /Users/lee-kyu-hwan/code/dotfiles

# PLAN-003 — 실패할 수 있는 무영향 검사. 배포된 quality-goal 23개 파일 전체의
# 해시와 mtime을 apply 전후로 비교한다. cmp 한 파일로는 판별력이 없다.
find ~/.claude/skills/quality-goal -type f -exec shasum -a 256 {} \; | sort > /tmp/qg-before.sha
find ~/.claude/skills/quality-goal -type f -exec stat -f '%m %N' {} \; | sort > /tmp/qg-before.mtime
wc -l < /tmp/qg-before.sha    # 23 기대

chezmoi diff ~/.claude/skills/create-worktree ~/.agents/skills/create-worktree

chezmoi apply ~/.claude/skills/create-worktree ~/.agents/skills/create-worktree
echo "apply: $?"

# AC-55 — 소스 ↔ 적용본
cmp dot_claude/skills/create-worktree/SKILL.md ~/.claude/skills/create-worktree/SKILL.md; echo "cmp claude: $?"
cmp dot_agents/skills/create-worktree/SKILL.md ~/.agents/skills/create-worktree/SKILL.md; echo "cmp agents: $?"
cmp dot_agents/skills/create-worktree/agents/openai.yaml ~/.agents/skills/create-worktree/agents/openai.yaml; echo "cmp openai: $?"

# quality-goal 무영향 (해시·mtime 둘 다)
find ~/.claude/skills/quality-goal -type f -exec shasum -a 256 {} \; | sort > /tmp/qg-after.sha
find ~/.claude/skills/quality-goal -type f -exec stat -f '%m %N' {} \; | sort > /tmp/qg-after.mtime
diff /tmp/qg-before.sha /tmp/qg-after.sha;     echo "qg 해시 동일: $?"
diff /tmp/qg-before.mtime /tmp/qg-after.mtime; echo "qg mtime 동일: $?"
```

**기대**: `cmp` 3개 exit 0. quality-goal 해시·mtime `diff` 둘 다 exit 0. **mtime이 바뀌면
내용이 같아도 apply가 파일을 다시 쓴 것이므로 위반으로 본다.**

**실패 처리**: `chezmoi apply`가 "modified since chezmoi last wrote it" 프롬프트를 내면
적용본이 손으로 수정된 것이다. 자동 응답하지 말고 중단·보고한다.

---

### T7.5. 스모크 하네스 준비

위 "스모크 실행 하네스"의 구성 블록을 실행하고, 로그가 비어 있는 상태로 시작하는지
확인한다.

위 "스모크 실행 하네스" 절의 구성 블록과 `newphase()` 정의를 **그대로** 실행한다(생략
부호 없이 그 블록 전체다 — PLAN-018). 그다음 동작을 확인한다.

```bash
/tmp/qg-harness/run.sh "workmux --version"
grep -c . /tmp/qg-harness/cmd.log        # 1 이상 (shim 동작 확인)
grep -q '^workmux --version' /tmp/qg-harness/cmd.log && echo "shim OK"

# PLAN-019: workmux list --json의 필드 이름을 여기서 실측한다.
# 공통 프리앰블과 롤백 루프가 handle·path·branch를 파싱하므로 전제를 먼저 굳힌다.
workmux list --json | python3 -c "
import json,sys
rows=json.load(sys.stdin)
need={'handle','path','branch','is_open','is_main'}
missing=need - set(rows[0].keys()) if rows else need
print('필드 누락:', missing or '없음')
"
```

**기대**: `cmd.log`에 `workmux --version`이 기록되고, 필드 누락이 "없음"이다.
2026-08-27 실측에서 `handle`·`path`·`branch`·`is_open`·`mode`·`is_main`·`project`가
확인되었다.

**실패 처리**: shim이 기록하지 않으면 스모크 실행 기준을 문서 검토로 강등한다. 필드가
누락되면 공통 프리앰블의 파싱을 실제 필드명으로 고친 뒤 진행하고, 고칠 수 없으면 T9~T12를
문서 검토로 강등한다(T8의 폴백 b와 같은 처리 — PLAN-019).

---

### T8. 스모크 0차 — AC-9(환경 전제) + AC-9b(산출물)

**전제 확인 (읽기 전용)**

```bash
PRN=31; BR=30-enhancement/tmux-open-pr-shortcut
OID=9cfc6267ced574945814536710cf1019a37dc354
gh pr view $PRN --repo lee-kyu-hwan/dotfiles --json state,headRefName,headRefOid
git ls-remote origin "refs/pull/$PRN/head"
git worktree list --porcelain | grep -F "refs/heads/$BR" && echo "FAIL: worktree 이미 존재"
git rev-parse --verify "$BR" 2>/dev/null    # 없거나 $OID와 같아야 한다
workmux add --pr $PRN --dry-run
```

2026-08-28 실측: PR #31 OPEN, worktree 없음, 동명 로컬 브랜치가 존재하나 OID가 `$OID`와
**동일**해 R4.4에 걸리지 않는다. 어긋나면 대체 PR로 교체하거나 폴백(b).

**키 기준선 (유일한 권위 — PLAN-010)**

```bash
HARNESS=/tmp/qg-harness
F=pr31-fixture-handle; W=pr31-fixture-window; SLUG=30-enhancement-tmux-open-pr-shortcut
git config --get-regexp '^workmux\.worktree\.' > "$HARNESS/wm-keys-before.txt" || : > "$HARNESS/wm-keys-before.txt"
for k in "$SLUG" "$W" "$F"; do
  git config --get "workmux.worktree.$k.window-session" && echo "FAIL 잔여 키: $k"
done
```

셋 다 exit 1이어야 한다. 하나라도 값이 있으면 이름을 바꾸거나 폴백(b).

**A부 — 환경 전제 (AC-9)**

```bash
workmux add --pr $PRN --name "$F" --target-name "$W" --parent-session 2-review
git config --get "workmux.worktree.$F.window-session";    echo "F: $?"     # 0 + 값
git config --get "workmux.worktree.$SLUG.window-session"; echo "SLUG: $?"  # 1
git config --get "workmux.worktree.$W.window-session";    echo "W: $?"     # 1
```

**픽스처 경로 확보 (PLAN-018)** — B부 프롬프트에 넣을 값이다. 추측하지 않고 읽는다.

```bash
FWT=$(workmux list --json | python3 -c \
  "import json,sys;r=[w['path'] for w in json.load(sys.stdin) if w['handle']=='$F'];print(r[0] if r else '')")
[ -n "$FWT" ] || { echo "FAIL: 픽스처 경로 확보 실패"; exit 1; }
```

**B부 — 산출물 (AC-9b) · 하네스 경유**

`newphase T8B`로 로그를 분리한 뒤, Agent 도구로 `general-purpose` 에이전트를 띄운다.
주는 것은 다음뿐이다. **키 이름을 주지 않는다.**

> 모든 셸 명령을 `/tmp/qg-harness/run.sh "<명령>"` 형태로 실행해라. 명령에 작은따옴표가
> 들어가면 바깥은 큰따옴표로 감싼다.
> `~/.claude/skills/create-worktree/SKILL.md`의 "워크트리 식별자"와 "기존 worktree 처리"
> 절차를 따라, 아래 worktree의 handle과 창 위치를 판정하고 결과만 보고해라.
> worktree 경로: {위에서 확보한 `$FWT` 값}

에이전트 종료 후 로그를 판정한다.

```bash
LOG=/tmp/qg-harness/cmd.log
grep -E '^git config' "$LOG"                      # 실행된 config 명령 전수
grep -cE "workmux\.worktree\.$F\." "$LOG"         # 1 이상 기대
grep -cE "workmux\.worktree\.$SLUG\." "$LOG"      # 0 기대
grep -cE "workmux\.worktree\.$W\." "$LOG"         # 0 기대
grep -cE '^workmux list' "$LOG"                   # 1 이상 (handle을 조회했다는 증거)
```

**판정**: `$F` 기준 조회가 있고 `$SLUG`·`$W` 기준 조회가 0건이며 `workmux list` 호출이
있어야 한다. **`git config` 줄이 하나도 없거나 `workmux list` 호출이 없으면 하네스를
우회한 것이므로 "검증 불가"로 기록한다**(SPEC-019 확정). 통과로 적지 않는다.

**정리 (T9 시작 전 필수) — 브랜치 보존 (PLAN-005)**

```bash
workmux remove "$F" -k          # -k: 로컬 브랜치를 남긴다. 이 브랜치는 사전 존재했다
git worktree list | grep -F "$F" && echo "FAIL 잔여 worktree"
workmux list --json | grep -F "\"$F\"" && echo "FAIL 잔여 handle"
git config --get-regexp "^workmux\.worktree\.$F\."; echo "키 잔여: $?"   # 1 기대
diff <(git config --get-regexp '^workmux\.worktree\.' || :) "$HARNESS/wm-keys-before.txt"; echo "키 원복: $?"
git rev-parse --verify "$BR" >/dev/null 2>&1 || git branch "$BR" "$OID"   # 만약을 위한 복구
```

`-k`를 쓰는 이유: `workmux remove`는 기본적으로 **로컬 브랜치까지 지운다**
(`remove-worktree/SKILL.md:26`). `$BR`은 T8 이전부터 있던 사용자 브랜치이므로 지우면 안
된다. `-k`가 그것을 보존한다(같은 파일 36행).

**폴백(b)**: 픽스처 생성 실패, 전제 위반, 잔여 키 미해소, 하네스 미동작 중 하나라도
발생하면 AC-9·AC-9b를 문서 검토로 강등하고 사유를 보고서에 기록한다.

---

### T9. 스모크 1차 — 신규 생성 (입력은 PR URL만)

**하위 에이전트에게 주는 입력** — 세션명도, 창 이름도, `--pr` 인자 형태도 주지 않는다.

> 모든 셸 명령을 `/tmp/qg-harness/run.sh '<명령>'` 형태로 실행해라.
> `~/.claude/skills/create-worktree/SKILL.md`의 절차를 따라 다음을 처리해라.
> https://github.com/lee-kyu-hwan/dotfiles/pull/31

에이전트 종료 후 오케스트레이터가 관찰한다(공통 프리앰블 먼저 실행).

```bash
grep -E '^workmux add' /tmp/qg-harness/cmd.log         # 실제 호출된 명령줄
git -C "$WT" rev-parse --abbrev-ref HEAD               # == $BR
git -C "$WT" rev-parse HEAD                            # == $OID
tmux list-windows -a -F '#{session_name}:#{window_index} #{window_id} #{window_name}'
git config --get "workmux.worktree.$H.target-window"
wids | grep -c .                                        # 1 기대
```

| 관찰 | 기대 | AC | 왜 조작 불가인가 |
|---|---|---|---|
| 창이 열린 세션 | `2-review` | AC-58 | 입력에 세션명을 주지 않았다 |
| 로그의 `--pr` 인자 | 숫자 `31`만 | AC-27 | 입력은 URL이었다. 숫자면 스킬이 정규화한 것 |
| 창 이름 | `31-`로 시작, `30-`이 아님 | AC-30 | 입력에 이름을 주지 않았다 |
| 로그에 positional·`--name` 없음 | 없음 | AC-36 | 로그가 실제 argv다 |
| worktree 브랜치 | `$BR` | AC-36 | |
| worktree HEAD | `$OID` | AC-40 | |
| handle·경로 | `workmux list --json`에서 읽음 | AC-41 | |
| `target-window` 값 | 실제 창 이름과 일치 | AC-44(b) | |
| 고유 `window_id` | 정확히 1 | AC-44(a) | `grep -c .`로 셈 |
| 창 위치 기록 | `tmux list-windows -a` 출력 보존 | AC-50 | |
| 보고 7항목 | 경로·handle·브랜치·세션·창이름·PR번호·head OID | AC-52 | |

**실패 처리**: HEAD가 `$OID`와 다르면 PR 내용이 없는 worktree이므로 성공으로 보고하지
않고 즉시 정리·보고한다. 로그에 `workmux add`가 없으면 "검증 불가".

---

### T10. 스모크 2차 — 같은 세션 재호출 (중복 창 금지)

공통 프리앰블 실행 후:

```bash
BEFORE=$(wids); [ -n "$BEFORE" ] || { echo "FAIL: 창 없음"; exit 1; }
echo "$BEFORE" | grep -c .    # 1 기대
```

**에이전트 입력** — 이번에는 세션이 검증 대상이 아니라 *입력*이므로 준다. 창 이름은 주지
않는다.

> 모든 셸 명령을 `/tmp/qg-harness/run.sh '<명령>'` 형태로 실행해라.
> `~/.claude/skills/create-worktree/SKILL.md`의 절차를 따라라.
> https://github.com/lee-kyu-hwan/dotfiles/pull/31 을 2-review 세션에 열어줘

```bash
AFTER=$(wids); [ -n "$AFTER" ] || { echo "FAIL: 창 사라짐"; exit 1; }
echo "$AFTER" | grep -c .                      # 1 기대 (증가 없음)
[ "$BEFORE" = "$AFTER" ] && echo "AC-47 OK: window_id 동일"
```

**기대**: 고유 `window_id`가 1개로 유지되고 값이 재호출 전과 같다. 빈 값이면 비교 전에
중단하므로 공허한 통과가 생기지 않는다(PLAN-004).

---

### T11. 스모크 3차 — 다른 세션 명시 이동

**전제 확인 (PLAN-015 — 실행 전 필수)**

```bash
newphase T11
TARGET=3-personal
# (a) 대상 세션이 실재하는가. 스킬은 세션을 만들지 않으므로(AC-16) 없으면 진행 불가
tmux list-sessions -F '#{session_name}' | grep -qxF -- "$TARGET" \
  || { echo "SKIP: $TARGET 없음"; exit 1; }
# (b) 원본 세션의 마지막 창을 옮기면 세션이 소멸하고, detach-on-destroy=on +
#     .zshrc의 exec tmux 때문에 사용자의 터미널 창이 닫힌다
#     (move-window-to-session/SKILL.md:47-48, 199)
SRC_SESS=$(tmux display-message -p -t "$BEFORE3" '#{session_name}')
N=$(tmux list-windows -t "$SRC_SESS" -F '#{window_index}' | grep -c .)
[ "$N" -ge 2 ] || { echo "SKIP: $SRC_SESS 창이 $N개 — 옮기면 세션 소멸·터미널 닫힘"; exit 1; }
```

2026-08-28 실측: `3-personal` 존재, `2-review` 창 9개 → 두 조건 모두 충족. 실행 시점에
어긋나면 **다른 기존 세션으로 대상을 바꾸거나** 이 단계를 건너뛰고 AC-49·AC-13을 문서
검토로 강등하며 사유를 보고서에 남긴다.

```bash
BEFORE3=$(wids); [ -n "$BEFORE3" ] || { echo "FAIL"; exit 1; }
```

**에이전트 입력**

> 모든 셸 명령을 `/tmp/qg-harness/run.sh '<명령>'` 형태로 실행해라.
> `~/.claude/skills/create-worktree/SKILL.md`의 절차를 따라라.
> https://github.com/lee-kyu-hwan/dotfiles/pull/31 을 3-personal 세션으로 옮겨줘

```bash
AFTER3=$(wids); [ -n "$AFTER3" ] || { echo "FAIL"; exit 1; }
[ "$BEFORE3" = "$AFTER3" ] && echo "AC-49 OK: 재생성 아님(window_id 동일)"
tmux display-message -p -t "$AFTER3" '#{session_name}'     # 3-personal 기대
git config --get "workmux.worktree.$H.window-session"      # 3-personal 기대 (AC-13)
grep -E 'move-window|display-message' /tmp/qg-harness/cmd.log   # 이동 경로를 탔다는 증거
```

**기대**: 창이 `3-personal`로 이동, `window_id`가 T9와 동일(이동이지 재생성이 아님),
`window-session`이 `3-personal`로 갱신.

---

### T12. 스모크 4차 — 레거시 저장값 + 세션 미명시 (R2.6·R7.4)

SPEC-011이 지적한 경로를 실제로 만든다. **이 Plan에서 가장 중요한 실행 검증이다.**

```bash
git config "workmux.worktree.$H.window-session" legacy      # 형식 불만족 값을 심는다
WID4=$(wids); [ -n "$WID4" ] || { echo "FAIL"; exit 1; }
SESS_BEFORE=$(tmux display-message -p -t "$WID4" '#{session_name}')
[ -n "$SESS_BEFORE" ] || { echo "FAIL: 세션 확인 불가"; exit 1; }
```

**에이전트 입력** — 세션을 주지 않는다. 이것이 우선순위 2를 건너뛰게 만드는 조건이다.

> 모든 셸 명령을 `/tmp/qg-harness/run.sh '<명령>'` 형태로 실행해라.
> `~/.claude/skills/create-worktree/SKILL.md`의 절차를 따라라.
> https://github.com/lee-kyu-hwan/dotfiles/pull/31

```bash
WID4_AFTER=$(wids)
SESS_AFTER=$(tmux display-message -p -t "$WID4" '#{session_name}')
STORED=$(git config --get "workmux.worktree.$H.window-session")
[ "$WID4" = "$WID4_AFTER" ] && [ "$SESS_BEFORE" = "$SESS_AFTER" ] && echo "AC-48 OK: 창 불이동"
[ -n "$STORED" ] && [ "$STORED" = "$SESS_AFTER" ] \
  && echo "AC-12b OK: 실제 세션으로 갱신" \
  || echo "AC-12b FAIL: stored=$STORED actual=$SESS_AFTER"
```

**기대**: 창이 옮겨지지 않고(`window_id`·세션 불변), `window-session`이 `2-review`
(우선순위 3)가 **아니라** 창의 실제 세션(`3-personal`)으로 갱신된다.

`2-review`로 바뀌면 SPEC-011의 결함이 남은 것이므로 **실패**다.

---

### T13. 정리·하네스 제거·최종 확인

**공통 프리앰블을 먼저 실행한다(PLAN-014).** `$H`가 비어 있으면 아래 어떤 명령도 실행하지
않는다.

```bash
HARNESS=/tmp/qg-harness; BR=30-enhancement/tmux-open-pr-shortcut
OID=9cfc6267ced574945814536710cf1019a37dc354
# ↑ 공통 프리앰블로 $WT·$H를 재파생하고 [ -n "$H" ] 가드를 통과한 뒤에만 진행

# PLAN-016: 아래 remove는 자동 실행하지 않는다. 사용자에게 제시해 직접 실행하게 한다.
echo "사용자 실행 필요:  ! workmux remove \"$H\" -k"
# (사용자 실행 완료 후 아래 검증을 이어간다)

git worktree list
workmux list --json
tmux list-windows -a -F '#{session_name}:#{window_index} #{window_name}'
git config --get-regexp "^workmux\.worktree\.$H\."; echo "키 잔여: $?"   # 1 기대
diff <(git config --get-regexp '^workmux\.worktree\.' || :) "$HARNESS/wm-keys-before.txt"; echo "키 원복: $?"

# 사전 존재하던 브랜치 확인·복구
git rev-parse --verify "$BR" >/dev/null 2>&1 && echo "브랜치 보존됨" || git branch "$BR" "$OID"

# 하네스 제거
rm -rf "$HARNESS"

# 소스 변경 범위 (허용 3파일 외 0건)
git status --short
git diff --stat
```

**기대**: worktree·창·키 잔여 0건, 사전 브랜치 보존, `git status`에 허용 3파일과 산출물
디렉터리만 표시.

## Verification commands

| # | 명령 | 기대 | 단계 |
|---|---|---|---|
| 1 | `diff $B/qv-claude-before.txt /tmp/qv-claude-after.txt` | exit 0 (경고 증가 없음) | T5 |
| 2 | `diff $B/qv-agents-before.txt /tmp/qv-agents-after.txt` | exit 0 | T5 |
| 3 | `grep -q 'argument-hint: ...'` | exit 0 | T5 |
| 4 | `sed -n '3p' {두 파일} \| grep -qiE 'pull request\|(^\|[^a-z])PR([^a-z]\|$)'` | 양쪽 exit 0 | T5 |
| 5 | `sed -n '3p'` 두 파일 문자열 비교 | 동일 | T5 |
| 6 | `diff dot_agents/... dot_claude/...` | `3a4,6` + `>` 3줄만 | T5 |
| 7 | `grep -qE '2-review\|pull/' openai.yaml` | exit 0 | T5 |
| 8 | `grep -n -- '1-main' {두 파일}` | 허용 3용례만 | T5+T6 |
| 9 | `tmux -L quality-goal-nonexistent-socket list-sessions` | exit 1 + `error connecting to` | T5 |
| 10 | `... \| grep -qxF -- 'definitely-not-a-session'` | exit 1 | T5 |
| 11 | `tmux has-session -t 2` / `-t 2-rev` | 둘 다 exit 0 | T5 |
| 12 | `... \| grep -qxF -- '2-rev'` | exit 1 | T5 |
| 13 | `git diff --check` | exit 0 | T5 |
| 14 | `pre-commit run --all-files` | 통과 | T5 |
| 15 | `chezmoi diff {두 경로}` | 예상 변경만 | T7 |
| 16 | `chezmoi apply {두 경로}` | exit 0, 프롬프트 없음 | T7 |
| 17 | `cmp` 3쌍 | 모두 exit 0 | T7 |
| 18 | quality-goal 23개 파일 해시·mtime `diff` | 둘 다 exit 0 | T7 |
| 19 | `/tmp/qg-harness/run.sh 'workmux --version'` 후 `grep -c . cmd.log` | 1 이상 | T7.5 |
| 20 | 0차 A부 프로브 3개 | `$F` 0, `$SLUG`·`$W` 1 | T8 |
| 21 | 0차 B부 로그 grep | `$F` ≥1, `$SLUG`·`$W` 0, `workmux list` ≥1 | T8 |
| 22 | 1차 관찰 11항목 | T9 표 | T9 |
| 23 | 2차 `window_id` 비교 | 비어 있지 않고 1개, 값 동일 | T10 |
| 24 | 3차 세션·`window_id`·config | `3-personal`, 동일 id, 갱신됨 | T11 |
| 25 | 4차 `stored == actual` | 실제 세션으로 갱신 | T12 |
| 26 | 정리 후 잔여물·브랜치·키 | 0건, 브랜치 보존, 키 원복 | T13 |

### 검증 카테고리 상태

| 카테고리 | 상태 | 근거 |
|---|---|---|
| 표적 테스트·전체 스위트·타입 체크·빌드 | `not configured` | `package.json`·`Makefile`·`justfile`·`.github/workflows` 부재 |
| 린트 | `not configured` | `.pre-commit-config.yaml`에 gitleaks 훅만 |
| E2E·수동 | **T8~T13에서 수행** | 스모크 0~4차 |

## Rollout and rollback

### 롤아웃 순서

1. 소스 3파일 수정(T2~T4) — 배포본 무영향
2. 결정적 검사·문서 검토 통과(T5·T6)
3. **경로 한정** `chezmoi apply`(T7) — 이 시점부터 배포본이 새 절차로 바뀐다
4. 하네스 준비(T7.5) → 스모크(T8~T12)
5. 정리(T13)

### 배포 영향

- **다른 세션이 `create-worktree`를 실행 중이면 T7 시점에 절차가 바뀐다.** 대화형 호출이라
  실행 중 교체 위험은 낮지만 승인 시점에 알린다.
- **quality-goal 배포본 23개 파일은 건드리지 않는다.** 검증 18번이 해시·mtime으로 확인한다.
- **커밋하지 않는다.**

### 롤백 트리거와 절차

| 트리거 | 절차 |
|---|---|
| T5·T6 실패 | 배포 전이므로 소스만 되돌린다 |
| T7의 `cmp` 실패 또는 quality-goal 해시·mtime 변경 | 즉시 전체 롤백 |
| T8~T12 중 스킬 결함 발견 | 스모크 정리(브랜치 보존 포함) 후 전체 롤백 |
| 스모크가 다른 세션의 worktree·창을 건드림 | 즉시 중단, 상태 그대로 보고. 자동 복구 금지 |
| **`workmux remove`가 프롬프트로 정지·타임아웃** | 자동 실행하지 않으므로 원칙적으로 발생하지 않는다. 그래도 정지하면 그 호출을 중단하고 사용자에게 `! workmux remove … -k` 실행을 요청한다. 픽스처가 남아 있으면 T9를 시작하지 않는다 |
| **원본 세션이 소멸(마지막 창 이동)** | T11 전제 확인이 막는다. 그럼에도 발생하면 즉시 중단하고 보고한다. `detach-on-destroy=on` + `.zshrc`의 `exec tmux` 때문에 사용자 터미널이 닫혔을 수 있으므로 자동 복구를 시도하지 않고 상태를 그대로 알린다 |
| **tmux resurrect 스냅샷 변경** | `move-window-to-session`이 4단계에서 즉시 저장한다. 이는 그 스킬의 정상 동작이며 되돌리지 않는다. 스모크가 공유 tmux 상태를 바꿨다는 사실을 보고서에 기록한다 |

```bash
# 전체 롤백 — 소스 복원 + 적용본 복원 + 스모크 잔여물 정리 + 사전 브랜치 복구
BR=30-enhancement/tmux-open-pr-shortcut
OID=9cfc6267ced574945814536710cf1019a37dc354

# 1) 스모크 잔여물 (있으면) — 브랜치를 지우지 않는 -k 를 쓴다
for h in $(workmux list --json | python3 -c \
  "import json,sys;print(' '.join(w['handle'] for w in json.load(sys.stdin) if w['branch']=='$BR'))"); do
  workmux remove "$h" -k
done
git rev-parse --verify "$BR" >/dev/null 2>&1 || git branch "$BR" "$OID"

# 2) 소스 복원
git checkout -- dot_claude/skills/create-worktree dot_agents/skills/create-worktree

# 3) 적용본 복원 (경로 한정)
chezmoi apply ~/.claude/skills/create-worktree ~/.agents/skills/create-worktree
cmp dot_claude/skills/create-worktree/SKILL.md ~/.claude/skills/create-worktree/SKILL.md

# 4) 하네스 제거
rm -rf /tmp/qg-harness
```

데이터 마이그레이션이 없으므로 롤백은 파일 복원과 worktree 정리로 끝난다. **모든 제거
경로가 `-k`와 브랜치 복구를 짝지어 갖는다**(PLAN-005).

## Acceptance-criteria traceability

| 기준 | 태스크 | 검증 명령·증거 | 기대 결과 |
|---|---|---|---|
| AC-1 | T2·T3 | T6 문서 검토 | 입력 계약·첫 인자 질문이 두 파일에 존재 |
| AC-2 | T2·T3 | T6 | positional 3개 이상 중단 |
| AC-3 | T2·T3 | T6 | PR 트리거 3종 |
| AC-4 | T2·T3 | T6 | 맨 숫자 금지와 번호 공간 근거 |
| AC-5 | T2·T3 | T6 | 2-튜플 환원, 두 개 이상 중단 |
| AC-6 | T2·T3 | T6 | 접두사 보정·추측 금지 |
| AC-7 | T2 | 검증 3 | exit 0 |
| AC-8 | T2·T3 | T6 | handle 정의·유추 금지·4개 키 |
| AC-9 | T8 A부 | 검증 20 | `$F` 0, `$SLUG`·`$W` 1 |
| AC-9b | T8 B부 | 검증 21 | 하네스 로그에 `$F`만, `$SLUG`·`$W` 0건 |
| AC-10 | T2·T3 | T6 | 저장값이 모드 기본값보다 위 |
| AC-11 | T2·T3 | T6 | 정규식과 glob 반례 |
| AC-12 | T2·T3 | T6 | 금지 4개 열거 + 예외 |
| AC-12b | T2·T3 + T12 | T6 + 검증 25 | 3행 표 + `stored == actual` |
| AC-13 | T11 | 검증 24 | `window-session` == `3-personal` |
| AC-14 | T2·T3 | T6 | 복구 4단계 |
| AC-15 | T2·T3 + T5 | 검증 9 + T6 | exit 1 + `error connecting to`, **문서에 구분 서술** |
| AC-16 | T2·T3 + T5 | 검증 10 + T6 | exit 1, **문서에 자동 생성 금지** |
| AC-17 | T2·T3 + T5 | 검증 11·12 + T6 | 0/0/1, **문서에 함정 근거** |
| AC-18 | T5·T6 | 검증 8 | 허용 3용례만 |
| AC-19 | T2·T3 | T6 | 입력 형태별 표와 폴백 |
| AC-20 | T2·T3 | T6 | 조회 필드와 소비처 |
| AC-21 | T2·T3 | T6 | 불일치 중단과 두 값 출처 |
| AC-22 | T2·T3 | T6 | 생성만 건너뛰고 창 처리로 |
| AC-23 | T2·T3 | T6 | OID 비교 후 중단 |
| AC-24 | T2·T3 | T6 | 추측 없이 중단 |
| AC-25 | T2·T3 | T6 | pull ref fetch와 래퍼 미호출 |
| AC-26 | T2·T3 | T6 | 4요소 |
| AC-27 | T2·T3 + T9 | T6 + 검증 22 | 문서 `--pr {PR번호}` + **로그의 실제 인자가 숫자** |
| AC-28 | T2·T3 | T6 | 마지막 `/` 뒤 |
| AC-29 | T2·T3 | T6 | 맨 앞 숫자 또는 `ZF-숫자` |
| AC-30 | T9 | 검증 22 | 창 이름이 `31-`, 입력에 이름 없음 |
| AC-31 | T2·T3 | T6 | `--target-name` 생략 |
| AC-32 | T2·T3 | T6 | 소문자 정규화 |
| AC-33 | T2·T3 | T6 | 모드별 재시도 |
| AC-34 | T2·T3 | T6 | 루트 기준 분기 |
| AC-35 | T2·T3 | T6 | git-crypt에 래퍼만 |
| AC-36 | T9 | 검증 22 | 로그에 positional·`--name` 없음, 브랜치가 `$BR` |
| AC-37 | T2·T3 | T6 | 확보 → 래퍼 → open |
| AC-38 | T2·T3 | T6 | 실패·권한 시 창 안 엶 |
| AC-39 | T2·T3 | T6 | 미지원 조합 예외 |
| AC-40 | T9 | 검증 22 | HEAD == `$OID` |
| AC-41 | T2·T3 + T9 | T6 + 검증 22 | 폴백 서술 + `workmux list --json`으로 확보 |
| AC-42 | T2·T3 | T6 | 필터만 있으면 확인 후 진행 |
| AC-43 | T2·T3 | T6 | worktree 판정이 세션 선택보다 앞 |
| AC-44 | T2·T3 + T9 | T6 + 검증 22 | 4단계 탐지 + 고유 `window_id` 1 + `target-window` 일치 |
| AC-45 | T2·T3 | T6 | 0건·2건·공백·`cd`·부재·스테일 |
| AC-46 | T2·T3 | T6 | 닫힘 시 직접 열기 |
| AC-47 | T10 | 검증 23 | 비어 있지 않고 1개, 값 동일 |
| AC-48 | T2·T3 + T12 | T6 + 검증 25 | 문서 경로 1·2 + 창 불이동 |
| AC-49 | T2·T3 + T11 | T6 + 검증 24 | 호출 형식·SPEC-022 분기 규칙 + 동일 `window_id` |
| AC-50 | T9 | 검증 22 | `tmux list-windows -a` 출력 보존 |
| AC-51 | T2·T3 | T6 | **사후 검증 세 갈래**(생성·이동·미이동) |
| AC-52 | T9 | 검증 22 | 보고 7항목 |
| AC-53 | T3 | 검증 6 | `3a4,6` + `>` 3줄 |
| AC-54 | T4 | 검증 7 | exit 0 |
| AC-55 | T7 | 검증 17 | `cmp` 3쌍 exit 0 |
| AC-56 | T2·T3 | 검증 4·5 | 양쪽 exit 0 + 동일 |
| AC-57 | T2·T3 | T6 | 18개 누락 0건 |
| AC-58 | T9 | 검증 22 | 창이 `2-review`, 입력에 세션 없음 |
| AC-59 | T5 | 검증 1·2 | 기준선과 동일 |
| AC-60 | T5 | 검증 13·14 | 둘 다 통과 |

**전수 확인**: Spec의 62개 기준이 모두 위 표에 있고 각각 구현 태스크와 검증 명령·증거를
갖는다. 미대응 기준 없음.

### 알려진 검증 한계

| 항목 | 한계 | 사유 |
|---|---|---|
| AC-37 (git-crypt 래퍼 경로) | 문서 검토만 | 실제 검증은 업무 저장소에 1~2GB 부작용. 래퍼 82–98행을 직접 읽어 근거 확보 |
| SPEC-022 분기(basename ≠ handle) | 문서 검토만 | 기본 명명에서 둘이 같아 스모크로 발동시킬 수 없다 |
| 실패 상황 기준(fetch 실패·저장소 불일치·래퍼 부재 등) | 문서 검토만 | 인위 조성이 다른 기준의 판정을 흐린다 |

## Codex 핸드오프 계약

`codex exec` (standard: `gpt-5.6-terra`, effort high).

- **허용 경로**: 위 3파일만.
- **읽기 허용**: 이 Plan, Spec, 현행 두 SKILL.md, `move-window-to-session/SKILL.md`,
  `remove-worktree/SKILL.md`, `dot_config/workmux/config.yaml`.
  `/Users/lee-kyu-hwan/code/zambaguni-front/scripts/create-worktree.sh`는 **이 저장소
  밖**이라 샌드박스에서 읽히지 않을 수 있다. 읽을 수 없으면 Spec이 인용한 82–98행 서술을
  근거로 쓴다(PLAN-011).
- **보존**: initial dirty path 2개 디렉터리를 바이트 단위로 유지.
- **금지**: 커밋·푸시, 인자 없는 `chezmoi apply`, 샌드박스 우회 플래그.
- **결과 계약**: `changed_files`, 실행 명령과 종료 코드, Plan 이탈, 남은 우려.
- **범위**: **T2~T4(문서 작성)만.** T5 이후의 검증·배포·스모크는 오케스트레이터가 직접
  수행한다 — 스모크는 tmux·worktree 부작용을 만들고 다른 세션과 공유 자원을 건드리므로
  샌드박스 안에서 실행하지 않는다.
