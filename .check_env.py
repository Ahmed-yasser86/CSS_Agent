import os
from pathlib import Path

repo_root = Path(r"C:\Users\DELL\graph-rag-agent")
dotenv_path = repo_root / ".env"
print('Checking for .env at', dotenv_path)
if dotenv_path.exists():
    print('.env found, reading contents:\n')
    print(dotenv_path.read_text())
else:
    print('.env not found in repo root')

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path)
    print('\nLoaded .env via python-dotenv')
except Exception as e:
    print('\nCould not load .env via python-dotenv:', type(e).__name__, e)

keys=['RETRIEVER','STRATEGIC_LLM','TAVILY_API_KEY','OPENAI_API_KEY','MISTRAL_API_KEY','LANGCHAIN_API_KEY']
print('\nRuntime environment values:')
for k in keys:
    print(f'{k}={os.getenv(k)}')
