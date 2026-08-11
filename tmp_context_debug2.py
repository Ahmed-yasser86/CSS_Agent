import sys
from pathlib import Path
sys.path.insert(0, str(Path('gpt-researcher').resolve()))
from gpt_researcher.context.compression import ContextCompressor
from langchain_classic.retrievers.document_compressors import EmbeddingsFilter
from langchain_community.document_transformers.embeddings_redundant_filter import _get_embeddings_from_stateful_docs, get_stateful_documents

class DummyEmbeddings:
    def embed_query(self, text):
        print('embed_query', repr(text))
        return [0.1, 0.2, 0.3]
    def embed_documents(self, texts):
        print('embed_documents', repr(texts))
        return [[0.1, 0.2, 0.3] for _ in texts]

pages=[{'raw_content':'A valid content paragraph for testing.', 'url': 'https://example.com/1'}]
compressor=ContextCompressor(documents=pages, embeddings=DummyEmbeddings(), similarity_threshold=0.0)
filtered=compressor._filter_documents()
print('filtered', filtered)
docs = [d for d in filtered]
print('docs', docs)
stateful = get_stateful_documents([d if hasattr(d,'page_content') else d for d in docs])
print('stateful len', len(stateful))
for i, doc in enumerate(stateful):
    print('stateful', i, doc.page_content, doc.state)
embedded_docs = _get_embeddings_from_stateful_docs(compressor.embeddings, stateful)
print('embedded_docs', embedded_docs)
print('len', len(embedded_docs))
print('similarity func', compressor._ContextCompressor__get_contextual_retriever(filtered).base_compressor.transformers[1].similarity_fn)

filter = EmbeddingsFilter(embeddings=compressor.embeddings, similarity_threshold=0.0)
for d in docs:
    print('doc page_content repr', repr(d.page_content))
print('running compress_documents')
print(filter.compress_documents(docs, 'query'))
