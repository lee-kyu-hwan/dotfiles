# 독립 검증 — fix 라운드 r8 이후 (공식 Code 리뷰 라운드 2 제출본)

- 시각: 2026-09-08T05:30:25Z
- 워크스페이스 지문: `record-verification` 으로 state.json 에 기록
- 대상: 5차 독립 점검의 `CODE-R5-01`~`03` 수정

## 판정 명령 (spec.md:246-257)

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

전체 스위트 **72 tests OK**.

## CODE-R5-01 실측 — 수정 전후

`R6.3` 은 "재실행 구분자로 A/B를 **교대**"를 요구한다. `make_run_id()` 가 만드는 run ID 가
`<target16>-<실행번호>` 라 실행 번호를 이미 포함하는데, 배정 함수가 그 전체를 해시하고 다시
실행 번호 parity 로 반전해 두 parity 가 상쇄됐다.

수정 전 (base/head 고정, 실행 1~12의 claude 그룹):

```
1:B 2:B(실패) 3:A 4:B 5:A 6:B 7:B(실패) 8:A 9:A(실패) 10:B 11:A 12:B
연속 11회 전이 중 교대 실패 3회
```

수정 후 (`run_id.rsplit("-", 1)[0]` 로 target 만 해시), base/head 6쌍 × 실행 1~12:

```
fixture 1: BABABABABABA    fixture 4: ABABABABABAB
fixture 2: ABABABABABAB    fixture 5: ABABABABABAB
fixture 3: BABABABABABA    fixture 6: ABABABABABAB
전체 전이 66회 중 교대 실패 0회
```

target 별로 base 배정이 갈리고(fixture 1·3 대 나머지), 같은 run ID 는 재현된다.

## 변이 자기점검 — r8

| 변이 | 대상 | 결과 |
|---|---|---|
| `run_id.rsplit("-", 1)[0]` target 추출 훼손 | CODE-R5-01 / R6.3 | 잡힘 |
| `합의`↔`불일치` 연결 뒤바꿈 | CODE-R5-02 / R6.4 | 잡힘 |
| `단일 출처`→`합의` 오연결 | CODE-R5-02 / R6.4 | 잡힘 |
| `불일치`→`단일 출처` 오연결 | CODE-R5-02 / R6.4 | 잡힘 |
| 병합·분할 자율성 문장 삭제 | CODE-R5-02 / D7 | 잡힘 |

`Classification rules` → `Classification hints` 처럼 **의미를 담지 않는 접두 문구** 변경은
잡히지 않는다. 이는 결함이 아니다 — 계약은 조건과 enum 의 연결이지 표제어가 아니다.

## 누적 변이 점검

| 라운드 | 경계 수 | 놓침 |
|---|---|---|
| r6 | 15 | 0 |
| r7 | 6 | 0 |
| r8 | 5 | 0 |
| **누적** | **26** | **0** |

`CODE-R4-05`(5차 점검)는 오케스트레이터의 r6 시점 15개 목록 **밖**의 경계에서 나왔다.
변이 점검을 했다는 사실이 변이 점검의 완전성을 뜻하지 않는다.

## 변경 범위

```
?? .codex-author/          (초기 dirty, 이 작업의 산출물 아님)
?? .codex-readiness/       (초기 dirty, 이 작업의 산출물 아님)
?? docs/development/2026-09-07-42-dual-review-stage1/
?? dot_claude/skills/dual-review/
```

커밋·머지·PR·`chezmoi apply` 를 수행하지 않았다. 다른 워크트리와 전역 배포본을 건드리지 않았다.
Codex 가 만든 무관 파일 `AGENTS.md` 1건은 회수했다(`verification-r6.md`).
