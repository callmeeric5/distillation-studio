"""Print a benchmark table from saved solution JSON files."""

import argparse
from pathlib import Path
from agent_smith.models.agent import SolutionOutput


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("solutions", nargs="+")
    parser.add_argument("--output")
    args = parser.parse_args()
    lines = [
        "| Model | Task | Pass | Iterations | Input | Output | Seconds | Retries | Mean request ms |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for filename in args.solutions:
        result = SolutionOutput.model_validate_json(Path(filename).read_text())
        model = result.steps[0].model_name if result.steps else "unknown"
        verdict = "Pass" if result.success else "Fail"
        retries = sum(step.retries for step in result.steps)
        latency = sum(step.request_time_ms for step in result.steps) / max(
            1, result.total_requests
        )
        lines.append(
            f"| {model} | {result.task_id} | {verdict} | {result.iterations} | "
            f"{result.total_input_tokens} | {result.total_output_tokens} | "
            f"{result.total_time_seconds:.2f} | {retries} | {latency:.0f} |"
        )
    table = "\n".join(lines) + "\n"
    if args.output:
        Path(args.output).write_text(table)
    else:
        print(table)


if __name__ == "__main__":
    main()
