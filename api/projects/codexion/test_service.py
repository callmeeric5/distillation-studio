from __future__ import annotations

import subprocess

import pytest
from fastapi import HTTPException

from api.projects.codexion import service
from api.projects.codexion.schemas import RunRequest


def test_parse_log_classifies_codexion_events() -> None:
    events = service.parse_log(
        [
            "0 1 has taken a dongle",
            "0 1 is compiling",
            "120 1 is debugging",
            "240 1 is refactoring",
        ]
    )

    assert [event["kind"] for event in events] == [
        "dongle_taken",
        "compiling",
        "debugging",
        "refactoring",
    ]
    assert events[1]["coder_id"] == 1
    assert events[2]["time"] == 120


def test_scheduler_mapping_uses_cli_values(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="0 1 has taken a dongle\n10 1 burned out\n", stderr="")

    monkeypatch.setattr(service, "ensure_binary", lambda: None)
    monkeypatch.setattr(service.subprocess, "run", fake_run)

    service.run_codexion(RunRequest(number_of_coders=1, scheduler="EDF"))

    assert commands[0][-1] == "edf"


def test_successful_run_adds_completion_frame() -> None:
    request = RunRequest(number_of_coders=2, time_to_compile=100, number_of_compiles_required=1)
    events = service.parse_log(
        [
            "0 1 has taken a dongle",
            "0 1 is compiling",
            "100 1 is debugging",
            "100 2 has taken a dongle",
            "100 2 is compiling",
        ]
    )

    response = service.build_response(request, events, [event["raw"] for event in events])

    assert response["stats"]["outcome"] == "completed"
    assert response["events"][-1]["kind"] == "completed"
    assert response["frames"][-1]["time"] == 200
    assert all(coder["state"] == "complete" for coder in response["frames"][-1]["coders"])


def test_coder_dongles_use_immediate_left_and_current_dongle() -> None:
    assert service.coder_dongles(4, 5) == [3, 4]
    assert service.coder_dongles(1, 5) == [5, 1]


def test_failed_codexion_run_returns_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="bad config")

    monkeypatch.setattr(service, "ensure_binary", lambda: None)
    monkeypatch.setattr(service.subprocess, "run", fake_run)

    with pytest.raises(HTTPException) as error:
        service.run_codexion(RunRequest())

    assert error.value.status_code == 400
    assert error.value.detail == "bad config"
