from __future__ import annotations

import random
import subprocess
from pathlib import Path

from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[3]
PUSH_SWAP_DIR = ROOT / "backend" / "push_swap"
PUSH_SWAP_BIN = PUSH_SWAP_DIR / "push_swap"
ALGORITHMS = {"simple", "medium", "complex", "adaptive"}


def generate_unique_values(size: int, minimum: int, maximum: int) -> list[int]:
    if maximum - minimum + 1 < size:
        raise HTTPException(status_code=400, detail="Range is too small for unique values.")
    return random.sample(range(minimum, maximum + 1), size)


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
