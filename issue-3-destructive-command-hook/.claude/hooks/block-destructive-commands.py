#!/usr/bin/env python3
"""Claude Code PreToolUse guard for destructive Bash commands.

Reads a hook payload from stdin. Bash commands matching destructive patterns are
logged and denied with exit code 2; all other tool calls are allowed.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Iterable

SHELL_SEPARATORS = {";", "&&", "||", "|", "&"}
SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3"}
SAFE_TEXT_COMMANDS = {"echo", "printf"}

DROP_TABLE_RE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE)
DELETE_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def shell_tokens(command: str) -> list[str]:
    """Tokenize enough shell syntax to inspect commands without executing it."""
    prepared = re.sub(r"(\&\&|\|\||[;|&])", r" \1 ", command)
    try:
        return shlex.split(prepared, posix=True)
    except ValueError:
        return prepared.split()


def command_groups(tokens: Iterable[str]) -> list[list[str]]:
    groups: list[list[str]] = [[]]
    for token in tokens:
        if token in SHELL_SEPARATORS:
            if groups[-1]:
                groups.append([])
            continue
        groups[-1].append(token)
    return [group for group in groups if group]
def has_recursive_force_rm(group: list[str]) -> bool:
    for index, token in enumerate(group):
        if os.path.basename(token) != "rm":
            continue
        flags: set[str] = set()
        recursive = False
        force = False
        for arg in group[index + 1 :]:
            if arg == "--":
                break
            if not arg.startswith("-"):
                continue
            if arg == "--recursive":
                recursive = True
            elif arg == "--force":
                force = True
            elif arg.startswith("--"):
                continue
            else:
                flags.update(arg[1:])
        recursive = recursive or "r" in flags or "R" in flags
        force = force or "f" in flags
        if recursive and force:
            return True
    return False


def has_forced_git_push(group: list[str]) -> bool:
    for index, token in enumerate(group):
        if os.path.basename(token) != "git":
            continue
        rest = group[index + 1 :]
        if not rest or rest[0] != "push":
            continue
        return any(
            arg == "--force"
            or arg.startswith("--force=")
            or (arg.startswith("-") and not arg.startswith("--") and "f" in arg[1:])
            for arg in rest[1:]
        )
    return False


def dangerous_sql(sql: str) -> str | None:
    for statement in re.split(r";|\n", sql):
        candidate = statement.strip()
        if not candidate:
            continue
        if DROP_TABLE_RE.search(candidate):
            return "DROP TABLE"
        if TRUNCATE_RE.search(candidate):
            return "TRUNCATE"
        if DELETE_RE.search(candidate) and not WHERE_RE.search(candidate):
            return "DELETE FROM without WHERE"
    return None
def sql_reason(command: str, groups: list[list[str]]) -> str | None:
    stripped = command.lstrip()
    first_word = stripped.split(None, 1)[0].lower() if stripped else ""
    if first_word in {"drop", "truncate", "delete"}:
        return dangerous_sql(stripped)

    # Do not block inert text display such as: echo "DROP TABLE demo".
    if first_word in SAFE_TEXT_COMMANDS:
        return None

    for group in groups:
        if not group:
            continue
        executable = os.path.basename(group[0]).lower()
        if executable in SQL_CLIENTS:
            reason = dangerous_sql(" ".join(group[1:]))
            if reason:
                return reason
    return None


def nested_shell_reason(group: list[str], depth: int) -> str | None:
    if depth >= 2 or not group:
        return None
    executable = os.path.basename(group[0]).lower()
    if executable not in {"sh", "bash", "zsh"}:
        return None
    for index, token in enumerate(group[1:], start=1):
        if token in {"-c", "-lc"} and index + 1 < len(group):
            return classify(group[index + 1], depth + 1)
    return None


def classify(command: str, depth: int = 0) -> str | None:
    tokens = shell_tokens(command)
    groups = command_groups(tokens)
    for group in groups:
        if has_recursive_force_rm(group):
            return "recursive forced removal"
        if has_forced_git_push(group):
            return "forced git push"
        nested = nested_shell_reason(group, depth)
        if nested:
            return nested
    return sql_reason(command, groups)
def log_block(command: str, cwd: str, reason: str) -> Path:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": command,
        "project_path": cwd,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = classify(command)
    if not reason:
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    log_path = log_block(command, cwd, reason)
    print(
        f"BLOCKED destructive Bash command ({reason}). "
        f"Review the command or use a safer scoped alternative. Logged to {log_path}.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
