# Neovim 키맵 & 치트시트

Leader 키: `<Space>`

`★` = 커스텀 키맵 (chezmoi로 관리, `dot_config/nvim/` 하위 파일에 정의)

## 첫 실행 안내

1. `nvim` 실행 → lazy.nvim이 플러그인 자동 다운로드 (네트워크 필요)
2. mason-lspconfig이 LSP 서버 자동 설치 (ts_ls, tailwindcss, eslint, lua_ls, jsonls)
3. 설치 상태 확인: `:Mason` → 목록에서 installed 확인
4. treesitter 파서 자동 설치: `:TSInstallInfo`로 확인
5. 문제 발생 시: `:checkhealth`로 진단

## 커스텀 키맵

### 파일 탐색기 (neo-tree)

> 설정 파일: `dot_config/nvim/lua/plugins/neo-tree.lua`

| 키 | 기능 | 구분 |
|----|------|------|
| `<Space>e` | 파일 탐색기 토글 | ★ |

#### neo-tree 내부

| 키 | 기능 | 구분 |
|----|------|------|
| `<Enter>` | 파일 열기 / 디렉토리 펼치기 | 기본 |
| `<Backspace>` | 상위 디렉토리로 이동 | 기본 |
| `.` | 현재 디렉토리를 cwd로 설정 | 기본 |
| `a` | 새 파일/디렉토리 생성 | 기본 |
| `d` | 삭제 | 기본 |
| `r` | 이름 변경 | 기본 |
| `y` | 파일명 복사 | ★ |
| `Y` | 상대 경로 복사 | ★ |
| `gy` | 절대 경로 복사 | ★ |
| `z` | 전체 디렉토리 접기 | ★ |
| `Z` | 전체 디렉토리 펼치기 | ★ |

### 검색 (telescope)

> 설정 파일: `dot_config/nvim/lua/plugins/telescope.lua`

| 키 | 기능 | 구분 |
|----|------|------|
| `<Space>ff` | 파일 검색 | ★ |
| `<Space>fg` | 텍스트 검색 (live grep) | ★ |
| `<Space>fb` | 버퍼 목록 | ★ |
| `<Space>fh` | 도움말 검색 | ★ |
| `<Space>fr` | 최근 파일 | ★ |

### LSP (코드 탐색)

> 설정 파일: `dot_config/nvim/lua/plugins/lsp.lua`
> Neovim 0.11+ 빌트인 키맵 기반. `gd`만 Telescope로 오버라이드 (import문이 아닌 실제 파일로 이동).

#### 탐색

| 키 | 기능 | 구분 |
|----|------|------|
| `gd` | 정의로 이동 (Telescope) | ★ |
| `gD` | 선언으로 이동 | 0.11 빌트인 |
| `grr` | 참조 목록 | 0.11 빌트인 |
| `gri` | 구현으로 이동 | 0.11 빌트인 |
| `grt` | 타입 정의로 이동 | 0.11 빌트인 |
| `gO` | 문서 심볼 목록 | 0.11 빌트인 |

#### 정보 확인

| 키 | 기능 | 구분 |
|----|------|------|
| `K` | 호버 정보 (타입, 문서) | 0.11 빌트인 |
| `<C-s>` (Insert) | 시그니처 도움말 | 0.11 빌트인 |

#### 리팩터링

| 키 | 기능 | 구분 |
|----|------|------|
| `gra` | 코드 액션 | 0.11 빌트인 |
| `grn` | 이름 변경 | 0.11 빌트인 |

#### 컴포넌트 드릴링 워크플로우

```
<Button /> 위에 커서 → gd → Button 정의 파일로 점프
  → 내부의 <Icon /> 위에 커서 → gd → Icon 정의로 점프
    → 돌아가고 싶으면 Ctrl-o, Ctrl-o (점프 리스트)
```

| 키 | 기능 |
|----|------|
| `<C-o>` | 이전 위치로 돌아가기 (뒤로) |
| `<C-i>` | 다음 위치로 이동 (앞으로) |

### Git

> 설정 파일: `dot_config/nvim/lua/plugins/git.lua`

| 키 | 기능 | 구분 |
|----|------|------|
| `<Space>gg` | LazyGit 열기 | ★ |
| `]h` | 다음 변경 hunk | ★ |
| `[h` | 이전 변경 hunk | ★ |
| `<Space>hp` | hunk 미리보기 | ★ |
| `<Space>hs` | hunk stage | ★ |
| `<Space>hr` | hunk reset | ★ |

#### LazyGit에서 diff 보기

`<Space>gg`로 LazyGit을 연 뒤 사용할 수 있는 diff 관련 키:

| 키 | 기능 |
|----|------|
| 파일 선택 | 오른쪽 패널에 diff 자동 표시 |
| `Enter` | 파일의 staged/unstaged 변경사항 줄 단위 확인 |
| `Shift+W` | diff 모드 시작 (커밋/브랜치 비교) |
| `Escape` | diff 모드 해제 |
| `w` | diff 옵션 메뉴 (whitespace 무시 등) |
| `{` / `}` | diff 컨텍스트 줄 수 조절 (더 많이/적게) |
| `Ctrl+e` | diff를 외부 에디터(nvim)에서 열기 |

**커밋 간 비교**: Commits 패널에서 기준 커밋 → `Shift+W` → 대상 커밋으로 이동

**브랜치 간 비교**: Branches 패널에서도 동일하게 `Shift+W`로 비교 가능

### 포매팅

> 설정 파일: `dot_config/nvim/lua/plugins/conform.lua`

| 키 | 기능 | 구분 |
|----|------|------|
| `<Space>cf` | 코드 포맷 (수동) | ★ |
| 저장 시 | 자동 포맷 (format-on-save) | ★ |

### 편집

> 설정 파일: `dot_config/nvim/lua/plugins/editor.lua`

| 키 | 기능 | 구분 |
|----|------|------|
| `gcc` | 주석 토글 (현재 줄) | 플러그인 기본 |
| `gc` (비주얼) | 주석 토글 (선택 영역) | 플러그인 기본 |

### 태그/감싸기 (nvim-surround)

> 설정 파일: `dot_config/nvim/lua/plugins/editor.lua`

`ys`, `cs`, `ds` 세 가지 동작으로 감싸기/변경/삭제.

#### 감싸기 (ys = you surround)

| 키 | 기능 | 예시 |
|----|------|------|
| `ysiw"` | 단어를 `""`로 감싸기 | `hello` → `"hello"` |
| `ysiw)` | 단어를 `()`로 감싸기 | `hello` → `(hello)` |
| `ysiw(` | 단어를 `( )`로 감싸기 (공백 포함) | `hello` → `( hello )` |
| `ysiwt` + 태그명 | 단어를 태그로 감싸기 | `text` → `<div>text</div>` |
| `yss"` | 줄 전체를 `""`로 감싸기 | |
| `S"` (비주얼) | 선택 영역을 `""`로 감싸기 | |

#### 변경 (cs = change surround)

| 키 | 기능 | 예시 |
|----|------|------|
| `cs"'` | `""` → `''`로 변경 | `"hello"` → `'hello'` |
| `cs"(` | `""` → `()`로 변경 | `"hello"` → `(hello)` |
| `cst<div>` | 태그명 변경 | `<b>text</b>` → `<div>text</div>` |

#### 삭제 (ds = delete surround)

| 키 | 기능 | 예시 |
|----|------|------|
| `ds"` | `""` 삭제 | `"hello"` → `hello` |
| `ds)` | `()` 삭제 | `(hello)` → `hello` |
| `dst` | 태그 삭제 | `<div>text</div>` → `text` |

### JSX 태그 자동 완성 (nvim-ts-autotag)

> 설정 파일: `dot_config/nvim/lua/plugins/treesitter.lua`

별도 키맵 없이 자동 동작:

- `<div>` 입력 시 `</div>` 자동 생성
- 여는 태그 이름 수정 시 닫는 태그 자동 동기화 (`<div>` → `<span>` 으로 바꾸면 `</div>` → `</span>`)

### 빠른 이동 (flash.nvim)

> 설정 파일: `dot_config/nvim/lua/plugins/editor.lua`

| 키 | 모드 | 기능 | 구분 |
|----|------|------|------|
| `s` | Normal/Visual/Operator | Flash 점프 (글자 입력 → 라벨 선택 → 이동) | ★ |
| `S` | Normal/Visual/Operator | Treesitter 노드 단위 선택 | ★ |

#### 사용법

```
s를 누른 후 → 이동할 위치의 글자 입력 (예: "di")
→ 화면에 라벨(a, b, c...)이 표시됨
→ 라벨 키를 눌러 해당 위치로 즉시 점프
```

`f`/`t`와 달리 화면 내 아무 위치로 이동 가능. 줄을 넘나드는 이동에 유용.

### 코드 구조 선택/이동 (treesitter-textobjects)

> 설정 파일: `dot_config/nvim/lua/plugins/treesitter.lua`

Treesitter가 코드 구조(함수, 클래스, 파라미터)를 인식해서 정확한 범위를 선택/이동.

#### 선택 (Visual 모드 또는 Operator와 조합)

| 키 | 기능 | 예시 |
|----|------|------|
| `vaf` | 함수 전체 선택 | `function foo() { ... }` 전체 |
| `vif` | 함수 본문만 선택 | `{ ... }` 안쪽만 |
| `vac` | 클래스 전체 선택 | |
| `vic` | 클래스 본문만 선택 | |
| `vaa` | 파라미터 전체 선택 | `(a, b, c)` 에서 `b,` 포함 |
| `via` | 파라미터 내부만 선택 | `(a, b, c)` 에서 `b`만 |

`d`, `c`, `y`와 조합 가능: `daf` (함수 삭제), `caa` (파라미터 교체), `yif` (함수 본문 복사)

#### 이동

| 키 | 기능 | 구분 |
|----|------|------|
| `]m` | 다음 함수 시작으로 | ★ |
| `[m` | 이전 함수 시작으로 | ★ |
| `]M` | 다음 함수 끝으로 | ★ |
| `[M` | 이전 함수 끝으로 | ★ |

#### 파라미터 순서 교환

| 키 | 기능 | 구분 |
|----|------|------|
| `<Space>a` | 다음 파라미터와 교환 | ★ |
| `<Space>A` | 이전 파라미터와 교환 | ★ |

```
커서가 첫 번째 파라미터에 있을 때:
foo(alpha, beta)  →  <Space>a  →  foo(beta, alpha)
```

### 파일 즐겨찾기 (harpoon)

> 설정 파일: `dot_config/nvim/lua/plugins/harpoon.lua`

자주 사용하는 파일을 최대 4개까지 등록하고 번호로 즉시 전환. 컴포넌트 ↔ 테스트 ↔ 스타일 파일 간 이동에 유용.

| 키 | 기능 | 구분 |
|----|------|------|
| `<Space>ha` | 현재 파일을 Harpoon에 추가 | ★ |
| `<Space>hh` | Harpoon 메뉴 열기 (목록 확인/편집) | ★ |
| `<Space>1` | 1번 파일로 이동 | ★ |
| `<Space>2` | 2번 파일로 이동 | ★ |
| `<Space>3` | 3번 파일로 이동 | ★ |
| `<Space>4` | 4번 파일로 이동 | ★ |

#### 워크플로우 예시

```
1. Button.tsx 열기 → <Space>ha (1번으로 등록)
2. Button.test.tsx 열기 → <Space>ha (2번으로 등록)
3. Button.module.css 열기 → <Space>ha (3번으로 등록)
4. 이후 <Space>1, <Space>2, <Space>3 으로 즉시 전환
```

### 진단/에러 목록 (trouble.nvim)

> 설정 파일: `dot_config/nvim/lua/plugins/editor.lua`

LSP 진단(에러, 경고)을 하단 패널에 목록으로 표시. quickfix보다 보기 편한 UI.

| 키 | 기능 | 구분 |
|----|------|------|
| `<Space>xx` | 프로젝트 전체 진단 목록 토글 | ★ |
| `<Space>xd` | 현재 파일 진단만 토글 | ★ |

### 창 이동

> 설정 파일: `dot_config/nvim/lua/config/keymaps.lua`

| 키 | 기능 | 구분 |
|----|------|------|
| `<C-h>` | 왼쪽 창으로 | ★ |
| `<C-j>` | 아래 창으로 | ★ |
| `<C-k>` | 위 창으로 | ★ |
| `<C-l>` | 오른쪽 창으로 | ★ |

### 버퍼

> 설정 파일: `dot_config/nvim/lua/config/keymaps.lua`

| 키 | 기능 | 구분 |
|----|------|------|
| `<S-h>` | 이전 버퍼 | ★ |
| `<S-l>` | 다음 버퍼 | ★ |

### 기타

> 설정 파일: `dot_config/nvim/lua/config/keymaps.lua`

| 키 | 기능 | 구분 |
|----|------|------|
| `<Esc>` | 검색 하이라이트 제거 | ★ |
| `<` / `>` (비주얼) | 들여쓰기 유지하며 이동 | ★ |

### 자동완성 (nvim-cmp)

> 설정 파일: `dot_config/nvim/lua/plugins/cmp.lua`

| 키 | 기능 | 구분 |
|----|------|------|
| `<C-n>` | 다음 항목 | ★ |
| `<C-p>` | 이전 항목 | ★ |
| `<CR>` | 선택 확인 | ★ |
| `<Tab>` | 다음 항목 / 스니펫 점프 | ★ |
| `<C-Space>` | 자동완성 수동 호출 | ★ |
| `<C-d>` | 문서 위로 스크롤 | ★ |
| `<C-f>` | 문서 아래로 스크롤 | ★ |

---

## Vim 기본 치트시트

### 모드 전환

| 키 | 기능 |
|----|------|
| `i` | Insert 모드 (커서 앞에 입력) |
| `a` | Insert 모드 (커서 뒤에 입력) |
| `o` | 아래 새 줄에서 Insert |
| `O` | 위 새 줄에서 Insert |
| `v` | Visual 모드 (문자 선택) |
| `V` | Visual Line 모드 (줄 선택) |
| `<C-v>` | Visual Block 모드 (블록 선택) |
| `<Esc>` | Normal 모드로 돌아가기 |
| `:` | Command 모드 |

### 이동

| 키 | 기능 |
|----|------|
| `h/j/k/l` | 좌/하/상/우 |
| `w` | 다음 단어 시작 |
| `b` | 이전 단어 시작 |
| `e` | 단어 끝 |
| `0` | 줄 처음 |
| `$` | 줄 끝 |
| `gg` | 파일 처음 |
| `G` | 파일 끝 |
| `{` / `}` | 문단 위/아래 |
| `%` | 짝 괄호로 이동 |
| `<C-d>` | 반 페이지 아래 |
| `<C-u>` | 반 페이지 위 |

### 편집

| 키 | 기능 |
|----|------|
| `x` | 글자 삭제 |
| `dd` | 줄 삭제 |
| `dw` | 단어 삭제 |
| `D` | 커서~줄 끝 삭제 |
| `cc` | 줄 교체 (삭제 + Insert) |
| `cw` | 단어 교체 |
| `ciw` | 단어 전체 교체 |
| `ci"` | 따옴표 안 내용 교체 |
| `di"` | 따옴표 안 내용 삭제 |
| `u` | 되돌리기 (undo) |
| `<C-r>` | 다시 실행 (redo) |
| `.` | 마지막 동작 반복 |
| `p` | 붙여넣기 (아래) |
| `P` | 붙여넣기 (위) |

### 복사 (yank)

| 키 | 기능 |
|----|------|
| `yy` | 줄 복사 |
| `yw` | 단어 복사 |
| `yi"` | 따옴표 안 복사 |
| `yap` | 문단 복사 |

### 검색/치환

| 키 | 기능 |
|----|------|
| `/패턴` | 검색 |
| `n` / `N` | 다음/이전 결과 |
| `*` | 현재 단어 검색 |
| `:%s/old/new/g` | 전체 치환 |
| `:%s/old/new/gc` | 전체 치환 (확인) |

### 파일

| 키 | 기능 |
|----|------|
| `:w` | 저장 |
| `:q` | 종료 |
| `:wq` | 저장 후 종료 |
| `:qa` | 전체 종료 |
| `:q!` | 저장 안 하고 종료 |

### Fold (코드 접기)

| 키 | 기능 |
|----|------|
| `zc` | 현재 블록 접기 |
| `zo` | 현재 블록 펼치기 |
| `zM` | 전체 접기 |
| `zR` | 전체 펼치기 |

### 파일 경로 복사 (Command 모드)

```vim
:let @+ = expand('%:p')   " 절대 경로
:let @+ = expand('%:.')   " 상대 경로
:let @+ = expand('%:t')   " 파일명만
```
