from __future__ import annotations

import json
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any

DEFAULT_BASE_MODEL_ID = "Qwen/Qwen3.5-2B"


@dataclass(frozen=True)
class LoraTrainingConfig:
    base_model_id: str = DEFAULT_BASE_MODEL_ID
    model_family: str = "qwen3_5_image_text_to_text"
    dataset_path: Path = Path("data/training/explanations/train.jsonl")
    validation_path: Path | None = Path("data/training/explanations/validation.jsonl")
    output_dir: Path = Path("models/xiangqi-sifu-qwen35-2b-lora")
    max_length: int = 1536
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    target_modules: str | list[str] = "all-linear"
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 16
    learning_rate: float = 1e-4
    num_train_epochs: int = 1
    max_steps: int | None = None
    save_steps: int = 200
    logging_steps: int = 10
    bf16: bool = True
    gradient_checkpointing: bool = True

    @classmethod
    def from_json_file(cls, path: str | Path) -> "LoraTrainingConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_mapping(data)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "LoraTrainingConfig":
        valid_fields = {field.name for field in fields(cls)}
        values = {key: value for key, value in data.items() if key in valid_fields}
        for key in ("dataset_path", "validation_path", "output_dir"):
            if key in values and values[key] is not None:
                values[key] = Path(values[key])
        return cls(**values)

    def with_overrides(
        self,
        *,
        base_model_id: str | None = None,
        dataset_path: str | Path | None = None,
        output_dir: str | Path | None = None,
        max_steps: int | None = None,
    ) -> "LoraTrainingConfig":
        return replace(
            self,
            base_model_id=base_model_id or self.base_model_id,
            dataset_path=Path(dataset_path) if dataset_path else self.dataset_path,
            output_dir=Path(output_dir) if output_dir else self.output_dir,
            max_steps=max_steps if max_steps is not None else self.max_steps,
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, Path):
                data[field.name] = value.as_posix()
            else:
                data[field.name] = value
        return data
