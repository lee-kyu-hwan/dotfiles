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
