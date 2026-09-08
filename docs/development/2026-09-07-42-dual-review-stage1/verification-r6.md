# 독립 검증 — fix 라운드 r6 이후

- 시각: 2026-09-08T04:07:17Z
- 워크스페이스 지문: `record-verification` 으로 state.json 에 기록 (문서 본문에 적으면 자기 참조가 되어 값이 어긋난다)
- 실행 디렉터리: 워크트리 루트

## 판정 명령 재실행 (spec.md:246-257)

| ID | 종료 코드 | 판정 |
|---|---|---|
| CMD-1 | 0 | PASS |
| CMD-2 | 0 | PASS |
| CMD-3 | 0 | PASS |
| CMD-4 | 0 | PASS |
| CMD-5 | 0 | PASS |
| CMD-6 | 0 | PASS |
| CMD-7 | 0 | PASS |
| CMD-8 | 0 | PASS |
| CMD-9 | 0 | PASS |
| CMD-10 | 0 | PASS |
| CMD-11 | 0 | PASS |
| CMD-12 | 0 | PASS |

## 금지 문자열 스캔 자기 문서 오탐 점검

CMD-4·5 는 스킬 디렉터리 전체(`--hidden --no-ignore`)를 스캔한다. 스킬 자신의 문서가
금지 옵션·GitHub 쓰기 명령을 우회 표기(플레이스홀더)로만 언급하므로 무매치가 성립한다.

우회 표기 실제 출현 위치:
```
  dot_claude/skills/dual-review/references/verification.md:23:use the safe placeholders `<forbidden-codex-option-N>` and
  dot_claude/skills/dual-review/references/verification.md:24:`<github-write-command-N>`.
```

## 변이 자기점검 (테스트가 실제로 결함을 잡는지)

`review_state.py` 를 한 곳씩 고쳐 전체 스위트가 실패하는지 확인 후 복구했다.

| 변이 | 대상 경계 | 결과 |
|---|---|---|
| drift 중단 시 판정 기록 제거 | CODE-19 | 잡힘 |
| drift 최종 후보 선정 변경 | CODE-19 | 잡힘 |
| 라운드 0 read/start 순서 뒤집기 | 독립성 | 잡힘 |
| `fid_` 접두사 제거 | R3.2 | 잡힘 |
| 종료 사유 전순서 뒤섞기 | R7.1 | 잡힘 |
| `CLAUDE_PRODUCERS` 목록 축소 | R2.1 | 잡힘 |
| 심각도 변환표 항목 제거 | R2.1 | 잡힘 |
| `PUBLIC_FINDING_FIELDS` 에 실제 `source` 재추가 | R6.2 | 잡힘 (경화 후) |
| 사이드카에서 `original_id` 삭제 | R7.2 | 잡힘 (경화 후) |
| 마스크 정렬 키 되돌리기 | R6.3 | 잡힘 (경화 후) |
| synthesis required 에서 `classification` 제거 | CODE-R3-04 | 잡힘 |
| synthesis required 에서 `decision_confidence` 제거 | CODE-R3-04 | 잡힘 |
| 익명 그룹 소속 검사 무력화 (`review_state.py:253`) | CODE-R3-04 | 잡힘 |
| `structured_output` 추출 제거 | CODE-R3-01 | 잡힘 |
| `_claude_payload` 무력화 | CODE-R3-02 | 잡힘 |

놓친 변이 없음. 변이 후 매번 원본으로 복구하고 전체 스위트 OK 를 재확인했다.

## 변경 범위

```
  ?? .codex-author/
  ?? .codex-readiness/
  ?? docs/development/2026-09-07-42-dual-review-stage1/
  ?? dot_claude/skills/dual-review/
```

`.codex-author/`·`.codex-readiness/` 는 Codex author·readiness 실행 디렉터리로 산출물이
아니다. 구현 산출물은 `dot_claude/skills/dual-review/` 와 문서 디렉터리 둘뿐이다.

### 무관 변경 1건 회수

Codex 라운드 중 워크트리 루트에 `AGENTS.md` 가 생성되어 있었다. 내용은 `CLAUDE.md` 를
`Claude`→`Codex` 로 기계 치환한 것으로, `~/.Codex/skills/`·`Codex.ai/code`·
`run_once_install-Codex-plugins.sh.tmpl` 처럼 실재하지 않는 경로를 만들어낸 오염본이다.
Plan 어느 태스크의 산출물도 아니므로 워크트리 밖으로 회수했고, 회수 후 지문을 재계산했다.

구현 파일 수: 17
테스트 수: Ran 63 tests

## AC 식별자 전수 대조

`spec.md` 의 AC 71건에서 백틱 식별자 118개를 뽑아 구현 트리(17파일) 전문과 대조했다.
판정 명령 자체를 제외하면 실제 식별자는 넷이고 전부 해명된다.

| AC | 식별자 | 대조 결과 |
|---|---|---|
| AC-5 | `.claude/dual-review-state/` | 존재 — `review_state.py:282`(스캔 제외), `review_state.py:294`(run root 생성) |
| AC-28·29 | `--rounds=1` / `--rounds=2` | 존재 — `review_state.py:25` 가 `--rounds=` 등호 형식을, `:27` 이 분리 형식을 파싱 |
| AC-8·50 | `code-simplifier` | **의도적 부재.** `test_no_mutation_contract` 가 `"code" + "-simplifier"` 로 문자 분리해 단언하므로 리터럴이 트리에 남지 않는다. CMD-4·5 자기 오탐 회피와 같은 규약이다 |

AC-8("`code-simplifier` 가 호출 목록에 없는 fixture 테스트가 있다")은 `test_reviewer_contract`
가 `CLAUDE_PRODUCERS` 를 다섯 역할과 **정확 일치**로 단언해 충족된다. 정확 일치는 특정 이름의
부재를 단언하는 것보다 강하다.

이 대조는 판정 명령 통과와 독립적이다 — r1 에서 12/12 exit 0 이면서 구현이 Plan 을 수행하지
못했던 실패 양상을 겨냥한 것이다.
