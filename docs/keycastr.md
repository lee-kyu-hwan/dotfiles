# KeyCastr 설정

키 입력을 화면에 시각화하는 macOS 앱. 화면 녹화, 프레젠테이션, 페어 프로그래밍에 유용.

## 설치

```bash
brew install --cask keycastr
```

Brewfile에 포함되어 있어 `brew bundle --global`로 자동 설치.

## 설정 값

| 항목 | 값 | 설명 |
|------|-----|------|
| 비주얼라이저 | Svelte | 모던 UI |
| 표시 모드 | Modifier 키만 | 일반 타이핑 숨김, 단축키만 표시 |
| 폰트 크기 | 18pt | |
| 투명도 | 70% | |
| 페이드 지연 | 1초 | 표시 후 1초 뒤 사라짐 |
| 페이드 아웃 | 0.3초 | 빠르게 사라짐 |
| 마우스 클릭 | 표시 | |
| 위치 | 상단 중앙 | |

## 설정 적용 방식

chezmoi의 `run_once_configure-keycastr.sh.tmpl`로 관리. 새 머신에서 `chezmoi apply` 시 자동 실행 (macOS에서만).

## 로그인 시 자동 실행

수동으로 설정 필요:

```bash
osascript -e 'tell application "System Events" to make login item at end with properties {path:"/Applications/KeyCastr.app", hidden:false}'
```

## 한글 제한사항

KeyCastr는 비라틴 문자(한글, 일본어 등)를 정상 표시하지 못하는 [알려진 제한](https://github.com/keycastr/keycastr/issues/248)이 있음. Modifier 키만 표시 모드를 사용하면 실질적으로 문제 없음.

## 설정 초기화

```bash
defaults delete io.github.keycastr
```
