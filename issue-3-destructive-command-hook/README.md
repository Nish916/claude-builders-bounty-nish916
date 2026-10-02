# Destructive Bash Command Guard

A Claude Code `PreToolUse` hook for issue #3. It inspects Bash tool calls before execution, denies destructive commands, records an audit line, and leaves normal commands alone.

## Install

From the repository root:

```bash
chmod +x issue-3-destructive-command-hook/install.sh
issue-3-destructive-command-hook/install.sh
```

The installer copies the hook to `~/.claude/hooks/block-destructive-commands.py` and idempotently registers a `PreToolUse` matcher for the Bash tool in `~/.claude/settings.json`. If settings already exist, they are preserved and a `.bak` backup is created before modification.

## Blocked commands

The guard denies:

- recursive + forced `rm` invocations, including combined flags such as `rm -rf` and `rm -fr`;
- `git push --force` and `git push -f`;
- `DROP TABLE`;
- `TRUNCATE`;
- `DELETE FROM` statements that do not contain a `WHERE` clause.

Nested `bash -c`, `sh -c`, and `zsh -c` payloads are checked as well.

A blocked command exits with status `2` and writes a clear reason to stderr so Claude can explain the refusal and choose a safer scoped command.

## Audit log

Every denied attempt appends one JSON line to:

```text
~/.claude/hooks/blocked.log
```

Each record contains:

- UTC timestamp;
- attempted command;
- current project path from the hook payload;
- block reason.

No allowed command is logged.

## Safety behavior

The hook fails open for malformed/non-Bash hook payloads so it does not break unrelated Claude Code tools. Inert display commands such as `echo "rm -rf /tmp/example"` are not blocked. A scoped SQL delete containing `WHERE` is allowed.

## Tests

Run:

```bash
python3 -m unittest discover -s issue-3-destructive-command-hook/tests -v
```

The suite covers required destructive patterns, combined flags, nested shells, SQL-client commands, safe deletes, ordinary Bash commands, inert text, non-Bash tool calls, UTC-stamped logging, and malformed input. Installer tests also verify that existing Claude settings are preserved, a backup is created, the installed hook is mode `0700`, and repeated installation does not register duplicate hooks.

## Hook payload

The hook reads Claude Code's JSON payload from stdin and uses `tool_name`, `tool_input.command`, and `cwd`. It emits no output for allowed calls. For blocked `PreToolUse` calls, exit code `2` plus stderr is used to deny execution and return the reason to Claude.
