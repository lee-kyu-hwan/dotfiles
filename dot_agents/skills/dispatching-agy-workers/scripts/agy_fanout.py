#!/usr/bin/env python3
"""프롬프트 파일마다 agy 를 독립 호출로 병렬 실행하고 응답과 사용량을 모은다.

파일 하나가 호출 하나다. 대화를 이어가지 않는다. 결과는 --out 아래에 쓴다.
  <이름>.result.json   --expect-json 일 때 응답에서 꺼낸 JSON 객체
  <이름>.result.txt    --expect-json 이 아닐 때 응답 원문
  <이름>.raw.<n>.json  n 번째 시도의 agy 출력 원본
  summary.json         시도별 상태·시간·사용량과 합계
종료 코드: 전부 성공 0, 하나라도 실패 1, 입력 오류 2.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

# macOS ARG_MAX 는 1 MiB 이고 환경 변수도 그 안에 들어간다. agy 는 프롬프트를 argv 로만 받는다.
MAX_PROMPT_BYTES = 900_000
USAGE_KEYS = ("input_tokens", "cache_read_tokens", "output_tokens", "thinking_tokens", "total_tokens")


def extract_json(text):
    """응답에서 파싱되는 첫 번째 JSON 객체를 꺼낸다. 코드펜스와 앞뒤 설명을 허용한다."""
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        value = json.loads(text[start : i + 1])
                    except json.JSONDecodeError:
                        break
                    if isinstance(value, dict):
                        return value
                    break
        start = text.find("{", start + 1)
    return None


def call_agy(prompt, args, workdir):
    cmd = ["agy", "-p", prompt, "--model", args.model, "--output-format", "json", "--disable-slash-commands"]
    t0 = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT"}, time.monotonic() - t0
    wall = time.monotonic() - t0
    try:
        raw = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raw = {"status": "BAD_STDOUT", "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
    return raw, wall


def run_job(path, args, out, workdir):
    name = path.stem
    prompt = path.read_text()
    # 같은 --out 으로 다시 돌릴 때 이전 결과가 남아 이번 실패를 가리지 않게 한다
    stale = [p for p in out.iterdir() if p.name.startswith(f"{name}.raw.") and p.name.endswith(".json")]
    for path in [*stale, out / f"{name}.result.json", out / f"{name}.result.txt"]:
        path.unlink(missing_ok=True)
    attempts = []
    for n in range(1, args.retries + 2):
        raw, wall = call_agy(prompt, args, workdir)
        (out / f"{name}.raw.{n}.json").write_text(json.dumps(raw, ensure_ascii=False, indent=1))
        response = raw.get("response") or ""
        parsed = extract_json(response) if args.expect_json else None
        attempts.append({
            "attempt": n,
            "wall_seconds": round(wall, 1),
            "status": raw.get("status"),
            "error": raw.get("error"),
            "usage": raw.get("usage"),
            "empty_response": not response.strip(),
            "json_ok": (parsed is not None) if args.expect_json else None,
        })
        if raw.get("status") != "SUCCESS" or not response.strip():
            continue
        if args.expect_json:
            if parsed is None:
                continue
            (out / f"{name}.result.json").write_text(json.dumps(parsed, ensure_ascii=False, indent=1))
        else:
            (out / f"{name}.result.txt").write_text(response)
        return {"name": name, "ok": True, "attempts": attempts}
    return {"name": name, "ok": False, "attempts": attempts}


def totals(jobs):
    """모든 시도의 사용량 합. 실패한 시도도 한도를 쓰므로 포함한다."""
    sums = dict.fromkeys(USAGE_KEYS, 0)
    for job in jobs:
        for attempt in job["attempts"]:
            for key in USAGE_KEYS:
                sums[key] += (attempt.get("usage") or {}).get(key) or 0
    return sums


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompts", nargs="+", type=pathlib.Path, help="프롬프트 파일. 파일 하나가 독립 호출 하나다")
    ap.add_argument("--out", required=True, type=pathlib.Path, help="결과를 쓸 디렉터리")
    ap.add_argument("--model", default="gemini-3.1-pro-low")
    ap.add_argument("--jobs", type=int, default=5, help="동시 호출 수")
    ap.add_argument("--timeout", type=int, default=600, help="호출 한 번의 제한 시간(초)")
    ap.add_argument("--retries", type=int, default=1, help="실패·빈 응답·JSON 파싱 실패 시 재시도 횟수")
    ap.add_argument("--expect-json", action="store_true", help="응답에서 JSON 객체를 꺼내고, 없으면 실패로 본다")
    args = ap.parse_args()

    names = [p.stem for p in args.prompts]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        ap.error(f"프롬프트 파일 이름(확장자 제외)이 겹친다: {', '.join(duplicates)}")
    for path in args.prompts:
        size = len(path.read_bytes())
        if size > MAX_PROMPT_BYTES:
            ap.error(f"{path} 가 {size} 바이트다. agy 는 프롬프트를 argv 로만 받아 {MAX_PROMPT_BYTES} 바이트를 넘길 수 없다. "
                     "자료(다이제스트)를 줄여라")

    args.out.mkdir(parents=True, exist_ok=True)
    # 빈 작업 디렉터리에서 실행해 호출한 저장소의 지시 파일(AGENTS.md 등)이 섞이지 않게 한다
    with tempfile.TemporaryDirectory(prefix="agy-fanout-") as workdir:
        t0 = time.monotonic()
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            jobs = list(pool.map(lambda p: run_job(p, args, args.out, workdir), args.prompts))
        batch_wall = round(time.monotonic() - t0, 1)

    summary = {"model": args.model, "batch_wall_seconds": batch_wall, "totals": totals(jobs), "jobs": jobs}
    (args.out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1))
    for job in jobs:
        last = job["attempts"][-1]
        usage = last.get("usage") or {}
        print(f"{job['name']:<24} {'OK  ' if job['ok'] else 'FAIL'} tries={len(job['attempts'])} "
              f"wall={last['wall_seconds']}s " + " ".join(f"{k.split('_')[0]}={usage.get(k)}" for k in USAGE_KEYS))
    print(f"batch_wall={batch_wall}s " + " ".join(f"{k}={v}" for k, v in summary["totals"].items()))
    sys.exit(0 if all(job["ok"] for job in jobs) else 1)


if __name__ == "__main__":
    main()
