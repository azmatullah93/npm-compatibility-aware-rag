"""Fill the GitHub repository in the last abstract line and optional author email.

Usage:
  python scripts/finalize_paper.py --github https://github.com/user/repo \
      --email student@university.edu
"""
import argparse
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'paper'/'milestone1.tex'
parser=argparse.ArgumentParser()
parser.add_argument('--github',required=True)
parser.add_argument('--email',default=None)
a=parser.parse_args()
url=a.github.rstrip('/')
if not re.fullmatch(r'https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',url):
    raise SystemExit('Invalid repository URL; expected https://github.com/OWNER/REPO')
contents=p.read_text(encoding='utf-8')
match=re.search(r'Code repository: .*',contents)
if not match: raise SystemExit('Missing source link line; file may have changed')
contents=contents[:match.start()]+f'Code repository: \\url{{{url}}}'+contents[match.end():]
if a.email:
    if not re.fullmatch(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}',a.email):
        raise SystemExit('Invalid institutional email')
    marker='Registration No.: 26i-7841'
    # \\ inside file is the LaTeX line break. We only insert when absent.
    if a.email not in contents:
        contents=contents.replace(marker, marker+r'\\'+'\n'+r'Email: \texttt{\detokenize{'+a.email+'}}')
p.write_text(contents,encoding='utf-8')
for _ in range(2):
    subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','milestone1.tex'],cwd=ROOT/'paper',check=True,stdout=subprocess.DEVNULL)
print('Updated paper/milestone1.tex and paper/milestone1.pdf',url)
