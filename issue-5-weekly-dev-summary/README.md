# Weekly GitHub Dev Summary — n8n + Claude

1. Import `workflow.json` into n8n.
2. Create/select a GitHub API credential for the three GitHub HTTP nodes.
3. Set `GITHUB_REPO=owner/repo`, `SUMMARY_LANGUAGE=EN` (or `FR`), `ANTHROPIC_API_KEY`, `SLACK_WEBHOOK_URL`, and optional `SLACK_CHANNEL` in the n8n environment.
4. Run once manually and verify the Slack message; the schedule is Friday at 17:00.
5. Activate the workflow.

The workflow fetches commits, closed issues, and merged PRs from the last seven days in a deterministic sequential chain, asks `claude-sonnet-4-20250514` for a factual narrative summary, then posts it to the configured Slack destination.

## Verification
`validate_workflow.py` checks that the export is valid JSON, contains the required schedule/GitHub/Claude/Slack stages, uses the requested Claude model, exposes configurable repo/language/destination values, and guarantees all three GitHub fetches complete before aggregation.

The production workflow remains credential-bound. To make import and execution reviewable without publishing secrets or incurring API spend, `verification_workflow.json` is a separate credential-free workflow that preserves the summary data shape, mocks the Claude boundary, and captures the delivery instead of sending it.

It was imported and executed end-to-end in **n8n 2.41.6** on 2026-10-03. All four nodes completed successfully and the last node emitted `status: PASS` plus `delivery: captured-not-sent`. See the [rendered n8n CLI evidence](verification-n8n-execution.svg) and machine-readable [execution receipt](verification_receipt.json).

Evidence boundary: this proves real n8n importability and node execution. It does **not** claim a live Anthropic API call or Slack delivery. A production run still requires the reviewer's own GitHub credential, Anthropic key, and Slack webhook.

Fresh validation: `python validate_workflow.py` → **workflow contract: PASS** and **verification contract: PASS**.
