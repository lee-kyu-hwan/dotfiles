# Brainstorming Policy

This is an adapted requirement-discovery policy for the quality-goal orchestrator. It preserves useful discovery principles while fitting the agreed workflow. The bundled brainstorming skill must not be invoked or modified.

- Inspect repository conventions, neighboring code, existing interfaces, tests, and documentation before proposing changes.
- Ask only materially necessary questions, one at a time. Questions resolve missing requirements; they are not approval gates.
- For an architectural decision, compare 2–3 approaches, explain the trade-offs, and recommend one.
- Make scope, non-goals, acceptance criteria, interfaces, error cases, and testability explicit.
- Decompose requests containing independent subsystems into independently understandable and testable parts, with clear boundaries and dependencies.
- Never begin implementation while requirements remain materially ambiguous. Record the unresolved decision and obtain the information needed to make it concrete first.

The resulting discovery output must be specific enough for a reviewer to check claims against repository evidence and for planning to map each acceptance criterion to work and verification.
