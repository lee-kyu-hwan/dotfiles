# macOS 앱 목록

Brewfile로 관리되는 macOS 애플리케이션 중 **GUI 앱(cask)** 과 **런타임/플랫폼 도구** 중심의 목록이다.
`bat`, `eza`, `ripgrep` 같은 범용 CLI 도구는 여기서 다루지 않으며 [cli-tools.md](cli-tools.md)를 참고한다.

> 정리 기준: 데스크톱 앱·SDK·폰트·플랫폼 CLI(클라우드/모바일/DB 런타임)는 이 문서, 셸 작업용 범용 CLI는 cli-tools.md.

## 요약 테이블

| 이름 | 종류 | 설명 |
|------|------|------|
| [android-studio](#android-studio) | Cask (앱) | Android/Flutter/React Native 개발 IDE |
| [copilot-cli](#copilot-cli) | Cask (앱) | GitHub Copilot CLI |
| [flutter](#flutter) | Cask (SDK) | Flutter SDK |
| [gcloud-cli](#gcloud-cli) | Cask (CLI) | Google Cloud CLI |
| [ghostty](#ghostty) | Cask (앱) | GPU 가속 터미널 에뮬레이터 |
| [hammerspoon](#hammerspoon) | Cask (앱) | macOS 자동화/윈도우 매니저 |
| [keycastr](#keycastr) | Cask (앱) | 키 입력 시각화 도구 |
| [reactotron](#reactotron) | Cask (앱) | React Native 디버깅 도구 |
| [font-meslo-lg-nerd-font](#font-meslo-lg-nerd-font) | Cask (폰트) | 터미널/Neovim 아이콘 폰트 |
| [cocoapods](#cocoapods) | Formula (CLI) | iOS 의존성 관리자 |
| [firebase-cli](#firebase-cli) | Formula (CLI) | Firebase 프로젝트 관리 CLI |
| [fvm](#fvm) | Formula (CLI, tap) | Flutter 버전 관리자 |
| [supabase](#supabase) | Formula (CLI) | Supabase 백엔드 플랫폼 CLI |
| [gemini-cli](#gemini-cli) | Formula (CLI) | Google Gemini CLI |
| [openjdk@17](#openjdk17) | Formula (CLI) | Java 17 런타임 |
| [mysql-client](#mysql-client) | Formula (CLI) | MySQL 클라이언트 |
| [redis](#redis) | Formula (CLI) | 인메모리 데이터 스토어 |

---

## macOS 앱 (Casks)

### android-studio

Android, Flutter, React Native 앱 개발을 위한 JetBrains 기반 공식 IDE.
Android SDK, AVD(에뮬레이터 관리자), 디버거가 내장되어 있어 별도 SDK 설치 없이 바로 개발 환경을 구성할 수 있다.

- **주요 용도**: Android 앱 빌드, Flutter 앱 Android 타깃 실행, React Native Android 디버깅
- **포함 항목**: Android SDK, Android 에뮬레이터(AVD), Gradle 빌드 툴

---

### copilot-cli

GitHub Copilot을 터미널에서 사용할 수 있게 해주는 CLI 도구.
셸 명령어 제안, Git 명령어 자동완성, 터미널 작업 보조 기능을 제공한다.

- **주요 용도**: 셸 명령어 제안 (`gh copilot suggest`), 명령어 설명 (`gh copilot explain`)
- **전제 조건**: GitHub Copilot 구독 및 `gh auth login` 인증 필요

---

### flutter

Google의 크로스플랫폼 UI 프레임워크 SDK. Brewfile에서는 공식 cask로 설치한다.

- **주요 용도**: Flutter 앱 개발, 빌드, 테스트, 패키지 관리
- **주요 명령어**: `flutter run`, `flutter build`, `flutter pub get`, `flutter doctor`
- **의존 관계**: Android 빌드에 `android-studio` + `openjdk@17`, iOS 빌드에 `cocoapods` 필요

---

### gcloud-cli

Google Cloud 리소스를 터미널에서 관리하는 공식 CLI.

- **주요 용도**: GCP 프로젝트/인증/배포 관리, Firebase와 Google Cloud 연동 작업
- **주요 명령어**: `gcloud auth login`, `gcloud config set project`, `gcloud app deploy`

---

### ghostty

Rust로 작성된 GPU 가속 터미널 에뮬레이터. 빠른 렌더링과 낮은 레이턴시가 특징.

- **주요 용도**: 기본 터미널 에뮬레이터
- **테마**: One Dark
- **관련 설정**: `dot_config/ghostty/` — 폰트, 테마, 키바인딩 등 설정 관리

---

### hammerspoon

Lua로 macOS 자동화와 윈도우 매니지먼트를 구성하는 앱. 이 dotfiles에서는 Magnet 호환 단축키를 제공한다.

- **주요 용도**: 윈도우 분할, 앱 토글, 자동 리로드
- **설정 상세**: [docs/hammerspoon.md](hammerspoon.md) 참고
- **관련 설정**: `dot_hammerspoon/init.lua`

---

### keycastr

키보드 입력을 화면에 실시간으로 시각화하는 macOS 앱.
화면 녹화, 발표, 페어 프로그래밍 중 단축키를 청중에게 보여줄 때 유용하다.

- **주요 용도**: 화면 녹화 중 단축키 표시, 프레젠테이션, 튜토리얼 제작
- **설정 상세**: [docs/keycastr.md](keycastr.md) 참고
- **자동 설정**: `chezmoi apply` 실행 시 `run_once_configure-keycastr.sh.tmpl`로 설정 자동 적용

---

### reactotron

React Native 및 React 앱 전용 데스크톱 디버깅 도구.
앱과 WebSocket으로 연결해 네트워크 요청, Redux/MobX 상태, 로그, 성능 지표를 실시간으로 확인할 수 있다.

- **주요 용도**: React Native 앱 네트워크 요청 모니터링, 상태(state) 확인, 커스텀 로그 확인
- **연결 방식**: 앱 코드에 Reactotron 플러그인 추가 후 동일 네트워크에서 자동 연결

---

### font-meslo-lg-nerd-font

Meslo LG Nerd Font. 터미널, Starship, lazygit, Neovim 아이콘 표시에 사용한다.

- **주요 용도**: 터미널 글꼴, Nerd Font 아이콘 렌더링
- **관련 설정**: Ghostty와 lazygit의 아이콘 표시

---

## 언어 및 런타임 (Formulae)

### cocoapods

Ruby로 작성된 iOS/macOS 앱의 의존성 관리자. Xcode 프로젝트에 서드파티 라이브러리를 통합할 때 사용한다.

- **주요 용도**: Flutter iOS 빌드 시 네이티브 의존성 설치 (`pod install`), React Native iOS 링킹
- **주요 명령어**: `pod install`, `pod update`, `pod repo update`

---

### firebase-cli

Firebase 프로젝트를 관리하는 공식 CLI.

- **주요 용도**: Firebase Hosting 배포, Cloud Functions 관리, 프로젝트 설정 확인
- **주요 명령어**: `firebase login`, `firebase projects:list`, `firebase deploy`

---

### fvm

Flutter SDK 버전을 프로젝트별로 고정하고 전환하는 CLI.

- **주요 용도**: Flutter 프로젝트별 SDK 버전 관리
- **주요 명령어**: `fvm install`, `fvm use`, `fvm flutter doctor`
- **설치 경로**: Homebrew 코어가 아닌 `leoafarias/fvm` tap 경유 (`tap "leoafarias/fvm"` → `brew "leoafarias/fvm/fvm"`)

---

### gemini-cli

Google Gemini AI 모델을 터미널에서 직접 사용할 수 있는 공식 CLI 도구.

- **주요 용도**: AI 텍스트 생성, 코드 보조, Google 생태계 연동 작업
- **전제 조건**: Google 계정 인증 또는 API 키 설정 필요

---

### supabase

오픈소스 Firebase 대안인 Supabase 백엔드 플랫폼을 관리하는 공식 CLI. 로컬 개발 스택 실행과 마이그레이션/배포에 사용한다.

- **주요 용도**: 로컬 Supabase 스택 실행, DB 마이그레이션 관리, 프로젝트 배포
- **주요 명령어**: `supabase init`, `supabase start`, `supabase db push`, `supabase functions deploy`
- **전제 조건**: 로컬 스택 실행 시 Docker 필요, 원격 작업 시 `supabase login` 인증

---

### openjdk@17

OpenJDK 17 LTS 버전. Android 빌드 도구(Gradle)가 Java 런타임을 필요로 한다.

- **주요 용도**: Android 앱 Gradle 빌드, React Native Android 빌드
- **참고**: Android Studio 내장 JDK와 별개로 CLI 빌드 시 `JAVA_HOME` 환경변수에 이 경로를 지정해야 할 수 있음

---

## 데이터

### mysql-client

MySQL 서버에 접속하기 위한 클라이언트 CLI. `dot_zshrc.tmpl`과 Neovim database 플러그인에서 Homebrew 경로를 PATH에 추가한다.

- **주요 용도**: 로컬/원격 MySQL 접속, SQL 실행
- **주요 명령어**: `mysql`, `mysqldump`

---

### redis

인메모리 키-값 데이터 스토어. 캐싱, 세션 관리, 메시지 큐 등 다양한 용도로 사용되는 오픈소스 DB.

- **주요 용도**: 로컬 개발 환경의 캐시 서버, 백엔드 API 세션 저장소, 작업 큐(BullMQ 등)
- **주요 명령어**: `redis-server` (서버 실행), `redis-cli` (CLI 클라이언트)
- **서비스 등록**: `brew services start redis`로 시스템 시작 시 자동 실행 가능

## Brewfile 외 설치

Claude Code CLI는 Brewfile이 아니라 `install.sh`에서 공식 설치 스크립트로 설치한다.

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Maestro CLI는 `run_once_install-maestro.sh.tmpl`에서 최초 1회 설치한다.

```bash
curl -fsSL "https://get.maestro.mobile.dev" | bash
```
