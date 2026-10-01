# Weekly GitHub Dev Summary — n8n + Claude

1. Import `workflow.json` into n8n.
2. Create/select a GitHub API credential for the three GitHub HTTP nodes.
3. Set `GITHUB_REPO=owner/repo`, `SUMMARY_LANGUAGE=EN` (or `FR`), `ANTHROPIC_API_KEY`, and `SLACK_WEBHOOK_URL` in the n8n environment.
4. Run once manually and verify the Slack message; the schedule is Friday at 17:00.
5. Activate the workflow.

The workflow fetches commits, closed issues, and merged PRs from the last seven days, asks `claude-sonnet-4-20250514` for a factual narrative summary, then posts it to Slack.

## Verification
`validate_workflow.py` checks that the export is valid JSON, contains the required schedule/GitHub/Claude/Slack stages, uses the requested Claude model, and exposes configurable repo/language/destination values.

The submission machine has Node/npm but not a running n8n instance, so a successful real-instance execution screenshot is **not claimed**. The export is structurally validated locally; a real n8n import/execution remains the acceptance item that needs environment credentials.
