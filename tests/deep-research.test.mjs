import assert from "node:assert/strict"
import { readFile } from "node:fs/promises"
import test from "node:test"

const WORKFLOW_PATH = new URL("../dot_claude/workflows/deep-research.js", import.meta.url)
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor

const loadWorkflow = async () => {
  const source = (await readFile(WORKFLOW_PATH, "utf8")).replace(/^export const meta/m, "const meta")
  return new AsyncFunction("args", "agent", "parallel", "pipeline", "phase", "log", source)
}

const runWorkflow = async ({ args, respond }) => {
  const calls = [], logs = [], phases = []
  const agent = async (prompt, options = {}) => {
    const call = { prompt, options }
    calls.push(call)
    return respond(call, calls.length - 1)
  }
  const parallel = async tasks => Promise.all(tasks.map(task => task()))
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

test("fetch 실패·paywall·무관 상태를 보존해 인프라 실패와 skip을 집계한다", async () => {
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

  assert.equal(result.status, "infrastructure_failure")
  assert.equal(result.stats.anglesSucceeded, 3)
  assert.equal(result.stats.sourcesSelected, 3)
  assert.equal(result.stats.sourcesFetched, 0)
  assert.equal(result.stats.fetchErrored, 1)
  assert.equal(result.stats.fetchSkipped, 2)
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
  const scope = makeScope(["유효성", "보조-1", "보조-2"])
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
        return { status: "no_results", results: [] }
      }
      if (options.phase === "Fetch") {
        return { status: "irrelevant", sourceQuality: "unreliable", claims: [], errorReason: "fixture" }
      }
      throw new Error("unexpected agent call: " + options.label)
    },
  })

  assert.equal(calls.filter(call => call.options.phase === "Fetch").length, 1)
  assert.equal(result.stats.invalidUrlDropped, 4)
  assert.equal(result.stats.sourcesSelected, 1)
})
