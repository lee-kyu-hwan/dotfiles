import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"

const WORKFLOW_PATH = new URL("../dot_claude/workflows/deep-research.js", import.meta.url)
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor

const loadWorkflow = async () => {
  const source = (await readFile(WORKFLOW_PATH, "utf8")).replace(/^export const meta/m, "const meta")
  return new AsyncFunction("args", "agent", "parallel", "pipeline", "phase", "log", source)
}

const runWorkflow = async ({ args, respond, parallelOverride }) => {
  const calls = [], logs = [], phases = []
  const agent = async (prompt, options = {}) => {
    const call = { prompt, options }
    calls.push(call)
    return respond(call, calls.length - 1)
  }
  const defaultParallel = async tasks => Promise.all(tasks.map(task => task()))
  let parallelCall = 0
  const parallel = async tasks => {
    const callIndex = parallelCall++
    return parallelOverride
      ? parallelOverride(tasks, defaultParallel, callIndex)
      : defaultParallel(tasks)
  }
  const pipeline = async () => {
    throw new Error("pipeline must not be used after the search barrier refactor")
  }
  const phase = value => phases.push(value)
  const log = value => logs.push(value)
  const workflow = await loadWorkflow()
  const result = await workflow(args, agent, parallel, pipeline, phase, log)
  return { result, calls, logs, phases }
}

const makeScope = labels => ({
  question: "테스트 질문",
  summary: "테스트 검색 범위",
  angles: labels.map(label => ({
    label,
    query: label + " query",
    rationale: label + " rationale",
  })),
})

const searchResult = (url, relevance = "high") => ({
  url,
  title: url,
  snippet: "relevant",
  relevance,
})

const verifierResult = (outcome, evidence = outcome + " evidence") => ({
  outcome,
  evidence,
  confidence: "high",
})

const makeSingleClaimResponder = ({
  verdicts,
  synthesis = { summary: "ok", findings: [], caveats: "", openQuestions: [] },
}) => {
  const scope = makeScope(["핵심", "보조-1", "보조-2"])
  const sourceUrl = "https://primary.example/report"
  return async ({ prompt, options }) => {
    if (options.label === "scope") return scope
    if (options.phase === "Search") {
      return prompt.includes("## Web Searcher: 핵심")
        ? { status: "ok", results: [searchResult(sourceUrl)] }
        : { status: "no_results", results: [] }
    }
    if (options.phase === "Fetch") {
      return {
        status: "ok",
        sourceQuality: "primary",
        publishDate: "2026-07-01",
        claims: [{
          claim: "핵심 주장은 검증 가능하다.",
          quote: "핵심 주장을 뒷받침하는 원문",
          importance: "central",
        }],
      }
    }
    if (options.phase === "Verify") {
      const voter = Number(options.label.match(/^v(\d+):/)?.[1])
      return verdicts[voter]
    }
    if (options.label === "synthesize") return synthesis
    throw new Error("unexpected agent call: " + options.label)
  }
}

test("빈 입력은 공통 result shape의 invalid_input을 반환한다", async () => {
  const { result, calls } = await runWorkflow({
    args: " \t\n ",
    respond: async () => {
      throw new Error("agent must not be called for invalid input")
    },
  })

  assert.equal(result.status, "invalid_input")
  assert.equal(result.error, "No research question provided.")
  assert.deepEqual(result.findings, [])
  assert.deepEqual(result.sources, [])
  assert.equal(result.stats.agentCalls, 0)
  assert.equal(result.stats.anglesPlanned, 0)
  assert.deepEqual(calls, [])
})

test("검색 실패와 결과 없음 상태를 구분하고 빈 ok 결과를 no_results로 정규화한다", async () => {
  const scope = makeScope(["실패", "없음", "빈 성공"])
  const { result } = await runWorkflow({
    args: "테스트 질문",
    respond: async ({ prompt, options }) => {
      if (options.label === "scope") return scope
      if (prompt.includes("## Web Searcher: 실패")) {
        return { status: "failed", results: [], errorReason: "rate limited" }
      }
      if (prompt.includes("## Web Searcher: 없음")) return { status: "no_results", results: [] }
      if (prompt.includes("## Web Searcher: 빈 성공")) return { status: "ok", results: [] }
      throw new Error("unexpected agent call: " + options.label)
    },
  })

  assert.equal(result.status, "no_claims")
  assert.equal(result.stats.anglesPlanned, 3)
  assert.equal(result.stats.anglesSucceeded, 0)
  assert.equal(result.stats.anglesNoResults, 2)
  assert.equal(result.stats.anglesFailed, 1)
  assert.equal(result.stats.sourcesSelected, 0)
})

test("fetch 실패·paywall·무관 혼합은 no_claims로 상태와 skip을 집계한다", async () => {
  const scope = makeScope(["fetch 실패", "paywall", "무관"])
  const fetchStatus = {
    "fetch 실패": { status: "failed", sourceQuality: "unreliable", claims: [], errorReason: "timeout" },
    paywall: { status: "paywalled", sourceQuality: "unreliable", claims: [], errorReason: "subscription required" },
    무관: { status: "irrelevant", sourceQuality: "unreliable", claims: [], errorReason: "off topic" },
  }
  const { result } = await runWorkflow({
    args: "테스트 질문",
    respond: async ({ prompt, options }) => {
      if (options.label === "scope") return scope
      if (options.phase === "Search") {
        const angle = scope.angles.find(candidate =>
          prompt.includes("## Web Searcher: " + candidate.label)
        ).label
        return {
          status: "ok",
          results: [searchResult("https://" + encodeURIComponent(angle) + ".example/source")],
        }
      }
      if (options.label.startsWith("fetch:")) {
        const angle = scope.angles.find(candidate =>
          prompt.includes("**Found via:** " + candidate.label + " search")
        )
        return fetchStatus[angle.label]
      }
      throw new Error("unexpected agent call: " + options.label)
    },
  })

  assert.equal(result.status, "no_claims")
  assert.equal(result.stats.anglesSucceeded, 3)
  assert.equal(result.stats.sourcesSelected, 3)
  assert.equal(result.stats.sourcesFetched, 0)
  assert.equal(result.stats.fetchErrored, 1)
  assert.equal(result.stats.fetchSkipped, 2)
})

test("선택된 fetch가 모두 실패하면 infrastructure_failure를 반환한다", async () => {
  const scope = makeScope(["실패-1", "실패-2", "실패-3"])
  const { result } = await runWorkflow({
    args: "테스트 질문",
    respond: async ({ prompt, options }) => {
      if (options.label === "scope") return scope
      if (options.phase === "Search") {
        const angleIndex = scope.angles.findIndex(candidate =>
          prompt.includes("## Web Searcher: " + candidate.label)
        )
        return {
          status: "ok",
          results: [searchResult("https://failure-" + angleIndex + ".example/source")],
        }
      }
      if (options.phase === "Fetch") {
        return { status: "failed", sourceQuality: "unreliable", claims: [], errorReason: "timeout" }
      }
      throw new Error("unexpected agent call: " + options.label)
    },
  })

  assert.equal(result.status, "infrastructure_failure")
  assert.equal(result.stats.sourcesSelected, 3)
  assert.equal(result.stats.sourcesFetched, 0)
  assert.equal(result.stats.fetchErrored, 3)
  assert.equal(result.stats.fetchSkipped, 0)
})

test("6개 검색 각도에서 라운드로빈으로 정확히 15개를 선택해 모든 각도를 포함한다", async () => {
  const labels = Array.from({ length: 6 }, (_, index) => "각도-" + index)
  const scope = makeScope(labels)
  const { result, calls } = await runWorkflow({
    args: "테스트 질문",
    respond: async ({ prompt, options }) => {
      if (options.label === "scope") return scope
      if (options.phase === "Search") {
        const angleIndex = labels.findIndex(label => prompt.includes("## Web Searcher: " + label))
        // Later angles finish first. Completion order must not affect selection.
        await new Promise(resolve => setTimeout(resolve, (labels.length - angleIndex) * 2))
        return {
          status: "ok",
          results: Array.from({ length: 6 }, (_, resultIndex) =>
            searchResult("https://angle-" + angleIndex + ".example/source-" + resultIndex)
          ),
        }
      }
      if (options.phase === "Fetch") {
        return { status: "irrelevant", sourceQuality: "unreliable", claims: [], errorReason: "fixture" }
      }
      throw new Error("unexpected agent call: " + options.label)
    },
  })

  const fetchCalls = calls.filter(call => call.options.phase === "Fetch")
  assert.equal(fetchCalls.length, 15)
  for (const label of labels) {
    assert.ok(
      fetchCalls.some(call => call.prompt.includes("**Found via:** " + label + " search")),
      label + " must receive a fetch slot"
    )
  }
  assert.equal(result.stats.sourcesSelected, 15)
  assert.equal(result.stats.anglesWithoutFetch, 0)
  assert.equal(result.stats.budgetDropped, 21)
})

test("같은 경로의 서로 다른 query URL은 별도 fetch 후보로 유지한다", async () => {
  const scope = makeScope(["동영상", "보조-1", "보조-2"])
  const { result, calls } = await runWorkflow({
    args: "테스트 질문",
    respond: async ({ prompt, options }) => {
      if (options.label === "scope") return scope
      if (options.phase === "Search") {
        if (prompt.includes("## Web Searcher: 동영상")) {
          return {
            status: "ok",
            results: [
              searchResult("https://video.example/watch?v=a"),
              searchResult("https://video.example/watch?v=b"),
            ],
          }
        }
        return { status: "no_results", results: [] }
      }
      if (options.phase === "Fetch") {
        return { status: "irrelevant", sourceQuality: "unreliable", claims: [], errorReason: "fixture" }
      }
      throw new Error("unexpected agent call: " + options.label)
    },
  })

  const fetchedPrompts = calls
    .filter(call => call.options.phase === "Fetch")
    .map(call => call.prompt)
  assert.equal(fetchedPrompts.length, 2)
  assert.ok(fetchedPrompts.some(prompt => prompt.includes("https://video.example/watch?v=a")))
  assert.ok(fetchedPrompts.some(prompt => prompt.includes("https://video.example/watch?v=b")))
  assert.equal(result.stats.urlDupes, 0)
})

test("http(s)가 아닌 검색 URL은 fetch 전에 제외한다", async () => {
  const scope = makeScope(["유효성", "잘못된 URL만", "보조"])
  const { result, calls } = await runWorkflow({
    args: "테스트 질문",
    respond: async ({ prompt, options }) => {
      if (options.label === "scope") return scope
      if (options.phase === "Search") {
        if (prompt.includes("## Web Searcher: 유효성")) {
          return {
            status: "ok",
            results: [
              searchResult("ftp://files.example/report"),
              searchResult("javascript:alert(1)"),
              searchResult("https://invalid-port.example:not-a-port/report"),
              searchResult("https://invalid-port.example:65536/report"),
              searchResult("https://valid.example/report"),
            ],
          }
        }
        if (prompt.includes("## Web Searcher: 잘못된 URL만")) {
          return {
            status: "ok",
            results: [searchResult("mailto:invalid-only@example.com")],
          }
        }
        return { status: "no_results", results: [] }
      }
      if (options.phase === "Fetch") {
        return { status: "irrelevant", sourceQuality: "unreliable", claims: [], errorReason: "fixture" }
      }
      throw new Error("unexpected agent call: " + options.label)
    },
  })

  assert.equal(calls.filter(call => call.options.phase === "Fetch").length, 1)
  assert.equal(result.stats.invalidUrlDropped, 5)
  assert.equal(result.stats.sourcesSelected, 1)
  assert.equal(result.stats.anglesWithoutFetch, 1)
})

test("supported-refuted-null 패널은 1-1 (1 errored) unverified로 보존한다", async () => {
  const { result } = await runWorkflow({
    args: "테스트 질문",
    respond: makeSingleClaimResponder({
      verdicts: [
        verifierResult("supported"),
        verifierResult("refuted"),
        null,
      ],
    }),
  })

  assert.equal(result.status, "inconclusive")
  assert.equal(result.stats.claimsVerified, 1)
  assert.equal(result.stats.confirmed, 0)
  assert.equal(result.stats.killed, 0)
  assert.equal(result.stats.unverified, 1)
  assert.equal(result.stats.verifierErrored, 1)
  assert.equal(result.unverified[0].vote, "1-1 (1 errored)")
  assert.equal(result.unverified[0].erroredVotes, 1)
})

test("supported 두 표와 unverified 한 표는 claim을 확인하고 합성한다", async () => {
  const { result, calls } = await runWorkflow({
    args: "테스트 질문",
    respond: makeSingleClaimResponder({
      verdicts: [
        verifierResult("supported"),
        verifierResult("supported"),
        verifierResult("unverified", "rate limited"),
      ],
    }),
  })

  assert.equal(result.stats.claimsVerified, 1)
  assert.equal(result.stats.confirmed, 1)
  assert.equal(result.stats.killed, 0)
  assert.equal(result.stats.unverified, 0)
  assert.equal(result.stats.verifierErrored, 1)
  assert.equal(calls.filter(call => call.options.label === "synthesize").length, 1)
})

test("refuted 두 표와 supported 한 표는 1-2로 기각하고 합성하지 않는다", async () => {
  const { result, calls } = await runWorkflow({
    args: "테스트 질문",
    respond: makeSingleClaimResponder({
      verdicts: [
        verifierResult("refuted", "specific contradiction"),
        verifierResult("refuted", "primary counterevidence"),
        verifierResult("supported"),
      ],
    }),
  })

  assert.equal(result.status, "inconclusive")
  assert.equal(result.stats.claimsVerified, 1)
  assert.equal(result.stats.confirmed, 0)
  assert.equal(result.stats.killed, 1)
  assert.equal(result.stats.unverified, 0)
  assert.equal(result.refuted[0].vote, "1-2")
  assert.equal(calls.filter(call => call.options.label === "synthesize").length, 0)
})

test("누락된 외부 검증 panel도 0-0 (3 errored) unverified로 복원한다", async () => {
  const { result, calls, logs } = await runWorkflow({
    args: "테스트 질문",
    respond: makeSingleClaimResponder({
      verdicts: [
        verifierResult("supported"),
        verifierResult("supported"),
        verifierResult("supported"),
      ],
    }),
    parallelOverride: async (tasks, run, callIndex) =>
      callIndex === 2 ? [null] : run(tasks),
  })

  assert.equal(result.status, "inconclusive")
  assert.equal(result.stats.claimsVerified, 1)
  assert.equal(result.stats.confirmed, 0)
  assert.equal(result.stats.killed, 0)
  assert.equal(result.stats.unverified, 1)
  assert.equal(result.stats.verifierErrored, 3)
  assert.equal(result.unverified[0].vote, "0-0 (3 errored)")
  assert.ok(logs.some(message => message.includes("0-0 (3 errored) ?")))
  assert.equal(calls.filter(call => call.options.phase === "Verify").length, 0)
  assert.equal(calls.filter(call => call.options.label === "synthesize").length, 0)
})
