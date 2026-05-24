from __future__ import annotations

import random
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


ROOT = Path(__file__).resolve().parent
PUSH_SWAP_DIR = ROOT.parent / "backend" / "push_swap"
PUSH_SWAP_BIN = PUSH_SWAP_DIR / "push_swap"
ALGORITHMS = {"simple", "medium", "complex", "adaptive"}
MAX_VALUES = 500

app = FastAPI(title="Distillation Studio API")


class RunRequest(BaseModel):
    values: list[int] = Field(..., min_length=1, max_length=MAX_VALUES)
    algorithm: str = "medium"


class GenerateRequest(BaseModel):
    size: int = Field(20, ge=2, le=MAX_VALUES)
    minimum: int = Field(-250, ge=-100000)
    maximum: int = Field(250, le=100000)


def validate_values(values: list[int]) -> None:
    if len(values) != len(set(values)):
        raise HTTPException(status_code=400, detail="Input values must be unique.")
    for value in values:
        if value < -(2**31) or value > 2**31 - 1:
            raise HTTPException(status_code=400, detail="Values must fit in a 32-bit signed integer.")


def ensure_binary() -> None:
    if PUSH_SWAP_BIN.exists():
        return
    result = subprocess.run(
        ["make"],
        cwd=PUSH_SWAP_DIR,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Could not build push_swap: {result.stderr or result.stdout}",
        )


def run_push_swap(values: list[int], algorithm: str) -> list[str]:
    if algorithm not in ALGORITHMS:
        raise HTTPException(status_code=400, detail="Unknown algorithm.")
    validate_values(values)
    ensure_binary()
    command = [str(PUSH_SWAP_BIN), f"--{algorithm}", *[str(value) for value in values]]
    result = subprocess.run(
        command,
        cwd=PUSH_SWAP_DIR,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=20,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=400, detail=result.stderr.strip() or "push_swap failed.")
    return [line for line in result.stdout.splitlines() if line]


@app.post("/api/projects/push-swap/run")
def run_sort(request: RunRequest) -> dict:
    moves = run_push_swap(request.values, request.algorithm)
    return {
        "values": request.values,
        "algorithm": request.algorithm,
        "moves": moves,
        "move_count": len(moves),
    }


@app.post("/api/projects/push-swap/generate")
def generate_values(request: GenerateRequest) -> dict:
    if request.maximum - request.minimum + 1 < request.size:
        raise HTTPException(status_code=400, detail="Range is too small for unique values.")
    values = random.sample(range(request.minimum, request.maximum + 1), request.size)
    return {"values": values}
