# Xiangqi-Sifu LoRA Training Framework

This framework prepares a Xiangqi-R1-inspired explanation adapter for Xiangqi-Sifu. It does not include an official Xiangqi-R1 checkpoint and does not start training automatically.

## Base Model

Default:

```text
Qwen/Qwen3.5-2B
```

The model is configured in:

```text
config/lora_qwen35_2b.json
```

The framework treats Qwen3.5-2B as a text-only explanation target for now, even though the upstream model supports image-text usage. Training records contain chat messages with Xiangqi engine facts and a conservative explanation target.

## Install Training Dependencies

Training dependencies are optional:

```bash
pip install -e ".[training]"
```

Regular development and unit tests do not require these packages.

## Build Training JSONL

The training corpus defaults to the two raw databases:

```text
data/raw/WXF-41743games.pgns
data/raw/dpxq-99813games.pgns
```

Preview the corpus build without running Pikafish:

```bash
PYTHONPATH=src python3 scripts/build_explanation_training_corpus.py --dry-run
```

Build a small review slice first:

```bash
PYTHONPATH=src python3 scripts/build_explanation_training_corpus.py \
  --engine engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon \
  --output data/training/explanations/train.jsonl \
  --max-records-per-source 250 \
  --skip-errors
```

This produces a balanced 500-record review slice when both sources provide enough mistake positions.

Run the full corpus only after reviewing the small slice:

```bash
PYTHONPATH=src python3 scripts/build_explanation_training_corpus.py \
  --engine engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon \
  --output data/training/explanations/train.jsonl \
  --skip-errors
```

Each record contains:

```text
system message
user message with FEN, played move, best move, PVs, eval loss
assistant target explanation with:
    reason
    better move
    confidence
metadata with engine-ground-truth fields
```

Split a small source-balanced validation set for human review:

```bash
PYTHONPATH=src python3 scripts/split_explanation_training_data.py \
  --source data/training/explanations/train.jsonl \
  --train-output data/training/explanations/train.jsonl \
  --validation-output data/training/explanations/validation.jsonl \
  --validation-count 50
```

Validation records are marked:

```text
review_status: pending_human_review
```

## Dry Run

Validate the config and dataset without training:

```bash
PYTHONPATH=src python3 scripts/train_lora.py \
  --config config/lora_qwen35_2b.json \
  --dataset data/training/explanations/train.jsonl \
  --dry-run
```

The trainer refuses to start unless `--yes-start-training` is passed.

Run a bounded smoke configuration before a full job:

```bash
PYTHONPATH=src python3 scripts/train_lora.py \
  --config config/lora_qwen35_2b.json \
  --dataset data/training/explanations/train.jsonl \
  --max-steps 1 \
  --dry-run
```

Remove `--dry-run` and add `--yes-start-training` only when the base model is cached or the download/training runtime is acceptable.

For the current 450-record MVP slice, all tokenized records are under 512 tokens. The completed local test adapter used:

```text
max_length: 512
num_train_epochs: 2
output: models/xiangqi-sifu-qwen35-2b-lora
```

Measured result on the local MacBook MPS path:

```text
steps: 58
runtime: about 31.7 minutes
first loss: 2.625
final logged loss: 0.0154
final train_loss: 0.1643
```

## Benchmark Validation Records

Evaluate the held-out validation records against the grounded-format verifier:

```bash
PYTHONPATH=src python3 scripts/evaluate_explanation_benchmark.py \
  --dataset data/training/explanations/validation.jsonl \
  --output data/training/explanations/benchmark.json
```

The benchmark checks:

```text
format validity
best-move consistency
eval-loss consistency
verifier status
```

## Start Training

Only run this after reviewing the dataset and config:

```bash
PYTHONPATH=src python3 scripts/train_lora.py \
  --config config/lora_qwen35_2b.json \
  --yes-start-training
```

Adapter output defaults to:

```text
models/xiangqi-sifu-qwen35-2b-lora
```

## Export Adapter

After training, write the Phase 2 adapter manifest and model card:

```bash
PYTHONPATH=src python3 scripts/export_lora_adapter.py \
  --adapter-dir models/xiangqi-sifu-qwen35-2b-lora \
  --base-model models/base/Qwen3.5-2B \
  --training-records 450 \
  --validation-records 50
```

The export script requires `adapter_config.json` plus `adapter_model.safetensors` or `adapter_model.bin`. It does not create a fake checkpoint.

Generated datasets and model outputs are ignored by git.

## Current Limits

- This is an SFT-first framework; RL/GRPO refinement is deferred.
- Conservative targets are generated from engine data. The current adapter proves the framework, but larger training runs should use more diverse human-reviewed targets.
- The verifier still needs to mature before generated explanations can be used as high-confidence labels.
- In the Codex sandbox, MPS is hidden. Run training from a normal terminal or approved unsandboxed process so PyTorch can see `mps:0`.
