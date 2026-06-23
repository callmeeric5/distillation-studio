MAP ?= maps/easy/01_linear_path.txt

install:
	uv sync

run:
	uv run main.py $(MAP)

debug:
	uv run python3 -m pdb main.py $(MAP)

clean:
	find . -not -path "./.venv*" -name "__pycache__" -exec rm -rf {} +
	find . -not -path "./.venv*" -name ".mypy_cache" -exec rm -rf {} +

lint:
	uv run flake8 . --exclude=.venv
	uv run mypy . --exclude "(.venv|tests)"

lint-strict:
	uv run flake8 . --exclude=.venv
	uv run mypy . --strict --exclude "(.venv|tests)"

.PHONY: install run debug clean lint lint-strict
