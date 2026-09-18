# Installed CLI contract evidence

Captured on 2026-09-15 in the #103 worktree. These commands only read `--version` and `--help`; no auth/status/login/logout, provider request, or network-dependent model probe was executed.

## Codex

```text
$ codex --version
codex-cli 0.154.0
```

`codex --help` exited 0 and advertised `--model`, `--profile`, `--sandbox` with `read-only|workspace-write|danger-full-access`, `--ask-for-approval` with `on-request|never`, repeatable `--disable`, `--add-dir`, `--strict-config`, and the `exec`, `login`, and `doctor` commands.

`codex exec --help` exited 0 and advertised `--model`, `--profile`, `--sandbox`, `--ask-for-approval`, `--disable`, `--add-dir`, `--ignore-user-config`, `--ignore-rules`, `--output-schema`, `--output-last-message`, `--json`, and `--ephemeral`.

```text
$ codex login status --help
Show login status
Usage: codex login status [OPTIONS]

$ codex doctor --help
Diagnose local Codex installation, config, auth, and runtime health
Usage: codex doctor [OPTIONS]
      --json    Emit a redacted machine-readable report
```

The offline help surface accepts an arbitrary `--model <MODEL>` string and does not enumerate or prove server-side model availability. Therefore `gpt-5.6-sol` and `gpt-6-astra` are pinned role-policy identifiers, not an offline availability guarantee; provider rejection must remain a nonzero launch result with no automatic fallback.

## Claude Code

```text
$ claude --version
2.1.272 (Claude Code)
```

`claude --help` exited 0 and advertised `--model`, `--effort <low|medium|high|xhigh|max>`, `--permission-mode` including `dontAsk`, `--settings`, `--setting-sources`, `--append-system-prompt`, `--disallowedTools`, `--strict-mcp-config`, `--restricted`, `--tools`, and `--permission-prompts`.

The installed 2.1.272 help does **not** advertise `--append-system-prompt-file`; the supported additive instruction surface is `--append-system-prompt <prompt>`. It also warns that invalid settings files can be silently ignored in print mode, which reinforces the launcher-side strict JSON/schema pre-scan and interactive TTY launch requirement.

```text
$ claude auth status --help
Usage: claude auth status [options]
Show authentication status
  --json      Output as JSON (default)
  --text      Output as human-readable text
```

The installed official auth-status help exposes authentication status only and no usage/quota command or field contract. Since actual auth status and provider/network calls are prohibited for this workflow, no usage evidence was read. A Claude verifier on this host must therefore return `usage_unknown` and block admission until a separately reviewed official usage adapter is available; it must not infer `within_limit` from login state, scrape a TUI, or use a private endpoint.

The offline help accepts a model alias or full name but does not enumerate or prove provider-side availability. `opus[1m]` and `claude-fable-5-1` are pinned role-policy identifiers whose availability is checked only by the eventual provider launch; rejection must not trigger fallback.

## Claude Code settings-composition surface (2026-09-15 addendum)

Captured with `claude --help` only. No auth/status/login/logout, provider request, network probe, account-home credential read, or `chezmoi apply` was executed.

```text
  --settings <file-or-json>             Path to a settings JSON file or a JSON
                                        string to load additional settings from
  --setting-sources <sources>           Comma-separated list of setting sources
                                        to load (user, project, local).
  --plugin-dir <path>                   Load a plugin from a directory or .zip
                                        for this session only; a folder of
                                        plugins loads each child (repeatable:
                                        --plugin-dir A --plugin-dir B.zip)
                                        (default: [])
  --plugin-url <url>                    Fetch a plugin .zip from a URL for this
                                        session only (repeatable: --plugin-url A
                                        --plugin-url B) (default: [])
  --strict-mcp-config                   Only use MCP servers from --mcp-config,
                                        ignoring all other MCP configurations
  --mcp-config <configs...>             Load MCP servers from JSON files or
  --agents <json>                       JSON object defining custom agents
  --add-dir <directories...>            Additional directories to allow tool
```

Evidence properties relied upon by this revision:

- `--settings` is advertised as a single `<file-or-json>` value with no `(repeatable: …)` or `(default: [])` marker, unlike `--plugin-dir`/`--plugin-url`/`--mcp-config`. A launcher that must supply more than one settings document therefore composes one reviewed document rather than passing the flag twice.
- `--setting-sources` is advertised as a comma-separated allowlist of `user`, `project`, `local`. The help text states the list of sources to load; it does not document the effective merge precedence against `--settings`, so this revision still does not rely on unobserved precedence semantics (Spec D6).
- `--plugin-url` fetches over the network and is therefore outside this workflow's allowed launcher surface; `--plugin-dir` is a local path surface.
- `--bare` explicitly describes skipping hooks, plugin sync and auto-memory, and instructs the operator to "explicitly provide context via: --system-prompt[-file], --append-system-prompt[-file], --add-dir (CLAUDE.md dirs), --mcp-config, --settings, --agents, --plugin-dir". This is the installed CLI's own statement that `--settings` and `--plugin-dir` are the supported explicit composition surface for settings and plugins.

## User-reported account-profile settings isolation (2026-09-15)

The user reported, without this workflow reading any account home or credential file:

- `~/.local/share/ai-account-profiles/claude/dotfiles/settings.json` currently contains a theme setting only, and no `hooks`, `enabledPlugins`, `env`, or `permissions`.
- `~/.claude/settings.json` contains `Notification`, `PermissionRequest`, `PostToolUse`, `Stop`, `SubagentStop`, `TaskCompleted`, and `UserPromptSubmit` hooks plus `enabledPlugins`, `env`, and `permissions`.
- Claude sessions started manually under the separated `CLAUDE_CONFIG_DIR` answered normally with correct model and authentication, but disappeared from `workmux status`.

The operational consequence is that `CLAUDE_CONFIG_DIR` separates user settings and plugin state, not only authentication, so an account-profile split silently removes the workmux status hooks that make a session observable. The repository record of the default account's settings shape is `docs/claude-settings-reference.json`, whose `hooks` events are `Notification`, `PermissionRequest`, `PostToolUse`, `Stop`, `SubagentStop`, `TaskCompleted`, `UserPromptSubmit`, and whose workmux commands are `workmux set-window-status waiting|working|done`. The repository currently ships no `dot_claude/settings.json`; the default account's user settings are not chezmoi-managed at the base revision.

## User-reported Claude default-home behavior (2026-09-15)

The user performed login-state checks without reading account identifiers or secrets and reported:

- with `CLAUDE_CONFIG_DIR` set to the separated dotfiles path, `claude auth status` reports logged in via `claude.ai` and reports that separated config directory;
- with `CLAUDE_CONFIG_DIR` unset, `claude auth status` reports the existing default account logged in;
- with `CLAUDE_CONFIG_DIR` explicitly set to `~/.claude`, Claude interprets the path differently and reports logged out.

The operational consequence is that the provider-default Claude configuration is expressed by the **absence** of `CLAUDE_CONFIG_DIR`, never by exporting `CLAUDE_CONFIG_DIR=~/.claude`.
