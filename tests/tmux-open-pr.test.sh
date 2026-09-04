#!/usr/bin/env bash
# tmux-open-pr 회귀 테스트.
#
#   tests/tmux-open-pr.test.sh
#
# 이 스크립트의 계약은 "무엇을 stdout 으로 내고 어떤 종료코드로 끝나는가" 다 — run-shell -b
# 가 그 두 개만 보고 패인을 view-mode 로 덮치기 때문이다. 그래서 tmux 를 스텁으로 갈아끼우고
# 계약을 직접 고정한다. 실제 tmux 서버는 **격리 소켓에서만** 띄우고(맨 아래), 기본 소켓은
# 건드리지 않는다.
#
# 여기 고정된 회귀 4건:
#   [F1] display-message 호출이 실패하면 알림 실패로 봐야 한다 (예전엔 rc 를 버려 무음 exit 0).
#   [C1] 상한은 하드 상한이어야 한다 — TERM 을 무시하는 gh·자손이 KILL 로 정리돼야 한다.
#   [C2] helper 가 신호로 죽을 때 gh·감시자·그 sleep 이 고아로 남지 않아야 한다.
#   그리고 위 셋을 고치면서 정상 성공·정상 실패 경로가 깨지지 않았는지.
set -u

repo_root=$(cd "$(dirname "$0")/.." && pwd)
script="$repo_root/dot_local/bin/executable_tmux-open-pr"
[ -x "$script" ] || { echo "실행 파일을 찾을 수 없음: $script"; exit 1; }

work=$(mktemp -d "${TMPDIR:-/tmp}/tmux-open-pr-test.XXXXXX")
# helper 의 임시 파일도 이 안에 떨어지게 해 테스트끼리 격리한다 — 공용 TMPDIR 을 그대로
# 쓰면 다른 실행이 남긴 파일을 잔존으로 세게 된다(실측: 수정 전 실행의 유출물을 수정 후
# 실행이 자기 것으로 셌다).
export TMPDIR="$work"
export TMUX_STUB_DIR="$work"
export TMUX_OPEN_PR_TIMEOUT=2
export TMUX_OPEN_PR_KILL_GRACE=1

pass=0
fail=0

cleanup_all() {
  for f in "$work"/pid.*; do
    [ -f "$f" ] || continue
    while read -r p; do [ -n "$p" ] && kill -9 "$p" 2>/dev/null; done < "$f"
  done
  rm -rf "$work"
}
trap cleanup_all EXIT

ok()  { pass=$((pass + 1)); printf '  \033[32m✔\033[0m %s\n' "$1"; }
no()  { fail=$((fail + 1)); printf '  \033[31m✘\033[0m %s\n' "$1"; }
is()  { # is <설명> <기대> <실제>
  if [ "$2" = "$3" ]; then ok "$1"; else no "$1 — 기대[$2] 실제[$3]"; fi
}
alive()  { [ -n "${1:-}" ] && kill -0 "$1" 2>/dev/null; }
gone()   { # gone <설명> <pid>
  if [ -z "${2:-}" ]; then no "$1 — PID 를 못 읽음"; return; fi
  if alive "$2"; then no "$1 — PID $2 생존 (PPID=$(ps -o ppid= -p "$2" | tr -d ' '))"; else ok "$1"; fi
}
survives() { if alive "$2"; then ok "$1"; else no "$1 — PID $2 이미 종료"; fi; }

# ---------------------------------------------------------------- tmux 스텁
mkdir -p "$work/bin"
cat > "$work/bin/tmux" <<'STUB'
#!/usr/bin/env bash
w="$TMUX_STUB_DIR"
cmd=${1:-}; shift 2>/dev/null || true
case "$cmd" in
  list-clients) cat "$w/clients" 2>/dev/null; exit 0 ;;
  list-panes)   cat "$w/panes"   2>/dev/null; exit 0 ;;
  display-message)
    for a in "$@"; do
      [ "$a" = "-p" ] && { cat "$w/pane_path" 2>/dev/null; exit 0; }
    done
    # tmux <3.2 재현: -d 를 모르는 tmux 는 호출 자체를 rc=1 로 거부한다.
    if [ -e "$w/no_d_flag" ]; then
      for a in "$@"; do [ "$a" = "-d" ] && exit 1; done
    fi
    printf '%s\n' "$*" >> "$w/messages"
    exit "$(cat "$w/dm_rc" 2>/dev/null || echo 0)"
    ;;
esac
exit 0
STUB
chmod +x "$work/bin/tmux"
export PATH="$work/bin:$PATH"

reset_stub() {
  printf '/dev/ttys999\n' > "$work/clients"
  printf '%%1\n'           > "$work/panes"
  printf '%s\n' "$work"    > "$work/pane_path"
  printf '0\n'             > "$work/dm_rc"
  rm -f "$work/no_d_flag" "$work/messages" "$work"/pid.*
}

run_helper() { # run_helper -> stdout 은 $out, 종료코드는 $rc
  out=$("$script" '%1' '/dev/ttys999' 2>/dev/null)
  rc=$?
}

# ---------------------------------------------------------------- 가짜 gh
mk_gh() { # mk_gh <이름> <본문>
  local p="$work/bin/gh-$1"
  { echo '#!/usr/bin/env bash'; echo "$2"; } > "$p"
  chmod +x "$p"
  echo "$p"
}

# 아래 본문들은 가짜 gh **가 실행될 때** 확장돼야 하므로 작은따옴표가 맞다.
# shellcheck disable=SC2016
# 즉시 성공
gh_ok=$(mk_gh ok 'exit 0')
# 즉시 실패 + 사유를 stderr 로
gh_err=$(mk_gh err 'echo "no pull requests found for branch \"x\"" >&2; exit 1')
# 오래 걸리지만 TERM 에는 죽는다
# shellcheck disable=SC2016
gh_slow=$(mk_gh slow 'echo "$$" > "$TMUX_STUB_DIR/pid.gh"; sleep 30')
# TERM 을 끝까지 무시한다 (KILL 승격이 없으면 wait 이 영원히 안 돌아온다)
# shellcheck disable=SC2016
gh_stubborn=$(mk_gh stubborn 'trap "" TERM; echo "$$" > "$TMUX_STUB_DIR/pid.gh"; sleep 30')
# 자기는 TERM 에 죽지만 자손이 TERM 을 무시한다 (그룹 KILL 이 없으면 자손이 고아로 남는다)
# shellcheck disable=SC2016
gh_desc=$(mk_gh desc '
  bash -c '"'"'trap "" TERM; echo "$$" > "$TMUX_STUB_DIR/pid.desc"; exec sleep 30'"'"' &
  echo "$$" > "$TMUX_STUB_DIR/pid.gh"
  wait')

# shellcheck disable=SC2012
leftovers() { ls "$work"/tmux-open-pr.* 2>/dev/null | wc -l | tr -d ' '; }

echo
echo "== 정상 경로 =="
reset_stub; export TMUX_OPEN_PR_GH="$gh_ok"
before=$(leftovers); run_helper
is  "성공: stdout 없음 (view-mode 를 열지 않는다)" "" "$out"
is  "성공: exit 0"                                 "0" "$rc"
is  "성공: 상태바 알림 없음"                       "0" "$([ -f "$work/messages" ] && wc -l < "$work/messages" | tr -d ' ' || echo 0)"
is  "성공: 임시 파일 잔존 없음"                    "$before" "$(leftovers)"

reset_stub; export TMUX_OPEN_PR_GH="$gh_err"
run_helper
is  "실패+알림성공: stdout 없음"  "" "$out"
is  "실패+알림성공: exit 0"       "0" "$rc"
if grep -q 'no pull requests found' "$work/messages" 2>/dev/null; then
  ok "실패+알림성공: gh 사유가 상태바 문구에 그대로 실린다"
else
  no "실패+알림성공: gh 사유가 문구에 없음 — $(cat "$work/messages" 2>/dev/null)"
fi

reset_stub; : > "$work/clients"   # 키를 누른 클라이언트가 사라진 상태
export TMUX_OPEN_PR_GH="$gh_err"
run_helper
case "$out" in *"no pull requests found"*) ok "알림 불가: 사유를 stdout 으로 내보낸다" ;;
                *) no "알림 불가: stdout=[$out]" ;; esac
is  "알림 불가: exit 1 (view-mode 폴백)" "1" "$rc"

echo
echo "== [F1] display-message 실패를 성공으로 오판하지 않는가 =="
# tmux <3.2 재현: -d 는 거부되지만 -d 없는 폴백은 통한다 -> 알림은 성공해야 한다.
reset_stub; : > "$work/no_d_flag"; export TMUX_OPEN_PR_GH="$gh_err"
run_helper
is  "-d 미지원: 폴백으로 알림 성공 -> stdout 없음" "" "$out"
is  "-d 미지원: exit 0"                            "0" "$rc"
if grep -q 'no pull requests found' "$work/messages" 2>/dev/null; then
  ok "-d 미지원: 폴백 호출이 실제로 문구를 전달했다"
else
  no "-d 미지원: 폴백이 문구를 전달하지 못했다"
fi

# 두 호출 모두 실패 -> 알림 실패로 판정해 view-mode 폴백으로 가야 한다.
# 고치기 전에는 rc 를 버려 exit 0 + 무출력, 즉 완전 무음이었다.
reset_stub; : > "$work/no_d_flag"; printf '1\n' > "$work/dm_rc"
export TMUX_OPEN_PR_GH="$gh_err"
run_helper
case "$out" in *"no pull requests found"*) ok "알림 전부 실패: 사유를 stdout 으로 내보낸다 (무음 아님)" ;;
                *) no "알림 전부 실패: stdout=[$out] — 무음 실패 회귀" ;; esac
is  "알림 전부 실패: exit 1 (view-mode 폴백 생존)" "1" "$rc"

echo
echo "== [C1] 하드 상한: TERM 을 무시해도 상한 안에 끝나는가 =="
reset_stub; export TMUX_OPEN_PR_GH="$gh_stubborn"
start=$SECONDS
run_helper
elapsed=$((SECONDS - start))
gh_pid=$(cat "$work/pid.gh" 2>/dev/null)
if [ "$elapsed" -le 8 ]; then
  ok "TERM 무시 gh: ${elapsed}초에 반환 (상한 $((TMUX_OPEN_PR_TIMEOUT + TMUX_OPEN_PR_KILL_GRACE))초 + 여유)"
else
  no "TERM 무시 gh: ${elapsed}초 — 상한이 걸리지 않았다"
fi
is  "TERM 무시 gh: 알림 성공이라 exit 0" "0" "$rc"
if grep -q '안에 끝나지 않아' "$work/messages" 2>/dev/null; then
  ok "TERM 무시 gh: 시간 초과로 보고한다"
else
  no "TERM 무시 gh: 시간 초과 문구가 없다 — $(cat "$work/messages" 2>/dev/null)"
fi
sleep 0.5
gone "TERM 무시 gh: KILL 승격으로 정리됐다" "$gh_pid"

echo
echo "== [C1] 그룹 KILL: TERM 을 무시하는 자손도 거두는가 =="
reset_stub; export TMUX_OPEN_PR_GH="$gh_desc"
run_helper
sleep 0.5
gone "TERM 무시 자손: 그룹 KILL 로 정리됐다" "$(cat "$work/pid.desc" 2>/dev/null)"

echo
echo "== [C2] helper 가 신호로 죽을 때 고아를 남기지 않는가 =="
reset_stub; export TMUX_OPEN_PR_GH="$gh_slow"
"$script" '%1' '/dev/ttys999' >/dev/null 2>&1 &
helper=$!
# gh 와 감시자가 자리를 잡을 때까지 (상한 2초보다 훨씬 전에)
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -s "$work/pid.gh" ] && break; sleep 0.1; done
sleep 0.3
gh_pid=$(cat "$work/pid.gh" 2>/dev/null)
wd_pid=$(pgrep -P "$helper" 2>/dev/null | grep -vx "$gh_pid" | head -1)
wd_sleep=$(pgrep -P "${wd_pid:-0}" 2>/dev/null | head -1)
survives "사전 조건: gh 실행 중"        "$gh_pid"
survives "사전 조건: 감시자 실행 중"    "${wd_pid:-}"
survives "사전 조건: 감시자의 sleep 실행 중" "${wd_sleep:-}"
kill -TERM "$helper" 2>/dev/null
wait "$helper" 2>/dev/null
# 확인 창은 **상한(TMUX_OPEN_PR_TIMEOUT)보다 짧아야** 한다. 더 기다리면 고아가 된 감시자가
# 제 시간에 발화해 gh 를 거둬 버려, 정리하지 않는 구현도 통과해 버린다(실측: 상한 2초에
# 1.8초를 기다리자 고치기 전 코드도 통과했다).
sleep 0.6
gone "helper TERM: gh 정리됨"            "$gh_pid"
gone "helper TERM: 감시자 정리됨"        "${wd_pid:-}"
gone "helper TERM: 감시자 sleep 정리됨"  "${wd_sleep:-}"
is   "helper TERM: 임시 파일 잔존 없음"  "0" "$(leftovers)"

echo
echo "== 격리 tmux 서버에서 view-mode 규약 확인 (기본 소켓은 건드리지 않는다) =="
sock="tmux-open-pr-test-$$"
T() { command tmux -L "$sock" "$@"; }
if PATH=${PATH#"$work/bin":} command -v tmux >/dev/null 2>&1; then
  # 스텁이 아니라 진짜 tmux 를 쓴다.
  real_tmux=$(PATH=${PATH#"$work/bin":} command -v tmux)
  T() { "$real_tmux" -L "$sock" "$@"; }
  T kill-server 2>/dev/null
  T new-session -d -x 80 -y 24 2>/dev/null
  T run-shell -b -t ':' "exit 0";               sleep 0.6
  is "무출력+exit 0 -> view-mode 안 열림" "0" "$(T display-message -p -t ':' '#{pane_in_mode}')"
  T run-shell -b -t ':' "echo x >&2; exit 0";   sleep 0.6
  is "stderr만+exit 0 -> view-mode 안 열림" "0" "$(T display-message -p -t ':' '#{pane_in_mode}')"
  T run-shell -b -t ':' "exit 1";               sleep 0.6
  is "무출력+exit 1 -> view-mode 열림" "1" "$(T display-message -p -t ':' '#{pane_in_mode}')"
  T kill-server 2>/dev/null
else
  echo "  - tmux 가 없어 건너뜀"
fi

echo
echo "결과: ${pass}건 통과, ${fail}건 실패"
[ "$fail" -eq 0 ]
