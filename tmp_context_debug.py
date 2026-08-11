import sys
from pathlib import Path
sys.path.insert(0, str(Path('gpt-researcher').resolve()))
from gpt_researcher.context.compression import ContextCompressor
from langchain_core.documents import Document

class DummyEmbeddings:
    def embed_query(self, text):
        return [0.1, 0.2, 0.3]
    def embed_documents(self, texts):
        print('embed_documents called with', texts)
        return [[0.1, 0.2, 0.3] for _ in texts]

pages = [
    {'raw_content': 'A valid content paragraph for testing.', 'url': 'https://example.com/1'}
]
compressor = ContextCompressor(documents=pages, embeddings=DummyEmbeddings(), similarity_threshold=0.0)
print('filtered docs', compressor._filter_documents())
retriever = compressor._ContextCompressor__get_contextual_retriever(compressor._filter_documents())
print('retriever', retriever)
print('methods', [m for m in dir(retriever) if 'invoke' in m])
print('has invoke:', hasattr(retriever, 'invoke'))
print('call invoke:')
print(retriever.invoke('query'))
print('done')
