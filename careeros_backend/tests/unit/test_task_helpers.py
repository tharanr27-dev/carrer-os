"""Background-execution helpers must never block or crash the event loop."""

import asyncio
import time

import pytest

from app.core.tasks import enqueue, spawn


class _Task:
    name = "fake.task"

    def __init__(self, behaviour):
        self.behaviour = behaviour
        self.calls = []

    def apply_async(self, args=(), retry=True):
        self.calls.append((args, retry))
        self.behaviour()


@pytest.mark.asyncio
async def test_enqueue_sends_without_retries():
    task = _Task(lambda: None)
    assert await enqueue(task, "abc") is True
    assert task.calls == [(("abc",), False)]


@pytest.mark.asyncio
async def test_enqueue_swallows_broker_errors():
    def boom():
        raise ConnectionError("broker down")

    assert await enqueue(_Task(boom), "abc") is False


@pytest.mark.asyncio
async def test_enqueue_times_out_instead_of_freezing_the_loop():
    task = _Task(lambda: time.sleep(1.0))
    ticks = 0

    async def heartbeat():
        nonlocal ticks
        while True:
            ticks += 1
            await asyncio.sleep(0.01)

    beat = asyncio.create_task(heartbeat())
    started = time.monotonic()
    ok = await enqueue(task, "abc", timeout=0.1)
    elapsed = time.monotonic() - started
    beat.cancel()

    assert ok is False
    assert elapsed < 0.6
    assert ticks > 3  # the loop kept running while the send was stuck


@pytest.mark.asyncio
async def test_spawn_runs_coroutine_to_completion():
    done = asyncio.Event()

    async def work():
        done.set()

    spawn(work())
    await asyncio.wait_for(done.wait(), timeout=1)


@pytest.mark.asyncio
async def test_spawn_logs_but_does_not_propagate_failures():
    async def fail():
        raise RuntimeError("nope")

    task = spawn(fail())
    await asyncio.sleep(0.05)
    assert task.done()
