#!/usr/bin/env python3
"""워커 결과 JSON 의 인용이 원자료의 해당 섹션에 글자 그대로 있는지 검사한다.

결과 JSON 을 재귀로 훑어 키 필드와 인용 필드를 함께 가진 객체를 모두 검사한다.
원자료는 --section-regex 의 첫 캡처 그룹을 키로 하는 섹션들로 나눈다.
공백 차이만 무시한다. 줄임표로 이어 붙이거나 표기를 바꾼 인용은 실패다.
종료 코드: 전부 확인 0, 하나라도 실패 1, 입력 오류 2.
"""
import argparse
import json
import re
import sys


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def split_sections(source, pattern):
    matches = list(pattern.finditer(source))
    sections = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(source)
        sections[m.group(1)] = normalize(source[m.start() : end])
    return sections


def walk(value, path="$"):
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from walk(child, f"{path}[{i}]")


def check(result, sections, key_field, quote_field):
    verified, failures = 0, []
    for path, obj in walk(result):
        if key_field not in obj or quote_field not in obj:
            continue
        key, quote = obj[key_field], normalize(str(obj[quote_field] or ""))
        if key not in sections:
            reason = "unknown-key"
        elif not quote:
            reason = "empty-quote"
        elif quote not in sections[key]:
            reason = "not-found"
        else:
            verified += 1
            continue
        failures.append({"path": path, "key": key, "reason": reason, "quote": quote[:200]})
    return verified, failures


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", nargs="+", help="워커 결과 JSON 파일")
    ap.add_argument("--source", required=True, help="워커에게 준 원자료 파일")
    ap.add_argument("--section-regex", required=True, help="섹션 시작 줄에 맞는 정규식. 첫 캡처 그룹이 키다")
    ap.add_argument("--key-field", default="pr", help="인용이 속한 섹션 키를 담은 필드 이름")
    ap.add_argument("--quote-field", default="quote", help="인용을 담은 필드 이름")
    args = ap.parse_args()

    pattern = re.compile(args.section_regex, re.M)
    if pattern.groups < 1:
        ap.error("--section-regex 에 섹션 키를 잡는 캡처 그룹이 필요하다")
    with open(args.source, encoding="utf-8") as f:
        sections = split_sections(f.read(), pattern)
    if not sections:
        ap.error("--section-regex 에 맞는 섹션이 원자료에 없다")

    files = []
    for path in args.results:
        with open(path, encoding="utf-8") as f:
            verified, failures = check(json.load(f), sections, args.key_field, args.quote_field)
        files.append({"file": path, "verified": verified, "total": verified + len(failures), "failures": failures})
    json.dump({"sections": len(sections), "files": files}, sys.stdout, ensure_ascii=False, indent=1)
    print()
    sys.exit(1 if any(f["failures"] for f in files) else 0)


if __name__ == "__main__":
    main()
