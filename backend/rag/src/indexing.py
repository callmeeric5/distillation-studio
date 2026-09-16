import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from tqdm import tqdm

from .chunking import chunk_file
from .logger import logger


def split_camel_case(word: str) -> list[str]:
    """Split CamelCase words into smaller words."""
    return re.findall(
        r"[A-Z]+(?=[A-Z][a-z]|\d|$)|[A-Z]?[a-z]+|\d+",
        word,
    )


def tokenize(text: str) -> list[str]:
    tokens = []
    words = re.findall(
        r"[A-Za-z_][A-Za-z0-9_]*|\d+",
        text,
    )
    for word in words:
        tokens.append(word.lower())

        for part in word.split("_"):
            for item in split_camel_case(part):
                tokens.append(item.lower())

    return tokens


class InvertedIndex:
    """The documents and posting lists saved in ``index.json``."""

    def __init__(self, index_path: str | Path = "data/processed/index.json") -> None:
        path = Path(index_path)
        if not path.is_file():
            raise FileNotFoundError(
                f"Index not found: {path}. Run the index command first."
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        self.documents: list[dict[str, int | str]] = data["documents"]
        self.postings: dict[str, list[list[int]]] = data["postings"]
        self.average_length: float = data["average_length"]
        self.tfidf_norms: list[float] = data["tfidf_norms"]


def calculate_tfidf_norms(
    postings: dict[str, list[list[int]]], document_count: int
) -> list[float]:
    """
    Calculate the norm tfidf.
    Args:
    document_frequency: how many corpus contains the token
    term_frequency: how many times the token has been appeared in one corpus
    TF(t,d) = 1 + log(freq(t,d))
    IDF(t) = log((N + 1) / (df(t) + 1)) + 1
    TFIDF(t,d) = TF(t,d) x IDF(t)
    """
    squared_norms = [0.0] * document_count
    for token_meta in postings.values():
        document_frequency = len(token_meta)
        idf = math.log((document_count + 1) / (document_frequency + 1)) + 1
        for document_id, term_frequency in token_meta:
            tf = 1 + math.log(term_frequency)
            tfidf = tf * idf
            squared_norms[document_id] += tfidf**2

    return [math.sqrt(norm) for norm in squared_norms]


def build_index(
    corpus_path: str = "data/raw",
    output_path: str = "data/processed/index.json",
    max_chunk_size: int = 2000,
) -> tuple[int, int]:
    if not 1 <= max_chunk_size <= 2000:
        raise ValueError("Max chunk size shoud be between 1 and 2000")
    files = Path(corpus_path).rglob("*")
    corpus = sorted(
        file
        for file in files
        if file.is_file() and file.suffix.lower() in (".md", ".py", ".txt")
    )
    logger.info(f"Found {len(corpus)} raw files")
    documents: list[dict[str, int | str]] = []
    postings: defaultdict[str, list[list[int]]] = defaultdict(list)
    for path in tqdm(corpus, desc="indexing", unit="file"):
        chunks = chunk_file(path.as_posix(), max_chunk_size)
        for chunk in chunks:
            tokens = tokenize(chunk.text)
            # File names and AST definition names are compact, high-value
            # metadata.  Questions about code commonly name the module, class,
            # or method even when those words do not occur inside a split body.
            tokens.extend(tokenize(Path(chunk.file).stem))
            tokens.extend(tokenize(chunk.label))
            counts = Counter(tokens)
            document_id = len(documents)
            documents.append(
                {
                    "file": chunk.file,
                    "start": chunk.start,
                    "end": chunk.end,
                    "tokens": len(tokens),
                }
            )
            for word, count in counts.items():
                postings[word].append([document_id, count])

    average_tokens = sum(
        int(document["tokens"]) for document in documents
    ) / len(documents)
    posting_lists = dict(postings)
    data = {
        "documents": documents,
        "postings": posting_lists,
        "average_length": average_tokens,
        "tfidf_norms": calculate_tfidf_norms(posting_lists, len(documents)),
    }
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data), encoding="utf-8")
    return len(corpus), len(documents)
