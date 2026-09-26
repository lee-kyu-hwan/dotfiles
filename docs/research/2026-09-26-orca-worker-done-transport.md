# Orca 워커 완료 전송 경로 조사 (2026-09-26)

업데이트: 이 문서의 결과 파일 쓰기 미시험 표기는 작성 당시 상태다. 같은 날 수행한 지정 파일 허용·형제 파일 거부 실측은 [권한 시험 보충](./2026-09-26-orca-worker-done-fixture-addendum.md)에 기록했다. Orca worker_done과 C 단계 정산은 여전히 미시험이다.

## 범위와 성격

- 대상: dotfiles #67(epic) / #209(결과 파일 계약), 설치된 Orca 1.4.210, Claude Code 2.1.283
- 저장 위치: `docs/research/2026-09-26-orca-worker-done-transport.md`
- 목적: 옆 pane에서 진행한 Claude deep research의 결론을 저장소에 보관한다.
- 이 문서는 **C 단계 구현 보고나 시험 완료 보고가 아니다.**
- 이 문서는 Claude profile2의 도구 0개 단회 출력으로 작성했다. 새 워크트리의 이 파일 하나로만 캡처한다.
  - 이 실행은 Orca Dispatch가 아니다.
  - C 시험 성공을 뜻하지 않는다.
- 이번 실행에서 하지 않은 일: 외부 저장소, GitHub API, chezmoi, 전역 설정에 대한 쓰기.
- 이 문서에 적지 않은 내용: 원시 터미널 로그, capability 값, 인증 정보, 내부 프롬프트.

아래 내용은 **확인 사실 / 연구 pane 주장 / 추론 / 미검증**으로 나눈다.

## 1. 확인 사실 (로컬에서 직접 확인)

- **orchestration 가이드**: 설치된 `orca skills get orchestration` 가이드는 정식 완료 조건을 다음과 같이 규정한다.
  - 활성 Dispatch의 live preamble에 있는 Task ID, Dispatch ID, capability를 사용한다.
  - `worker_done`을 **정확히 한 번** 보낸다.
  - 수락되면 Task와 Dispatch가 정산(settlement)된다.
- **send 도움말**: `orca orchestration send --help`는 `worker_done`이 dispatched pane에서만 해당 Task를 완료한다고 명시한다.
- **옛 #209 Dispatch**: `ctx_75745663bdc9`는 다음 상태로 남아 있다.
  - `dispatched` / `stop_unknown`
  - capability revoked
  - terminal retained
  - 따라서 새 C 시험에 재사용하면 안 된다.
- **이전 A/B 시험에서 확인된 범위**: Claude가 명세 파일 3개를 Read하고 3줄 ACK를 남긴 것까지다.
  - 제한된 결과 파일 쓰기는 확인되지 않았다.
  - 실제 `worker_done` 전송도 확인되지 않았다.
- **새 워크트리**: 2026-09-26에 epic-67 아래 자식 워크트리 `209-result-file-contract`를 만들었다. 이 보고서 작업 전에는 clean 상태였다.
- **옛 초안**: 옛 #209 초안 3파일은 다른 워크트리의 미추적 파일이다. 손대지 않고 그대로 보존했다.

## 2. 연구 pane 주장 (옆 pane Claude deep research 제안)

아래 항목은 연구 pane의 주장이다. 이번 실행에서 독립적으로 검증하지 않았다.

1. **로컬 결과 파일**: 작업별 로컬 결과 파일은 증거로 유용하다. 명세, ACK, 테스트, diff 범위, 실패 내용을 남길 수 있다.
   - 다만 파일이 있다는 사실이나 JSON 스키마가 맞다는 사실만으로는 실행의 진실성을 보장하지 않는다. Orca settlement도 보장하지 않는다.
   - 조정자가 git diff와 테스트를 다시 검증해야 한다.
2. **공용 디렉터리**: 여러 문제가 있다.
   - 다중 writer 충돌
   - 같은 UID 아래에서 변조 가능성
   - Task/Dispatch 상태와의 불일치
3. **GitHub Issue/댓글/check-run**: 이번 전송 경로에서 제외한다.
   - 외부 쓰기 권한과 알림이 따라온다.
   - 로컬 Dispatch 정산을 대신하지 못한다.
4. **Orca reporter `worker_done`**: 공식 lifecycle authority다.
   - 그러나 제한된 Claude에 해당 Dispatch 권한만 사적으로 묶어 주는 경로는 설치 버전에서 확인되지 않았다.
   - 관련 Orca 이슈 [#17632](https://github.com/stablyai/orca/issues/17632), [#22653](https://github.com/stablyai/orca/issues/22653), [PR #22205](https://github.com/stablyai/orca/pull/22205)는 후속 확인 대상으로만 기록한다. 현재 상태는 단정하지 않는다.
5. **Dispatch 없는 작업**: 별도 runner가 `claude -p`의 종료 코드와 구조화 출력을 수집할 수 있다.
   - 하지만 이 방식은 Orca Run의 inbox, heartbeat, ask, `worker_done`을 갱신하지 않는다.
   - 이전 pane은 `--bare`가 OAuth/keychain을 읽지 않는다고 문서를 해석했다. 이번 실행은 `--bare`를 쓰지 않았다.

## 3. 경로 비교

| 경로 | 장점 | 위험·한계 | Orca 정산 | 이번 판단 |
|---|---|---|---|---|
| 공용 디렉터리 | 구현이 단순하고 로컬에서 끝난다 | 다중 writer 충돌, 같은 UID 변조, Task/Dispatch 상태 불일치 | 대체 불가 | 채택하지 않음 |
| GitHub Issue/댓글/check-run | 가시성이 높고 이력이 남는다 | 외부 쓰기 권한과 알림 발생, 게시 후 회수가 어렵다 | 대체 불가 | 이번 경로에서 제외 |
| 작업별 로컬 결과 파일 | 명세·ACK·테스트·diff 범위·실패 증거를 워크트리 단위로 격리할 수 있다 | 존재나 스키마만으로 진실성을 보장하지 못한다. 조정자 재검증이 필요하다 | 대체 불가(증거 보조) | 다음 시험 대상 |
| Orca reporter `worker_done` | 공식 lifecycle authority이고 Task/Dispatch를 정산한다 | 제한된 Claude에 Dispatch 전용 권한만 넘기는 경로가 설치 버전에서 미확인 | 유일한 정식 경로 | 안전 경로가 확인될 때까지 보류 |

## 4. 추론

아래는 1·2절을 바탕으로 한 이 문서의 추론이다. 확인된 사실이 아니다.

- 완료 신호와 완료 증거는 서로 다른 계층이다.
  - 완료 신호는 Orca의 `worker_done`이다.
  - 완료 증거는 로컬 결과 파일과 조정자의 재검증이다.
  - 두 계층을 섞으면 "파일이 있으니 완료"라는 잘못된 판정이 생길 수 있다.
- 로컬 결과 파일은 `worker_done`을 대체하지 않는다. 대신 `worker_done` 이전 단계로 먼저 검증할 수 있다.
  - 이 단계는 외부 쓰기도 없고 capability도 필요하지 않다.
  - 그래서 위험이 가장 낮다.
- 옛 Dispatch는 capability가 회수된 상태다. 재사용하면 정산 불일치나 이중 완료 시도가 생길 수 있다. 새 시험에는 새 Dispatch가 필요하다고 보는 것이 자연스럽다.
- 도구 0개 단회 출력으로 문서를 만든 이번 방식은 쓰기 권한 경계를 시험하지 않는다. 따라서 결과 파일 쓰기 시험의 선례로 볼 수 없다.

## 5. 미검증

- 제한된 Claude 세션이 허용된 경로에만 결과 파일을 쓰고 그 외 경로에는 쓰지 못하는지
- 실제 `worker_done` 전송과 수락, 그리고 그에 따른 Task/Dispatch 정산
- Orca 1.4.210에서 per-Dispatch 권한만 워커에 격리해 넘기는 방법이 있는지
- 위 Orca 이슈와 PR의 현재 상태, 그리고 이후 버전에 반영되었는지
- `--bare`의 인증 동작. 이전 pane의 문서 해석만 있고 실측은 없다.
- 아래 참고 문서의 현재 내용

## 6. 권장 순서

1. **보고서 저장**: 이 문서를 `209-result-file-contract` 워크트리에 보관한다.
2. **결과 파일 쓰기 시험**: 별도의 제한 세션에서 작업별 로컬 결과 파일 쓰기를 시험한다.
   - 쓰기 허용 범위는 해당 결과 파일 하나로 한정한다.
   - 옛 Dispatch `ctx_75745663bdc9`와 해당 터미널의 미제출 입력 초안 한 건 및 옛 워크트리의 미추적 초안 3파일은 손대지 않는다.
3. **결과 검증**: 조정자가 결과 파일 내용을 실제 상태와 대조한다.
   - git diff, 테스트 결과, 쓰기 범위 밖 변경이 없는지를 재검증한다.
   - 파일이 존재한다는 사실만으로 완료로 판정하지 않는다.
4. **C 단계 차단 유지**: 안전한 Dispatch 전용 reporter 경로가 확인되기 전까지 C는 차단 상태로 둔다.
   - 확인 후에는 새 Dispatch를 발급하고 `worker_done`을 정확히 한 번 보내는 시험으로 넘어간다.

## 참고 자료

아래 링크의 내용은 이번 실행에서 직접 읽지 않았다. 이전 조사의 출처이며, 재검증 대상으로 표기한다.

- Orca 공식 CLI 가이드 (orchestration): https://github.com/stablyai/orca/blob/main/skill-guides/orchestration.md
  - 설치본의 `orca skills get orchestration` 출력은 로컬에서 확인했다.
- Claude Code headless: https://code.claude.com/docs/en/headless
- Claude Code CLI reference: https://code.claude.com/docs/en/cli-reference
- Claude Code permissions: https://code.claude.com/docs/en/permissions
- GitHub REST issue comments: https://docs.github.com/en/rest/issues/comments
- GitHub REST checks 가이드: https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-checks
- Orca 후속 확인 대상: [#17632](https://github.com/stablyai/orca/issues/17632), [#22653](https://github.com/stablyai/orca/issues/22653), [PR #22205](https://github.com/stablyai/orca/pull/22205)
