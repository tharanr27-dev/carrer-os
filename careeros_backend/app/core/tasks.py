import asyncio
import logging
from typing import Any, Coroutine

logger = logging.getLogger("careeros")

# Strong references so fire-and-forget tasks are not garbage-collected mid-flight.
_running: set[asyncio.Task] = set()


def spawn(coro: Coroutine[Any, Any, Any]) -> asyncio.Task:
    """Runs a coroutine in the background of the current event loop.

    FastAPI only executes ``BackgroundTasks`` after an HTTP response is sent, so they never run
    for WebSocket routes. Long-lived socket handlers use this instead.
    """
    task = asyncio.create_task(coro)
    _running.add(task)

    def _done(t: asyncio.Task) -> None:
        _running.discard(t)
        if not t.cancelled() and t.exception():
            logger.error("Background task failed", exc_info=t.exception())

    task.add_done_callback(_done)
    return task


async def enqueue(task: Any, *args: Any, timeout: float = 2.0) -> bool:
    """Queues a Celery task without ever blocking the event loop.

    ``task.delay()`` is synchronous and, when the broker is unreachable, can stall for many seconds
    (DNS + connection retries), freezing every other request. Here the send runs in a worker thread
    with no retries and a hard timeout; failures are logged and reported as ``False`` so the
    request that triggered the work still succeeds.
    """

    def _send() -> None:
        task.apply_async(args=args, retry=False)

    try:
        await asyncio.wait_for(asyncio.to_thread(_send), timeout=timeout)
        return True
    except Exception as exc:  # broker down, timeout, serialisation problems...
        logger.warning("Could not enqueue %s: %s", getattr(task, "name", task), exc)
        return False
