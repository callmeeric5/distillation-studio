*This activity has been created as part of the 42 curriculum by ziwang.*

# RAG against the machine

This project implements a small lexical Retrieval-Augmented Generation (RAG)
pipeline for answering questions about the vLLM source tree.

## Project structure

```text
src/chunking.py   -> split source files into character-accurate chunks
src/indexing.py   -> tokenize chunks and build an inverted index
src/retrieval.py  -> rank chunks with BM25
src/generation.py -> generate answers from the retrieved context
src/models.py     -> define the input and output JSON models
src/__main__.py   -> expose the command-line interface
```

## How it works

### Chunking

Every returned source is an exact slice of its original file and is at most
2,000 characters long.

- Python files are parsed with the standard-library `ast` module. Classes,
  methods, functions, and nested functions are used as retrieval boundaries.
- Markdown and text files are split into overlapping character windows.
- Markdown headings are attached to their chunks as indexing metadata.
- Consecutive windows overlap by up to 200 characters to avoid losing context
  at a chunk boundary.

### Indexing

The tokenizer keeps complete identifiers while also splitting `snake_case` and
`CamelCase` names. For example, `trust_remote_code` is indexed both as a full
identifier and as the terms `trust`, `remote`, and `code`.

In addition to the exact chunk text, the index includes compact metadata such
as the file name, Markdown heading, and Python definition name. This helps
questions that explicitly mention a module, class, method, or documentation
section.

The generated index stores:

- each chunk's file path and character range;
- each chunk's token count;
- posting lists containing document IDs and term frequencies;
- the average document length;
- precomputed TF-IDF norms retained in the index format.

### Retrieval

Queries are tokenized with the same rules as the corpus. Chunks are ranked with
BM25 using term frequency, inverse document frequency, and document-length
normalization. The current retrieval path is BM25-only; it does not use a
hybrid ranking score.

### Answer generation

The retrieved source ranges are read from disk and supplied to
`Qwen/Qwen3-0.6B`. The model is instructed to answer using only that context.

## Installation

The project requires Python 3.13 and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
```

On the 42 environment, caches can be moved to `goinfre`:

```bash
export UV_CACHE_DIR=/goinfre/$USER/.cache/uv
export UV_PROJECT_ENVIRONMENT=/goinfre/$USER/.venv
export HF_HOME=/goinfre/$USER/.cache/huggingface
uv sync
```

## Usage

### 1. Build the index

The index must be rebuilt whenever chunking, tokenization, or indexing changes.

```bash
uv run python -m src index
```

The generated index is saved to `data/processed/index.json`.

### 2. Search one question

```bash
uv run python -m src search \
  "How does prefix caching work?" \
  --k 5
```

### 3. Generate public evaluation files

Documentation dataset:

```bash
uv run python -m src search_dataset \
  data/datasets/UnansweredQuestions/dataset_docs_public.json \
  --k 10 \
  --save_directory data/output/search_results/UnansweredQuestions
```

Code dataset:

```bash
uv run python -m src search_dataset \
  data/datasets/UnansweredQuestions/dataset_code_public.json \
  --k 10 \
  --save_directory data/output/search_results/UnansweredQuestions
```

The commands create:

```text
data/output/search_results/UnansweredQuestions/dataset_docs_public.json
data/output/search_results/UnansweredQuestions/dataset_code_public.json
```

### 4. Evaluate the generated files

Documentation evaluation:

```bash
./moulinette_pkg/moulinette-ubuntu \
  evaluate_student_search_results \
  data/output/search_results/UnansweredQuestions/dataset_docs_public.json \
  data/datasets/AnsweredQuestions/dataset_docs_public.json \
  --k 10 \
  --max_context_length 2000 \
  --threshold 0.8
```

Code evaluation:

```bash
./moulinette_pkg/moulinette-ubuntu \
  evaluate_student_search_results \
  data/output/search_results/UnansweredQuestions/dataset_code_public.json \
  data/datasets/AnsweredQuestions/dataset_code_public.json \
  --k 10 \
  --max_context_length 2000 \
  --threshold 0.5
```

The option is spelled `--threshold`, not `--thredshold`.

### 5. Generate an answer

```bash
uv run python -m src answer \
  "How does prefix caching work?" \
  --k 5
```

## Public evaluation results

The moulinette considers a source found when its Intersection over Union (IoU)
with a reference source is at least 5%. The required metric is Recall@5.

The following results were reproduced with `k=10`, a maximum context length of
2,000 characters, and the BM25-only implementation described above:

| Dataset | Recall@1 | Recall@3 | Recall@5 | Recall@10 | Required Recall@5 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Documentation | 56.0% | 78.0% | **85.0%** | 90.0% | 80.0% |
| Code | 39.4% | 61.6% | **66.7%** | 74.7% | 50.0% |

Both public datasets pass their Recall@5 requirements.

## Development checks

Run the tests:

```bash
make test
```

Run the style and type checks:

```bash
make lint
```

The chunking tests verify that returned ranges are non-empty, remain within the
2,000-character limit, match the exact original source text, and preserve
Python method boundaries.
