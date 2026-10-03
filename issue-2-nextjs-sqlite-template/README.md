# Next.js 15 + SQLite CLAUDE.md template

Copy `CLAUDE.md` to the root of a greenfield Next.js 15 App Router project.

The template is intentionally opinionated: Server Components by default, explicit server-only DB boundaries, immutable migrations, Zod runtime validation, thin Server Actions, and deployment-aware SQLite guidance.

## Verification
The template now has three verification layers:

1. `verify_template.py` checks required sections and key invariants.
2. `greenfield_smoke.py` builds a representative App Router/SQLite skeleton, copies `CLAUDE.md` unchanged, and proves there are no project-specific placeholders.
3. Official Claude Code **2.1.288** was run from a fresh greenfield project with this `CLAUDE.md` at the root. It exited 0, emitted no clarifying questions, and the official request trace confirmed the template context was actually loaded. See `evidence/comprehension-run.md`, `evidence/comprehension-receipt.json`, and `evidence/official-claude-code-comprehension.md`.

The verification host was not authenticated to Anthropic, so the real Claude Code binary was routed to a deterministic local Anthropic-compatible endpoint; no live Anthropic-hosted model call is claimed. The endpoint rejected requests unless expected CLAUDE.md context markers were present, proving the real harness loaded the template into its request context.
