import time
import json
from spintest.validator import input_validator_e2e_task
from spintest import logger
from jinja2 import Template


class E2ETask:
    """E2E Task handler."""

    def __init__(self, url: str, task: dict, output: dict = None):
        """Initialization of `E2ETask` class."""
        self.url = url
        self.task = task
        self.name = task.get("name")
        self.target = task.get("target")
        self.output = output

    def _response(self, status: str, task: str, message: str) -> dict:
        """Return the response with logging."""
        result = {
            "name": self.name,
            "status": status,
            "timestamp": time.asctime(),
            "duration_sec": self.task.get("duration_sec", None),
            "url": self.url,
            "task": task,
            "ignore": self.task.get("ignore", False),
            "message": message,
        }

        log_level = {"SUCCESS": logger.info, "FAILURE": logger.error}
        log_level.get(status, logger.critical)(json.dumps(result, indent=4))

        result["output"] = self.output
        return result

    async def run(self) -> dict:
        """Run the E2E task."""
        try:
            input_validator_e2e_task(self.task)
        except ValueError as e:
            logger.error(f"Validation error for E2ETask '{self.name}': {e}")
            return self._response(
                "FAILURE",
                "unknown",
                f"Task '{self.name}' schema validation failed: {str(e)}",
            )

        target_inputs = self.task.get("target_input", {})

        if self.output:
            template = Template(json.dumps(target_inputs))
            target_inputs = json.loads(template.render(**self.output))
            if isinstance(target_inputs, str):
                target_inputs = target_inputs.replace("'", '"')
                try:
                    target_inputs = json.loads(target_inputs)
                except json.JSONDecodeError:
                    return self._response(
                        "FAILURE",
                        "unknown",
                        f"Task '{self.name}' failed to parse target inputs.",
                    )

        logger.info(f"Running E2ETask: {self.name}")
        start_time = time.monotonic()

        try:
            target_output = await self.target(url=self.url, **target_inputs)
            self.task["duration_sec"] = round(time.monotonic() - start_time, 2)
            output_variable = self.task.get("output")
            if output_variable:
                self.output[output_variable] = target_output

            return self._response(
                "SUCCESS", self.target.__name__, "Task executed successfully."
            )
        except AssertionError as e:
            self.task["duration_sec"] = round(time.monotonic() - start_time, 2)
            logger.error(f"Assertion error in target for E2ETask '{self.name}': {e}")
            return self._response(
                "FAILURE",
                self.target.__name__,
                f"Task '{self.name}' failed due to assertion error: {str(e)}",
            )
        except Exception as e:
            self.task["duration_sec"] = round(time.monotonic() - start_time, 2)
            logger.error(f"Error executing target for E2ETask '{self.name}': {e}")
            return self._response(
                "ERROR",
                self.target.__name__,
                f"Task '{self.name}' encountered an error: {str(e)}",
            )
