from __future__ import annotations

import asyncio
import time

import tiktoken
from langchain_core.documents import Document
from rich.console import Console

from config.settings import DEFAULT_MAX_TOKENS_PER_MINUTE, DEFAULT_RATE_LIMIT_ENCODING

console = Console()

_WINDOW_SECONDS = 70


class TokenRateLimiter:
    def __init__(
        self,
        max_tokens_per_minute: int = DEFAULT_MAX_TOKENS_PER_MINUTE,
        encoding_name: str = DEFAULT_RATE_LIMIT_ENCODING,
    ):
        self.max_tokens_per_minute = max_tokens_per_minute
        self.encoding = tiktoken.get_encoding(encoding_name)

        self.tokens_used = 0
        self.window_start = time.monotonic()

        self._lock = asyncio.Lock()

    def count_tokens(self, docs: list[Document]) -> int:
        return sum(len(self.encoding.encode(doc.page_content)) for doc in docs)

    async def acquire(self, docs: list[Document]):
        batch_tokens = self.count_tokens(docs)

        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.window_start

                if elapsed >= _WINDOW_SECONDS:
                    self.tokens_used = 0
                    self.window_start = now

                if self.tokens_used + batch_tokens <= self.max_tokens_per_minute:
                    self.tokens_used += batch_tokens
                    console.print(
                        f"[green]TPM: {self.tokens_used}/{self.max_tokens_per_minute}[/green]"
                    )
                    return

                wait_time = _WINDOW_SECONDS - elapsed
                console.print(
                    f"[yellow]TPM limit reached. Waiting {wait_time:.1f}s...[/yellow]"
                )
                await asyncio.sleep(wait_time)
