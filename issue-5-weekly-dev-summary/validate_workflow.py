import json, pathlib

p = pathlib.Path(__file__).with_name("workflow.json")
data = json.loads(p.read_text())
names = {n["name"] for n in data["nodes"]}
for x in [
    "Friday 5pm",
    "Config",
    "GitHub Commits",
    "Closed Issues",
    "Closed PRs",
    "Aggregate Week",
    "Claude Summary",
    "Send to Slack",
]:
    assert x in names, x

raw = p.read_text()
for x in [
    "claude-sonnet-4-20250514",
    "GITHUB_REPO",
    "SUMMARY_LANGUAGE",
    "SLACK_WEBHOOK_URL",
    "SLACK_CHANNEL",
    "ANTHROPIC_API_KEY",
]:
    assert x in raw, x

expected_chain = {
    "Friday 5pm": "Config",
    "Config": "GitHub Commits",
    "GitHub Commits": "Closed Issues",
    "Closed Issues": "Closed PRs",
    "Closed PRs": "Aggregate Week",
    "Aggregate Week": "Claude Summary",
    "Claude Summary": "Send to Slack",
}
for source, target in expected_chain.items():
    actual = data["connections"][source]["main"][0][0]["node"]
    assert actual == target, (source, actual, target)

aggregate = next(n for n in data["nodes"] if n["name"] == "Aggregate Week")
code = aggregate["parameters"]["jsCode"]
assert "merged_at" in code
assert "Date.now()-7*86400000" in code

print("workflow contract: PASS")
