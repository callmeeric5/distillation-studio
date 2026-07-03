ifneq ($(wildcard /goinfre),)
export UV_CACHE_DIR := /goinfre/$(USER)/.cache/uv
export UV_PROJECT_ENVIRONMENT := /goinfre/$(USER)/.venv
export HF_HOME := /goinfre/$(USER)/.cache/huggingface
export TRANSFORMERS_CACHE := /goinfre/$(USER)/.cache/huggingface
SDK_PYTHON := $(UV_PROJECT_ENVIRONMENT)/bin/python3
else
export UV_CACHE_DIR := .uv-cache
export HF_HOME := .hf-cache
export TRANSFORMERS_CACHE := .hf-cache
SDK_PYTHON := .venv/bin/python3
endif
export UV_LINK_MODE := copy

SDK_DEPENDENCIES = \
	torch \
	transformers \
	huggingface-hub \
	accelerate \

ARGS = --functions_definition data/input/functions_definition.json \
	--input data/input/function_calling_tests.json \
	--output data/output/function_calls.json

install:
	uv sync
	uv pip install --python $(SDK_PYTHON) $(SDK_DEPENDENCIES)

run:
	uv run python -m src $(ARGS)

debug:
	uv run python -m src $(ARGS)

clean:
	find . -not -path "./.venv*" -name "__pycache__" -exec rm -rf {} +
	find . -not -path "./.venv*" -name ".mypy_cache" -exec rm -rf {} +

lint:
	uv run flake8 src
	uv run mypy src --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	uv run flake8 src
	uv run mypy src --strict

.PHONY: install run debug clean lint lint-strict
