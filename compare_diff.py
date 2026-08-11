from pathlib import Path
import difflib
files = [
    ('gpt-researcher/gpt_researcher/skills/researcher.py','GPT-Researcher-Original/gpt_researcher/skills/researcher.py'),
    ('gpt-researcher/gpt_researcher/vector_store/vector_store.py','GPT-Researcher-Original/gpt_researcher/vector_store/vector_store.py')
]
for a,b in files:
    print('===',a,'vs',b)
    pa = Path(a).read_text(encoding='utf-8', errors='replace').splitlines()
    pb = Path(b).read_text(encoding='utf-8', errors='replace').splitlines()
    diff = list(difflib.unified_diff(pa,pb,fromfile=a,tofile=b,n=3))
    if not diff:
        print('NO DIFF')
    else:
        for line in diff[:300]:
            print(line)
    print()