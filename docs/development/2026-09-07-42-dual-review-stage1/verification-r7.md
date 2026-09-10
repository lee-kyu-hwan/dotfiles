# 독립 검증 — fix 라운드 r7 이후

- 시각: 2026-09-08T05:03:56Z
- 대상: 4차 독립 점검의 `CODE-R4-02`~`06` 수정 (`CODE-R4-01` 은 반박·미수정)

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

## 변이 자기점검 — r7 다섯 수정

각 수정이 겨냥한 경계를 한 곳씩 고쳐 전체 스위트가 실패하는지 확인하고 복구했다.

| 변이 | 대상 | 결과 |
|---|---|---|
| `assign_anonymous_groups` 의 run ID SHA 유도를 `execution_number % 2` 로 되돌림 | CODE-R4-02 / R6.3 | 잡힘 |
| `snapshot_from_repository` 의 명시 `--base` 감지를 `False` 고정 | CODE-R4-04 / R1.1 | 잡힘 |
| 교차 비평 대상을 `(("claude","claude"),("codex","codex"))` 로 뒤집어 self-critique 화 | CODE-R4-05 / R4.1 | 잡힘 |
| synthesis 프롬프트에서 R6.4 세 분류 규칙 문장 삭제 | CODE-R4-03 / R6.4 | 잡힘 |
| `two_quiet_rounds` 후보 추가를 `pass` 로 | CODE-R4-05 / R5.2 | 잡힘 |
| critique provenance occurrence 누적을 지역 dict 로 폐기 | CODE-R4-06 / R4.4 | 잡힘 |

여섯 전부 잡혔고 놓친 변이는 없다. 매번 원본 복구 후 전체 스위트 OK 를 재확인했다.

## r7 수정 실측

| 요구사항 | 수정 전 | 수정 후 |
|---|---|---|
| `R6.3` | `assign_anonymous_groups()` 가 `run_id` 를 읽지 않음 — 홀수 실행은 언제나 claude=A | `sha256(run_id)` 첫 바이트 parity 로 base 배정, 실행 번호 parity 로 반전 (`review_state.py:184`) |
| `R1.1` | 인자 해석 전 무조건 `git rev-parse HEAD^` — 부모 없는 HEAD 에서 명시 base 여도 즉사 | 명시 `--base` 유무를 먼저 판정, 없을 때만 resolve (`review_state.py:633-634`) |
| `R6.4` | 세 분류 규칙이 프롬프트·스키마 어디에도 없음 | synthesis 프롬프트 `contract` 문자열에 명시 (`review_state.py:505`). **Python 에 oracle 은 추가하지 않음** |
| `R4.4` | provenance 가 `finding_id` 당 단일 dict 를 `update` — 재등장 시 앞 라운드 유실 | `finding_id` 당 occurrence 배열로 누적 (`review_state.py:161-163`) |

테스트 63 → **72** (+9).

## 워치독 결함 — 이번에 실측된 것

r7 실행에서 워치독이 `events_stale` 로 프로세스를 회수했는데(`13:57:29`), **Codex 는
`14:02:38` 까지 계속 작업해 정상 완료했다.** 두 가지가 겹쳤다.

1. **`proc.terminate()` 가 `sh -c` 만 죽이고 자식 `codex` 를 고아로 남긴다.** 프로세스 그룹을
   죽이지 않으므로 회수가 실제로 회수가 아니다.
2. **정체 판정 근거인 events 파일 mtime 이 진행도를 반영하지 않는다.** `> events.jsonl`
   리다이렉트는 블록 버퍼링이라 mtime 이 수 분씩 건너뛴다. 실측: 544KB / 135행.

결과적으로 이번엔 손해가 없었지만(고아 프로세스가 일을 끝냈다), 워치독은 **정상 작업을 죽이려
시도하고 실패했다.** 진짜 무응답이었다면 회수에도 실패했을 것이다. 감시 신호를 mtime 이 아니라
events **행 수 증가** 로 바꾸고, 종료는 프로세스 그룹(`start_new_session=True` + `killpg`)으로
해야 한다.
