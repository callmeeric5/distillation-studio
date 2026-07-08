from __future__ import annotations

import re
import subprocess
from pathlib import Path

from fastapi import HTTPException

from api.projects.codexion.schemas import RunRequest


ROOT = Path(__file__).resolve().parents[3]
CODEXION_DIR = ROOT / "backend" / "codexion"
CODEXION_BIN = CODEXION_DIR / "codexion"
LOG_RE = re.compile(r"^(?P<time>\d+)\s+(?P<coder>\d+)\s+(?P<message>.+)$")
SCHEDULER_ARGS = {"FIFO": "fifo", "EDF": "edf"}
RUN_TIMEOUT_SECONDS = 15


def ensure_binary() -> None:
    if CODEXION_BIN.exists():
        return
    result = subprocess.run(
        ["make"],
        cwd=CODEXION_DIR,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Could not build codexion: {result.stderr or result.stdout}",
        )


def run_codexion(request: RunRequest) -> dict:
    ensure_binary()
    command = [
        str(CODEXION_BIN),
        str(request.number_of_coders),
        str(request.time_to_burnout),
        str(request.time_to_compile),
        str(request.time_to_debug),
        str(request.time_to_refactor),
        str(request.number_of_compiles_required),
        str(request.dongle_cooldown),
        SCHEDULER_ARGS[request.scheduler],
    ]
    try:
        result = subprocess.run(
            command,
            cwd=CODEXION_DIR,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=RUN_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        raise HTTPException(status_code=408, detail="Codexion run timed out.") from error

    if result.returncode != 0:
        raise HTTPException(
            status_code=400,
            detail=(result.stderr or result.stdout or "Codexion failed.").strip(),
        )

    raw_log = [line for line in result.stdout.splitlines() if line.strip()]
    events = parse_log(raw_log)
    if not events:
        raise HTTPException(status_code=500, detail="Codexion returned no simulation events.")
    return build_response(request, events, raw_log)


def parse_log(raw_log: list[str]) -> list[dict]:
    events = []
    for line in raw_log:
        match = LOG_RE.fullmatch(line.strip())
        if not match:
            events.append(
                {
                    "index": len(events),
                    "time": events[-1]["time"] if events else 0,
                    "coder_id": None,
                    "kind": "log",
                    "message": line.strip(),
                    "raw": line,
                }
            )
            continue
        message = match.group("message")
        events.append(
            {
                "index": len(events),
                "time": int(match.group("time")),
                "coder_id": int(match.group("coder")),
                "kind": classify_message(message),
                "message": message,
                "raw": line,
            }
        )
    return events


def classify_message(message: str) -> str:
    if message == "has taken a dongle":
        return "dongle_taken"
    if message == "is compiling":
        return "compiling"
    if message == "is debugging":
        return "debugging"
    if message == "is refactoring":
        return "refactoring"
    if message == "burned out":
        return "burned_out"
    return "log"


def build_response(request: RunRequest, events: list[dict], raw_log: list[str]) -> dict:
    replay_events = [*events]
    outcome = "burned_out" if any(event["kind"] == "burned_out" for event in events) else "completed"
    if outcome == "completed":
        replay_events.append(
            {
                "index": len(replay_events),
                "time": infer_completion_time(request, events),
                "coder_id": None,
                "kind": "completed",
                "message": "simulation completed",
                "raw": "simulation completed",
            }
        )

    frames = build_frames(request, replay_events)
    final_frame = frames[-1]
    coders_completed = sum(1 for coder in final_frame["coders"] if coder["state"] == "complete")
    compiles_completed = sum(coder["compiles_done"] for coder in final_frame["coders"])

    return {
        "config": request.model_dump(),
        "events": replay_events,
        "frames": frames,
        "raw_log": raw_log,
        "stats": {
            "outcome": outcome,
            "total_events": len(replay_events),
            "total_time": replay_events[-1]["time"],
            "coders_completed": coders_completed,
            "compiles_completed": compiles_completed,
            "scheduler": request.scheduler,
        },
    }


def infer_completion_time(request: RunRequest, events: list[dict]) -> int:
    last_time = events[-1]["time"]
    compiling_times = [
        event["time"]
        for event in events
        if event["kind"] == "compiling" and event["coder_id"] is not None
    ]
    if not compiling_times:
        return last_time
    return max(last_time, max(compiling_times) + request.time_to_compile)


def build_frames(request: RunRequest, events: list[dict]) -> list[dict]:
    coders = [
        {
            "id": coder_id,
            "state": "idle",
            "compiles_done": 0,
            "dongles": [],
            "deadline": request.time_to_burnout,
        }
        for coder_id in range(1, request.number_of_coders + 1)
    ]
    dongles = [
        {"id": dongle_id, "state": "available", "holder": None, "cooldown_until": 0}
        for dongle_id in range(1, request.number_of_coders + 1)
    ]
    frames = [snapshot(0, 0, None, coders, dongles)]

    for event in events:
        apply_event(request, event, coders, dongles)
        frames.append(snapshot(len(frames), event["time"], event, coders, dongles))
    return frames


def apply_event(request: RunRequest, event: dict, coders: list[dict], dongles: list[dict]) -> None:
    update_cooldowns(event["time"], dongles)
    coder_id = event["coder_id"]
    kind = event["kind"]
    if kind == "completed":
        complete_successful_run(request, event["time"], coders, dongles)
        return
    if coder_id is None or not (1 <= coder_id <= len(coders)):
        return

    coder = coders[coder_id - 1]
    if kind == "dongle_taken":
        if coder["state"] not in {"compiling", "burned_out", "complete"}:
            coder["dongles"] = coder_dongles(coder_id, len(coders))
            for dongle_id in coder["dongles"]:
                dongle = dongles[dongle_id - 1]
                dongle["state"] = "in_use"
                dongle["holder"] = coder_id
                dongle["cooldown_until"] = 0
    elif kind == "compiling":
        coder["state"] = "compiling"
        coder["dongles"] = coder_dongles(coder_id, len(coders))
        coder["deadline"] = event["time"] + request.time_to_burnout
        for dongle_id in coder["dongles"]:
            dongle = dongles[dongle_id - 1]
            dongle["state"] = "in_use"
            dongle["holder"] = coder_id
            dongle["cooldown_until"] = 0
    elif kind == "debugging":
        if coder["state"] == "compiling":
            coder["compiles_done"] += 1
        coder["state"] = "debugging"
        release_dongles(request, event["time"], coder, dongles)
    elif kind == "refactoring":
        coder["state"] = "refactoring"
        coder["dongles"] = []
        if coder["compiles_done"] >= request.number_of_compiles_required:
            coder["state"] = "complete"
    elif kind == "burned_out":
        coder["state"] = "burned_out"
        coder["dongles"] = []


def complete_successful_run(
    request: RunRequest,
    time: int,
    coders: list[dict],
    dongles: list[dict],
) -> None:
    for coder in coders:
        if coder["state"] == "compiling":
            coder["compiles_done"] += 1
            release_dongles(request, time, coder, dongles)
        coder["compiles_done"] = max(coder["compiles_done"], request.number_of_compiles_required)
        coder["state"] = "complete"
        coder["dongles"] = []
    update_cooldowns(time + request.dongle_cooldown, dongles)


def release_dongles(request: RunRequest, time: int, coder: dict, dongles: list[dict]) -> None:
    cooldown_until = time + request.dongle_cooldown
    for dongle_id in coder["dongles"]:
        dongle = dongles[dongle_id - 1]
        dongle["holder"] = None
        dongle["cooldown_until"] = cooldown_until
        dongle["state"] = "cooldown" if cooldown_until > time else "available"
    coder["dongles"] = []


def update_cooldowns(time: int, dongles: list[dict]) -> None:
    for dongle in dongles:
        if dongle["holder"] is None and dongle["cooldown_until"] <= time:
            dongle["state"] = "available"


def coder_dongles(coder_id: int, coders_count: int) -> list[int]:
    if coders_count == 1:
        return [1]
    left = coder_id - 1 if coder_id > 1 else coders_count
    return [left, coder_id]


def snapshot(index: int, time: int, event: dict | None, coders: list[dict], dongles: list[dict]) -> dict:
    return {
        "index": index,
        "time": time,
        "event": event,
        "coders": [{**coder, "dongles": [*coder["dongles"]]} for coder in coders],
        "dongles": [dict(dongle) for dongle in dongles],
    }
