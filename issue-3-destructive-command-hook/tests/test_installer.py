from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.sh"


class InstallerTests(unittest.TestCase):
    def run_installer(self, home: Path):
        env = os.environ.copy()
        env["HOME"] = str(home)
        return subprocess.run(
            ["bash", str(INSTALLER)],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_preserves_existing_settings_and_creates_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            claude_dir = home / ".claude"
            claude_dir.mkdir(parents=True)
            settings = claude_dir / "settings.json"
            original = {
                "permissions": {"allow": ["Read"]},
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Read",
                            "hooks": [{"type": "command", "command": "echo keep"}],
                        }
                    ]
                },
            }
            settings.write_text(json.dumps(original), encoding="utf-8")

            proc = self.run_installer(home)
            self.assertEqual(proc.returncode, 0, proc.stderr)

            backup = claude_dir / "settings.json.bak"
            self.assertTrue(backup.is_file())
            self.assertEqual(json.loads(backup.read_text(encoding="utf-8")), original)

            data = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(data["permissions"], original["permissions"])
            read_matchers = [
                item
                for item in data["hooks"]["PreToolUse"]
                if item.get("matcher") == "Read"
            ]
            self.assertEqual(read_matchers, original["hooks"]["PreToolUse"])

            target = claude_dir / "hooks" / "block-destructive-commands.py"
            self.assertTrue(target.is_file())
            self.assertEqual(target.stat().st_mode & 0o777, 0o700)

    def test_install_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)

            first = self.run_installer(home)
            second = self.run_installer(home)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)

            data = json.loads(
                (home / ".claude" / "settings.json").read_text(encoding="utf-8")
            )
            registered = []
            for matcher in data["hooks"]["PreToolUse"]:
                for hook in matcher.get("hooks", []):
                    if "block-destructive-commands.py" in str(hook.get("command", "")):
                        registered.append((matcher.get("matcher"), hook))
            self.assertEqual(len(registered), 1)
            self.assertEqual(registered[0][0], "Bash")


if __name__ == "__main__":
    unittest.main()
