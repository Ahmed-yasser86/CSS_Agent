from __future__ import annotations

import asyncio

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from rich.console import Console

from config.settings import DEFAULT_EMBED_BATCH_SIZE, DEFAULT_EMBED_SEMAPHORE_LIMIT
from infra.rate_limiter import TokenRateLimiter
from infra.vector_store import add_documents_with_retry
from utils.logger import log_error

console = Console()


async def process_batch(
    vector_store: QdrantVectorStore,
    batch: list[Document],
    batch_num: int,
    semaphore: asyncio.Semaphore,
    limiter: TokenRateLimiter,
) -> bool:
    async with semaphore:
        try:
            console.print(f"Embedding batch {batch_num}")

            await limiter.acquire(batch)
            await add_documents_with_retry(vector_store, batch)

            console.print(f"✓ Batch {batch_num} completed")
            return True

        except Exception as e:
            log_error(f"Failed batch {batch_num}: {e}")
            return False


def _partition_into_batches(
    docs: list[Document],
    batch_size: int,
) -> list[tuple[int, list[Document]]]:
    total_batches = (len(docs) + batch_size - 1) // batch_size

    return [
        (batch_num + 1, docs[batch_num * batch_size : batch_num * batch_size + batch_size])
        for batch_num in range(total_batches)
    ]


async def embed_documents_in_batches(
    vector_store: QdrantVectorStore,
    docs: list[Document],
    batch_size: int = DEFAULT_EMBED_BATCH_SIZE,
    semaphore: asyncio.Semaphore | None = None,
    limiter: TokenRateLimiter | None = None,
) -> dict[str, int]:
    semaphore = semaphore or asyncio.Semaphore(DEFAULT_EMBED_SEMAPHORE_LIMIT)
    limiter = limiter or TokenRateLimiter()

    batches = _partition_into_batches(docs, batch_size)

    tasks = [
        process_batch(vector_store, batch, batch_num, semaphore, limiter)
        for batch_num, batch in batches
    ]

    results = await asyncio.gather(*tasks)

    return {
        "total_documents": len(docs),
        "total_batches": len(batches),
        "successful_batches": sum(results),
        "failed_batches": results.count(False),
    }
