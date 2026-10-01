import importlib.util, pathlib
P=pathlib.Path(__file__).parents[1]/'claude_review.py'
s=importlib.util.spec_from_file_location('review',P); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
def test_parse(): assert m.parse_pr('https://github.com/o/r/pull/12')==('o','r','12')
def test_output_shape():
    out=m.fallback_review('diff --git a/a.py b/a.py\n+def x(): return 1\n')
    for h in ['## Summary','## Risks','## Improvement suggestions','## Confidence']: assert h in out
