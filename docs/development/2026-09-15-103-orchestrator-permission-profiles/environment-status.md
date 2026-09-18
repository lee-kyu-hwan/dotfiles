# Environment status

## 2026-09-15 user-applied #111 account-profile bootstrap

The user explicitly reported applying only the already-merged #111 targets from dotfiles:

- `~/.config/ai-session/accounts.toml`
- `~/.local/bin/ai-session`

The user reported that the `codex-dotfiles` and `claude-dotfiles` `config_home` directories now exist with mode `0700`, and that neither newly prepared profile is logged in yet. The authoritative topology keeps Codex multi-account capability but initially activates only the existing shared `~/.codex` account: `codex-default` handles every current role and repository, while `codex-dotfiles` remains a declared, separate-home, unbound candidate. It is not a login or credential-copy target during this workflow and must fail closed while unlogged. Later, after an explicit official login, changing only a reviewed registry binding may activate it without code or launcher changes. Claude has separate default and dotfiles accounts now. The workflow does not inspect or delete either prepared directory.

This is user-provided environment status, not a result of #103 automation. The workflow did not inspect credential contents, execute provider auth/status/usage commands, copy credentials, log in, log out, enroll an identity, or run a broader `chezmoi apply`.

The currently running pane's account binding remains unchanged. #103 must not rebind, restart, or mutate that pane. Role/account composition tests continue to use synthetic temporary homes and fake provider/verifier executables. New Codex launches initially select only `codex-default` backed by `~/.codex`; `codex-dotfiles` has no default, scope, or task binding and therefore is never selected automatically. An explicit attempt to use the unlogged candidate must fail closed. Dotfiles Claude launches select the prepared-but-unlogged `claude-dotfiles` profile and must not fall back to `~/.claude`; a real verifier would be expected to deny launch as `not_logged_in` (or another more conservative verifier status when official evidence is unavailable), but this workflow does not call the live verifier to observe it. Outside the dotfiles repository and its linked worktrees, new Claude launches select `claude-default` backed by `~/.claude`.

The final deployment and verification report must distinguish:

- #111 targets already applied by the user;
- #103 source changes and fixture rendering, which are not applied to the real home during this workflow;
- no Codex relogin for the active `codex-default` account and no authentication copied into the `codex-dotfiles` candidate;
- host-local `claude-dotfiles` login and identity enrollment still requiring later explicit user interaction;
- the deployed v1 registry's temporary default/binding mismatch and a fail-closed, no-copy transition to the corrected registry;
- preservation of the empty `codex-dotfiles` directory as a future candidate slot, with activation permitted only after explicit official login plus a reviewed registry-only binding change.
