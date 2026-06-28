import asyncio
import logging
from typing import Callable, Any, Type, Tuple

logger = logging.getLogger(__name__)

async def execute_with_retry(
    func: Callable[[], Any],
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    exceptions_to_retry: Tuple[Type[Exception], ...] = (Exception,)
) -> Any:
    """Executes a function with exponential backoff retry policy."""
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions_to_retry as e:
            if attempt == max_retries:
                logger.error(f"Retry policy exhausted. Failed after {max_retries} retries: {str(e)}")
                raise e
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
            delay *= backoff_factor
