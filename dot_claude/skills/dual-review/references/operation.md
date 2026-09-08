# Operation contract

The skill source is `dot_claude/skills/dual-review/SKILL.md`; its managed target is
`~/.claude/skills/dual-review/SKILL.md`.

Round zero builds independent Claude and Codex prompts in Python. The script entrypoint
starts all five Claude producer processes and the Codex process before reading any
response. Claude uses only the five finding-producing review
roles: `pr-review-toolkit:code-reviewer`, `pr-test-analyzer`, `comment-analyzer`,
`silent-failure-hunter`, and `type-design-analyzer`. Claude runs each process with
the CLI's `plan` permission mode, `Read,Glob,Grep` tool allowlist, and no permission
prompter; the adapter also fingerprints the target tree before and after reading it.

The pinned Claude CLI contract is Claude Code 2.1.263. Every Claude invocation emits
the common flags `-p`, `--no-session-persistence`, `--permission-mode plan`,
`--permission-prompts none`, and `--allowedTools Read,Glob,Grep`. A round-zero
producer additionally emits `--agent <role>`. Cross critique and fresh synthesis
instead emit the complete structured-output pair `--output-format json` and
`--json-schema <schema>`. The `--permission-prompts <target>` help describes who
answers prompts when `--print` is used, `--allowedTools` accepts a comma- or
space-separated tool list, and `--json-schema` validates structured output. The
allowlist is deliberately limited to the read-only `Read,Glob,Grep` tools.

Codex uses the skill-owned reviewer schema with the read-only sandbox. `codex exec`
accepts the prompt through stdin, so the adapter sends the constructed prompt to the
process standard input rather than supplying a positional prompt. Cross critique receives only the opposing
normalized findings and target diff. Fresh Claude performs synthesis from the
anonymous view; no network publication or source edits are part of this skill.

The state script owns base resolution, snapshots, process adapters, provenance,
rejection handling, round transitions, termination, and local report rendering. The
skill markdown only routes orchestration to that boundary.

Anonymous-view masking removes the five Claude producer names and original finding
IDs, but never a per-finding `producer` value. The public finding allowlist omits
both `source` and `producer`, so plain `claude` and `codex` aliases are treated
symmetrically and remain available when they occur in legitimate finding text or
repository-relative paths.
