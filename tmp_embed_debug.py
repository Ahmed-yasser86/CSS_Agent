import sys
from pathlib import Path
sys.path.insert(0, str(Path('gpt-researcher').resolve()))
from gpt_researcher.memory.resilient_embeddings import ResilientEmbeddingsAdapter

class DummyEmbeddings:
    def embed_query(self, text):
        print('DummyEmbeddings.embed_query', repr(text))
        return [0.1, 0.2, 0.3]
    def embed_documents(self, texts):
        print('DummyEmbeddings.embed_documents', repr(texts))
        return [[0.1, 0.2, 0.3] for _ in texts]

adapter = ResilientEmbeddingsAdapter(DummyEmbeddings())
print('Calling adapter.embed_documents')
res = adapter.embed_documents(['hello'])
print('result', res, type(res))
print('Calling adapter.embed_query')
q = adapter.embed_query('hello')
print('q', q, type(q))
