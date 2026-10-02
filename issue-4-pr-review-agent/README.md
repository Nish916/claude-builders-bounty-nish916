# Claude PR Review Agent

A small Claude Code sub-agent + CLI for reviewing a GitHub PR and emitting a structured Markdown comment.

## Setup
1. Install/authenticate GitHub CLI (`gh`) and Claude Code (`claude`).
2. Copy `.claude/agents/pr-reviewer.md` into your project (or keep this folder as-is).
3. Run: `python3 claude_review.py --pr https://github.com/owner/repo/pull/123`.

The CLI fetches the diff with `gh pr diff`. When Claude Code is available it sends the diff to `claude -p`; otherwise it uses a conservative deterministic fallback so the command still returns the required structure. Set `CLAUDE_BIN` to override the executable. `--fallback-only` is useful for offline verification.

## Output contract
`Summary` (2-3 sentences), `Risks`, `Improvement suggestions`, and `Confidence` (`Low`, `Medium`, or `High`).

## Verification
The local runner used for this submission does not have a real Claude binary installed, so no Claude-generated model result is claimed. The Claude execution path is nevertheless covered with an injected executable contract test proving `CLAUDE_BIN` is invoked with `-p` and its structured output is returned. Fresh test run: `python -m pytest -q issue-4-pr-review-agent/tests` → **3 passed**. Two real public PR diffs were also exercised through the deterministic fallback; their outputs are committed in `samples/`.
