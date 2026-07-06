#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";

function parseArgs(argv) {
  const options = {
    cwd: process.cwd(),
    source: null,
    pluginRoot: null,
    list: false,
    json: false,
    dryRun: false,
    limit: 10,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--cwd") {
      options.cwd = argv[++index];
    } else if (token === "--source") {
      options.source = argv[++index];
    } else if (token === "--plugin-root") {
      options.pluginRoot = argv[++index];
    } else if (token === "--limit") {
      options.limit = Number(argv[++index]);
    } else if (token === "--list") {
      options.list = true;
    } else if (token === "--json") {
      options.json = true;
    } else if (token === "--dry-run") {
      options.dryRun = true;
    } else if (token === "--help" || token === "-h") {
      printHelp();
      process.exit(0);
    } else {
      throw new Error(`Unknown argument: ${token}`);
    }
  }

  return options;
}

function printHelp() {
  console.log(`Usage:
  node scripts/import-claude-session.mjs [--cwd <workspace>] [--source <jsonl>]
  node scripts/import-claude-session.mjs --list [--cwd <workspace>]

Options:
  --cwd <path>          Workspace whose Claude transcript should be imported.
  --source <path>       Exact Claude JSONL transcript to import.
  --plugin-root <path>  Claude openai-codex plugin root to use.
  --list               List candidate transcripts instead of importing.
  --limit <n>           Candidate count for --list. Default: 10.
  --json               Emit JSON.
  --dry-run            Print the transfer command without running it.
`);
}

function resolveUserPath(value, cwd = process.cwd()) {
  if (!value) {
    return null;
  }
  if (value === "~") {
    return os.homedir();
  }
  if (value.startsWith("~/")) {
    return path.join(os.homedir(), value.slice(2));
  }
  return path.resolve(cwd, value);
}

function claudeProjectName(workspace) {
  return path.resolve(workspace).replace(/[\\/]/g, "-");
}

function statMtimeMs(filePath) {
  try {
    return fs.statSync(filePath).mtimeMs;
  } catch {
    return 0;
  }
}

function listJsonlFiles(directory) {
  if (!fs.existsSync(directory)) {
    return [];
  }
  return fs
    .readdirSync(directory, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith(".jsonl"))
    .map((entry) => path.join(directory, entry.name));
}

function findWorkspaceCandidates(workspace) {
  const projectsDir = path.join(os.homedir(), ".claude", "projects");
  const expectedDir = path.join(projectsDir, claudeProjectName(workspace));
  const exact = listJsonlFiles(expectedDir);

  if (exact.length > 0) {
    return exact
      .map((filePath) => ({
        path: filePath,
        projectDir: expectedDir,
        mtimeMs: statMtimeMs(filePath),
        match: "exact",
      }))
      .sort((left, right) => right.mtimeMs - left.mtimeMs);
  }

  if (!fs.existsSync(projectsDir)) {
    return [];
  }

  const workspaceBase = path.basename(path.resolve(workspace));
  const fuzzyDirs = fs
    .readdirSync(projectsDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && entry.name.includes(workspaceBase))
    .map((entry) => path.join(projectsDir, entry.name));

  return fuzzyDirs
    .flatMap((projectDir) =>
      listJsonlFiles(projectDir).map((filePath) => ({
        path: filePath,
        projectDir,
        mtimeMs: statMtimeMs(filePath),
        match: "fuzzy",
      })),
    )
    .sort((left, right) => right.mtimeMs - left.mtimeMs);
}

function findCompanionScript(pluginRootOption) {
  const explicitRoot = resolveUserPath(pluginRootOption);
  if (explicitRoot) {
    const script = path.join(explicitRoot, "scripts", "codex-companion.mjs");
    if (!fs.existsSync(script)) {
      throw new Error(`codex-companion.mjs not found under --plugin-root: ${explicitRoot}`);
    }
    return script;
  }

  const codexPluginDir = path.join(os.homedir(), ".claude", "plugins", "cache", "openai-codex", "codex");
  if (!fs.existsSync(codexPluginDir)) {
    throw new Error(`Claude Codex plugin cache not found: ${codexPluginDir}`);
  }

  const candidates = fs
    .readdirSync(codexPluginDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(codexPluginDir, entry.name, "scripts", "codex-companion.mjs"))
    .filter((script) => fs.existsSync(script))
    .map((script) => ({ script, mtimeMs: statMtimeMs(script) }))
    .sort((left, right) => right.mtimeMs - left.mtimeMs);

  if (candidates.length === 0) {
    throw new Error(`No codex-companion.mjs found under ${codexPluginDir}`);
  }

  return candidates[0].script;
}

function renderCandidates(candidates, limit) {
  if (candidates.length === 0) {
    return "No Claude transcript candidates found for this workspace.\n";
  }

  const lines = candidates.slice(0, limit).map((candidate, index) => {
    const updatedAt = new Date(candidate.mtimeMs).toISOString();
    return `${index + 1}. ${candidate.path}\n   match=${candidate.match} updated=${updatedAt}`;
  });
  return `${lines.join("\n")}\n`;
}

function runTransfer({ cwd, source, pluginRoot, json, dryRun }) {
  const companionScript = findCompanionScript(pluginRoot);
  const args = [companionScript, "transfer", "--cwd", cwd, "--source", source];
  if (json) {
    args.push("--json");
  }

  if (dryRun) {
    return {
      status: 0,
      stdout: `node ${args.map((value) => JSON.stringify(value)).join(" ")}\n`,
      stderr: "",
    };
  }

  const result = spawnSync(process.execPath, args, {
    cwd,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });

  return {
    status: result.status ?? 1,
    stdout: result.stdout ?? "",
    stderr: result.stderr ?? "",
  };
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  const cwd = resolveUserPath(options.cwd) ?? process.cwd();
  const source = resolveUserPath(options.source, cwd);
  const candidates = source
    ? [{ path: source, projectDir: path.dirname(source), mtimeMs: statMtimeMs(source), match: "source" }]
    : findWorkspaceCandidates(cwd);

  if (options.list) {
    if (options.json) {
      console.log(JSON.stringify({ cwd, candidates: candidates.slice(0, options.limit) }, null, 2));
    } else {
      process.stdout.write(renderCandidates(candidates, options.limit));
    }
    return;
  }

  const selected = source ?? candidates[0]?.path;
  if (!selected) {
    throw new Error("No Claude transcript candidates found. Retry with --source <path-to-claude-jsonl>.");
  }

  if (!selected.endsWith(".jsonl")) {
    throw new Error(`Claude transcript source must be a JSONL file: ${selected}`);
  }

  const result = runTransfer({
    cwd,
    source: selected,
    pluginRoot: options.pluginRoot,
    json: options.json,
    dryRun: options.dryRun,
  });

  if (result.stdout) {
    process.stdout.write(result.stdout);
  }
  if (result.stderr) {
    process.stderr.write(result.stderr);
  }
  process.exitCode = result.status;
}

try {
  main();
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`${message}\n`);
  process.exitCode = 1;
}
