import asyncio
from typing import Any, Awaitable, Callable, Iterable, List


async def gather_limited(
    coros: Iterable[Awaitable[Any]], limit: int
) -> List[Any]:
    """Run coroutines concurrently with a concurrency limit."""
    semaphore = asyncio.Semaphore(limit)

    async def _sem_task(coro: Awaitable[Any]):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(_sem_task(c) for c in coros))