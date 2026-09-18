# #138 profile2 quality-goal 미러 제거 — 실측과 사라진 계약

`dot_local/share/private_ai-account-profiles/private_claude/private_profile2/` 아래
`skills/quality-goal/**` 44개와 `agents/quality-reviewer.md` 1개, 모두 45개 파일을 source에서
지웠다. 정본은 `dot_claude/skills/quality-goal`·`dot_claude/agents/quality-reviewer.md` 한 벌이다.
정본과 `~/.claude` 배포 경로는 바꾸지 않았다.

## 착수 전 실측 (이슈 항목 5)

명령: `python3 -m unittest -v tests.test_ai_session tests.test_orchestrator_profiles`
(Python 3.14.7, base `05c4731`).

| 상태 | 결과 |
| --- | --- |
| 변경 전 | 121개 실행, `OK` |
| 미러 45개만 `git rm` | 121개 실행, `FAILED (failures=3, errors=1)` |

빨개진 테스트는 모두 `tests.test_orchestrator_profiles.OrchestratorProfileContractTests` 안에 있고,
`tests.test_ai_session` 에서는 하나도 없다.

| 메서드 | 결과 | 실패 지점 |
| --- | --- | --- |
| `test_file_ownership` | FAIL | 기대 소유 파일에 미러 45개 경로가 들어 있어 `all(is_file())` 가 False |
| `test_profile2_quality_bundle_mirror` | FAIL | 정본 45개 경로 집합과 미러 집합(빈 집합)이 다름 |
| `test_profile2_chezmoi_diff_redaction` | FAIL | 렌더 대상 목록 `rendered_targets` 가 비어 있음 |
| `test_public_asset_private_boundary` | ERROR | `PROFILE2_PUBLIC_ROOT.iterdir()` 에서 `FileNotFoundError` |

미러를 전제하지만 빨개지지 않은 테스트도 있었다. 조건문이나 상수 비교 때문에 공허하게
통과했을 뿐이라 함께 정리했다.

| 메서드 | 공허하게 통과한 이유 |
| --- | --- |
| `test_profile2_public_asset_denylist` | symlink 검사가 `if PROFILE2_PUBLIC_ROOT.exists()` 안에 있음 |
| `test_account_home_private_source_and_profile1_denylist` | 실제 디렉터리가 아니라 상수 경로의 `parts` 만 비교 |
| `test_profile_onboarding_documentation_contract` | 문서 문자열만 검사하고 문서는 그대로였음 |

## 테스트 처리

| 메서드 | 처리 |
| --- | --- |
| `test_profile2_quality_bundle_mirror` | 제거 |
| `test_profile2_chezmoi_diff_redaction` | 제거 |
| `test_public_asset_private_boundary` | 제거 |
| `test_file_ownership` | 수정 — 미러 45개 기대 경로 제거 |
| `test_profile2_public_asset_denylist` | 수정·개명 → `test_profile2_account_state_denylist`. 계정 상태 제외 규칙만 남김 |
| `test_account_home_private_source_and_profile1_denylist` | 수정 — 상수 경로 비교를 지우고 실제 `private_profile1` 존재와 `private_profile2` 부재를 검사 |
| `test_profile_onboarding_documentation_contract` | 수정 — 필수 문자열에서 `quality-reviewer.md`, `skills/quality-goal` 제거 |
| `test_profile2_mirror_removal_is_exact` | 추가 — 한시적 `.chezmoiremove` 고정 |

모듈 상수 `PROFILE2_PUBLIC_SOURCE`, `PROFILE2_PUBLIC_ROOT`, `CANONICAL_QUALITY_SKILL`,
`CANONICAL_QUALITY_REVIEWER` 와 헬퍼 `is_public_quality_file` 는 쓰는 곳이 없어져 지웠다.

## 영구 스위트에서 사라진 계약 (11개)

남은 테스트 어디에서도 더는 검사하지 않는 계약이다.

1. profile2 source의 파일 집합이 정본 quality-goal(`__pycache__`·`*.pyc`·symlink 제외)과
   `quality-reviewer.md` 에 상대 경로 단위로 정확히 같다. (`test_profile2_quality_bundle_mirror`)
2. 대응 파일끼리 바이트가 같다. (같은 테스트)
3. 미러 파일은 symlink가 아닌 regular file이다. (같은 테스트)
4. 렌더된 profile2 home에서 `skills/quality-goal/SKILL.md` 기준 `../../agents/quality-reviewer.md` 가
   정본과 같은 바이트의 regular file로 해석된다. (같은 테스트)
5. 렌더 시뮬레이션 결과가 임시 루트 안에 머물고 최상위가 `agents`·`skills` 뿐이다.
   (`test_profile2_chezmoi_diff_redaction`)
6. `ai-session` selector 소스가 `PROFILE2_PUBLIC_ROOT` 를 참조하지 않는다.
   (`test_public_asset_private_boundary`)
7. `.chezmoiignore` 가 `profile2/skills/**/__pycache__`, `profile2/skills/**/*.pyc` 를 제외한다.
   규칙 자체도 지웠다. (`test_profile2_public_asset_denylist`)
8. 소유 파일 목록에 미러 45개 경로가 있고 모두 존재한다. (`test_file_ownership`)
9. 두 가이드 문서가 `quality-reviewer.md` 와 `skills/quality-goal` 을 언급한다.
   (`test_profile_onboarding_documentation_contract`)
10. chezmoi가 `~/.local/share/ai-account-profiles/claude/profile2` 를 만들고 0700으로 관리한다.
    테스트가 아니라 `docs/session-account-profiles.md` 의 계약이었다. 이제 새 머신에서는 profile2
    home이 생기지 않고, 기존 home의 mode는 chezmoi 밖에서 유지된다.
11. `CLAUDE_CONFIG_DIR` 가 profile2 home인 세션에서 `quality-goal` 스킬과 `quality-reviewer`
    에이전트를 쓸 수 있다. `.chezmoiremove` 적용 뒤에는 배포본도 사라진다. `claude-profile2` 는
    기본 home(`~/.claude`)을 쓰므로(#136) 그 경로의 스킬에는 영향이 없다.

## 더 강한 검사로 대체된 계약 (7개)

1. profile2 source의 git 관리 파일이 공개 파일 집합과 같다(여분 파일 없음) →
   `private_profile2` 가 파일 시스템에 아예 없다.
2. source·렌더 내용에 비밀 sentinel이 없다 → 같은 부재 검사로 포섭.
3. profile2 source 최상위가 정확히 `{agents, skills}` 다 → 같은 부재 검사로 포섭.
4. profile2 source에 계정 상태 이름이 없다 → 부재 검사 + `.chezmoiremove` 에 계정 상태 경로가 없다.
5. `.chezmoiignore` 가 `profile2/agents/**`·`profile2/skills/**` 를 무시하지 않는다 → 제거 대상 두
   경로와 그 상위를 덮는 무시 규칙이 하나도 없다(`fnmatchcase`, 과잉 매칭 방향).
6. profile2 source에 symlink가 없다 → 부재 검사로 포섭.
7. profile2 source 경로가 세 단계 모두 `private_` 다(상수 비교) → 실제 디렉터리
   `dot_local/share/private_ai-account-profiles/private_claude/private_profile1` 이 존재하고, 세 단계의
   public twin이 없다. profile1 source 내용은 `tests/test_claude_profile1_launcher.py` 가 검사한다.

## 이미 배포된 profile2 사본 (이슈 항목 4)

조정자 결정으로 chezmoi가 제거한다. 저장소 최초의 `.chezmoiremove` 에 리터럴 두 경로만 적었다.

- `.local/share/ai-account-profiles/claude/profile2/skills/quality-goal`
- `.local/share/ai-account-profiles/claude/profile2/agents/quality-reviewer.md`

근거는 다음과 같다. 2026-09-18 실측에서 `CLAUDE_CONFIG_DIR` 가 profile2 home인 프로세스는
0개였고, 배포본은 이미 source 정본과 3개 파일(`SKILL.md`, `scripts/quality_state.py`,
`tests/test_quality_state.py`)이 달랐다. 그대로 두면 그 home으로 띄운 세션이 구버전 스킬을 조용히
실행한다. 수동 삭제는 다른 머신에서 재현되지 않는다.

격리한 source·destination·state로 chezmoi v2.70.0 동작을 확인했다.

- `chezmoi diff` 는 두 경로를 삭제로 먼저 보여 주고, `apply` 는 묻지 않고 두 대상만 지운다. 무시
  규칙에 걸린 `__pycache__` 도 디렉터리와 함께 지워진다. `settings.json`, `sessions/`, 다른
  `agents/*.md` 는 남는다.
- 주석 줄(`#`)은 허용된다. 대상이 없는 머신에서는 아무 일도 하지 않는다.
- `.chezmoiignore` 가 대상을 덮으면(예: `profile2/skills/**`) chezmoi는 삭제를 **조용히 건너뛴다**.
  그래서 `test_profile2_mirror_removal_is_exact` 가 이 조합을 막는다.

이 `.chezmoiremove` 는 한시적이다. 모든 머신에 적용이 끝나면 두 줄과 파일, 고정 테스트를 함께
걷어낸다. 적용(`chezmoi apply`)은 이 작업에서 실행하지 않았다.

## #70 2단계 Plan 인계 (이슈 완료 기준 6)

`docs/development/2026-09-15-70-quality-goal-plan-author-readiness/plan.md` 의 미러 항목이 필요 없어졌다.

- 21행·188행: 착수 선행 조건 중 "profile2 미러와 `test_profile2_quality_bundle_mirror`" 설명.
- 22행: "profile2 미러 동기화" 규칙 전체.
- 44~47행 "미러에도 추가" 문구와 48행 File map의 미러 행.
- 62행 완료 조건의 미러 반영 문장, 74·86·98·112·124·140·152행의 태스크별 "미러:" 줄.
- 184행 CMD-11. 이 명령은 이제 `NO TESTS RAN` 으로 **종료 코드 5** 를 낸다. 그대로 두면 T8 최종
  검증이 실패하므로 반드시 빼야 한다.
