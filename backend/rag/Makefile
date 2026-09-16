ifneq ($(wildcard /goinfre),)
export UV_CACHE_DIR := /goinfre/$(USER)/.cache/uv
export UV_PROJECT_ENVIRONMENT := /goinfre/$(USER)/.venv
export HF_HOME := /goinfre/$(USER)/.cache/huggingface
else
export UV_CACHE_DIR := .uv-cache
export HF_HOME := .hf-cache
endif
export TRANSFORMERS_CACHE := $(HF_HOME)
export UV_LINK_MODE := copy

ARGS ?= --help

install:
	uv sync

run:
	uv run python -m src $(ARGS)

debug:
	uv run python -m pdb -m src $(ARGS)

clean:
	find . -not -path "./.venv*" -name "__pycache__" -exec rm -rf {} +
	find . -not -path "./.venv*" -name ".mypy_cache" -exec rm -rf {} +
	find . -not -path "./.venv*" -name ".pytest_cache" -exec rm -rf {} +

lint:
	uv run flake8 src
	uv run mypy src --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	uv run flake8 .
	uv run mypy . --strict

test:
	uv run python -m pytest

.PHONY: install run debug clean lint lint-strict test
