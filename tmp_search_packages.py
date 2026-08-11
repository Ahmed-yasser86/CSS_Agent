import os, sys, re
roots = [r'C:\Users\DELL\graph-rag-agent\.venv\Lib\site-packages']
for root in roots:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {'.git', '__pycache__', '.pytest_cache'}]
        for fn in filenames:
            if not fn.endswith(('.py', '.pyi', '.json', '.md')):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            except Exception:
                continue
            if 'Unknown web research tool' in text or 'web_research_tool_call' in text or 'web research tool' in text:
                print(path)
                break
        else:
            continue
        break
