import asyncio
from typing import Callable, Any

async def execute_with_timeout(coro: Any, timeout_seconds: float) -> Any:
    """Executes an asynchronous coroutine under a strict timeout threshold."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError as e:
        raise asyncio.TimeoutError(f"Execution timed out after {timeout_seconds} seconds.") from e
