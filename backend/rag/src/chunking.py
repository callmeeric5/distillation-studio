import ast
import re
from dataclasses import dataclass
from pathlib import Path

from .logger import logger


@dataclass(frozen=True)
class Chunk:
    file: str
    start: int
    end: int
    text: str
    label: str = ""


def _split(
    corpus: str,
    file: str,
    start: int,
    end: int,
    max_chunk_size: int = 2000,
    label: str = "",
) -> list[Chunk]:
    """Split the corpus from the start to the end in max chunk size:
    1. If the current chunk is not the last -> chunk end stops
    at the right most \n
    2. If the current chunk is not empty -> add it to the chunks
    """
    chunks: list[Chunk] = []
    overlap_size = min(max_chunk_size // 10, 200)
    chunk_start = start
    while chunk_start < end:
        chunk_end = min(chunk_start + max_chunk_size, end)
        if chunk_end < end:
            newline = corpus.rfind(
                "\n", chunk_start + max_chunk_size // 2, chunk_end
            )
            if newline != -1:
                chunk_end = newline + 1
        if corpus[chunk_start:chunk_end].strip():
            chunks.append(
                Chunk(
                    file,
                    chunk_start,
                    chunk_end,
                    corpus[chunk_start:chunk_end],
                    label,
                )
            )
        if chunk_end == end:
            break
        chunk_start = max(chunk_start + 1, chunk_end - overlap_size)
    return chunks


def chunk_text(corpus: str, file: str, max_chunk_size: int) -> list[Chunk]:
    """Chunk .txt and .md files"""
    chunks = _split(corpus, file, 0, len(corpus), max_chunk_size)
    if Path(file).suffix.lower() != ".md":
        return chunks

    headings = [
        (match.start(), match.group(1).strip())
        for match in re.finditer(r"(?m)^#{1,6}\s+(.+)$", corpus)
    ]
    if not headings:
        return chunks

    labelled = []
    for chunk in chunks:
        preceding = [
            heading for pos, heading in headings if pos <= chunk.start
        ]
        label = preceding[-1] if preceding else ""
        if not label:
            label = next(
                (
                    heading
                    for pos, heading in headings
                    if chunk.start < pos < chunk.end
                ),
                "",
            )
        labelled.append(
            Chunk(chunk.file, chunk.start, chunk.end, chunk.text, label)
        )
    return labelled


def chunk_python(
    corpus: str,
    file: str,
    max_chunk_size: int,
) -> list[Chunk]:
    """Chunk Python files using top-level AST definitions."""
    try:
        tree = ast.parse(corpus)
    except (SyntaxError, ValueError):
        logger.info(f"{file} can't be AST parsed, treating it as a text file")
        return chunk_text(corpus, file, max_chunk_size)
    starts = [0]
    starts.extend(idx + 1 for idx, char in enumerate(corpus) if char == "\n")
    labels: dict[int, str] = {0: "module"}

    def add_boundary(
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    ) -> None:
        """Add the starting character index of a definition."""
        lines = [node.lineno]

        for decorator in node.decorator_list:
            lines.append(decorator.lineno)

        first_line = min(lines)
        labels[starts[first_line - 1]] = node.name

    # Methods and nested functions are useful retrieval boundaries too.
    # Limiting boundaries to ``tree.body`` turns a large class into arbitrary
    # character windows, separating a method name from the relevant body.
    for node in ast.walk(tree):
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            add_boundary(node)
    boundaries = sorted(set(labels) | {len(corpus)})
    chunks: list[Chunk] = []
    for idx in range(len(boundaries) - 1):
        start = boundaries[idx]
        end = boundaries[idx + 1]
        chunks.extend(
            _split(
                corpus,
                file,
                start,
                end,
                max_chunk_size,
                labels[start],
            )
        )

    return chunks


def chunk_file(file: str, max_size: int) -> list[Chunk]:
    """Read a file and apply the strategy for its suffix."""
    path = Path(file)
    corpus = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".py":
        logger.info(f"Chunking code file: {path.name}")
        return chunk_python(corpus, file, max_size)
    logger.info(f"Chunking text file: {path.name}")
    return chunk_text(corpus, file, max_size)
