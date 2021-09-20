"""Task Manager representation."""

import asyncio
import itertools
import json

from typing import Callable, Dict, List, Union, Optional

from spintest import logger
from spintest.task import Task


class TaskManager(object):
    """Task manager."""

    def __init__(
        self,
        urls: List[str],
        tasks: List[Dict[str, str]],
        token: Union[str, Callable[..., str], None] = None,
        parallel: bool = False,
        verify: bool = True,
        generate_report: Optional[str] = None,
    ):
        """Initialization of `TaskManager` class."""
        self.urls = urls
        self.tasks = tasks
        self.rollback_tasks = []
        self.token = token
        self.verify = verify
        self.parallel = parallel
        self.generate_report = generate_report

        if self.parallel:
            self.outputs = [{"__token__": self.token}] * len(self.urls)
            self.stack = self._parallel_executor()
        else:
            self.outputs = [{"__token__": self.token}]
            self.stack = self._executor()

    @staticmethod
    def _error(critical: Optional[str] = None):
        """Throw a custom error."""
        if critical:
            logger.critical(critical)
        return [{"status": "FAILED", "ignore": False}]

    def validate_refs(self) -> bool:
        """Validate the integrity of task references."""
        task_names = [task["name"] for task in self.tasks if task.get("name")]
        for task in self.tasks:
            for rollback in task.get("rollback", []):
                if isinstance(rollback, str) and rollback not in task_names:
                    logger.critical("Reference validation failed.")
                    return False
        return True

    def rollback_lookup(self, name, activate_ignore=True):
        """Get a task from a name."""
        for task in self.tasks:
            if task.get("name") == name:
                rollback_task = task.copy()
                if activate_ignore:
                    rollback_task["ignore"] = True
                return rollback_task

    def rollback_register(self, url, task):
        """Register rollback tasks."""
        for rollback in task.get("rollback", [])[::-1]:
            if isinstance(rollback, str):
                self.rollback_tasks.append((url, self.rollback_lookup(rollback)))
            elif isinstance(rollback, dict):
                rollback["ignore"] = True
                self.rollback_tasks.append((url, rollback))
            else:
                return False
        return True

    async def rollback_executor(self, url=None):
        """Execute the rollback stack."""
        for rollback_url, rollback_task in self.rollback_tasks[::-1]:
            if url is not None and rollback_url != url:
                continue

            if self.parallel:
                output = self.outputs[self.urls.index(url)].copy()
            else:
                output = self.outputs[0].copy()

            result = await Task(
                rollback_url, rollback_task, output=output, verify=self.verify
            ).run()

            if self.parallel:
                self.outputs[self.urls.index(url)] = result["output"]
            else:
                self.outputs = [result["output"]]

            yield [result]

    async def _executor(self) -> list:
        """Private task executor."""
        is_refs_validated = self.validate_refs()
        if not is_refs_validated:
            yield self._error(critical="Rollback scenario validation failed.")
            return

        for url in self.urls:
            is_success = True
            for task in self.tasks:
                is_registered = self.rollback_register(url, task)
                if not is_registered:
                    yield self._error(critical="Invalid rollback schema.")
                    return

                result = await Task(
                    url, task, output=self.outputs[0].copy(), verify=self.verify
                ).run()

                self.outputs = [result["output"]]

                yield [result]
                if result["status"] != "SUCCESS" and result["ignore"] is False:
                    is_success = False
                    break

            if not is_success:
                async for rollback in self.rollback_executor():
                    yield rollback

    async def _parallel_executor(self) -> list:
        """Private parallel task executor."""
        is_refs_validated = self.validate_refs()
        if not is_refs_validated:
            yield self._error(critical="Rollback scenario validation failed.")
            return

        state = {url: None for url in self.urls}
        for task in self.tasks:
            task_run_list = []
            for i, url in enumerate(self.urls):
                if (
                    state[url] is not None
                    and state[url]["status"] != "SUCCESS"
                    and state[url]["ignore"] is False
                ):
                    continue

                is_registered = self.rollback_register(url, task)
                if not is_registered:
                    yield self._error(critical="Invalid rollback schema.")
                    return

                task_run_list.append(
                    Task(
                        url, task, output=self.outputs[i].copy(), verify=self.verify
                    ).run()
                )

            results = await asyncio.gather(*task_run_list)

            for url in state:
                for result in results:
                    if url == result["url"]:
                        self.outputs[self.urls.index(url)] = result["output"]
                        state[url] = result
                        break

            yield results

        for url in self.urls:
            if state[url]["status"] != "SUCCESS" and state[url]["ignore"] is False:
                async for rollback in self.rollback_executor(url=url):
                    yield rollback

    async def _next(self) -> list:
        """Execute the next task."""
        return await self.stack.__anext__()

    async def next(self) -> Union[str, list]:
        """Wrapper for better iterative output."""
        result = await self._next()
        if len(result) == 1:
            return result[0]
        else:
            return result

    async def run(self) -> bool:
        """Run the whole task queue."""
        results = []
        while True:
            try:
                results.append(await self._next())
            except StopAsyncIteration:
                break

        reports_per_url = {}
        for result in list(itertools.chain.from_iterable(results)):
            if "url" in result:
                url = result["url"]
                if url not in reports_per_url:
                    reports_per_url[url] = []
                reports_per_url[url].append(result)

        self.all_reports = [
            {
                "url": url,
                "reports": reports,
                "total_duration_sec": sum(
                    task["duration_sec"] or 0 for task in reports
                ),
            }
            for url, reports in reports_per_url.items()
        ]
        self._hide_token_from_all_reports(self.all_reports)

        if self.generate_report is not None:
            with open(self.generate_report, "w", encoding="utf-8") as file:
                json.dump(self.all_reports, file, ensure_ascii=False)

        return all(
            [
                result["status"] == "SUCCESS"
                for result in list(itertools.chain.from_iterable(results))
                if result["ignore"] is False
            ]
        )

    @staticmethod
    def _hide_token_from_all_reports(all_reports):
        for suite_report in all_reports:
            for task_report in suite_report["reports"]:
                task_report["output"]["__token__"] = "***"  # nosec
