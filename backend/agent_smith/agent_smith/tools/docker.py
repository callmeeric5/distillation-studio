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
            # SWE-bench's testbed environments intentionally use the historical
            # Python version required by the checked-out project (as old as 3.6).
            # The repository tool server uses modern syntax, so run it with the
            # base interpreter shipped by the SWE-bench image instead.
            for python in (
                "/opt/miniconda3/bin/python",
                "/usr/local/bin/python3",
                "python3",
                "python",
            ):
                version_result = subprocess.run(
                    [
                        "docker",
                        "exec",
                        self.container_id,
                        python,
                        "-c",
                        "import sys; raise SystemExit(sys.version_info < (3, 10))",
                    ],
                    capture_output=True,
                    timeout=10,
                )
                if version_result.returncode == 0:
                    self.tool_python = python
                    break
            else:
                state = subprocess.run(
                    [
                        "docker",
                        "inspect",
                        "--format",
                        "{{.State.Status}}: {{.State.Error}}",
                        self.container_id,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                ).stdout.strip()
                detail = f" ({state})" if state else ""
                raise RuntimeError(
                    "Task container has no Python 3.10+ tool interpreter"
                    f"{detail}. On ARM64 hosts, install amd64 binfmt emulation."
                )

            for python in (
                "/opt/miniconda3/envs/testbed/bin/python",
                "/opt/miniconda3/bin/python",
                "python3",
                "python",
            ):
                version_result = subprocess.run(
                    ["docker", "exec", self.container_id, python, "--version"],
                    capture_output=True,
                    timeout=10,
                )
                if version_result.returncode == 0:
                    self.task_python = python
                    break
            else:
                raise RuntimeError("Task image has no project Python interpreter")
        except BaseException:
            self.close()
            raise

    def call(self, name: str, arguments: Mapping[str, Any]) -> Any:
        """Send a tool name and its arguments to the task container."""
        script = Path(__file__).with_name("repository.py").read_text()
        request_arguments = dict(arguments)
        if name == "run_python":
            request_arguments["interpreter"] = self.task_python
        request = {"name": name, "arguments": request_arguments}
        # Equivalent to: docker exec -i <container> python -c <tool source>.
        result = subprocess.run(
            [
                "docker",
                "exec",
                "-i",
                self.container_id,
                self.tool_python,
                "-c",
                script,
            ],
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
