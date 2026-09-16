from pathlib import Path

import fire
from pydantic import BaseModel
from tqdm import tqdm

from .generation import AnswerGenerator
from .indexing import build_index
from .logger import logger
from .models import (
    MinimalAnswer,
    MinimalSearchResults,
    RagDataset,
    StudentSearchResults,
    StudentSearchResultsAndAnswer,
)
from .retrieval import Retriever


def save_json(model: BaseModel, directory: str, filename: str) -> Path:
    """Save a Pydantic model in the requested output directory."""
    output = Path(directory) / filename
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(model.model_dump_json(indent=2), encoding="utf-8")
    return output


class RagCLI:
    def index(self, max_chunk_size: int = 2000) -> None:
        files, chunks = build_index(max_chunk_size=max_chunk_size)
        print(f"Indexed {files} files into {chunks} chunks")
        logger.info(f"Indexed {files} files into {chunks} chunks")

    def search(self, query: str, k: int = 5) -> None:
        result = MinimalSearchResults(
            question_id="single-query",
            question=query,
            retrieved_sources=Retriever().search(query, k),
        )
        print(result.model_dump_json(indent=2))

    def search_dataset(
        self,
        dataset_path: str,
        k: int = 5,
        save_directory: str = "data/output/search_results",
    ) -> None:
        dataset = RagDataset.model_validate_json(
            Path(dataset_path).read_text(encoding="utf-8")
        )
        retriever = Retriever()
        results = []
        for question in tqdm(dataset.rag_questions, desc="Searching"):
            results.append(
                MinimalSearchResults(
                    question_id=question.question_id,
                    question=question.question,
                    retrieved_sources=retriever.search(question.question, k),
                )
            )
        output = StudentSearchResults(search_results=results, k=k)
        path = save_json(output, save_directory, Path(dataset_path).name)
        print(f"Saved search results to {path}")

    def answer(self, query: str, k: int = 5) -> None:
        sources = Retriever().search(query, k)
        answer = AnswerGenerator().generate(query, sources)
        result = MinimalAnswer(
            question_id="single-query",
            question=query,
            retrieved_sources=sources,
            answer=answer,
        )
        print(result.model_dump_json(indent=2))

    def answer_dataset(
        self,
        search_results_path: str,
        save_directory: str = "data/output/search_results_and_answer",
    ) -> None:
        search_results = StudentSearchResults.model_validate_json(
            Path(search_results_path).read_text(encoding="utf-8")
        )
        generator = AnswerGenerator()
        answers = []
        for result in tqdm(search_results.search_results, desc="Answering"):
            answers.append(
                MinimalAnswer(
                    **result.model_dump(),
                    answer=generator.generate(
                        result.question, result.retrieved_sources
                    ),
                )
            )
        output = StudentSearchResultsAndAnswer(
            search_results=answers, k=search_results.k
        )
        path = save_json(
            output, save_directory, Path(search_results_path).name
        )
        print(f"Saved answers to {path}")


def main() -> None:
    fire.Fire(RagCLI)


if __name__ == "__main__":
    main()
