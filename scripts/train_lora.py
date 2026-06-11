from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from xiangqi_sifu.training.dataset import read_jsonl
from xiangqi_sifu.training.lora_config import LoraTrainingConfig


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config = _load_config(args)
    records = read_jsonl(config.dataset_path)
    _validate_records(records)

    print("LoRA training configuration:")
    print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    print(f"Training records: {len(records)}")

    if args.dry_run or not args.yes_start_training:
        print("Training will not start. Pass --yes-start-training without --dry-run to train.")
        return 0

    _run_training(config, records)
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the Xiangqi-Sifu explanation LoRA adapter.",
    )
    parser.add_argument("--config", type=Path, default=Path("config/lora_qwen35_2b.json"))
    parser.add_argument("--dataset", type=Path, help="Override training JSONL path")
    parser.add_argument("--base-model", help="Override base model id/path")
    parser.add_argument("--output-dir", type=Path, help="Override adapter output directory")
    parser.add_argument("--max-steps", type=int, help="Override training max_steps for smoke runs")
    parser.add_argument("--dry-run", action="store_true", help="Validate config and data only")
    parser.add_argument(
        "--yes-start-training",
        action="store_true",
        help="Required to actually start fine-tuning",
    )
    return parser.parse_args(argv)


def _load_config(args: argparse.Namespace) -> LoraTrainingConfig:
    config = (
        LoraTrainingConfig.from_json_file(args.config)
        if args.config.exists()
        else LoraTrainingConfig()
    )
    return config.with_overrides(
        base_model_id=args.base_model,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        max_steps=args.max_steps,
    )


def _validate_records(records: list[dict[str, Any]]) -> None:
    if not records:
        raise ValueError("Training dataset is empty")
    for index, record in enumerate(records, start=1):
        messages = record.get("messages")
        if not isinstance(messages, list) or len(messages) < 3:
            raise ValueError(f"Record {index} must contain at least 3 chat messages")
        if messages[-1].get("role") != "assistant":
            raise ValueError(f"Record {index} last message must be an assistant target")


def _run_training(config: LoraTrainingConfig, records: list[dict[str, Any]]) -> None:
    try:
        import torch
        from datasets import Dataset
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            Trainer,
            TrainingArguments,
            default_data_collator,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Training requires the optional training dependencies. "
            'Install them with: pip install -e ".[training]"'
        ) from exc

    tokenizer = AutoTokenizer.from_pretrained(config.base_model_id, trust_remote_code=True)
    model_kwargs = {
        "torch_dtype": torch.bfloat16 if config.bf16 else torch.float16,
        "trust_remote_code": True,
    }
    device_map = training_device_map(torch)
    if device_map is not None:
        model_kwargs["device_map"] = device_map
    model = AutoModelForCausalLM.from_pretrained(config.base_model_id, **model_kwargs)

    peft_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.target_modules,
        task_type=TaskType.CAUSAL_LM,
    )
    model.enable_input_require_grads()
    model = get_peft_model(model, peft_config)
    model.config.use_cache = False

    dataset = Dataset.from_list(records)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.pad_token_id = tokenizer.eos_token_id
    tokenized = dataset.map(
        lambda example: _tokenize_record(example, tokenizer, config.max_length),
        batched=False,
        remove_columns=dataset.column_names,
    )

    training_args = TrainingArguments(
        output_dir=str(config.output_dir),
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        num_train_epochs=config.num_train_epochs,
        max_steps=config.max_steps if config.max_steps is not None else -1,
        save_steps=config.save_steps,
        logging_steps=config.logging_steps,
        report_to="tensorboard",
        gradient_checkpointing=config.gradient_checkpointing,
        bf16=should_use_bf16_training(torch, requested=config.bf16),
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=default_data_collator,
    )
    trainer.train()
    trainer.model.save_pretrained(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)


def _tokenize_record(example, tokenizer, max_length: int) -> dict[str, list[int]]:
    messages = example["messages"]
    prompt_messages = _qwen_text_messages(messages[:-1])
    target_message = messages[-1]
    prompt_text = tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    prompt = tokenizer(prompt_text, add_special_tokens=False)
    target = tokenizer(target_message["content"] + tokenizer.eos_token, add_special_tokens=False)
    input_ids = prompt["input_ids"] + target["input_ids"]
    attention_mask = prompt["attention_mask"] + target["attention_mask"]
    labels = [-100] * len(prompt["input_ids"]) + target["input_ids"]

    input_ids = input_ids[:max_length]
    attention_mask = attention_mask[:max_length]
    labels = labels[:max_length]
    padding_length = max_length - len(input_ids)
    if padding_length > 0:
        input_ids += [tokenizer.pad_token_id] * padding_length
        attention_mask += [0] * padding_length
        labels += [-100] * padding_length
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


def _qwen_text_messages(messages: list[dict[str, str]]) -> list[dict[str, object]]:
    return [
        {
            "role": message["role"],
            "content": [{"type": "text", "text": message["content"]}],
        }
        for message in messages
    ]


def should_use_bf16_training(torch_module, *, requested: bool) -> bool:
    if not requested:
        return False
    return bool(
        torch_module.cuda.is_available()
        or torch_module.backends.mps.is_available()
    )


def training_device_map(torch_module) -> str | None:
    if torch_module.backends.mps.is_available() and not torch_module.cuda.is_available():
        return None
    return "auto"


if __name__ == "__main__":
    raise SystemExit(main())
