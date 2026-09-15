# Operation contract

The skill source is `dot_claude/skills/dual-review/SKILL.md`; its managed target is
`~/.claude/skills/dual-review/SKILL.md`.

Round zero builds independent Claude and Codex prompts in Python. The script entrypoint
starts all five Claude producer processes and the Codex process before reading any
response. Claude uses only the five finding-producing review
roles: `pr-review-toolkit:code-reviewer`, `pr-test-analyzer`, `comment-analyzer`,
`silent-failure-hunter`, and `type-design-analyzer`. Claude runs each process with
the CLI's `plan` permission mode, `Read,Glob,Grep` tool allowlist, and no permission
prompter. The adapter fingerprints the target's git-tracked files before and after
reading it. The residual risk is that untracked and gitignored changes inside a Git
repository are not detected by this guard. When the target is not a Git repository
or has zero tracked files, the adapter falls back to a full-tree walk.

## Claude Code 2.1.268 confirmed capabilities

The pinned CLI contract is Claude Code 2.1.268. Its help confirms these nine relevant
capabilities: `-p`, `--no-session-persistence`, `--setting-sources`,
`--permission-mode`, `--permission-prompts`, `--allowedTools`, `--agent`,
`--output-format`, and `--json-schema`. In particular, `--permission-prompts
<target>` describes who answers prompts when `--print` is used, `--allowedTools`
accepts a comma- or space-separated tool list, and `--json-schema` validates
structured output. This is a capability inventory, not a claim that production
emits every listed option in every phase.

## Production-emitted flags

Every production Claude invocation emits `-p`, `--no-session-persistence`,
`--permission-mode plan`, `--permission-prompts none`, and
`--allowedTools Read,Glob,Grep`. A round-zero producer additionally emits
`--agent <role>`. Cross critique and fresh synthesis instead emit the complete
structured-output pair `--output-format json` and `--json-schema <schema>`. The
production allowlist is deliberately limited to the read-only `Read,Glob,Grep`
tools. Within this production boundary, `--allowedTools` is variable-arity and can
absorb a following positional prompt. Every production Claude invocation that uses
it therefore supplies the prompt only through stdin and appends no positional prompt.

## Spec CMD-6 harness-only flags

The Spec CMD-6 harness-only invocation flags are:

- `--setting-sources project`
- `--permission-mode default`
- `--allowedTools "Read,Glob,Grep,Bash(python3:*)"`

These flags are not part of the production command tuple and must not be inferred
from the capability inventory. Within this harness boundary, `--allowedTools` is
also variable-arity and can absorb a following positional prompt, so the harness
supplies its prompt only through stdin and appends no positional prompt.

## Runtime transport and state boundaries

Codex uses the skill-owned reviewer schema with the read-only sandbox. `codex exec`
accepts the prompt through stdin. The adapter connects a regular file containing the
complete constructed prompt before process start; the child reads it to EOF. The
final `-` explicitly selects stdin and is placed after the variable option allowlist.
No positional prompt is permitted after that allowlist. Cross critique receives only
the opposing normalized findings and target diff. Fresh Claude performs synthesis
from the anonymous view; no network publication or source edits are part of this
skill.

The state script owns base resolution, snapshots, process adapters, provenance,
rejection handling, round transitions, termination, and local report rendering. The
skill markdown only routes orchestration to that boundary.

Anonymous-view masking removes the five Claude producer names and original finding
IDs, but never a per-finding `producer` value. The public finding allowlist omits
both `source` and `producer`, so plain `claude` and `codex` aliases are treated
symmetrically and remain available when they occur in legitimate finding text or
repository-relative paths.
