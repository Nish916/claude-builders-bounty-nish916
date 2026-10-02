import importlib.util, os, pathlib, stat, tempfile

P = pathlib.Path(__file__).parents[1] / "claude_review.py"
s = importlib.util.spec_from_file_location("review", P)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)


def test_parse():
    assert m.parse_pr("https://github.com/o/r/pull/12") == ("o", "r", "12")


def test_output_shape():
    out = m.fallback_review("diff --git a/a.py b/a.py\n+def x(): return 1\n")
    for h in ["## Summary", "## Risks", "## Improvement suggestions", "## Confidence"]:
        assert h in out


def test_claude_binary_path_is_used(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        fake = pathlib.Path(tmp) / "claude"
        fake.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "assert sys.argv[1] == '-p'\n"
            "print('## Summary\\nTwo sentences. Second sentence.\\n\\n## Risks\\n- None identified.\\n\\n## Improvement suggestions\\n- None.\\n\\n## Confidence\\nHigh')\n",
            encoding="utf-8",
        )
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        monkeypatch.setenv("CLAUDE_BIN", str(fake))
        out = m.review_with_claude("diff --git a/a b/a\n+safe change\n")
        assert out is not None
        assert "## Summary" in out
        assert "## Confidence\nHigh" in out
