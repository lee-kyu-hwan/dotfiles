# Verification

Run the Python unit suite with the repository's fixed interpreter. Type checking,
linting, and builds are **not configured** for this repository.

| Command | Purpose and pass condition |
|---|---|
| CMD-1 | Run every dual-review Python test; pass only at exit code 0 (not an empty test selection). |
| CMD-2 | Check argument parsing and defaults; pass at exit code 0. |
| CMD-3 | Check producer selection and Claude/Codex command contracts; pass at exit code 0. |
| CMD-4 | Scan the whole skill for forbidden Codex options; only the underlying search's no-match status is a pass, while a match or error fails. |
| CMD-5 | Scan the whole skill for GitHub write commands; only the underlying search's no-match status is a pass, while a match or error fails. |
| CMD-6 | Check the read-only and no-mutation source contract; pass at exit code 0. |
| CMD-7 | Check round-zero prompt identity and start-before-read independence; pass at exit code 0. |
| CMD-8 | Check the reviewer schema contract; pass at exit code 0. |
| CMD-9 | Check the critique schema contract; pass at exit code 0. |
| CMD-10 | Check the fresh-Claude synthesis schema and command boundary; pass at exit code 0. |
| CMD-11 | Check packaging, deployment path, and verification documentation; pass at exit code 0. |
| CMD-12 | Check that every deterministic Python boundary remains callable; pass at exit code 0. |

CMD-4 and CMD-5 scan this entire skill directory, including hidden and ignored
files. Their patterns are intentionally not reproduced here. Where a name is needed,
use the safe placeholders `<forbidden-codex-option-N>` and
`<github-write-command-N>`.
