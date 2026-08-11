import sys
from pathlib import Path
sys.path.insert(0, str(Path('gpt-researcher').resolve()))
from gpt_researcher.memory.resilient_embeddings import ResilientEmbeddingsAdapter
from langchain_core.documents import Document

class DummyEmbeddings:
    def embed_query(self, text):
        print('DummyEmbeddings.embed_query', repr(text))
        return [0.1, 0.2, 0.3]
    def embed_documents(self, texts):
        print('DummyEmbeddings.embed_documents', repr(texts))
        return [[0.1, 0.2, 0.3] for _ in texts]

class DebugAdapter(ResilientEmbeddingsAdapter):
    async def _embed_documents_async(self, texts):
        docs = [Document(page_content=text, metadata={}) for text in texts]
        result = await self._pipeline.embed_documents(docs, wait_for_result=True, wait_timeout=None)
        print('DEBUG _embed_documents_async result', result)
        if result.get('status') != 'completed':
            raise RuntimeError(result.get('error') or 'Embedding request did not complete')
        rv = result.get('result') or result.get('results') or []
        print('DEBUG _embed_documents_async rv', rv)
        return rv

adapter = DebugAdapter(DummyEmbeddings())
print('calling adapter.embed_documents')
res = adapter.embed_documents(['hello'])
print('adapter.embed_documents returned', res, type(res))
