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
import asyncio

async def main():
    print('calling _embed_documents_async directly')
    result = await adapter._embed_documents_async(['hello'])
    print('direct async result', result, type(result))

    print('calling _run_async on _embed_documents_async')
    result2 = adapter._run_async(adapter._embed_documents_async(['hello']))
    print('raw result2', result2, type(result2))

    print('calling embed_documents regular')
    result3 = adapter.embed_documents(['hello'])
    print('result3', result3, type(result3))

asyncio.run(main())
