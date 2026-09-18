# Quality Goal Report

- Task ID: 20260915T065141Z-80-post-review-hardening-curated-contrib-52ae436a
- Mode: strict
- Status: completed
- Created: 2026-09-15
- Updated: 2026-09-16
- Source goal: #80 post-review hardening: curated contribution PR collector의 보안·페이지네이션·manifest·분류·원자성 결함 수정

## Classification

auto 가 아닌 root 지정 strict 이며 위험 스캔이 이를 독립적으로 뒷받침했다. 보안 통제(원격 텍스트가
GitHub API 경로를 조종), 데이터 무결성(manifest append-only 이력 소실), 외부 API 호환(GitHub pagination
계약 위반), 멱등성·원자성(임시 파일 잔존)이 각각 strict 트리거다.

## Review history

| 산출물 | 라운드 | score | verdict | 게이트 |
|---|---|---|---|---|
| Spec | 1 | 91 | PASS | **불합격** — 오케스트레이터가 `material_decisions_resolved: false` 로 차단 |
| Spec | 2 | 93 | PASS | 통과 |
| Plan | 1 | 91 | PASS | 통과했으나 Medium 2 건이 구현에 실제 영향을 주어 남은 라운드를 사용 |
| Plan | 2 | 93 | PASS | 통과 |
| 코드 | 1 | 91 | PASS | 통과 |

Spec 라운드 1 은 리뷰어가 PASS 를 냈으나 D1 이 root 승인 대기 상태였다. 미해결 정책을 안고 Plan 으로
넘어가지 않기 위해 오케스트레이터가 게이트를 막고 root 결정을 요청했다.

## Blocking-finding resolutions

blocker 는 발생하지 않았다. 게이트를 좌우한 항목은 다음과 같다.

- **SPEC-001 (Medium)**: R3.2·R3.3 이 복수형 제외를 확정으로 적었으나 D1 은 승인 대기였다.
  root 가 권고안을 승인해 해소했다. 확정 문법은 URL span 제거 후 영어
  `example|examples`·`notice|notices`·`announcement` 를 ASCII 글자 경계로, 한국어는 정규화된 label 의
  첫 토큰이 `예시|공지` 이고 바로 뒤가 label 끝 또는 `:`, `：`, `-`, `–`, `—` 일 때만 일치시키는 것이다.
- **PLAN-001 (Medium)**: 계약 문서가 D1 이전 어휘를 서술해 구현 후 문서-코드 불일치가 남을 상황이었다.
  계약 문서 갱신 단계를 T7 에 추가하고 `references/` 를 편집 대상으로 바꿔 해소했다.
- **PLAN-002 (Medium)**: `--print-revision` 을 최상위로 옮기면 subcommand requiredness 를 완화해야 하는데
  Plan 에 없었다. 오케스트레이터가 `add_subparsers(..., required=True)` 와 bare invocation 의 현재
  exit 2 를 실측해 확인했고, T15 에 requiredness 이동을 명시하고 AC-15 테스트에 bare·unknown subcommand
  단언을 추가해 해소했다.

## Plan approval

- Approval timestamp: 2026-09-16T00:00:00Z
- Plan digest: `4aa344c077fe036607f6135773c64bf3d74afcd05cbb267a216c8d1f5701cf3a`

root 오케스트레이터가 승인했다. root 제시값, 작업트리 실제 파일, `approve-plan` 이 기록한 digest 가
3 자 일치했다. `approve-plan` 은 통과한 Plan 리뷰의 digest 와 다르면 거부하므로 심사본과 승인본이 같다.

## Changed files

baseline 스냅샷 대비 변경은 커레이티드 스킬 안의 네 파일뿐이다.

| 파일 | 변경 |
|---|---|
| `scripts/collect_curated_contribution_prs.py` | 결함 16 건의 구현 수정 |
| `tests/test_collect_curated_contribution_prs.py` | `test_ac_01_post_review_*` ~ `test_ac_17_post_review_*` 17 개와 mapping·packaging 계약 테스트 |
| `references/collection-contract.md` | D1 문법 반영. same-line prefix → 앞줄 범위 모델과 label scope 기록 설명은 보존 |
| `evals/behavioral-eval.md` | worktree 절대 경로 2 곳만 `<worktree>` 로 치환 |

형제 collector, analyzer, candidate verifier, `#80` 감사 문서 6 개, 승인 Spec/Plan 은 모두 바이트 불변이다.

## Verification evidence

구현 완료 시점 fingerprint `63602e02398ba778d0fedbef7c222cbc7fa2e7a5870558fc95426fb982c03aea` 에서
오케스트레이터가 직접 실행했다. 모든 명령이 종료 코드 0 이다.

이 보고서를 산출물 디렉터리에 추가하면서 workspace fingerprint 가
`b4e17f81babe22cc8801f6db36f4ff450e5c9e0523fc211fd0564b19485e33e3` 로 바뀌었고, `COMPLETED` 전이가
workspace·검증·최종 PASS 리뷰 digest 의 정확한 일치를 요구해 한 번 거부됐다. 규정대로 새 fingerprint
에서 재검증해 curated 52, 형제 collector 115, analyzer 30, candidate verifier 62, `quick_validate` 가
모두 종료 코드 0 임을 확인하고 `record-verification` 으로 다시 기록했다. 소스 네 파일은 리뷰가 심사한
상태와 바이트 동일하며 차이는 이 보고서 추가 하나뿐이다. 재검증 기록은 `verification.json` 의
`post_report_reverification` 에 있다. 따라서 이 보고서의 마지막 정정까지 반영한 상태가 이 작업의 최종 workspace 다. 정확한 최종 fingerprint 값은
`.claude/quality-state/<task-id>/fingerprint.txt` 와 `state.json` 의 `verification.workspace_fingerprint`
가 정본이며, 보고서 본문에 숫자를 박아 두지 않는다. 보고서를 고칠 때마다 fingerprint 가 바뀌어
본문에 적은 값이 곧바로 낡아지기 때문이다.

| 대상 | 결과 |
|---|---|
| targeted `-k post_review` | `Ran 17 tests` OK |
| curated 전체 | `Ran 52 tests` OK (baseline 34) |
| 형제 collector | `Ran 115 tests` OK |
| analyzer | `Ran 30 tests` OK |
| candidate verifier | `Ran 62 tests` OK |
| `quick_validate.py` | `Skill is valid!` |
| analyzer validator (fresh) | `Validated 2 records (schema 1.0.0).` |
| analyzer validator (append-only) | `Validated 1 records ... against existing corpus.` |
| curated revision | `sha256:b2e9a04f02d3f9d229aab606a29b9d09c9c367475eddaf876d1f7b03c3664e67` |
| 형제 revision | `sha256:8a6d2d3b...` — baseline 과 동일(무변경 증명) |

오프라인 합성 E2E(네트워크 없음): F2·R2 의 마지막 페이지 Link 가 malformed 와 구분되고 정상 next 는
valid. F3a~F3d 네 건 교정, 보존 네 건(영어 설명형 label, 한국어 heading, same-line prefix 범위, 한국어
실제 제출) 유지. F7 임시 파일 잔존 없음. R5 는 `--print-rev`·`--hel` 이 exit 2 와 revision stdout 0 줄,
full spelling 은 exit 0 과 1 줄, bare invocation 은 exit 2.

변이 검증: `evals/behavioral-eval.md` 의 `<worktree>` 를 절대 경로로 되돌리면
`test_ac_17_post_review_portable_eval_paths` 와 `test_ac_22_contract_stdlib_synthetic_packaging` 이
실패(exit 1)하고, 복원하면 다시 통과(exit 0)하며 fingerprint 가 동일하게 돌아온다.

not configured 로 기록하는 범주: type check, lint, build. 저장소에 해당 설정 파일이 없다. 브라우저 E2E 는
해당 없으며 대신 오프라인 합성 하네스로 대체했다.

### 정직하게 남기는 사항

**오케스트레이터의 오판 1 건.** F1 첫 probe 가 `extract_references` 를 직접 호출해 `('../..', 1)` 을
보고 실패로 판단했다. `collect()` 레벨에서 재검증한 결과 방어는 `normalize_repository` 에 있고
T1 테스트가 exit 4, `excluded-invalid-repository`, `reference-identity` scope, API 호출에 `..` 없음을
단언하며 통과한다. probe 가 방어 이전 계층만 본 것이 원인이며 코드 결함이 아니다.

**실패 실행 3 건.** Plan author 시도 1, 구현 T1~T7, 구현 T7~T17 이 모두 900 초 hard timeout 으로
결과 파일 없이 종료됐다. 세 건 모두 실패로 기록했고 성공 라운드로 계산하지 않았다(`rounds.code` 는
코드 리뷰 라운드만 센다). Plan author 실패본은 `plan-attempt-1-evidence/` 에 보존하고 승인 경로에서
제외했다. 구현 실패 두 건의 산출물은 오케스트레이터가 직접 검증한 뒤 root 판단으로 보존했다.
최종 T17 실행은 exit 0 과 스키마 검증 통과로 끝났다.

## Execution watchdog

| Execution ID | PID | 경과 | child exit | result / schema | reason |
|---|---|---|---|---|---|
| exec-spec-r1 / r1b / r2 / r2b | — | — | 0 | 존재 / passed | None |
| exec-readiness-r1 / r2 | — | — | 0 | 존재 / passed | None |
| exec-plan-r1 | 39116 | 900.2s | unknown | 없음 / not_run | **hard_timeout** |
| exec-plan-r1-retry | 84924 | 510.8s | 0 | 존재 / passed | None |
| exec-plan-r2 | 65311 | 312.1s | 0 | 존재 / passed | None |
| exec-impl-t1-t7 | 43039 | 900.1s | unknown | 없음 / not_run | **hard_timeout** |
| exec-impl-t7-t17 | 50061 | 900.1s | unknown | 없음 / not_run | **hard_timeout** |
| exec-impl-t17 | 45923 | 335.2s | 0 | 존재 / passed | None |

세 hard timeout 모두 `preservation_status: created`, `residual_pids: []` 였다. 모델 대체는 하지 않았다.

## Watchdog restart budget

`exec-plan-r1` 의 `restart_candidate` 가 true 이고 `retry_consumed` 가 0 이어서 허용된 재시도 1 회를
정확히 소비했다(`exec-plan-r1-retry`, 성공). 구현 실행에는 watchdog 이 공식 재시작 예산을 할당하지
않았으므로(`retry_budget_initial`·`remaining` 모두 null) 임의 필드를 만들지 않고 root 승인 아래 새
bounded round 로 기록했다.

## Remaining advisory findings

| ID | 심각도 | 내용 | 후속 |
|---|---|---|---|
| `CODE-001` | Low | `_header` 가 Link 키는 있으나 값이 문자열이 아닌 경우를 `absent`(정상 마지막 페이지)로 분류한다. 승인 Spec R2.2 는 헤더 컨테이너만 범위로 하므로 이번 범위 밖이다 | 다음 재현·범위 주기에서 다룰 잔여 항목으로 기록 |
| `CODE-002` | Low | `test_ac_17_post_review_portable_eval_paths` 와 `test_ac_22_contract_stdlib_synthetic_packaging` 이 gitignore 대상인 `.claude/quality-state/.../baseline-snapshot` 을 읽는다. **fresh clone 과 chezmoi 배포본에서는 이 두 테스트를 실행할 수 없다.** 오케스트레이터가 `.gitignore:25` 와 테스트의 `parents[4]` 경로로 확인했다 | 배포 전 또는 quality-state 정리 전에 F8 oracle 을 스킬 안에 포함하거나, 스냅샷 부재 시 명시적 skip 으로 바꿔 패키지 suite 가 계속 실행 가능하게 한다 |
| `CODE-004` | Low | 코드 리뷰 라운드 2 가 지적했다. 이 보고서가 `63602e02…` 를 "최종" fingerprint 로 적었으나 보고서 추가 자체로 값이 바뀌어 낡은 표기였다. 위 § Verification evidence 에서 구현 완료 시점과 재검증을 구분해 서술하고 최종 값은 state 파일을 정본으로 삼도록 정정했다 | 정정 완료. 후속 없음 |
| `CODE-003` | Low | `_warnings_for_failed_scopes` 의 중복 제거가 부분 문자열 비교라 `pagination-link` 경고가 `pagination` 을 가릴 수 있다. 현재는 pagination 루프가 첫 gap 에서 멈춰 두 kind 가 공존하지 않는다 | 새 gap kind 추가 시 정확한 `kind` 토큰 비교로 전환 |

`SPEC-006`(argparse 등록 방식 미지정)은 Plan T15 가 `allow_abbrev=False` 단일 경로로 확정해 해소됐다.
`PLAN-004`·`PLAN-005`는 root 가 구현 조건으로 고정했고 구현과 리뷰에서 준수가 확인됐다.

## Final status

- Status: completed
- Machine-readable reason: `COMPLETED`

commit, push, PR, merge, 배포, 전역 설치본 변경은 이 작업자가 수행하지 않았다. 전부 root 담당이다.
