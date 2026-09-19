#!/usr/bin/env python3
"""Write one self-contained prompt file per independent extraction or verification call.

  extract  one prompt per digest shard and lens: OUT/prompts/extract-<lens>[-NN].md
  verify   one prompt per merged candidate: OUT/prompts/verify-<id>.md

A prompt file is the whole input of one call, so any executor can run it: agy
through dispatching-agy-workers, a tool-less sub-agent, or the coordinator
itself. Each call answers with one JSON object saved as
OUT/results/<prompt stem>.result.json. Every run empties OUT/prompts and
OUT/results first, so a glob never mixes in a stale prompt or answer. Use a
different OUT for extract and verify. Exit 0 on success, 2 on invalid input.
"""

import argparse
import json
from pathlib import Path
import re
import sys

LENSES = {
    "blind": "전체(관점 제한 없음). 모든 PR 에서 반복되는 행동을 찾아라.",
    "correctness": (
        "동작 정확성 — 오탐·미탐, 경계 조건, 자동 수정·코드 변환의 의미 보존, "
        "이름·형태만 보고 판정하는 로직의 한계, 바인딩·지원 버전·실행 환경 확인. "
        "이 관점에 해당하는 패턴만 찾아라."
    ),
    "structure": (
        "변경 구조 — 어떤 파일이 함께 바뀌는지(구현·등록·문서·테스트·fixture·README), "
        "문서와 실제 동작의 불일치, 외부 도구와 동작을 맞추는 회귀 테스트. "
        "이 관점에 해당하는 패턴만 찾아라."
    ),
    "maintenance": (
        "유지보수 — 의존성 업데이트(봇 PR 포함), 지원 런타임·engines·CI matrix 와의 호환, "
        "릴리스 PR, 자동 종료(autoclosed). 이 관점에 해당하는 패턴만 찾아라."
    ),
    "review": (
        "리뷰 동학 — 봇 리뷰어와 관리자 리뷰가 최종 diff 를 어떻게 바꿨는지, "
        "변경 요청→수정→승인의 흐름, 작성자가 리뷰 제안을 받아들이거나 거절한 근거. "
        "이 관점에 해당하는 패턴만 찾아라."
    ),
}
CANDIDATE_ID = re.compile(r"[A-Za-z0-9_-]+")

INTERPRETATION = """해석 규칙:
- closed-unmerged 는 머지되지 않았다는 사실뿐이다. 거절·잘못된 제안·종료 사유로 해석하지 마라. 종료 사유를 보여주는 직접 증거(관리자 발언 등)가 있을 때만 사유를 말한다.
- 승인(APPROVED) 리뷰와 머지는 다른 정보다.
- Copilot·coderabbit 같은 봇 리뷰 문장은 봇의 주장이다. 관리자 판단으로 취급하지 마라.
- 작성자의 테스트 실행 보고는 보고일 뿐이다. 실행 결과로 취급하지 마라."""

QUOTE_RULES = """인용 규칙:
- 인용(quote)은 다이제스트에서 글자 그대로 복사한 20~200자다. 번역·요약·수정하지 마라. 원문 언어 그대로다.
- 한 인용은 한 곳에서 이어진 글자다. 여러 줄이나 여러 곳을 `...` 로 이어 붙이지 마라. 백틱·따옴표도 원문 그대로 둔다.
- 인용은 그 PR 의 섹션 안에서만 가져온다. 제목·본문·diff·커밋 메시지·코멘트 원문만 인용이 된다. `###` 줄의 키, `url:`·`repository:`·`state:` 줄, `- 경로 (modified +3/-1)` 같은 목록 머리, `[작성자]` 표시, `…[+N chars]` 표시는 다이제스트가 붙인 것이라 인용이 될 수 없다."""

EXTRACT_TAIL = """패턴의 기준:
- 패턴은 서로 다른 PR 2개 이상에서 반복해서 관찰되는 행동이다. PR 1개에서만 보이는 것은 patterns 가 아니라 observations 에 넣는다.
- 모든 근거(evidence)에는 인용을 붙인다.
- 다른 오픈소스 저장소에서 기여 후보를 찾는 데 쓸 수 있어야 한다. search_clues 에는 후보 저장소에서 찾을 파일 경로·코드 형태·검색어를 적는다.
- 억지로 개수를 늘리지 마라. 근거가 약하면 rejected 에 이유와 함께 넣는다. 패턴이 0개여도 된다.

출력: 설명·코드펜스 없이 아래 형태의 JSON 객체 하나만 출력한다. 문자열 값은 한국어로 쓰되 quote 는 원문 그대로 둔다.
{
  "lens": "<이번 관점 이름>",
  "patterns": [
    {
      "title": "짧은 이름",
      "description": "재사용 가능한 행동을 1~2문장으로",
      "kind": "defect-class | convention | maintenance-policy | review-dynamic",
      "evidence": [
        {"pr": "<키>", "role": "supports | counterexample", "quote": "<원문 인용>", "claim": "이 PR 이 패턴을 어떻게 보여주는지"}
      ],
      "applicability": ["적용 조건"],
      "counterconditions": ["적용하면 안 되는 조건"],
      "search_clues": ["후보 저장소에서 찾을 단서"],
      "expected_tests": ["기여할 때 필요한 테스트"],
      "maintainer_judgment_required": ["관리자가 판단해야 할 남은 문제"],
      "confidence": "high | medium | low",
      "confidence_reason": "신뢰도의 이유와 한계"
    }
  ],
  "observations": [
    {"pr": "<키>", "note": "PR 1개에서만 보인 행동", "quote": "<원문 인용>"}
  ],
  "rejected": [
    {"idea": "검토했지만 패턴으로 삼지 않은 것", "reason": "이유"}
  ]
}"""

VERIFY_TAIL = """너는 반박 검증자다. 아래 후보 패턴 하나가 다이제스트로 뒷받침되는지 따진다. 후보를 만든 사람의 편을 들지 마라. 근거가 약하면 약하다고 말하는 것이 네 일이다.

확인할 것:
1. 인용된 PR 마다 다이제스트가 그 주장을 실제로 보여주는지. 인용 규칙을 지킨 인용을 붙인다.
2. 인용되지 않은 다른 PR 중 반례가 있는지.
3. 서로 다른 PR 2개 이상에서 반복되는지. 한 저장소 안의 반복인지 여러 저장소에 걸친 반복인지.
4. 다른 오픈소스 저장소에서 기여 후보를 찾는 데 쓸 수 있는지(actionable). 결함 종류를 가리키면 쓸 수 있고, 일상 절차나 관례 설명뿐이면 쓸 수 없다.
5. 신뢰도. 한 저장소의 사례만으로는 high 가 될 수 없다. closed-unmerged PR 은 머지된 변경의 근거가 아니다.

출력: 설명·코드펜스 없이 JSON 객체 하나만 출력한다.
{
  "id": "<후보 id>",
  "verdict": "supported | weak | unsupported",
  "evidence_checks": [{"pr": "<키>", "holds": true, "quote": "<원문 인용>", "reason": "…"}],
  "counterexamples": [{"pr": "<키>", "quote": "<원문 인용>", "reason": "…"}],
  "distinct_prs": 0,
  "distinct_repos": 0,
  "actionable": true,
  "actionable_reason": "…",
  "confidence": "high | medium | low",
  "revised_statement": "근거에 맞게 고친 패턴 문장 (고칠 필요 없으면 원문)"
}

후보:"""


class PromptError(ValueError):
    pass


def _load_keymap(digest_dir):
    path = Path(digest_dir) / "keymap.json"
    try:
        keymap = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PromptError("keymap.json could not be read; run build_digest.py first: " + str(error))
    if (
        not isinstance(keymap, dict)
        or not isinstance(keymap.get("sections"), dict)
        or not isinstance(keymap.get("shards"), list)
        or not all(isinstance(section, dict) for section in keymap["sections"].values())
    ):
        raise PromptError("keymap.json is not a build_digest.py keymap")
    return keymap


def _read_shard(digest_dir, name):
    try:
        return (Path(digest_dir) / name).read_text(encoding="utf-8")
    except OSError as error:
        raise PromptError("digest shard could not be read: " + str(error))


def _sections(text, keys):
    """Split a digest file into {key: section text} at the headers of known keys."""
    matches = [match for match in re.finditer(r"^### (\S+) — ", text, re.M) if match.group(1) in keys]
    sections = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.start():end].rstrip() + "\n"
    return sections


def _head(keymap, keys, scope):
    repositories = sorted({keymap["sections"][key]["repository"] for key in keymap["sections"]})
    examples = ", ".join(keys[:3])
    return (
        "너는 오픈소스 PR 코퍼스에서 재사용 가능한 변경 패턴을 다루는 분석 워커다. "
        "도구를 쓰지 마라. 파일을 읽거나 검색하지 마라. 아래 다이제스트만 근거로 쓴다.\n\n"
        "코퍼스는 저장소 " + str(len(repositories)) + "개(" + ", ".join(repositories) + ")에서 "
        "종료된 PR " + str(len(keymap["sections"])) + "개다. " + scope + " "
        "각 PR 은 `### <키> — <제목>` 으로 시작하고, 키(예: " + examples + ")가 PR 의 유일한 식별자다.\n\n"
        + INTERPRETATION + "\n\n" + QUOTE_RULES + "\n\n=== 다이제스트 시작 ===\n"
    )


def _prepare(out_dir, kind):
    """Empty OUT/prompts of this kind and OUT/results so no stale call or answer survives."""
    prompts, results = Path(out_dir) / "prompts", Path(out_dir) / "results"
    other = "verify" if kind == "extract" else "extract"
    if list(prompts.glob(other + "-*.md")):
        raise PromptError("--out already holds " + other + " prompts; use a separate run directory")
    prompts.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    for stale in [*prompts.glob(kind + "-*.md"), *results.glob("*.result.json")]:
        stale.unlink()
    return prompts


def _write(prompts_dir, name, text):
    path = Path(prompts_dir) / name
    path.write_text(text, encoding="utf-8")
    return {"file": str(path), "bytes": len(text.encode("utf-8"))}


def extract(digest_dir, out_dir, lenses):
    keymap = _load_keymap(digest_dir)
    unknown = [lens for lens in lenses if lens not in LENSES]
    if unknown:
        raise PromptError("unknown lens: " + ", ".join(unknown) + " (choose from " + ", ".join(LENSES) + ")")
    prompts = _prepare(out_dir, "extract")
    shards = keymap["shards"]
    written = []
    for index, shard in enumerate(shards, start=1):
        text = _read_shard(digest_dir, shard)
        keys = [key for key, section in keymap["sections"].items() if section.get("shard") == shard]
        if len(shards) == 1:
            scope = "다이제스트는 그 전체다."
        else:
            scope = (
                "PR 수가 많아 다이제스트를 " + str(len(shards)) + "조각으로 나눴고 이것은 그중 "
                + str(index) + "번째 조각(PR " + str(len(keys)) + "개)이다. 다른 조각의 PR 은 "
                "조정자가 나중에 합친다. 이 조각에서 PR 1개로만 보이는 행동도 observations 에 빠짐없이 적어라."
            )
        suffix = "" if len(shards) == 1 else "-" + str(index).zfill(2)
        for lens in lenses:
            prompt = (
                _head(keymap, keys, scope)
                + text.rstrip()
                + "\n=== 다이제스트 끝 ===\n\n이번 관점: "
                + lens
                + " — "
                + LENSES[lens]
                + "\n\n"
                + EXTRACT_TAIL
                + "\n"
            )
            written.append(_write(prompts, "extract-" + lens + suffix + ".md", prompt))
    return written


def _load_candidates(path, keymap):
    try:
        candidates = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PromptError("candidates could not be read as JSON: " + str(error))
    if not isinstance(candidates, list) or not candidates:
        raise PromptError("candidates must be a nonempty JSON array")
    seen = set()
    for index, candidate in enumerate(candidates):
        label = "candidates[" + str(index) + "]"
        if not isinstance(candidate, dict):
            raise PromptError(label + " must be an object")
        candidate_id = candidate.get("id")
        if not isinstance(candidate_id, str) or not CANDIDATE_ID.fullmatch(candidate_id):
            raise PromptError(label + ".id must match [A-Za-z0-9_-]+")
        if candidate_id in seen:
            raise PromptError("duplicate candidate id: " + candidate_id)
        seen.add(candidate_id)
        if not isinstance(candidate.get("statement"), str) or not candidate["statement"].strip():
            raise PromptError(label + ".statement must be a nonempty string")
        cited = candidate.get("cited_prs")
        if not isinstance(cited, list) or not cited or not all(isinstance(key, str) for key in cited):
            raise PromptError(label + ".cited_prs must be a nonempty array of digest keys")
        missing = [key for key in cited if key not in keymap["sections"]]
        if missing:
            raise PromptError(label + " cites unknown digest keys: " + ", ".join(map(str, missing)))
    return candidates


def verify(digest_dir, candidates_path, out_dir):
    keymap = _load_keymap(digest_dir)
    candidates = _load_candidates(candidates_path, keymap)
    prompts = _prepare(out_dir, "verify")
    shards = {name: _read_shard(digest_dir, name) for name in keymap["shards"]}
    all_keys = list(keymap["sections"])
    written = []
    for candidate in candidates:
        if len(shards) == 1:
            material = next(iter(shards.values())).rstrip()
            scope = "다이제스트는 그 전체다."
        else:
            sections = {}
            for text in shards.values():
                sections.update(_sections(text, keymap["sections"]))
            cited = list(dict.fromkeys(candidate["cited_prs"]))
            index = "\n".join(
                "- " + key + " — " + str(keymap["sections"][key]["title"])
                + " (" + str(keymap["sections"][key]["state"]) + ")"
                for key in all_keys
                if key not in cited
            )
            material = "\n\n".join(sections[key].rstrip() for key in cited)
            if index:
                material += "\n\n### 나머지 PR 목록 (본문 없음, 반례 후보를 가리킬 때만 쓴다)\n" + index
            scope = (
                "PR 이 많아 후보가 인용한 PR 섹션만 싣고 나머지는 제목 목록만 싣는다. "
                "목록에만 있는 PR 은 인용할 수 없으니 반례로 의심되면 counterexamples 의 reason 에 키만 적어라."
            )
        prompt = (
            _head(keymap, all_keys, scope)
            + material
            + "\n=== 다이제스트 끝 ===\n\n"
            + VERIFY_TAIL
            + "\n"
            + json.dumps(candidate, ensure_ascii=False, indent=1)
            + "\n"
        )
        written.append(_write(prompts, "verify-" + candidate["id"] + ".md", prompt))
    return written


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    extract_parser = commands.add_parser("extract", help="one prompt per digest shard and lens")
    extract_parser.add_argument("--digest-dir", required=True, help="build_digest.py --out directory")
    extract_parser.add_argument("--out", required=True, help="run directory; prompts/ and results/ go under it")
    extract_parser.add_argument(
        "--lens", action="append", choices=sorted(LENSES), help="lens to run; repeat. Default: all five"
    )
    verify_parser = commands.add_parser("verify", help="one adversarial prompt per candidate")
    verify_parser.add_argument("--digest-dir", required=True, help="build_digest.py --out directory")
    verify_parser.add_argument("--candidates", required=True, help='JSON array of {"id", "statement", "cited_prs"}')
    verify_parser.add_argument("--out", required=True, help="run directory, not the extract one; prompts/ and results/ go under it")
    args = parser.parse_args(argv)
    try:
        if args.command == "extract":
            written = extract(args.digest_dir, args.out, args.lens or list(LENSES))
        else:
            written = verify(args.digest_dir, args.candidates, args.out)
    except PromptError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(written, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
