from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "block-destructive-commands.py"


class HookTests(unittest.TestCase):
    def invoke(self, command: str, tool_name: str = "Bash"):
        with tempfile.TemporaryDirectory() as home:
            cwd = "/tmp/example-project"
            payload = {
                "session_id": "test-session",
                "cwd": cwd,
                "hook_event_name": "PreToolUse",
                "tool_name": tool_name,
                "tool_input": {"command": command},
            }
            env = os.environ.copy()
            env["HOME"] = home
            proc = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            log = Path(home) / ".claude" / "hooks" / "blocked.log"
            contents = log.read_text(encoding="utf-8") if log.exists() else ""
            return proc, contents
    def assert_blocked(self, command: str, reason: str | None = None):
        proc, log = self.invoke(command)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("BLOCKED destructive Bash command", proc.stderr)
        record = json.loads(log.strip())
        timestamp = dt.datetime.fromisoformat(record["timestamp"])
        self.assertIsNotNone(timestamp.tzinfo)
        self.assertEqual(timestamp.utcoffset(), dt.timedelta(0))
        self.assertEqual(record["command"], command)
        self.assertEqual(record["project_path"], "/tmp/example-project")
        if reason:
            self.assertEqual(record["reason"], reason)

    def assert_allowed(self, command: str):
        proc, log = self.invoke(command)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stderr, "")
        self.assertEqual(log, "")

    def test_blocks_recursive_forced_removal(self):
        self.assert_blocked("rm -rf build", "recursive forced removal")
        self.assert_blocked("rm -fr ./dist", "recursive forced removal")
        self.assert_blocked("rm --recursive --force cache", "recursive forced removal")

    def test_blocks_nested_shell_recursive_force(self):
        self.assert_blocked('bash -c "rm -rf build"', "recursive forced removal")

    def test_blocks_forced_git_push(self):
        self.assert_blocked("git push --force origin main", "forced git push")
        self.assert_blocked("git push -f origin main", "forced git push")

    def test_blocks_drop_and_truncate(self):
        self.assert_blocked("DROP TABLE users;", "DROP TABLE")
        self.assert_blocked("psql -c 'TRUNCATE TABLE audit_log;'", "TRUNCATE")

    def test_blocks_delete_without_where(self):
        self.assert_blocked('mysql -e "DELETE FROM sessions"', "DELETE FROM without WHERE")
    def test_allows_scoped_delete(self):
        self.assert_allowed('psql -c "DELETE FROM sessions WHERE id = 42"')

    def test_allows_normal_rm_and_git_push(self):
        self.assert_allowed("rm -r build")
        self.assert_allowed("rm -f artifact.zip")
        self.assert_allowed("git push origin main")

    def test_allows_inert_text(self):
        self.assert_allowed('echo "rm -rf /tmp/example"')
        self.assert_allowed('printf "%s\\n" "DROP TABLE demo"')

    def test_allows_normal_commands(self):
        self.assert_allowed("pytest -q")
        self.assert_allowed("git status")
        self.assert_allowed("python3 -m unittest")

    def test_non_bash_tool_is_ignored(self):
        proc, log = self.invoke("rm -rf build", tool_name="Read")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(log, "")

    def test_malformed_input_fails_open(self):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            proc = subprocess.run(
                [sys.executable, str(HOOK)],
                input="{not json",
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
