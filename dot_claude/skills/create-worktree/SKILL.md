---
name: create-worktree
description: Use when creating a git worktree for a branch or a pull request (PR) review, optionally opening it in a named tmux session
argument-hint: <branch-name|pr-ref> [target-session]
user-invocable: true
allowed-tools: Bash
---

# Create Worktree

브랜치 또는 PR의 git worktree를 만들거나 기존 worktree를 열고, 선택한 tmux 세션의
workmux 윈도우로 연결한다. 창과 세션 상태를 추측하지 말고 아래 순서대로 확인한다.

## 실행 순서 요약

1. 입력 파싱(파라미터)
2. PR 모드면 저장소 확정과 PR 해석 → head 브랜치·`headRefOid` 확보
3. 기존 worktree 존재·경로 판정 → handle 확보
4. 창이 있으면 창 탐지(`is_open` → 저장 세션 → `target-window` → pane 경로)
5. 세션 선택(명시값 > 유효·생존 저장값 > 모드 기본값 > 전역 기본값)
6. 세션 검증
7. 이름 파생
8. 분기: 기존 worktree면 창 처리, 없으면 생성·오픈 경로
9. 사후 검증과 보고

아래 절은 주제별로 묶여 있어 이 순서와 배열이 다르다. 실행은 이 순서를 따른다.

## 파라미터

- 첫 번째 positional 인자는 필수인 브랜치명 또는 PR 참조다. 없으면 사용자에게 묻는다.
- 두 번째 positional 인자는 선택 사항이며 정확한 tmux 세션명이다.
- positional 인자가 세 개 이상이면 추측하지 말고 `<branch-name|pr-ref> [target-session]`
  사용법을 안내한 뒤 중단한다.
- PR 모드는 다음 세 형태에서만 선택한다.
  - `https://github.com/{owner}/{repo}/pull/{번호}` 전체 URL
  - `{owner}/{repo}#{번호}`
  - `PR 1313`, `1313번 PR`, `pull request 1313`처럼 번호 앞뒤에 표지가 있는 자연어
- 표지 없는 맨 숫자(`1313`)는 PR로 단정하지 않는다. GitHub의 이슈와 PR은 번호 공간을
  공유하므로 엉뚱한 대상을 checkout할 수 있다. 브랜치로 해석하거나 해석할 수 없으면
  확인한다.
- 자연어 호출은 `(브랜치명|PR 참조, 대상 세션)` 2-튜플로 환원한다. 브랜치/PR 참조가
  둘 이상이거나 세션명이 둘 이상이면 중단하고 확인한다. 자연어가 2-튜플로 환원됐으면
  positional 인자 수 제한을 적용하지 않는다.
- 세션명에 접두사를 붙이거나 현재 세션 목록에서 비슷한 이름을 추측하지 않는다.

## 워크트리 식별자

git config 키의 `{handle}`은 `workmux list --json` 항목의 `handle` 필드다.
브랜치명이나 tmux 창 이름으로 유추하지 않는다. handle은 기본 명명에서는 `path`의
basename과 같을 수 있지만 `worktree_naming`, `worktree_prefix`, `--name`에 따라 달라질
수 있다. 특히 PR 모드의 `--target-name`은 handle과 창 이름을 구조적으로 갈라놓는다.

handle 하나에는 최대 `.mode`, `.target-window`, `.window-session`, `.window-token` 하위
키가 있다. 이 스킬은 `.window-session`만 읽거나 쓰고, `.target-window`는 창 탐지에서만
읽는다. 잘못된 handle로 `git config`를 쓰면 오류 없이 새 섹션이 생기므로 실제 값을
확보하기 전에는 쓰지 않는다.

`workmux list --json`을 쓸 수 없을 때만 worktree 절대경로의 basename을 폴백으로 쓴다.
그 경우 `path` 필드와 대조해 확인하며, 대조할 수 없으면 중단한다.

## 세션 선택

먼저 대상 브랜치의 기존 worktree와 경로를 확인해 handle을 확보한다. 그 후
`SELECTED_SESSION`을 다음 우선순위로 정한다.

1. 이번 호출에서 사용자가 명시한 세션
2. 기존 worktree의 `workmux.worktree.{handle}.window-session`이 `^[0-9]+-.+$`를 만족하고
   실제로 존재할 때의 저장값
3. 모드 기본값: PR 모드면 `2-review`
4. 전역 기본값 `1-main`

저장값은 사용자가 창을 직접 옮긴 기록이고 모드 기본값은 관습이므로, 저장값이 모드
기본값보다 우선한다.

| 명시 세션 | 유효하고 생존한 저장값 | 모드 | 선택 결과 |
| --- | --- | --- | --- |
| `3-personal` | `2-review` | PR | `3-personal` |
| 없음 | `3-personal` | PR | `3-personal` |
| 없음 | 없음 | PR | `2-review` |
| 없음 | 없음 | 브랜치 | 전역 기본값 `1-main` |

저장값은 셸 glob(`[0-9]*-*`)이 아니라 정규식 `^[0-9]+-.+$`로 판정한다. glob의 첫
`*`는 숫자 반복이 아닌 임의 문자열이어서 `1legacy-session`과 `1-`도 통과한다. 예전
마이그레이션에서 남은 값(예: `1-main`이 아닌 형식 밖 값)은 레거시로 취급한다.

선택 세션이 확정되기 전에는 영속 변경을 만드는 `workmux add`, `workmux open`,
`workmux remove`, `workmux close`를 실행하지 않는다. 읽기 전용 `workmux list --json`과
`--dry-run` 조회는 예외다.

명시 세션이 유효한 저장값을 덮었으면 창을 연 뒤 handle의 `window-session`이 명시 세션을
가리키는지 확인하고 다르면 갱신한다. 형식은 유효하지만 사라진 저장 세션이면 다음처럼
복구한다.

1. 사라진 저장값을 사용자에게 알린다.
2. 모드 기본값과 전역 기본값으로 계산한 대안을 제시하고 확인받는다.
3. 확인된 세션으로 진행한다.
4. 세션을 자동 생성하지 않는다.

레거시 또는 사라진 저장값을 고칠 때 기록할 값은 창의 실제 위치로 정한다.

| 상태 | `window-session` 갱신 대상 |
| --- | --- |
| 창이 닫혀 있음 | `SELECTED_SESSION` |
| 창이 열려 있고 명시 세션으로 이동함 | `SELECTED_SESSION` |
| 창이 열려 있으나 이동하지 않음 | 창 탐지로 확정한 실제 세션 |

실제 세션을 확정하지 못했으면 갱신하지 않는다. 세션 미명시 호출에서 열린 창을 옮기지
않는 경우에는 선택값이 아니라 실제 위치를 기록해야 config와 창 위치가 어긋나지 않는다.

## 세션 검증

선택 세션은 영속 workmux 명령 전에 검증한다.

```bash
tmux list-sessions -F '#{session_name}'
```

먼저 종료 코드를 확인한다. exit 1과 `error connecting to ...`는 tmux 서버 부재이므로
세션 부재와 구분해 보고하고 중단한다. 목록 조회가 성공했을 때만 다음처럼 전체 문자열
일치로 확인한다.

```bash
tmux list-sessions -F '#{session_name}' | grep -qxF -- "$SELECTED_SESSION"
```

`tmux has-session -t`는 쓰지 않는다. tmux target은 접두사 매칭을 하므로 `2`나 `2-rev`가
의도치 않은 세션에 매칭될 수 있다. 선택 세션이 없으면 자동 생성하지 않는다. 명시값이면
오타 가능성을 알리고 중단하며, 저장값이면 앞 절의 복구 경로를 따른다. 검증 없이
`--parent-session`에 없는 값을 주면 workmux가 세션을 만들고 config에 영구 저장하는 유령
세션 위험이 있다.

## PR 해석

PR 입력에서는 다음 표로 `{owner}/{repo}`를 확정한다.

| 입력 | `{owner}/{repo}` 출처 |
| --- | --- |
| 전체 PR URL | URL 경로 |
| `{owner}/{repo}#{번호}` | 입력 문자열 |
| 표지가 있는 자연어 | 현재 저장소 |

현재 저장소는 우선 `gh repo view --json owner,name -q '.owner.login + "/" + .name'`으로
구하고, 실패하면 `git remote get-url origin`을 파싱한다. 둘 다 실패하면 중단한다.
입력 저장소와 현재 저장소가 다르면 두 값을 알리고 중단한다.

확정한 저장소에서 다음 네 필드를 조회한다.

```bash
gh pr view {번호} --repo {owner}/{repo} --json number,state,headRefName,headRefOid
```

`number`, `headRefName`, `headRefOid`는 각각 이름 파생과 내용 검증에 쓰고, `state`는
CLOSED·MERGED 처리에 쓴다. `gh`가 없거나 인증·조회에 실패하면 추측하지 말고 중단한다.
CLOSED 또는 MERGED면 상태를 알리고 계속할지 확인한다. 자동 중단하지 않되 head 브랜치가
삭제되어 fetch가 실패할 수 있음을 안내한다.

동일한 head 브랜치의 worktree가 이미 있으면 생성만 건너뛰고 기존 경로의 창 처리로
진행한다. 같은 이름의 로컬 브랜치가 head OID와 다르면 덮어쓰지 않고 중단한다.

래퍼 경로에서 새 worktree를 만들기 전, 로컬 브랜치가 없을 때는 PR head를 확보한다.

```bash
git fetch origin "refs/pull/{PR번호}/head:{head브랜치명}"
git rev-parse --verify "refs/heads/{head브랜치명}"
```

검증 OID가 `headRefOid`와 다르거나 fetch가 실패하면 중단하고 래퍼를 호출하지 않는다.
래퍼는 브랜치를 찾지 못하면 현재 HEAD에서 빈 브랜치를 만들 수 있다.
래퍼가 없는 경로는 `workmux add --pr`가 체크아웃을 직접 하므로 사전 fetch가 필요 없다.
대신 생성 후 `HEAD`가 `headRefOid`와 같은지 검증해 같은 보장을 얻는다.

`workmux add --pr`에는 원시 입력을 넘기지 않는다. 저장소 일치와 PR 조회로 확정한 숫자만
정규화해 넘긴다. 따라서 `{owner}/{repo}#{번호}`와 자연어 표지 입력도 `--pr {PR번호}`가
된다.

## 이름 파생

- 짧은 이름은 브랜치명(또는 PR head 브랜치명)의 마지막 `/` 뒤 부분이다.
  `392-feat/add-partner-chat-enabled`의 짧은 이름은 `add-partner-chat-enabled`다.
- 브랜치 모드의 이슈 번호는 브랜치명 맨 앞의 숫자 또는 `ZF-숫자`만 인식한다.
  `feat/392-add-x`에는 이슈 번호가 없다.
- PR 모드 창 이름은 `{PR번호}-{짧은이름}`이며, head 브랜치의 이슈 번호보다 PR 번호를
  우선한다.
- 브랜치 모드에 이슈 번호가 없으면 `--target-name`을 생략한다.
- workmux가 target name을 소문자로 정규화하므로 안내와 재사용에도 소문자 값을 쓴다.
- 창 이름 충돌 시 브랜치 모드는 `{repo명}-{짧은이름}`, PR 모드는
  `{PR번호}-{repo명}-{짧은이름}`으로 재시도한다.

## 생성·오픈 경로

저장소 루트에서 분기한다. 서브디렉터리나 기존 worktree에서의 오판을 막기 위해 상대
경로로 판정하지 않는다.

```bash
ROOT=$(git rev-parse --show-toplevel)
test -f "$ROOT/scripts/create-worktree.sh"
git -C "$ROOT" config --get filter.git-crypt.smudge
```

git-crypt 저장소에서는 PR 모드를 포함해 원칙적으로 `workmux add`를 쓰지 않는다.

- 래퍼가 있으면 실행 권한을 먼저 확인한다. **실행 권한이 없으면** 경로를 바꾸지 말고
  오류로 보고한다. 래퍼가 실패하면 즉시 중단하고 `workmux open`으로 진행하지 않는다.
  확인 프롬프트를 `-y`나 `yes |`로 자동 우회하지 않는다.
- **예외:** git-crypt 필터가 있는데 래퍼가 없으면 `workmux add` 전에 사용자에게 확인받고
  진행한다.

래퍼 경로의 PR 모드는 head 브랜치를 확보한 뒤 다음 순서로 실행한다.

```bash
./scripts/create-worktree.sh {head브랜치명}
workmux open {handle} --target-name {PR번호}-{짧은이름} --parent-session "$SELECTED_SESSION"
```

브랜치 모드도 래퍼가 출력한 경로와 handle을 확보한 뒤 `workmux open`을 사용한다.
이슈 번호가 없으면 `--target-name`을 생략한다. 래퍼 출력에서 worktree 절대경로를 얻고,
그 경로와 일치하는 `workmux list --json` 항목의 handle을 쓴다. 아직 목록에 없으면
경로 basename을 `git worktree list --porcelain`으로 대조한 폴백으로만 사용하고, open 뒤
실제 창을 다시 확인한다. `workmux open`은 `git worktree list`로 찾으므로 `worktree_dir`
밖의 형제 디렉터리도 인식한다.

래퍼가 없는 PR 모드는 positional 브랜치명과 `--name`을 생략한다.

```bash
workmux add --pr {PR번호} --target-name {PR번호}-{짧은이름} --parent-session "$SELECTED_SESSION"
```

브랜치 모드는 이슈 번호가 있을 때만 `--target-name {이슈번호}-{짧은이름}`을 추가한다.
생성 전 `workmux add ... --dry-run`으로 예상 경로와 handle을 확인할 수 있다. 생성 뒤에는
출력과 `workmux list --json`에서 실제 경로·handle을 얻으며 이름을 추측하지 않는다.

`--parent-session`은 session mode, 샌드박스 안, `--count`, `--foreach`, 여러 `--agent`,
stdin을 통한 여러 worktree 생성에서는 지원되지 않으므로 그 조합에서는 생략한다.
PR worktree 생성 뒤에는 `git -C "{worktree경로}" rev-parse HEAD`가 `headRefOid`와 같은지
검증한다. 다르면 성공으로 보고하지 않는다.

## 기존 worktree 처리

세션 선택보다 먼저 `git worktree list --porcelain`과 `workmux list --json`으로 브랜치의
기존 worktree 경로·handle을 확인한다. 같은 브랜치가 이미 있으면 새로 만들지 않고 그
경로를 안내한다.

기존 창은 이번 호출에서 파생한 이름으로 찾지 않는다. 다음 순서로 탐지한다.

1. `workmux list --json`의 handle 항목에서 `is_open`을 확인한다. 이 값은 단서이며 최종
   판정이 아니다(아래 참조).
2. `workmux.worktree.{handle}.window-session` 저장값으로 세션 후보를 좁힌다.
3. `workmux.worktree.{handle}.target-window` 저장값으로 창 후보를 좁힌다. 저장값은 실제
   창 이름의 접미사다. `nerdfont` 설정에 따라 글리프와 공백이 앞에 붙을 수 있으므로
   동등 비교가 아니라 접미사 비교로 판정한다.
4. pane 현재 경로를 worktree 절대경로와 교차 확인한다.

```bash
tmux list-panes -a -F '#{session_name}:#{window_index} #{window_id} #{pane_id} #{pane_current_path}' \
  | awk -v wt="{worktree절대경로}" '$4 == wt || index($4, wt"/") == 1'
```

동일 `window_id`의 여러 pane은 하나의 창으로 중복 제거한다. 이후 조작은 바뀌지 않는
`window_id`와 `pane_id`를 기준으로 하며, 변하는 `session:index`를 기준으로 하지 않는다.
경로에 공백이 있으면 위 매칭은 신뢰할 수 없고 pane cwd는 사용자가 `cd`로 바꿀 수 있다.

`window-session` 또는 `target-window`가 없으면 그 단서만 제외하고 나머지와 pane 경로로
진행한다. 둘 다 없어도 pane 매칭이 정확히 하나면 사용하되 결과에 기록한다.

`is_open`도 같은 방식으로 다룬다. `is_open`이 거짓이라도 4단계 pane 매칭이 정확히 하나면
창이 열려 있는 것으로 판정한다. workmux는 `is_open`을 git config의
`workmux.worktree.{handle}.window-token`과 tmux 창의 `@workmux_token` 대조로 정하므로,
페인이 다른 handle의 창에 얹혀 있거나 `break-pane`으로 만든 창에 토큰이 없으면 살아 있는
창도 거짓이 된다. 이때는 메타데이터가 실측과 어긋난 것이므로 그 사실을 보고하고, 사용자
확인 후 `window-token`·`window-session`·`target-window` 키를 실측대로 복구한다. pane 매칭이
없을 때만 창이 닫혀 있다고 확정한다. 저장값과
pane 실측이 다르면 실측을 신뢰하고 차이를 보고한다. 단, `target-window` 앞의 글리프·공백
접두사 때문에 생기는 차이는 "저장값과 실측이 다르다"에 해당하지 않는다. 그 보고는 저장
세션이나 창 자체가 어긋났을 때만 한다. `is_open`인데 pane 매칭이 없거나 서로 다른
`window_id`가 둘 이상이면 추측하지 않는다. 저장된 세션·창 이름 후보를 보여 주고
확인받으며, 실제 위치를 확정하지 못했으면 `window-session`을 갱신하지 않는다.

- 창이 닫혀 있으면(`is_open`이 거짓이고 pane 매칭도 없으면) 선택 세션으로 연다.
- 창이 열려 있고 실제 세션이 선택 세션과 같으면 중복 창을 만들지 않고 기존 위치를
  안내한다.
- 창이 열려 있고 사용자가 세션을 명시하지 않았으면 다른 세션에 있어도 옮기지 않는다.
  레거시·사라진 저장값을 고치는 경우에는 실제 세션을 기록한다.
- 창이 열려 있고 사용자가 다른 세션을 명시했으면 `workmux open`으로 재구성하지 말고
  `move-window-to-session` 스킬로 이동한다.

이동 직전 `window_id`에서 현재 위치를 다시 해석해 `세션:번호` 형태로 얻고, 반드시
`move-window-to-session` 스킬을 호출한다. 그 스킬에 넘기는 인자는 `<세션:번호>`와
`<대상세션>` 두 개뿐이다. handle과 worktree 경로는 인자가 아니라 이후 확인에 쓰는 참고
값이다. 그 스킬을 인라인으로 베껴 수행하지 않는다. 그 스킬만이 agent state 동기화와
resurrect 즉시 저장을 수행하므로 이를 건너뛰면 재부팅 후 이동이 사라지거나 dashboard가
옛 세션을 가리킬 수 있다. 이동 후에도 같은 `window_id`로 위치를 확인한다. 그 스킬은
`workmux list`의 PATH basename에서 이름을 파생하므로, 기본 명명이 아니면 handle과
어긋날 수 있다. 이동이 끝나면
`workmux.worktree.{handle}.window-session`을 읽는다.

- 대상 세션과 같으면 정상이다.
- 다르면 그 스킬이 basename 키에 쓴 것이다. handle 키를 직접 대상 세션으로 갱신하고
  그 사실을 보고한다. 갱신도 실패하면 중단한다.

## 사후 검증

실제 창 이름과 세션은 다음으로 확인한다. `workmux list`에는 창 이름 열이 없으므로
추측해서 안내하지 않는다.

```bash
tmux list-windows -a -F '#{session_name}:#{window_index}\t#{window_name}'
```

실제 창 위치를 확인한 뒤의 처리는 이번 호출이 무엇을 했는지에 따라 다르다.

- **창을 새로 만들거나 열었으면**: 실제 세션이 선택 세션과 다르면 잘못 만들어진
  세션과 git config를 함께 정리한다.
- **창을 옮겼으면**: 최종 위치가 선택 세션과 다르면 이동이 완결되지 않은 것이다.
  그 사실을 보고하고, config에 잘못된 값을 쓰지 않는다.
- **창을 옮기지 않았으면**: 실제 세션이 선택 세션과 다른 것이 정상이다. 정리하지
  않는다. 이때의 `window-session` 갱신은 "세션 선택"의 갱신 대상 표가 관장한다.

결과에는 worktree 경로, handle, 브랜치, 실제 세션, 실제 창 이름을 보고한다. PR 모드는
PR 번호와 head OID도 포함한다.

## 주의사항

- 에이전트(Claude·Codex)는 자동 실행하지 않는다. 레이아웃은 nvim만 실행하고 나머지는
  빈 셸이므로 필요할 때 사용자가 직접 시작한다.
- 개발 서버는 별도 윈도우나 pane에서 실행한다. worktree마다 상주시켜서는 안 된다.
  포트가 충돌하고 개당 1~2GB를 쓸 수 있다.
- 레이아웃은 `~/.config/workmux/config.yaml`에서 바꾸며, 저장소별 설정은 저장소 루트의
  `.workmux.yaml`에 둔다.
