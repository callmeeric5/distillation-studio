import math
from collections import Counter, defaultdict
from pathlib import Path

from .indexing import InvertedIndex, tokenize
from .models import MinimalSource


class Retriever:
    def __init__(self, index_path: str | Path | None = None) -> None:
        project_root = Path(__file__).resolve().parents[1]
        resolved_index_path = (
            Path(index_path)
            if index_path is not None
            else project_root / "data/processed/index.json"
        )
        self.index = InvertedIndex(resolved_index_path)

    def bm25(self, query: Counter[str]) -> dict[int, float]:
        """Calculate BM25 scores for the query tokens."""

        scores: defaultdict[int, float] = defaultdict(float)
        document_count = len(self.index.documents)
        for token, token_count in query.items():
            matches = self.index.postings.get(token, [])
            if not matches:
                continue
            idf = math.log(
                1
                + (document_count - len(matches) + 0.5) / (len(matches) + 0.5)
            )
            for document_id, term_frequency in matches:
                length = int(self.index.documents[document_id]["tokens"])
                denominator = term_frequency + 1.5 * (
                    0.25 + 0.75 * length / self.index.average_length
                )
                scores[document_id] += (
                    token_count * idf * term_frequency * 2.5 / denominator
                )
        return dict(scores)

    @staticmethod
    def normalize(scores: dict[int, float]) -> dict[int, float]:
        """Scale scores so the largest value is one."""
        maximum = max(scores.values(), default=0)
        if maximum == 0:
            return {}
        return {
            document_id: score / maximum
            for document_id, score in scores.items()
        }

    def score(self, query: str) -> dict[int, float]:
        """Run the selected retrieval method."""
        tokens = Counter(tokenize(query))
        bm25 = self.normalize(self.bm25(tokens))
        return bm25

    def search(self, query: str, k: int = 5) -> list[MinimalSource]:
        """Return the ``k`` chunks with the highest scores."""
        if not query.strip() or k <= 0:
            return []
        scores = self.score(query)
        best_ids = sorted(
            scores, key=lambda document_id: scores[document_id], reverse=True
        )[:k]
        return [
            MinimalSource(
                file_path=str(self.index.documents[document_id]["file"]),
                first_character_index=int(
                    self.index.documents[document_id]["start"]
                ),
                last_character_index=int(
                    self.index.documents[document_id]["end"]
                ),
            )
            for document_id in best_ids
        ]
