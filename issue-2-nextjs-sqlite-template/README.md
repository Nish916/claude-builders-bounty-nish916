# Next.js 15 + SQLite CLAUDE.md template

Copy `CLAUDE.md` to the root of a greenfield Next.js 15 App Router project.

The template is intentionally opinionated: Server Components by default, explicit server-only DB boundaries, immutable migrations, Zod runtime validation, thin Server Actions, and deployment-aware SQLite guidance.

## Verification note
The submission host does not currently have the Claude Code binary installed, so I do not claim a live Claude Code comprehension session. The document is structured to be directly usable without project-specific edits; its required sections and key invariants are checked by `verify_template.py`. `greenfield_smoke.py` also creates a representative App Router/SQLite project skeleton, copies the file unchanged, and verifies the template can be used without project-specific placeholders. Fresh result: `greenfield copy smoke: PASS — CLAUDE.md used unchanged`.
