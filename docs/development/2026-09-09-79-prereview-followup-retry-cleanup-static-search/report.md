# Quality Goal Report

- Task ID: 20260909T015728Z-79-pr-전-보완-code-002-code-search-형태-검증-i5-4c5e2758
- Mode: strict
- Status: CODE_REVIEW → COMPLETED
- Created: 2026-09-09T01:57:28Z
- Updated: 2026-09-10T04:10:00Z
- Source goal: #79 PR 전 보완 — CODE-002 code search 형태 검증, I5 권한 거부와 rate limit 구분 재시도, I8 clone 정리 실패로 산출물 유실 방지, I11 정적 검색 읽기 실패와 의도적 제외 구분, I9 sha256 의미 문서화

## 실행 연결

이 실행은 #79 의 네 번째 quality-goal 실행이다. 1차(`20260906T125225Z-…-ec840cba`)는 Plan 한도로 `NEEDS_REDESIGN`, 2차(`20260906T194200Z-…-f0ac72ad`)는 `COMPLETED` 이며 `discover` 실경로를 1회 라이브 검증했다. 3차(`20260908T011803Z-…-2b100e8c`)는 PR 사전 리뷰가 차단한 Critical 4건과 포함 Important 8건을 수정해 `COMPLETED` 로 끝났고, 그 실행이 **의도적으로 보류** 한 항목이 이번 승인 범위다. 1·2·3차 실행 문서와 상태는 불변 이력이며 이 실행에서 수정하지 않았다(§ 검증 근거의 CMD-9).

## Classification

`quality_state.py classify` 로 `strict` 를 기록했다. 근거 7건 중 핵심은 넷이다. ① I8 이 `shutil.rmtree` 로 clone 을 지우는 되돌리기 어려운 파괴적 연산이고 현재 무보호 `finally` 가 예외를 내면 조사 결과가 유실된다. ② I11 이 `#80`~`#82` 가 소비하는 `static_search` 출력의 계약 변경을 요구하고 CODE-002 도 `code_search.available` 의미를 바꿔 `evidence_status` 에 파급된다. ③ I5 는 403 을 권한 거부와 rate limit 으로 나누는 권한 경계 해석 작업이다. ④ I5 의 재시도 정책 변경이 2차 실행에서 1회 라이브 검증된 예산·지연 계약과 직접 맞물린다.

## 승인 범위와 각 항목의 처리

| 항목 | 승인된 처리 | 결과 |
|---|---|---|
| CODE-002 | 구현 | code search 의 2xx 형태 검증. 완료 |
| I5 | 구현 | 403 을 권한 거부와 rate limit 으로 분류. 완료 |
| I8 | 구현 | clone 정리 격리와 산출물 보존. 완료 |
| I11 | 구현 | 정적 검색의 읽기 실패·의도적 제외 구분(additive 계약). 완료 |
| I9 | **문서만** | 세 `sha256` 의미 문서화 + 코드 대조 테스트. 완료. 필드명·스키마·계산 코드 미변경 |
| I13 | **후속 문서화만** | 배포 계약의 follow-up 절에 기록. 구현하지 않았고 GitHub Issue 도 만들지 않았다 |

## Review history

설치 quality-goal 은 **v5.1.0**, codex-cli 0.153.4, python 3.14.7 이다. 실행 도중 버전이 바뀌지 않았다. 오케스트레이터 모델은 Opus 5 (1M context, `claude-opus-5[1m]`) 이며 `model-routing.md` 의 orchestrator 라우트가 `inherit`/high 이므로 승인된 라우팅과 차이가 없다. Codex 는 strict 라우트 `gpt-5.6-sol`/high 를 유지했다.

| 산출물 | 라운드 | 역할·모델 | 판정 | 점수 | blocker | 라운드 사이의 변화 |
|---|---|---|---|---|---|---|
| readiness (advisory) | spec r1 | Codex `gpt-5.6-sol` / high | **invocation_failed** | — | — | 29분 2초 동안 모델 출력 없이 정체. 정책대로 기록만 하고 공식 리뷰를 막지 않았다 |
| spec | 1 | 리뷰어 opus / high | REVISE | 81 | `SPEC-001`, `SPEC-002` | finding 4건 |
| readiness (advisory) | spec r2 | Codex `gpt-5.6-sol` / high | READY | 100 | 없음 | 8/8 pass, 4개 target 전부 resolved |
| spec | 2 | 리뷰어 opus / high | **PASS** | 92 | 없음 | 4건 해소. 남은 것은 advisory Low `SPEC-005` |
| plan | 1 | 리뷰어 opus / high | PASS | 92 | 없음 | finding 5건(Medium 2 + Low 3) |
| plan | 2 | 리뷰어 opus / high | **PASS** | 95 | 없음 | 5건 전부 resolved. 새 Low `PLAN-006` |
| code | 1 | 리뷰어 opus / high | **PASS** | 93 | 없음 | Low 3건(`CODE-101`~`CODE-103`) |

구현 라운드는 Codex `gpt-5.6-sol` / high 1회다. 라운드 사용량은 **spec 2/3, plan 2/2(소진), code 1/3** 이다. 라운드 한도를 우회하지 않았다.

결정적 검사는 spec 라운드 2 와 plan 라운드 2 모두 `revision_check.py` 종료 0(`passed: true`, `empty_cells: 0`, `missing_rows: []`, `blank_cells: []`) 이며 개정 노트는 `spec-revision-notes.md` 와 `plan-revision-notes.md`(13행) 다.

## Blocking-finding resolutions

| finding | 심각도 | 해소 | 검증 근거 |
|---|---|---|---|
| `SPEC-001` | High | CMD-6·CMD-7·CMD-8 의 `-t` 를 각 스킬 tests 디렉터리 절대 경로로 고쳤다. 세 명령이 `-t <skill루트>` 형태라 전부 `ImportError: Start directory is not importable` 로 실행되지 않았고 AC-17·AC-18·AC-19 의 유일한 판정 수단이었다 | 오케스트레이터가 개정 표기를 그대로 실행해 `Ran 55 / Ran 30 / Ran 108`, 전부 `OK`. 이 finding 은 오케스트레이터의 `ORCH-1` 결정적 점검이 먼저 발견하고 리뷰어가 구조 근거(세 tests 디렉터리에 `__init__.py` 없음)로 확인했다 |
| `SPEC-002` | High | R3.2 에 `combination_partial` 의 record warning 검사에 `clone-cleanup-failed:` 접두를 OR 로 추가하는 정확한 메커니즘을 명시하고 discovery·manifest `status` 를 `partial`, 종료 코드를 3 으로 못박았다. 종료 4 선행 판정과 예산 소진 3 은 불변임을 적고 Architecture 의 잘못된 서술("기존 partial 판정에 포함된다")을 정정했으며 AC-7 을 확장했다 | 오케스트레이터가 코드로 확인했다. `combination_partial`(`:1565-1575`)은 네 조건만 보고 `status` 는 종료 코드에서만 도출된다(`:2039-2040`). 구현 후 접두가 `:1686` 에 OR 로 추가되고 CMD-3 이 종료 0 이며 변이 M3 로 커버리지를 확인했다 |

## Plan approval

- Approval timestamp: 2026-09-10T02:15:00Z
- Plan digest: `53941e53e7812c05cd0fe505c3ecc2bb208303b2e9f087cb56c4c277035c2bc2`

승인 게이트는 두 번 제시됐다. 첫 제시(Plan 라운드 1, digest `63fd6355…`)에서 사용자는 advisory finding 5건을 문서에서 해소하도록 선택해 `AWAITING_PLAN_APPROVAL → PLAN_REVIEW` 로 되돌렸다. 두 번째 제시에서 개정된 Plan(digest `53941e53…`, PASS 95)에 대해 구현을 승인했고 **`PLAN-006` 보완 조건을 승인에 포함** 했다. `approve-plan` 은 승인 직전에 파일의 현재 SHA-256 이 사용자가 승인한 값과 Plan 리뷰가 기록한 digest 양쪽과 같음을 확인한 뒤 기록했고, `IMPLEMENTING` 진입 전에 승인 digest 와 파일 해시를 한 번 더 대조했다.

## Changed files

구현 라운드가 신고한 5개가 실제 변경 5개와 정확히 일치한다. **이번 실행은 착수 전에 스킬 트리 전체(34개 파일)의 파일별 스냅숏과 SHA-256 목록을 상태 디렉터리에 남겼기 때문에 진짜 unified diff 를 만들 수 있었다.** 3차 실행의 `DEV-5` 한계를 해소한 것이다. `diff -qr` 결과 누락·초과 항목이 없었다.

| 파일 | 의도된 변경 |
|---|---|
| `scripts/verify_candidates.py` | `discover_code_search` 의 2xx 형태 게이트, `_retryable(status, headers)` 서명과 403 분류, `_retry_delay` 의 `math.isfinite` 가드, 두 transport 의 `retry_decision`·`retry_reason` 기록, `_append_response_warning` 의 403 접미, `_repository_failure` 의 optional headers, `static_search` 의 additive 3필드와 `os.walk(onerror=...)`, `_static_record` 기본 객체, `_cleanup_clone_sessions` 의 소유권 검사·시도별 격리, `discover_exit_code` 의 두 새 OR 항 |
| `tests/test_verify_candidates.py` | 신설 행위 테스트 6개 |
| `tests/test_skill_contract.py` | 신설 계약 테스트 `test_closed_sets_manifest_schema_and_exit_contract` 1개 + 기존 문서 계약 테스트에 세 `sha256` 실계산 대조와 새 문구 단정 추가 |
| `references/verification-contract.md` | 세 `sha256` 의미, additive static-search 필드와 fail-closed 소비, 두 새 partial 접두, I13 follow-up |
| `references/github-verification-contract.md` | malformed search payload 규칙, 403 재시도 정책과 네 reason |

`SKILL.md` 는 변경하지 않았고 신고 목록에 없는 것과 일치한다. **신설 fixture 파일은 없다.** Plan 이 선언한 대로 응답 map 주입, `tempfile` 로컬 repository 생성, `mock.patch` 로만 구성했다.

`compute_revision()` 해시 대상이 바뀌어 리비전 값이 달라졌다. 계약된 동작이며 `test_print_revision_matches_recomputation` 이 재계산 비교로 통과한다.

## Verification evidence

python `/opt/homebrew/bin/python3` 3.14.7, `PYTHONDONTWRITEBYTECODE=1`, 네트워크 없음, 오프라인 fixture 와 주입 runner/sleeper/clock 만 사용. 기준 커밋 `6d60011cbdaead7946b191d3f12029eef5c141c8`. 변경 전 기준선은 대상 스킬 55, 형제 스킬 30·108 이었다.

| ID | 대상 | 종료 코드 | 결과 |
|---|---|---|---|
| CMD-1 | `test_code_search_malformed_2xx_is_partial_and_allows_clone_fallback` | 0 | Ran 1 test OK |
| CMD-2 | 403 분류 + 재시도 경계·관측 2개 | 0 | Ran 2 tests OK |
| CMD-3 | cleanup 실패 보존 + 기존 정리 범위 2개 | 0 | Ran 2 tests OK |
| CMD-4 | 정적 검색 구분 + 불완전 근거 2개 | 0 | Ran 2 tests OK |
| CMD-5 | 계약 4개 + revision 재계산 | 0 | Ran 5 tests OK |
| CMD-6 | 전체 오프라인 스위트 | 0 | **정확히 `Ran 62 tests` OK** (기준선 55 + 신설 7. 하한이 아닌 정확값) |
| CMD-7 | 형제 `analyzing-open-source-pr-patterns` | 0 | Ran 30 tests OK — 기준선과 동일 |
| CMD-8 | 형제 `collecting-recent-closed-prs` | 0 | Ran 108 tests OK — 기준선과 동일 |
| CMD-9 | 보존 대상 22개 | 0 | 22/22 `OK` |
| CMD-10 | 사전 스냅숏 대비 diff | 1 | 차이 발견(정상 상태). 1581줄, 승인 경로 5개만 |

문서 줄 수는 `SKILL.md` 30(<200), `verification-contract.md` 170(<400), `github-verification-contract.md` 88(<400) 이다.

### 보존 확인

루트 `AGENTS.md`(이 세션이 만들지 않은 미추적 파일)와 1·2·3차 실행 문서 전부 byte-identical, 형제 스킬 두 곳의 변경 파일 0개, 전역 설치본·`main`·다른 워크트리 미변경이다.

### 미구성 범주 (통과로 적지 않는다)

| 범주 | 확인한 근거 | 기록 |
|---|---|---|
| lint | 스킬 디렉터리에 `ruff.toml`·`.flake8`·`setup.cfg`·`tox.ini`·`package.json` 없음 | not configured |
| type check | `mypy.ini`·`pyproject.toml`·`py.typed` 없음 | not configured |
| build | 빌드 시스템·`Makefile` 없음 | not configured |
| E2E / 라이브 | 승인이 추가 GitHub 요청·라이브 `discover`·`recheck`·대상 저장소 실행·의존성 설치를 금지 | 승인에 의한 범위 밖 |

### 승인에 포함된 `PLAN-006` 보완 조건

Plan 라운드 한도가 소진돼 문서에서 고칠 수 없었고 사용자가 이 조건을 승인에 포함했다. 요구는 "테스트 안에서 기존 `write_fixture`/`fixture_response` 로 4000자를 넘는 정책 content 를 주입해 실제 잘림과 세 해시 의미를 검증하되 신설 fixture 파일 없이 승인된 AC-14 범위에서" 였다.

구현 확인했다. `tests/test_skill_contract.py:221` 이 4000자 초과 content 를 base64 로 주입하고, `:261` `truncated: true`, `:262` 발췌 정확히 4000자, `:263` 발췌 `sha256` == 잘리기 전 전체 content 해시, `:264` policy result `sha256` 과도 동일, **`:265` 잘린 `text` 해시와 다름** 을 단정한다. 이 부등식이 두 의미가 구분됨을 증명하는 핵심이다. 일반 `_untrusted_text` 는 `:205-206`, 디렉터리 canonical JSON bytes 는 `:281-283` 이다. 신설 fixture 파일은 없고 필드명·스키마·계산 코드는 그대로다.

### 변이 테스트 (테스트가 실제로 결함을 잡는지)

스킬 트리를 세션 임시 경로에 복사해 **사본에서만** 변이했다. 작업트리는 변경하지 않았으므로 지문에 영향이 없다. 사본 기준선은 변이 전후 모두 `Ran 62 tests OK` 였다.

| 변이 | 결과 |
|---|---|
| 모호한 403 을 다시 재시도 가능하게 | CMD-2 FAILED (13 failures, 12 errors) — I5 커버 확인 |
| `static-search-incomplete:` 접두 제거 | CMD-4 FAILED — I11 partial 메커니즘 커버 확인 |
| `clone-cleanup-failed:` 접두 제거 | CMD-3 FAILED — I8 partial 메커니즘 커버 확인 |
| code search 를 상태 코드만 보게 되돌림 | CMD-1 FAILED — CODE-002 커버 확인 |
| 정책 발췌 `sha256` 덮어쓰기 제거 | CMD-5 FAILED — I9 문서·코드 대조 커버 확인 |
| 복원 | pristine 사본 `Ran 62 tests OK` |

### 지문

검증 시점 작업트리 지문은 `f8fb82b223302357234889ed1ab4bead9362d244d1fc186436b5c5f8b77fcb4a` 이고 코드 리뷰 라운드 1 의 심사 대상 digest 와 같다. 종결 가드는 기록된 검증 지문과 마지막 통과 리뷰의 digest 를 대조하며 두 값이 일치한다. 이 보고서 파일은 종결 직전에 등록되므로 종결 후 작업트리의 실시간 지문은 이 문서만큼 심사 시점과 다르다. 절차상 의도된 순서이며 **종결 후 이 보고서를 편집해 지문을 재불일치시키지 않는다.**

## Remaining advisory findings

blocker 는 없다. 남은 것은 Low 5건이다.

| finding | 출처 | 내용 | 영향 | 후속 |
|---|---|---|---|---|
| `SPEC-005` | Spec r2 | R4.2 의 warning 계기 문언이 "읽기 실패" 인데 `read_failures` 는 `walk` 항목도 담는다 | 없음. AC-11 이 stat·read·walk 세 주입을 단정해 동작은 고정됐다 | Plan 전역 제약에 구속 지시로 실어 구현이 `read_failures` 비어 있지 않을 때 warning 을 내고 `<count>` 를 `len(read_failures)` 로 하게 했다. 구현에서 확인 완료 |
| `PLAN-006` | Plan r2 | T5 가 지목한 fixture 로는 잘린 발췌 사례를 만들 수 없다(그 fixture 의 디코드 최대 22자, 잘림 임계값 4000자) | 없음 | **사용자 승인에 포함돼 구현에서 해소** 했다. 위 § 참조 |
| `CODE-101` | Code r1 | 403 이 파싱 가능한 **음수** `Retry-After` 와 유효한 `Remaining: 0`/`Reset` 를 함께 가지면 `_retryable` 은 `remaining-zero-and-reset` 로 재시도하지만 `_retry_delay` 는 `Retry-After` 우선을 적용하고 음수를 `0.0` 으로 clamp 해 세 번의 재시도가 대기 없이 연속 발사된다 | **승인 범위 밖.** Spec R2.2 가 "숫자로 해석 가능한 `Retry-After` 다음 `X-RateLimit-Reset`" 우선순위를 명시하므로 현재 동작이 승인된 설계와 일치한다. 고치려면 Spec 변경이 필요하다. 경계는 유지된다(`MAX_RETRIES` 3, ≤300초, 예산 4) | 오케스트레이터가 직접 재현했다. `_retryable` → `(True, 'remaining-zero-and-reset')`, `_retry_delay` → `0.0`(대조군: `Retry-After` 없으면 `300.0`). **후속 범위 항목.** 분류에서 거부된 지연 근거를 지연 우선순위에서도 건너뛰게 하려면 별도 승인이 필요하다 |
| `CODE-102` | Code r1 | `read_failures` 가 상한 없는 배열이고 clone root 밖 walk 오류 경로가 `"."` 로 합쳐진다 | 낮음. 비밀·절대 경로 유출은 없다(신설 테스트가 단정). Spec 이 상한을 정하지 않았다 | 후속 범위 항목. 문서화된 상한과 총계 보존, 알 수 없는 walk 경로와 clone root 의 구분은 별도 계약 승인이 필요하다 |
| `CODE-103` | Code r1 | 계약 스위트가 import 시점에 `sys.path` 를 조작해 행위 스위트의 헬퍼를 가져오므로 그 모듈의 import 시점 부작용에 결합된다 | 낮음. 승인된 "신설 fixture 파일 없이 기존 헬퍼 재사용" 조건을 지키기 위한 선택이다 | 후속 범위 항목. 공용 헬퍼 모듈로 분리하면 결합을 끊을 수 있고 신설 fixture 파일 제약도 유지된다 |

## 편차와 사건

상세는 `.claude/quality-state/<task-id>/orchestrator-deviations.md` 에 있다.

- **DEV-1** 초기 dirty 경로가 5개로 늘었고 그중 루트 `AGENTS.md` 는 **이 세션이 만든 것이 아니다.** `CLAUDE.md` 를 Claude → Codex 로 기계 치환한 사본(3,903 바이트, mtime 2026-09-08 12:35:47, diff 22줄, `~/.Codex/skills/` 처럼 대문자 오타 포함)이며 3차 실행 중 워크트리 전체 쓰기 범위 점검 두 번이 이 파일을 보고하지 않았고 그 시점에 돌던 것은 읽기 전용 프로세스뿐이었다. 다른 세션·도구가 만든 것으로 보인다. 승인 범위 밖이므로 착수 전 SHA-256 을 기준선에 넣고 바이트 동일 보존했다. CMD-9 로 종료 시점까지 불변을 확인했다.
- **DEV-2** 3차 `DEV-5` 교훈을 반영해 착수 전에 스킬 디렉터리의 파일별 SHA-256(34개)과 전체 사본을 상태 디렉터리에 남겼다. 그 덕에 이번 코드 리뷰에는 실제 unified diff(1581줄)를 실었다.
- **INC-1** Codex preflight 가 두 번 감시 창을 넘겼으나 stderr 전사 확인 결과 **preflight 자체는 성공** 했다(모델이 비어 있지 않은 한 줄 응답, 두 번째는 종료 0). 이 환경의 Codex 고정 오버헤드(훅과 스킬 컨텍스트 로딩에 약 2만 토큰과 수 분)가 원인이다. 모델 부재가 아니므로 `BLOCKED_MODEL_UNAVAILABLE` 복구 경로를 발동하지 않고 모델을 대체하지도 않았다. 이후 모든 Codex 감시 창을 늘렸다.
- **INC-2** 맥북 종료로 세션이 끊겼다가 복구했다. **완료된 작업을 재실행하지 않았다.** 기록된 author PID 는 소멸했고 실행 중이던 `codex exec` 4개는 모두 다른 워크트리(`85-feat-quality-goal-execution-w…`)의 것이라 건드리지 않았다. Spec author 는 종료 전에 완료해 산출물과 결과 JSON 이 온전했으므로 그대로 사용하고 미실행 단계(readiness·공식 리뷰·Spec 등록)만 이어갔다. 보존 기준선 22개·34개와 세 스위트 55·30·108 을 재확인했다. 세션 임시 경로의 preflight 산출물과 3차 실행의 변이 사본은 사라졌을 수 있으나 3차 결과는 영구 산출물에 기록돼 있다.
- **INC-3** Spec readiness 라운드 1 이 29분 2초 동안 모델 출력 없이 정체했다. 이벤트 4줄 중 둘은 하네스 통지이고 `ps` 상태 `SN`·CPU 0.0%, stderr 비어 있었다. 정책대로 `record-readiness --invocation-status failed --stderr-path <stderr>` 로 기록하고 단계를 `SPEC_REVIEW` 로 유지했다. readiness 는 advisory 이며 공식 리뷰의 시작 조건이 아니므로 리뷰를 막지 않았다. record-only advisory 단계에 30분급 재시도를 반복하지 않고 공식 리뷰로 진행한 판단과 근거 부재를 `readiness-evidence-spec-r1.md` 에 명시했으며 그 라운드의 구조 점검은 오케스트레이터가 대체 수행했다. 라운드 2 에서는 프롬프트에 시간 제약과 미확인 항목의 `verified: false` 처리를 명시해 READY 100 을 받았다.

## 유지되는 한계 주장

- **`discover` 실경로만 1회 라이브 검증됐다.** 그 근거는 2차 실행의 읽기 전용 이력이며 이번 변경의 검증으로 재사용하지 않았다.
- **`assessment`·`record`·`recheck` 실경로는 라이브 미검증이고 실제 `CAN-*` 산출물은 없다.** 이번 모든 판정은 오프라인 fixture 와 주입 transport 로 실행했다.
- **이번 수정본의 제한된 라이브 검증은 권장하지만 승인되지 않았다.** 대상 저장소·PAT 입력·실행 명령·총 API 예산(재시도 포함)·clone 허용/정리·출력 경로가 아직 정해지지 않았다. 2차 실행의 80회 승인은 재사용하지 않는다.
- **`#79` 전체 완료를 주장하지 않는다.** 공용 배포 검증은 `#82` 로 남긴다.
- **배포하지 않았다.** commit·push·PR 생성·merge·`chezmoi apply`·배포·GitHub 이슈·댓글 작성을 수행하지 않았고 `main`·다른 워크트리·전역 설치본·`$HOME` 설정을 수정하지 않았다.
- **미해결 후속 3건**: `CODE-101`(음수 `Retry-After` 지연 우선순위), `CODE-102`(`read_failures` 상한과 walk 경로 구분), `CODE-103`(계약 스위트의 헬퍼 결합). 모두 별도 승인이 필요한 범위다.

## Final status

- Status: `completed`
- Machine-readable reason: `null` (정상 종결. spec 2/3, plan 2/2, code 1/3 라운드, 마지막 코드 리뷰 PASS 93, blocker 0, 미해소 advisory Low 5건)
