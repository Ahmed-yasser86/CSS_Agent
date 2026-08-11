import sys
from pathlib import Path
sys.path.insert(0, str(Path('gpt-researcher').resolve()))
from gpt_researcher.context.compression import ContextCompressor
from langchain_classic.retrievers.document_compressors import EmbeddingsFilter
from langchain_community.document_transformers.embeddings_redundant_filter import get_stateful_documents, _get_embeddings_from_stateful_docs

class DummyEmbeddings:
    def embed_query(self, text):
        print('embed_query called with', repr(text))
        return [0.1, 0.2, 0.3]

    def embed_documents(self, texts):
        print('embed_documents called with', repr(texts))
        return [[0.1, 0.2, 0.3] for _ in texts]

pages = [{'raw_content': 'A valid content paragraph for testing.', 'url': 'https://example.com/1'}]
compressor = ContextCompressor(documents=pages, embeddings=DummyEmbeddings(), similarity_threshold=0.0)
filtered = compressor._filter_documents()
print('filtered', filtered)
docs = [
    __import__('langchain_core').documents.Document(page_content=(page.get('raw_content') or '')[:10000], metadata={'title': page.get('title',''), 'source': page.get('url','')})
    for page in filtered
]
print('docs', docs)
print('doc page_content repr', repr(docs[0].page_content))
stateful = get_stateful_documents(docs)
print('stateful len', len(stateful))
for i, doc in enumerate(stateful):
    print('stateful', i, repr(doc.page_content), doc.state)
embedded_docs = _get_embeddings_from_stateful_docs(compressor.embeddings, stateful)
print('embedded_docs', embedded_docs)
print('embedded_docs type', type(embedded_docs), len(embedded_docs))
try:
    similarity_fn = compressor._ContextCompressor__get_contextual_retriever(filtered).base_compressor.transformers[1].similarity_fn
    print('similarity_fn', similarity_fn)
    print('similarity_fn source:', getattr(similarity_fn, '__module__', None), getattr(similarity_fn, '__name__', None))
    similarity = similarity_fn([compressor.embeddings.embed_query('query')], embedded_docs)
    print('similarity shape', similarity, type(similarity))
    print('similarity[0]', similarity[0])
except Exception as e:
    print('error computing similarity', type(e).__name__, e)
