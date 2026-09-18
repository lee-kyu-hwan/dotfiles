# #80 최종 정리 handoff

이 문서는 quality-goal 워크플로가 `COMPLETED` 로 끝난 **뒤에** root 지시로 수행한 별도 최종 점검의
기록이다. 기존 완료 판정을 대체하거나 갱신하지 않는다. quality-goal 의 라운드 기록(Spec 2, Plan 2,
코드 3)과 `COMPLETED` 상태는 그대로이며, 이 점검 결과는 그 게이트를 다시 통과했다는 뜻이 아니다.

- 대상 base commit: `067923b`
- 점검일: 2026-09-15
- 소유 범위: 이 문서와 `report.md` 뿐. 스킬 소스·테스트·픽스처·계약 문서·승인 Spec/Plan 은 수정하지 않았다.

## 1. report.md 정정 (2 건)

| 항목 | 이전 | 정정 |
|---|---|---|
| 분류 평가 범위 | "어휘와 한 줄 범위라는 한계" | `same-line-prefix` 우선, 이어서 `previous-line`. 두 범위 모두에서 PR URL 제거 후 키워드 탐색. 더 떨어진 라벨·목록 밖 동의어·모호한 산문은 호출자 검토 |
| 픽스처 개수 | 7 개 | 10 개 (실측) |

## 2. 최종 재실행 결과

전부 `PYTHONDONTWRITEBYTECODE=1` 로 실행했고 종료 코드는 모두 0 이다.

| 대상 | 결과 |
|---|---|
| 신규 curated 전체 | `Ran 34 tests` OK |
| 형제 collector | `Ran 115 tests` OK |
| analyzer | `Ran 30 tests` OK |
| candidate verifier | `Ran 62 tests` OK |
| skill validator (`quick_validate.py`) | `Skill is valid!` |
| analyzer validator (fresh) | `Validated 2 records (schema 1.0.0).` |
| analyzer validator (append-only) | `Validated 1 records ... against existing corpus.` |
| curated revision | `sha256:72f3798b39443c9021097bbf0c235b9f39388af892ec52de5851816d286927cb` |
| 형제 revision | `sha256:8a6d2d3b4744c761fa6ee217991ec94e0f6323eb336de429f3f15b664f5ed58e` |

`diff-check` 전문은 `.claude/quality-state/<task-id>/final-handoff/diff-check.md` 에 있다. 요약:
추적 파일 변경은 형제 collector 3 개(+282/−18)뿐이고, 병합 영역 밖 함수 8 개
(`_observation_identity`, `collect_repository_hits`, `_append_state_history`, `_json_equal`,
`_greatest_pr_id`, `_record_body_sha256`, `_record_updated_at`, `_find_merge_match`)가 바이트 동일하며,
형제 `github-rest-contract.md`·`SKILL.md`·`agents/openai.yaml` 과 analyzer·verifier 는 변경 0 건이다.

## 3. 읽기 전용 무결성

리뷰 대상 25 개 파일의 SHA-256 을 리뷰 전후로 비교해 전부 동일함을 확인했다
(`final-handoff/integrity-before.txt`, `integrity-after.txt`). 점검 도중 형제 스킬에
`scripts/__pycache__` 가 한 번 생겼는데 이는 리뷰 에이전트가 모듈을 import 하며 남긴 점검측 부산물이고
`.gitignore` 대상이라 변경 집합에 포함되지 않는다. 삭제 후 0 건을 확인했다.

## 4. pr-review-toolkit 최종 리뷰

공식 스킬 절차대로 스킬 본문과 필요한 원본 역할 정의를 읽고, 적용 영역 다섯 개를 **읽기 전용**으로
수행했다. `code-simplifier` 는 소스를 수정하는 에이전트이므로 "소스 수정 금지" 지시에 따라 제외했다.

수행: code-reviewer, pr-test-analyzer, silent-failure-hunter, comment-analyzer, type-design-analyzer.

### 4.1 오케스트레이터가 직접 실행으로 확정한 결함

아래는 에이전트 보고를 받아 오케스트레이터가 **스스로 재현**한 것만 적는다.

**F1. 원격 텍스트가 GitHub API 경로를 조종한다.**
`PULL_REQUEST_URL` 이 `.` 을 허용해 트래커 댓글의 `https://github.com/../../pull/1` 이
저장소 식별자 `('../..', 1)` 로 추출되고, `_default_hydrator` 가 `/repos/../..` 를 요청한다.
`REPOSITORY` 검증 정규식은 `--tracker-repo` 에만 적용되고 추출된 식별자에는 적용되지 않는다.
셸 주입은 아니지만(argv, `shell=False`) "원격 텍스트는 불활성 데이터" 불변식 위반이다.

**F2. 다중 페이지 트래커가 항상 partial 로 오보고된다.**
`collect_issue_thread` 는 `link is None` 일 때만 정상 종료한다. `Link` 헤더가 있고 `rel="next"` 만
없는 경우(GitHub 이 마지막 페이지에서 실제로 주는 `rel="prev"`/`rel="first"` 형태)는
`link_validation != "valid"` 분기로 떨어져 `pagination-link` failed scope 가 붙고 run 이 partial 이 된다.
`validate_next_link` 는 헤더 없음·마지막 페이지 형태·빈 문자열을 모두 `malformed Link rel=next` 로
동일 분류한다. 댓글 100 개를 넘는 트래커 Issue 는 모두 정상 수집하고도 항상 partial 이 된다.

**F3. 예시·공지 분류가 양방향으로 틀린다.** 네 사례를 실행으로 확인했다.

| 입력 | 기대 | 실제 |
|---|---|---|
| 실제 제출 위에 무관한 "예시" 문장 | submission | **제외됨** (한국어는 단어 경계 없는 부분 문자열) |
| `Examples:` (복수형) | 제외 | **수집됨** (영어는 글자 경계 필요) |
| `Notices:` (복수형) | 제외 | **수집됨** |
| 라벨에 issue URL + 실제 제출 | submission | **제외됨** (`PULL_REQUEST_URL.sub` 는 `/pull/` URL 만 제거) |

**F4. manifest append-only 위반.** `main` 의 후처리 `ValueError` 처리부가
`records: [failed_record]` 만 써서 이전 이력을 버린다. 별칭 검사는 `--output` 대 `--manifest` 만 비교하고
`--manifest` 가 `--existing-manifest` 와 같은 경로인 경우를 막지 않는다.
재현 가설이던 `--resume-run-id` 불일치는 네트워크 **이전** 검사라 트리거가 아님을 확인했다.
따라서 트리거는 요청 이후 처리 오류이며, 라이브 재현이 아니라 코드 경로 확인까지다.

**F5. 실패 경로 manifest record 가 계약 필수 필드를 빠뜨린다.**
run record 키 집합이 정상 30 개, preflight 실패 21 개, 후처리 실패 20 개다. 계약은 "Every run records
... cap" 을 요구하지만 두 실패 경로 모두 `max_prs` 가 없고 `cap_exclusions`, `reference_exclusions`,
`checkpoint`, `preflight` 도 없다. 테스트의 필수 필드 집합에 `max_prs` 가 없어 잡히지 않는다.

**F6. 같은 저장소 PR 마다 저장소 메타데이터와 license 를 중복 요청한다.**
`_default_hydrator` 는 호출마다 `license_cache={}` 를 새로 만들고 저장소 메타데이터 캐시도 없어
`client.get_json("/repos/" + repository)` 를 PR 마다 다시 호출한다. 형제 본 흐름은 `license_cache` 를
한 번 만들어 전체 hydration 에 공유한다. 같은 저장소 PR 이 N 건이면 불필요한 요청이 `2×(N-1)` 건이며,
공유 `--request-budget` 를 조기 소진시켜 complete 실행을 partial 로 떨어뜨릴 수 있다.
`_default_hydrator` 를 타는 유일한 테스트가 `--max-prs 1` 이라 잡히지 않는다.

**F7. 두 번째 임시 파일 생성이 실패하면 첫 번째 임시 파일이 남는다.**
`persist_outputs` 에서 manifest 쪽 `_write_temporary` 가 던지면 정리용 `try` 블록에 진입하기 전이라
corpus 임시 파일이 목적지 디렉터리에 남는다. 계약의 "임시 파일을 제거한다" 와 어긋난다.

**F8. `evals/behavioral-eval.md` 에 절대 경로가 들어 있다.**
이 파일은 `docs/**` 와 달리 `dot_codex/` 아래라 chezmoi 로 `~/.codex` 에 배포된다. 현재 2 곳에
사용자 홈 경로가 그대로 있다. 이번 변경이 만든 관행은 아니지만(저장소에 선례 있음) 배포 대상이라는
점에서 한 번 정리해 둘 만하다. 독립 평가자가 작성한 증거 문서라 이번 점검에서는 수정하지 않았다.

### 4.2 에이전트가 보고했고 오케스트레이터가 재현하지 않은 항목

아래는 각 에이전트가 자체 하네스로 재현했다고 보고한 것이며, 오케스트레이터는 코드 위치만 확인했다.
그대로 인용하되 검증 주체를 구분해 둔다.

- resume checkpoint 재사용이 corpus 를 대조하지 않고 `complete`/exit 0 을 반환한다.
- `_header` 가 "헤더 없음" 과 "헤더 형태를 이해하지 못함" 을 모두 `None` 으로 뭉개 페이지네이션이
  조용히 멈추고 `complete`/exit 0 이 된다.
- `canonicalize_curated_state_history` 의 두 guard clause 가 `state_history` 없는 record 를
  `collected`/`complete`/exit 0 으로 내보낼 수 있다(이미 고친 CODE-002 와 같은 계열).
- 모든 참조가 예시로 분류돼 0 건 수집된 run 이 `complete`/exit 0 으로 보고된다.
- `except OSError` 가 revision 입력 누락·형제 스크립트 권한 오류까지 "output persistence failed"/exit 4 로
  분류한다(계약상 exit 2 대상).
- `persist_outputs` 의 복원이 실패하면 corpus 는 새 내용, manifest 는 옛 내용으로 불일치가 남는다.
- `--existing-corpus` 내용이 `null` 이면 경로 검사와 값 검사가 어긋나 기존 corpus 가 덮인다.
- 예산 소진이 위치에 따라 `hydration`/`budget`/`pagination` 세 가지 `kind` 로 갈린다.
- `usable_records` 가 병합 후 corpus 를 보므로 이번 run 이 0 건이어도 partial/exit 3 이 된다.
- 테스트 픽스처가 살아 있는 skill revision 을 고정해, 어떤 변경이든 픽스처 재생성을 강요하고
  그 과정에서 행위 변화가 흡수될 수 있다. 재생성 후 13 개 변이가 테스트 실패 없이 생존했다.
- `validate_next_link` 의 다섯 guard 중 네 개(외부 host, 미지원 query, page 불일치, `per_page`)가
  픽스처로 도달되지 않는다.
- `warnings` 는 초기화만 되고 어디서도 append 되지 않으며, `checkpoint` 는 항상 `False` 인데
  계약은 체크포인트의 존재를 전제한다.
- `--print-revision` 이 파서에 등록되지 않고 argv 완전일치로만 처리돼 `--help` 에 나오지 않는다.
  `SKILL.md` 는 `--help` 로 인터페이스를 확인하라고 안내한다.
- `api_version` 폴백 문자열이 세 곳에 하드코딩돼 형제 `API_VERSION` 과 조용히 어긋날 수 있다.

### 4.3 문서가 코드보다 넓게 약속한 항목

- 계약의 "접근 실패 PR 은 `unknown` state 로 보존" 은 hydrator 가 레코드를 **반환할 때만** 성립한다.
  저장소 자체가 404 면 예외가 발생해 제출이 corpus 에서 제외된다. 3 차 독립 평가에서 `gone-lib#77` 이
  corpus 3 건에 없던 것이 이 현상이며, eval 문서 기술이 정확하고 계약 문서가 틀렸다.
- 계약의 exit 4("no usable record")는 `--existing-corpus` 에 이전 레코드가 있으면 도달하지 않는다.
- `SKILL.md` 에 exit 2 안내가 없다.

## 5. 상태

- 소스·테스트·픽스처·계약 문서·승인 Spec/Plan: **수정하지 않음**
- 이번 점검에서 수정한 파일: `report.md`(2 건 정정), 이 문서
- commit, push, PR, merge, 배포: **수행하지 않음**. 전부 root 담당.
- `CODE-013`(`canonicalize_curated_state_history` 의 미사용 `captured_at`)은 root 지시대로
  이번 검증된 소스에서 유지하고 후속으로 남긴다.

위 4.1 의 F1~F5 와 4.2 의 항목들은 root 의 판단 대상이다. 수정 여부와 범위가 정해지면 그 변경은
새 검증과 새 리뷰를 거쳐야 하며, 이 문서의 재실행 결과를 그 근거로 재사용할 수 없다.
