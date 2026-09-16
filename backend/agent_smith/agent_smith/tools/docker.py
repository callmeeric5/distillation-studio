"""Run repository tool operations inside a SWE-bench Docker container."""

import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class DockerWorkspace:
    def __init__(self, image: str, timeout: int = 120) -> None:
        self.timeout = timeout
        self.container_id = ""
        result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "--platform",
                "linux/amd64",
                "--network",
                "none",
                "--memory",
                "4g",
                "--pids-limit",
                "256",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--entrypoint",
                "sleep",
                image,
                "infinity",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode:
            raise RuntimeError(f"Cannot start task container: {result.stderr.strip()}")
        self.container_id = result.stdout.strip()
        try:
            for python in (
                "/opt/miniconda3/envs/testbed/bin/python",
                "python3",
                "python",
            ):
                version_result = subprocess.run(
                    ["docker", "exec", self.container_id, python, "--version"],
                    capture_output=True,
                    timeout=10,
                )
                if version_result.returncode == 0:
                    self.python = python
                    break
            else:
                raise RuntimeError("Task image has no Python interpreter")
        except BaseException:
            self.close()
            raise

    def call(self, name: str, arguments: Mapping[str, Any]) -> Any:
        """Send a tool name and its arguments to the task container."""
        script = Path(__file__).with_name("repository.py").read_text()
        request = {"name": name, "arguments": arguments}
        # Equivalent to: docker exec -i <container> python -c <tool source>.
        result = subprocess.run(
            ["docker", "exec", "-i", self.container_id, self.python, "-c", script],
            input=json.dumps(request),
            capture_output=True,
            text=True,
            timeout=self.timeout + 10,
        )
        if result.returncode:
            raise RuntimeError(f"Container operation failed: {result.stderr[-4000:]}")
        response = json.loads(result.stdout)
        if not response["ok"]:
            raise RuntimeError(response["error"])
        return response["value"]

    def run_command(
        self, command: str, workdir: str = "/testbed"
    ) -> dict[str, Any]:
        return self.call(
            "run_command",
            {
                "command": command,
                "workdir": workdir,
                "timeout": self.timeout,
            },
        )

    def close(self) -> None:
        if self.container_id:
            subprocess.run(
                ["docker", "rm", "-f", self.container_id],
                capture_output=True,
                timeout=10,
            )
            self.container_id = ""
