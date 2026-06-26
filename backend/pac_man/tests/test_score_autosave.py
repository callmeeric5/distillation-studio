import asyncio
from types import SimpleNamespace

from api.projects.pacman import service


def test_auto_save_run_score_saves_eligible_run_once(monkeypatch) -> None:
    inserted = []

    async def fake_insert_score(payload):
        inserted.append(payload)
        return SimpleNamespace(id=1, created_at=None, **payload.model_dump())

    monkeypatch.setattr(service, "insert_score", fake_insert_score)
    run = _run(score_eligible=True)

    asyncio.run(service.auto_save_run_score(run))
    asyncio.run(service.auto_save_run_score(run))

    assert len(inserted) == 1
    assert inserted[0].player_name == "Ada"
    assert run.score_saved is True
    assert run.score_save_error is None


def test_auto_save_run_score_skips_cheat_run(monkeypatch) -> None:
    inserted = []

    async def fake_insert_score(payload):
        inserted.append(payload)

    monkeypatch.setattr(service, "insert_score", fake_insert_score)
    run = _run(score_eligible=False)

    asyncio.run(service.auto_save_run_score(run))

    assert inserted == []
    assert run.score_saved is False


def _run(score_eligible: bool):
    run = SimpleNamespace(
        score_saved=False,
        score_save_error=None,
        status="lost",
    )

    def snapshot():
        return {
            "completed": False,
            "elapsed_seconds": 12,
            "level": 2,
            "player_name": "Ada",
            "score": 340,
            "score_eligible": score_eligible,
        }

    def mark_score_saved():
        run.score_saved = True
        run.score_save_error = None

    def mark_score_save_failed(error: str):
        run.score_saved = False
        run.score_save_error = error

    run.snapshot = snapshot
    run.mark_score_saved = mark_score_saved
    run.mark_score_save_failed = mark_score_save_failed
    return run
