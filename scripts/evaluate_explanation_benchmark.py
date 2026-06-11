from __future__ import annotations

import argparse
import json
from pathlib import Path

from xiangqi_sifu.training.dataset import read_jsonl
from xiangqi_sifu.training.evaluation import evaluate_explanation_records


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    records = read_jsonl(args.dataset)
    if args.max_records is not None:
        records = records[: args.max_records]

    summary_with_records = evaluate_explanation_records(records)
    records_result = summary_with_records.pop("records")
    output = {
        "dataset": args.dataset.as_posix(),
        "summary": summary_with_records,
        "records": records_result,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote benchmark results to {args.output}")
    print(json.dumps(summary_with_records, ensure_ascii=False, indent=2))
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate Xiangqi-Sifu explanation records against grounded metadata.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/training/explanations/validation.jsonl"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/training/explanations/benchmark.json"),
    )
    parser.add_argument("--max-records", type=int)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
