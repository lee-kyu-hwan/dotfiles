# #209 결과 파일 권한 시험 보충 (2026-09-26)

[원본 조사 보고서](./2026-09-26-orca-worker-done-transport.md)의 후속 실측이며, 원본을 대체하지 않는다.

워커가 결과 파일을 쓸 때 Write 권한 경계가 실제로 어떻게 동작하는지 확인했다. 세 가지 조건에서 결과 파일 쓰기는 성공했고, 금지 파일 쓰기는 모두 거부됐다.

## 시험 조건

- Claude Code 2.1.283, Orca 1.4.210, profile2 비-Dispatch 단회 실행
- 실행 명령에서 GH_TOKEN, GITHUB_TOKEN 제거
- Bash/MCP/Web 도구 미제공
- 외부 저장소 쓰기 없음

## 결과

| 시험 | 조건 | 결과 |
|---|---|---|
| 1 | 임시 fixture, `--restricted --tools Write --permission-mode acceptEdits` | result.json 성공, 상위 디렉터리 금지 파일 거부(is_error true, 미생성), permission_denials 1건, 종료코드 0 |
| 2 | 임시 fixture, `--allowedTools 'Edit(result.json)' --permission-mode dontAsk` | result.json 성공, 같은 디렉터리 sibling.json 거부(미생성), permission_denials 1건, 종료코드 0 |
| 3 | #209 워크트리, `--allowedTools 'Edit(...fixture.json)' --permission-mode dontAsk --no-session-persistence` | 허용 파일 성공, 같은 디렉터리 금지 파일 거부(미생성), permission_denials 1건, 종료코드 0 |

결과 파일 fixture: [결과 파일](./2026-09-26-209-result.fixture.json)

## 확인한 증거

- 세 시험 모두 stream-json 로그에서 Write 도구 호출과 결과를 확인함
- [권한 문서](https://code.claude.com/docs/en/permissions)를 2026-09-26에 직접 확인: 경로 기반 권한 규칙은 `Write(path)`가 아니라 `Edit(path)` 형식이며, Write 파일 도구에도 동일 규칙이 적용됨 → 실측과 일치
- 원시 run.jsonl 로그는 /private/tmp에만 보관, Git 저장소에는 미포함
- 기존 #209 관련 Dispatch 기록은 변경 없이 보존

## 한계 / 다음 순서

- 기존 A/B 시험(Read 도구, 3줄 ACK)과 이번 Write 시험을 하나의 Dispatch 실행으로 결합한 End-to-End 시험은 미수행
- 결과 파일 내용이 실제 테스트/코드 변경 사실을 반영하는지 검증하는 자동 절차 없음
- Orca worker_done 신호 전송·조정자 수락, C 단계 정산 로직은 시험 범위 외
- 다음 단계: 결과 파일 스키마와 조정자 재검증 계약을 #209 문서에 명시하고, 안전한 Dispatch 전용 reporter 경로 마련 후에만 C 단계 시험 진행
- 현재까지 실측만으로 결과 파일 존재가 작업 완료를 의미한다고 주장할 수 없음
