from __future__ import annotations

import argparse
from pathlib import Path

from xiangqi_sifu.training.dataset import (
    read_jsonl,
    split_train_validation,
    write_jsonl,
)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    records = read_jsonl(args.source)
    train, validation = split_train_validation(
        records,
        validation_count=args.validation_count,
        balance_by_metadata_key=None if args.no_balance_by_source else "source_name",
    )
    write_jsonl(train, args.train_output)
    write_jsonl(validation, args.validation_output)
    print(f"Read {len(records)} records from {args.source}")
    print(f"Wrote {len(train)} training records to {args.train_output}")
    print(f"Wrote {len(validation)} validation records to {args.validation_output}")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split explanation SFT JSONL into train and human-review validation sets.",
    )
    parser.add_argument("--source", type=Path, default=Path("data/training/explanations/train.jsonl"))
    parser.add_argument("--train-output", type=Path, default=Path("data/training/explanations/train.jsonl"))
    parser.add_argument("--validation-output", type=Path, default=Path("data/training/explanations/validation.jsonl"))
    parser.add_argument("--validation-count", type=int, default=50)
    parser.add_argument("--no-balance-by-source", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
