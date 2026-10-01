#!/usr/bin/env python3
import argparse, os, re, shutil, subprocess, sys, urllib.parse

def parse_pr(url):
    m=re.fullmatch(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)',url.rstrip('/'))
    if not m: raise SystemExit('Expected https://github.com/owner/repo/pull/123')
    return m.groups()

def fetch_diff(url):
    owner,repo,num=parse_pr(url)
    cp=subprocess.run(['gh','pr','diff',num,'--repo',f'{owner}/{repo}'],capture_output=True,text=True,check=True)
    return cp.stdout

def fallback_review(diff):
    files=len(re.findall(r'^diff --git ',diff,re.M))
    adds=len(re.findall(r'^\+(?!\+\+\+)',diff,re.M)); dels=len(re.findall(r'^-(?!---)',diff,re.M))
    risks=[]; suggestions=[]
    if re.search(r'password|secret|token|api[_-]?key',diff,re.I): risks.append('Diff contains credential-sensitive terms; verify no secret material is committed.')
    if re.search(r'\b(eval|exec)\s*\(',diff): risks.append('Dynamic execution appears in the diff; validate inputs and threat model.')
    if adds+dels>500: risks.append('Large change surface increases review risk; consider splitting or adding targeted tests.')
    if not re.search(r'test|spec',diff,re.I): suggestions.append('Add or confirm targeted regression coverage for the changed behavior.')
    if files>5: suggestions.append('Call out cross-file behavior changes in the PR description to make verification easier.')
    if not risks: risks=['No high-signal risk detected by the deterministic fallback; human/Claude review is still recommended.']
    if not suggestions: suggestions=['Keep the regression test focused on the reported behavior and edge cases.']
    conf='High' if files<=3 and adds+dels<=150 else 'Medium'
    return f'''## Summary\nThis PR changes {files} file(s) with approximately {adds} added and {dels} removed lines. The fallback reviewer summarizes only signals visible in the diff and does not infer unobserved runtime behavior.\n\n## Risks\n''' + ''.join(f'- {x}\n' for x in risks) + '\n## Improvement suggestions\n' + ''.join(f'- {x}\n' for x in suggestions) + f'\n## Confidence\n{conf}\n'

def review_with_claude(diff):
    binary=os.environ.get('CLAUDE_BIN','claude')
    if not shutil.which(binary): return None
    prompt='Review this PR diff using the pr-reviewer format.\n\n'+diff
    cp=subprocess.run([binary,'-p',prompt],capture_output=True,text=True)
    if cp.returncode!=0: return None
    return cp.stdout.strip()+'\n'

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--pr',required=True); ap.add_argument('--fallback-only',action='store_true'); a=ap.parse_args()
    diff=fetch_diff(a.pr)
    out=None if a.fallback_only else review_with_claude(diff)
    if not out: out=fallback_review(diff)
    print(out,end='')
if __name__=='__main__': main()
