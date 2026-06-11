from __future__ import annotations

import argparse
import json
from pathlib import Path

from xiangqi_sifu.training.lora_config import DEFAULT_BASE_MODEL_ID

MANIFEST_NAME = "xiangqi_sifu_adapter_manifest.json"
MODEL_CARD_NAME = "README.md"


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        _validate_adapter_dir(args.adapter_dir)
    except ValueError as exc:
        print(f"Cannot export adapter: {exc}")
        return 2

    manifest = _build_manifest(
        adapter_dir=args.adapter_dir,
        base_model=args.base_model,
        training_records=args.training_records,
        validation_records=args.validation_records,
    )
    manifest_path = args.adapter_dir / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (args.adapter_dir / MODEL_CARD_NAME).write_text(
        _build_model_card(manifest),
        encoding="utf-8",
    )
    print(f"Wrote adapter manifest to {manifest_path}")
    print(f"Wrote model card to {args.adapter_dir / MODEL_CARD_NAME}")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a trained Xiangqi-Sifu LoRA adapter for Phase 2 inference.",
    )
    parser.add_argument(
        "--adapter-dir",
        type=Path,
        default=Path("models/xiangqi-sifu-qwen35-2b-lora"),
    )
    parser.add_argument("--base-model", default=DEFAULT_BASE_MODEL_ID)
    parser.add_argument("--training-records", type=int)
    parser.add_argument("--validation-records", type=int)
    return parser.parse_args(argv)


def _validate_adapter_dir(adapter_dir: Path) -> None:
    if not adapter_dir.exists():
        raise ValueError(f"{adapter_dir} does not exist")
    if not (adapter_dir / "adapter_config.json").exists():
        raise ValueError("adapter_config.json is missing")
    has_weights = any(
        (adapter_dir / filename).exists()
        for filename in ("adapter_model.safetensors", "adapter_model.bin")
    )
    if not has_weights:
        raise ValueError("adapter_model.safetensors or adapter_model.bin is missing")


def _build_manifest(
    *,
    adapter_dir: Path,
    base_model: str,
    training_records: int | None,
    validation_records: int | None,
) -> dict[str, object]:
    return {
        "adapter_type": "peft_lora",
        "base_model_id": base_model,
        "adapter_path": adapter_dir.as_posix(),
        "prompt_template": "prompts/explanation_sft_prompt.md",
        "compatible_provider": "LoraExplanationProvider",
        "training_records": training_records,
        "validation_records": validation_records,
        "intended_use": "Pikafish-grounded Xiangqi mistake explanation",
    }


def _build_model_card(manifest: dict[str, object]) -> str:
    return (
        "# Xiangqi-Sifu Qwen3.5-2B LoRA Adapter\n\n"
        "This adapter is trained for Xiangqi-Sifu Phase 1.5. It converts "
        "Pikafish engine facts into short, cautious coaching explanations.\n\n"
        "## Base Model\n\n"
        f"{manifest['base_model_id']}\n\n"
        "## Intended Use\n\n"
        f"{manifest['intended_use']}\n\n"
        "## Training Data\n\n"
        f"- Training records: {manifest['training_records']}\n"
        f"- Validation records: {manifest['validation_records']}\n\n"
        "## Limitations\n\n"
        "- Explanations must still pass the Phase 2 verifier before display.\n"
        "- The adapter should not be treated as a source of tactical truth; "
        "Pikafish remains the ground truth provider.\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
