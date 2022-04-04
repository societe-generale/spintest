"""Initialization of `spintest` package."""

import asyncio
import colorlog
import logging

from typing import Callable, Dict, List, Union, Optional


handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter("%(log_color)s%(asctime)s - %(levelname)s - %(message)s")
)
logger = colorlog.getLogger("spintest")
logger.setLevel(logging.INFO)
logger.addHandler(handler)


from spintest.manager import TaskManager  # noqa: E402


def spintest(
    urls: List[str],
    tasks: List[Dict[str, str]],
    token: Union[str, Callable[..., str], None] = None,
    parallel: bool = False,
    verify: bool = True,
    generate_report: Optional[str] = None,
):
    """Programmatic wrapper for spintest."""
    loop = asyncio.new_event_loop()
    task_manager = TaskManager(
        urls,
        tasks,
        token=token,
        parallel=parallel,
        verify=verify,
        generate_report=generate_report,
    )
    result = loop.run_until_complete(task_manager.run())
    loop.close()
    return result


__all__ = ["spintest", "TaskManager"]
__version__ = "0.4.2"
