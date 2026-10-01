from pathlib import Path
p=Path(__file__).with_name('CLAUDE.md').read_text()
required=['Stack and versions','Project structure','Database rules','Migrations','Commands','Component patterns','What we do not do (and why)','Change protocol for Claude Code']
missing=[x for x in required if x not in p]
assert not missing, missing
for phrase in ['server-only','prepared statements','Zod','better-sqlite3','Turso/libSQL','regression test']:
    assert phrase.lower() in p.lower(), phrase
print('template contract: PASS')
