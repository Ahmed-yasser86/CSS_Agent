import sys
from pathlib import Path
sys.path.insert(0, str(Path('gpt-researcher').resolve()))
import inspect
from langchain_classic.retrievers import ContextualCompressionRetriever
print(inspect.getsource(ContextualCompressionRetriever))
