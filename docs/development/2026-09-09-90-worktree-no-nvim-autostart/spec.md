# Quality Goal Specification

- Task ID: 90-worktree-no-nvim-autostart
- Mode: standard
- Status: Draft
- Created: 2026-09-09
- Updated: 2026-09-09
- Source goal: #90 — 새 worktree 창의 0번 페인에서 nvim 자동 실행을 없앤다.

## Problem and context

`create-worktree`가 전역 workmux 설정을 사용해 창을 만들면 0번 페인에서 nvim이 자동 실행된다. 사용자는 이 페인을 worktree 경로의 빈 셸로 사용하려 하므로, 매번 nvim을 종료해야 한다.

저장소의 `dot_config/workmux/config.yaml`은 첫 pane에 `command: nvim`을 두고, 1·2번 pane은 command가 없는 상태다. workmux 0.1.248 문서의 pane 옵션 표에서 command 기본값은 Shell이며, 실측으로 command를 생략한 1·2번 pane은 빈 셸이다. 이 source 설정을 쓰는 `workmux add`와 `workmux open`으로 앞으로 만드는 창이 영향을 받는다. 프로젝트별 `.workmux.yaml`은 없다.

두 `create-worktree` 스킬의 본문은 바이트 동일하고, Claude 전용 frontmatter에만 세 줄이 더 있다. `executable_tmux-stack-layout`의 3-pane 분기는 현재 workmux 배치를 설명하지만 nvim 자동 실행을 전제하는 주석을 포함한다. 이 작업은 네 source 파일의 설정·문언만 동기화한다.

## Goals

- 앞으로 workmux가 이 전역 source 설정으로 만드는 3-pane 창의 0번 pane을 빈 셸로 연다.
- 좌측 전체 높이 + 우측 상하, 1번 pane focus, 3-pane 구성은 유지한다.
- 네 변경 대상 어디에도 nvim 자동 실행을 전제하는 문언을 남기지 않고, 두 스킬 본문의 바이트 동일성을 유지한다.

## Non-goals

- pane 수, 배치, split 방향, focus 대상의 변경.
- Claude·Codex 자동 실행 도입. 이슈 #9에서 확인한 프로세스 증식(에이전트당 400MB/55MB) 때문에 계속 자동 실행하지 않는다.
- `status_format`, `base_branch`, `nerdfont`를 포함한 다른 workmux 설정의 변경.
- 이미 열려 있는 창·pane의 소급 적용, 기존 nvim·에이전트 프로세스 종료 또는 재구성. 이 변경은 앞으로 만들어지는 창에만 적용된다.
- nvim 자체 제거 또는 사용자의 수동 실행 제한.
- `docs/development/2026-08-27-*` 과거 기록의 소급 수정.
- `workmux merge`·`remove` 등 다른 workmux 동작 변경.
- 이 워크플로우에서 `chezmoi apply`, 머지, main 브랜치 변경. 배포본 `~/.config/workmux/config.yaml`과 다른 worktree(#42·#85·#79)는 변경하지 않는다.

## Requirements

- **R1.1** `dot_config/workmux/config.yaml`의 첫 pane을 빈 매핑 `- {}`로 남겨 command를 생략하고, 이로써 0번 pane이 workmux의 Shell 기본값으로 worktree 경로의 빈 셸이 되게 한다. 첫 pane에는 `split` 키를 추가하지 않으며, 나머지 두 pane의 horizontal/vertical split과 1번 pane focus는 현행대로 유지한다. 레이아웃 및 자동 실행 설명 주석도 세 pane이 빈 셸임을 반영한다.
- **R2.1** `dot_claude/skills/create-worktree/SKILL.md`와 `dot_agents/skills/create-worktree/SKILL.md`의 해당 주의사항을 "어떤 프로그램도 자동 실행하지 않으며 세 pane 모두 빈 셸"이라는 사실로 같은 내용으로 고치고, 두 본문을 바이트 동일하게 유지한다. Claude 전용 frontmatter의 기존 세 줄만 차이로 남긴다.
- **R3.1** `dot_local/bin/executable_tmux-stack-layout`의 3-pane 분기 주석에서 nvim 자동 실행 전제를 제거하고, workmux 기본 배치가 좌 1개(세로 전체)와 우 상하 2개이며 행 단위 배치에서는 좌측 pane 높이가 절반이 된다는 확인된 사실로 열 단위 배치 근거를 다시 쓴다. 실행 코드는 한 줄도 변경하지 않는다.
- **R4.1** 작업 시작 baseline 커밋 `9ff32a30c9498df007ec5dfa558a442cc7841be1`과 비교해 Git이 보고하는 변경 경로는 네 source 파일 및 이 문서 산출물 디렉터리뿐이고, source config의 `status_format: false`, `base_branch: auto`, `nerdfont: true`를 보존한다. 이 비교는 staged·committed·untracked 상태를 모두 포함한다.

## Acceptance criteria

- **AC-1** source YAML의 `panes` 값은 정확히 `[{}, {"split": "horizontal", "focus": true}, {"split": "vertical"}]`이며, 첫 항목에 `command` 또는 `split` 키가 없다. [실행](CMD-1)
- **AC-2** 저장소 source 설정은 현재 설치된 workmux 파서로 `workmux add --dry-run --config`를 수행해 성공한다. 이 검사는 파싱만 판정하며 pane 레이아웃이 dry-run 출력에 없다는 사실을 동작 증명으로 오용하지 않는다. [실행](CMD-2)
- **AC-3** 네 변경 대상에는 `command: nvim`, `nvim만 실행`, `좌 nvim`, `우상 claude`, `우하 codex`, `nvim이 상단` 전제가 없고, source config의 레이아웃·자동 실행 주석 블록과 두 스킬의 해당 주의사항 항목은 모든 pane이 빈 셸이고 어떤 프로그램도 자동 실행하지 않는다는 정확한 기대 문언과 일치한다. [실행](CMD-3)
- **AC-4** 두 create-worktree 스킬의 frontmatter 뒤 본문은 바이트 동일하고, frontmatter 차이는 Claude 문서에만 있는 `argument-hint`, `user-invocable`, `allowed-tools` 세 줄뿐이다. [실행](CMD-4)
- **AC-5** `- 패인 3개:`부터 다음 `- 패인` 항목 전까지의 주석 블록은 좌측 전체 높이 + 우측 상하의 workmux 배치, 행 단위 배치 시 좌측 pane 높이 절반, 그리고 이 키의 레이아웃 복구 역할을 명시하며 nvim을 언급하지 않는다. [실행](CMD-5)
- **AC-6** 구현 후 baseline `9ff32a30c9498df007ec5dfa558a442cc7841be1`과 비교한 `executable_tmux-stack-layout`의 diff에는 주석(`#`) 줄만 있고 실행 코드 변경이 없다. [실행](CMD-6)
- **AC-7** source config는 첫 pane이 빈 매핑인 상태에서 `status_format: false`, `base_branch: auto`, `nerdfont: true`를 정확히 보존한다. [실행](CMD-7)
- **AC-8** 구현 후 baseline `9ff32a30c9498df007ec5dfa558a442cc7841be1` 대비 Git이 보고하는 변경 경로는 네 source 파일 또는 `docs/development/2026-09-09-90-worktree-no-nvim-autostart/` 아래 문서 산출물뿐이며, 네 source 파일은 모두 변경 집합에 있다. [실행](CMD-8)

## Requirements traceability

This table maps every requirement to acceptance criteria and the judgement method that proves the mapping.

| Requirement | Acceptance criteria | Judgement method |
|---|---|---|
| R1.1 | AC-1, AC-2, AC-3 | CMD-1의 YAML 구조 단언, CMD-2의 실제 workmux 파싱, CMD-3의 문언 검사 |
| R2.1 | AC-3, AC-4 | CMD-3의 문언 검사, CMD-4의 바이트·frontmatter 불변식 검사 |
| R3.1 | AC-3, AC-5, AC-6 | CMD-3의 전제 문언 검사, CMD-5의 주석 사실 검사, CMD-6의 diff 검사 |
| R4.1 | AC-7, AC-8 | CMD-7의 보존 키 단언, CMD-8의 baseline 기준 변경 경로 검사 |

## Architecture

변경 경계는 chezmoi source 네 파일과 이 작업의 문서 산출물 디렉터리다. `dot_config/workmux/config.yaml`은 workmux가 창을 만들 때 해석하는 pane 선언을 제공하고, 첫 목록 항목은 창 자체를 나타내므로 split 없이 남는다. `dot_claude`와 `dot_agents`의 스킬은 동일한 작업 절차를 설명하는 문서 쌍이며, 서로 다른 frontmatter는 도구별 메타데이터 경계다. `dot_local/bin/executable_tmux-stack-layout`은 workmux가 만든 3-pane 배치를 복구할 수 있는 tmux 레이아웃 스크립트이고, 이번 변경 범위는 그 설명 주석이다. baseline SHA 기준 diff와 untracked 경로를 함께 검사해 이 경계를 staged·committed 상태와 무관하게 강제한다.

## Interfaces and data flow

앞으로의 흐름은 `create-worktree` → `workmux add` 또는 `workmux open` → workmux가 source에서 배포된 전역 설정을 해석 → 3-pane 창 생성이다. 첫 pane의 `- {}`에는 command가 없으므로 workmux의 Shell 기본값이 적용되고, 나머지 pane 선언은 기존 split/focus 계약을 유지한다.

검증 흐름은 source YAML 구조 단언 → 별도 임시 git 저장소에서 `workmux add --dry-run --config <source>` 파싱 → 문서 및 body 동일성 검사 → 스크립트 주석·baseline diff 검사 → 다른 config 키·전체 변경 경로 검사다. dry-run은 worktree를 만들지 않지만 레이아웃을 출력하지 않으므로, shell pane 결과는 YAML 구조와 workmux의 문서화된 기본값으로 판단한다. 실제 창 동작은 배포 뒤 사용자가 다음 worktree를 만들 때만 확인한다.

## Failure behavior

YAML 구조가 달라지거나 workmux 파싱이 실패하면 구현은 배포하거나 실제 창을 만들지 않고 실패한 판정 명령의 출력으로 중단한다. dry-run이 성공해도 pane 레이아웃을 출력하지 않으므로, 그 결과만으로 0번 pane의 nvim 부재를 주장하지 않는다.

두 스킬 본문 또는 허용된 frontmatter 차이가 달라지면 문서 동기화 검사에 실패한다. 스크립트의 baseline diff에 주석 이외의 줄이 있으면 코드 변경으로 실패한다. 보존 키 또는 baseline 이후 변경 경로가 허용 범위를 벗어나도 실패한다. 기존 창은 이 작업이 건드리지 않으므로 nvim이 남아 있어도 실패로 해석하지 않는다.

## Security and risk

이 작업은 로컬 설정과 문서의 작은 변경이며 비밀값·외부 서비스·권한 경계를 다루지 않는다. 주된 위험은 전역 설정을 실제로 적용하거나 새 worktree를 만드는 부작용, 또는 3-pane 레이아웃을 우연히 바꾸는 것이다. source만 검사하고 `--dry-run`을 사용하며, 구조 단언과 code-only diff 검사로 이를 완화한다.

배포본은 다른 세션이 사용하므로 읽기 또는 수정 대상으로 삼지 않는다. 이 브랜치에 커밋하는 것은 허용하지만, 머지·`chezmoi apply`·main 브랜치 변경은 금지한다.

## Test strategy

모든 판정 명령은 이 worktree 루트 `/Users/lee-kyu-hwan/code/dotfiles__worktrees/90-fix-worktree-no-nvim-autostart`에서 실행한다. Python을 쓰는 검사에는 `/opt/homebrew/bin/python3`과 `PYTHONDONTWRITEBYTECODE=1`을 사용한다. 대상은 모두 저장소 source 파일이며 `~/.config/workmux/config.yaml`은 판정 대상이 아니다.

실제 창 생성은 하지 않는다. 특히 dry-run 없는 `workmux add`와 `workmux open`은 판정 명령에 포함하지 않는다. CMD-2는 결정적인 `/private/tmp/workmux-config-parse-90` 경로를 비어 있을 때만 만들고 EXIT에서 지워, 저장소 source를 실제 파서로 부작용 없이 검증한다. CMD-6과 CMD-8은 구현 후 실행하며, 작업 시작 baseline은 `9ff32a30c9498df007ec5dfa558a442cc7841be1`이다. 이 두 명령은 baseline과 비교하므로 staged·committed 상태도 판정한다. `.claude/quality-state/`의 Git-ignored 개정 노트는 CMD-8의 Git 보고 범위 밖인 워크플로우 산출물이다. 배포 후 사용자가 다음 worktree를 만들 때의 실제 창 동작은 이 워크플로우 밖에서 확인한다.

판정 명령은 변경 전 baseline 에서 반드시 실패하고 변경 후에 통과해야 한다. 음성 대조가 없으면 그 명령은 채택하지 않는다. 다만 CMD-2와 CMD-4는 변경으로 새로 성립하는 성질이 아니라 변경 전후로 계속 유지돼야 하는 불변식이므로 baseline에서 통과한다. 이 둘의 음성 대조는 변경 전 상태가 아니라 고의로 위반 상태를 만든 입력으로 증명하며, 그 결과를 숨기지 않는다.

| 부류 | CMD와 baseline 종료 코드 | 변경 후 통과 또는 음성 대조 | 실측과 증거 계획 |
|---|---|---|---|
| baseline에서 실패해야 하는 변경 판정 명령 | CMD-1: 1 | 구현 후 종료 코드 0이 필요하다. | baseline 실패 전사가 있으며, 변경 후 통과 전사는 구현 단계에서 첨부한다. |
| baseline에서 실패해야 하는 변경 판정 명령 | CMD-3: 1 | 구현 후 종료 코드 0이 필요하다. | baseline 실패 전사가 있으며, 구현 후에는 `panes:` 앞 config 주석 전체와 두 스킬 `## 주의사항`의 첫 항목이 각각 기대값과 등가여야 한다. |
| baseline에서 실패해야 하는 변경 판정 명령 | CMD-5: 1 | 구현 후 종료 코드 0이 필요하다. | baseline 실패 전사가 있으며, 변경 후 통과 전사는 구현 단계에서 첨부한다. |
| baseline에서 실패해야 하는 변경 판정 명령 | CMD-6: 1 | 구현 후 종료 코드 0이 필요하다. | baseline 실패 전사가 있으며, 변경 후 통과 전사는 구현 단계에서 첨부한다. |
| baseline에서 실패해야 하는 변경 판정 명령 | CMD-7: 1 | 구현 후 종료 코드 0이 필요하다. | baseline 실패 전사가 있으며, 변경 후 통과 전사는 구현 단계에서 첨부한다. |
| baseline에서 실패해야 하는 변경 판정 명령 | CMD-8: 1 | 구현 후 종료 코드 0이 필요하다. | baseline 실패 전사가 있으며, 변경 후 통과 전사는 구현 단계에서 첨부한다. |
| 변경 전후로 유지돼야 하는 불변식 명령 | CMD-2: 0 | `panes[0].split`을 `BROKEN`으로 바꾼 config를 `--config`로 넘긴 음성 대조는 종료 코드 1이며 `Failed to parse config ... unknown variant`를 보고한다. | 정상 환경의 CMD-2는 종료 코드 0으로 실측됐다. read-only 샌드박스에서는 rolling-log 초기화 권한 오류로 `workmux add --dry-run`을 실행할 수 없으므로 판정은 정상 환경에서 수행한다. |
| 변경 전후로 유지돼야 하는 불변식 명령 | CMD-4: 0 | 임시 디렉터리에서 관련 파일만 복제해 agents 본문 끝에 한 줄 추가, claude frontmatter 세 줄 삭제, agents에도 세 줄 추가를 각각 만들면 모두 종료 코드 1이다. | 앞쪽 두 frontmatter 경계만 잘라 본문 바이트 동일성·세 줄 존재·각 키의 Claude 전용성을 검증하므로, 본문의 동일한 Markdown 구분선은 허용한다. 저장소는 변경하지 않았다. |

Spec 심사 시점에는 baseline 전사만 존재한다. 구현 완료 시 baseline 실패 또는 불변식 전사와 변경 후 통과 전사를 함께 증거로 남기며, CMD-2와 CMD-4에는 위 고의 위반 입력의 음성 대조 전사도 함께 보관한다.

라운드 3에서 강화한 단언의 모의 구현 음성 대조는 다음과 같다. 정상 모의 구현은 CMD-3·CMD-4 모두 종료 코드 0이어야 하며, 반례 1~3은 해당 계약 위반을 거부하고 반례 4는 본문 허용 편집을 거부하지 않아야 한다.

| 반례 | 상태 | 명령 | 라운드 2 결과 | 라운드 3 목표 |
|---|---|---|---|---|
| 1 | config에 옛 `# nvim만 자동 실행한다…` 잔존 | CMD-3 | 0 (통과 — 결함) | 1 |
| 2 | 기대 주의사항 뒤에 `단, 첫 pane에서는 편집기가 시작된다.` 추가 | CMD-3 | 0 (통과 — 결함) | 1 |
| 3 | 두 파일에 `user-invocable: false` 개별 추가 | CMD-4 | 0 (통과 — 결함) | 1 |
| 4 | 두 본문 끝에 동일한 `---` 구분선 추가 | CMD-4 | 1 (거짓 실패 — 결함) | 0 |

### 판정 명령 표

| ID | 명령 | 통과 조건 |
|---|---|---|
| CMD-1 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; import yaml; panes = yaml.safe_load(Path("dot_config/workmux/config.yaml").read_text())["panes"]; assert panes == [{}, {"split": "horizontal", "focus": True}, {"split": "vertical"}], panes'` | source YAML의 pane 목록이 빈 첫 pane과 기존 3-pane 배치 계약에 정확히 일치한다. |
| CMD-2 | `set -euo pipefail; scratch=/private/tmp/workmux-config-parse-90; test ! -e "$scratch"; mkdir "$scratch"; trap 'rm -rf "$scratch"' EXIT; git -C "$scratch" init -q -b main; git -C "$scratch" config user.email spec@example.invalid; git -C "$scratch" config user.name spec; git -C "$scratch" commit --allow-empty -qm baseline; (cd "$scratch" && workmux add --dry-run --config /Users/lee-kyu-hwan/code/dotfiles__worktrees/90-fix-worktree-no-nvim-autostart/dot_config/workmux/config.yaml workmux-config-parse-90)` | exit 0. 임시 git 저장소와 source config가 workmux 파서를 통과하고 EXIT에서 임시 경로가 제거된다. |
| CMD-3 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; paths = [Path("dot_config/workmux/config.yaml"), Path("dot_claude/skills/create-worktree/SKILL.md"), Path("dot_agents/skills/create-worktree/SKILL.md"), Path("dot_local/bin/executable_tmux-stack-layout")]; config = paths[0].read_text(); skills = [p.read_text() for p in paths[1:3]]; text = "\n".join(p.read_text() for p in paths); banned = ("command: nvim", "nvim만 자동 실행", "nvim만 실행", "좌 nvim", "우상 claude", "우하 codex", "nvim이 상단"); assert not [s for s in banned if s in text]; config_expected = "# workmux 전역 설정\n# https://workmux.raine.dev\n#\n# 레이아웃: 좌측 pane(세로 전체) / 우측 상단 pane / 우측 하단 pane\n#\n# split 방향은 tmux와 같다 (horizontal=좌우, vertical=위아래).\n# Orca는 반대이므로 혼동하지 않도록 주의.\n#\n# 어떤 프로그램도 자동 실행하지 않는다. 모든 pane은 빈 셸로 열리며,\n# 필요할 때 사용자가 직접 시작한다 — 에이전트는 개당 400MB/55MB를 쓰므로\n# worktree를 만들 때마다 띄우지 않는다."; assert config[:config.index("panes:")].rstrip("\n") == config_expected; expected = "- 에이전트(Claude·Codex)를 포함해 어떤 프로그램도 자동 실행하지 않는다. 레이아웃의 세 pane은 모두 빈 셸이므로 필요할 때 사용자가 직접 시작한다."; normalize = lambda value: " ".join(value.split()); first_item = lambda skill: (lambda notice: notice[notice.index("- "):notice.index("\n- ", notice.index("- ") + 1)])(skill.split("## 주의사항\n", 1)[1]); assert all(normalize(first_item(skill)) == expected for skill in skills)'` | 자동 실행 전제가 없고 `panes:` 앞 config 주석 전체 및 줄바꿈을 정규화한 두 스킬 주의사항 첫 항목이 정확한 교정 문언과 각각 등가다. |
| CMD-4 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; c = Path("dot_claude/skills/create-worktree/SKILL.md").read_bytes(); a = Path("dot_agents/skills/create-worktree/SKILL.md").read_bytes(); assert c.startswith(b"---\n") and a.startswith(b"---\n"); cf, cb = c.split(b"---\n", 2)[1:]; af, ab = a.split(b"---\n", 2)[1:]; description = b"description: Use when creating a git worktree for a branch or a pull request (PR) review, optionally opening it in a named tmux session\n"; extra = b"argument-hint: <branch-name" + bytes([124]) + b"pr-ref> [target-session]\nuser-invocable: true\nallowed-tools: Bash\n"; keys = (b"argument-hint:", b"user-invocable:", b"allowed-tools:"); assert cb == ab; assert description in cf and description in af; assert extra in cf; assert all(not any(line.startswith(key) for line in af.splitlines()) for key in keys); assert cf == af.replace(description, description + extra)'` | 앞쪽 두 frontmatter 경계만으로 두 본문과 허용된 Claude 전용 세 줄의 존재·순서·각 키의 전용성을 단언하며, 본문의 추가 Markdown 구분선은 허용한다. |
| CMD-5 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; lines = Path("dot_local/bin/executable_tmux-stack-layout").read_text().splitlines(); start = next(i for i, line in enumerate(lines) if line == "#   - 패인 3개: 좌 1개(세로 전체) + 우 2개(상하)"); end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("#   - 패인 ")); block = "\n".join(lines[start:end]); required = ("#       workmux 기본 배치(좌 1개(세로 전체) + 우 2개(상하))와 같다.", "#       행 단위로 쌓으면 좌측 패인의 높이가 절반으로 줄어드므로,", "#       이 개수에서는 열 단위로 배치한다.", "#       결과적으로 이 키가 workmux 레이아웃을 복구하는 역할을 한다."); assert all(line in block for line in required); assert "nvim" not in block'` | 내용 경계로 추출한 3-pane 주석 블록이 확인된 배치·기하학·복구 역할만으로 열 단위 근거를 설명하고 nvim을 언급하지 않는다. |
| CMD-6 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'import subprocess; baseline = "9ff32a30c9498df007ec5dfa558a442cc7841be1"; target = "dot_local/bin/executable_tmux-stack-layout"; diff = subprocess.run(["git", "diff", "--unified=0", baseline, "--", target], check=True, capture_output=True, text=True).stdout; changed = [line for line in diff.splitlines() if line[:1] in ("+", "-") and not line.startswith(("+++", "---"))]; assert changed and all(line[1:].startswith("#") for line in changed), changed'` | 구현 후 baseline과 비교한 해당 파일의 변경 줄이 존재하며 모두 주석 줄이다. |
| CMD-7 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'from pathlib import Path; import yaml; data = yaml.safe_load(Path("dot_config/workmux/config.yaml").read_text()); assert data["panes"][0] == {}, data["panes"]; assert {key: data[key] for key in ("status_format", "base_branch", "nerdfont")} == {"status_format": False, "base_branch": "auto", "nerdfont": True}'` | 첫 pane 변경과 무관한 세 source config 키가 현재 기준값으로 보존된다. |
| CMD-8 | `PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3 -c 'import subprocess; baseline = "9ff32a30c9498df007ec5dfa558a442cc7841be1"; sources = {"dot_config/workmux/config.yaml", "dot_claude/skills/create-worktree/SKILL.md", "dot_agents/skills/create-worktree/SKILL.md", "dot_local/bin/executable_tmux-stack-layout"}; docs_prefix = "docs/development/2026-09-09-90-worktree-no-nvim-autostart/"; run = lambda args: subprocess.run(args, check=True, capture_output=True, text=True).stdout.splitlines(); tracked = set(run(["git", "-c", "core.quotePath=false", "diff", "--name-only", baseline])); status = run(["git", "-c", "core.quotePath=false", "status", "--porcelain=v1", "--untracked-files=all"]); untracked = {line[3:] for line in status if line.startswith("?? ")}; changed = tracked.union(untracked); allowed = sources.union({path for path in changed if path.startswith(docs_prefix)}); assert sources <= changed, sorted(sources - changed); assert changed <= allowed, sorted(changed - allowed)'` | 구현 후 staged·committed 변경과 untracked 문서를 합친 경로 집합에 네 source 파일이 모두 있고 allowlist 밖 경로가 없으며 비ASCII 경로도 인용 해제해 판정한다. |

## Decisions

### D1. 첫 pane은 `- {}`로 표현한다

선택: 첫 pane은 빈 매핑 `- {}`로 둔다. `command`가 의도적으로 없다는 점과 목록 항목 자체가 남아 3-pane 구성이 유지된다는 점을 동시에 가장 분명하게 보인다.

대안 `-`(null 항목)은 workmux 0.1.248 파서를 통과하지만, pane 선언인지 누락값인지 읽는 사람에게 모호하다. 대안 `- focus: false`도 파서를 통과하지만 기본값을 불필요하게 명시해 focus가 설계상 바뀐 것처럼 보일 수 있다. 세 후보 모두 파싱 가능했으므로, 선택 근거는 동작 차이가 아니라 가독성·의미 명확성·오해 위험이다.

### D2. 파싱 검증과 pane 결과 검증을 분리한다

`workmux add --dry-run --config <source>`는 source가 전역 전용 키를 포함해 실제 파서에서 유효함을 판정한다. 그러나 dry-run 출력은 worktree 경로·브랜치·base·target만 보여 panes를 표시하지 않는다. 따라서 CMD-2는 파싱 유효성에만 쓰고, CMD-1의 YAML 구조 단언으로 첫 pane에 nvim command가 없고 배치가 유지됨을 판정한다.

### D3. 3-pane 주석의 근거는 검증된 기하학으로 제한한다

새 주석은 workmux의 좌 1개(세로 전체) + 우 상하 2개 배치, 행 단위 배치에서 좌측 pane 높이가 절반이 되는 사실, 그리고 키가 workmux 레이아웃을 복구한다는 기존 설명만 쓴다. 셸 출력이나 편집에 더 유리하다는 확인되지 않은 이유는 추가하지 않는다.
