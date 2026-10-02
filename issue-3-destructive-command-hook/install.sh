#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_HOOK="$SOURCE_DIR/.claude/hooks/block-destructive-commands.py"
TARGET_DIR="$HOME/.claude/hooks"
TARGET_HOOK="$TARGET_DIR/block-destructive-commands.py"
SETTINGS="$HOME/.claude/settings.json"

mkdir -p "$TARGET_DIR"
install -m 700 "$SOURCE_HOOK" "$TARGET_HOOK"

python3 - "$SETTINGS" "$TARGET_HOOK" <<'PY'
import json
import shutil
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_path = Path(sys.argv[2])

if settings_path.exists():
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Refusing to modify invalid JSON in {settings_path}: {exc}")
    shutil.copy2(settings_path, settings_path.with_suffix(".json.bak"))
else:
    data = {}

hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
command = f'python3 "{hook_path}"'

already_registered = False
for matcher in pre:
    for hook in matcher.get("hooks", []):
        if "block-destructive-commands.py" in str(hook.get("command", "")):
            already_registered = True
            break

if not already_registered:
    pre.append(
        {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": command}],
        }
    )

settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"Installed hook: {hook_path}")
print(f"Registered PreToolUse guard in: {settings_path}")
PY
