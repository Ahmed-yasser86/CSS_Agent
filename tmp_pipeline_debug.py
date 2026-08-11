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
print('pipeline', adapter._pipeline)
print('calling _pipeline.embed_documents directly')
import asyncio
res = asyncio.run(adapter._pipeline.embed_documents([__import__('langchain_core').documents.Document(page_content='hello', metadata={})], wait_for_result=True, wait_timeout=None))
print('direct pipeline res', res)
print('calling adapter.embed_documents')
res2 = adapter.embed_documents(['hello'])
print('adapter.embed_documents res', res2)
print('calling adapter.embed_query')
q = adapter.embed_query('hello')
print('adapter.embed_query res', q)
