import json, pathlib
p=pathlib.Path(__file__).with_name('workflow.json')
data=json.loads(p.read_text())
names={n['name'] for n in data['nodes']}
for x in ['Friday 5pm','Config','GitHub Commits','Closed Issues','Closed PRs','Aggregate Week','Claude Summary','Send to Slack']:
    assert x in names,x
raw=p.read_text()
for x in ['claude-sonnet-4-20250514','GITHUB_REPO','SUMMARY_LANGUAGE','SLACK_WEBHOOK_URL','ANTHROPIC_API_KEY']:
    assert x in raw,x
assert data['connections']['Claude Summary']['main'][0][0]['node']=='Send to Slack'
print('workflow contract: PASS')
