# xiangqi-sifu

`xiangqi-sifu` is a Phase 1 MVP for personal Xiangqi game review. It ingests one game at a time, normalizes coordinate moves, generates FEN positions, runs engine-style analysis, detects evaluation-loss mistakes, stores results in SQLite, and renders a Markdown review report.

## Current Scope

Runs 1, 2, and 3 are implemented for the constrained Phase 1 MVP. The CLI and Streamlit UI can run either the deterministic mocked engine or a real Pikafish UCI subprocess.

The project does not implement full Xiangqi legality validation. The position generator applies tested ICCS/UCI coordinate moves to FEN boards so analysis can be reproducible without inventing rules prematurely.

`PLAN.md` is the current planning source for future phases. Do not edit it unless the project direction changes intentionally.

Phase 1.5 LoRA training framework files are included for review. They prepare a Qwen/Qwen3.5-2B-based explanation adapter but do not start training automatically.

## Repo Structure

```text
xiangqi-sifu/
|-- README.md
|-- pyproject.toml
|-- .env.example
|-- data/
|   |-- raw/
|   |-- processed/
|   `-- examples/
|-- engine/
|   `-- README.md
|-- engines/
|   `-- pikafish-2026-01-02/
|-- src/
|   `-- xiangqi_sifu/
|       |-- __init__.py
|       |-- config.py
|       |-- cli.py
|       |-- parsers/
|       |   |-- base.py
|       |   |-- pgn_parser.py
|       |   `-- simple_move_parser.py
|       |-- board/
|       |   |-- representation.py
|       |   |-- fen.py
|       |   `-- move.py
|       |-- engine/
|       |   |-- pikafish.py
|       |   `-- analysis.py
|       |-- database/
|       |   |-- models.py
|       |   |-- schema.sql
|       |   `-- repository.py
|       |-- knowledge/
|       |   |-- schema.sql
|       |   |-- repository.py
|       |   `-- builder.py
|       |-- training/
|       |-- coach/
|       |   |-- mistake_detector.py
|       |   |-- explanation.py
|       |   `-- report.py
|       `-- api/
|           |-- main.py
|           `-- routes.py
|-- frontend/
|   `-- streamlit_app.py
|-- scripts/
|   |-- import_games.py
|   |-- build_knowledge_base.py
|   |-- query_knowledge_base.py
|   |-- train_lora.py
|   `-- evaluate_explanation_benchmark.py
|-- tests/
|   |-- test_parser.py
|   |-- test_fen.py
|   |-- test_pikafish.py
|   |-- test_mistake_detector.py
|   |-- test_report.py
|   `-- test_database.py
`-- notebooks/
    `-- analysis_scratch.ipynb
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Install the frontend extra when running the Streamlit app:

```bash
pip install -e ".[dev,frontend]"
```

Install the training extra only when preparing or running LoRA fine-tuning:

```bash
pip install -e ".[training]"
```

If using the system Python on this machine, disable third-party pytest plugin autoload because a global plugin currently imports an incompatible `pydantic_core` wheel:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest
```

## Pikafish

Pikafish is a UCI engine and must be launched as a subprocess. Do not import engine code directly.

The local official release binary is expected at:

```text
engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon
```

Configure it with:

```bash
cp .env.example .env
export XIANGQI_SIFU_ENGINE_PATH=engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon
```

The CLI can use this path directly:

```bash
PYTHONPATH=src python3 -m xiangqi_sifu.cli analyze data/examples/simple_game.txt \
  --engine engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon \
  --db data/processed/xiangqi_sifu.db \
  --report data/processed/pikafish_report.md \
  --depth 8
```

`--movetime-ms` can be used instead of depth when you want fixed time per position.

## Example Usage

Without installing the package:

```bash
PYTHONPATH=src python3 -m xiangqi_sifu.cli analyze data/examples/simple_game.txt --engine mock --db data/processed/xiangqi_sifu.db --report data/processed/simple_report.md
```

After editable install with the mocked engine:

```bash
xiangqi-sifu analyze data/examples/simple_game.txt --engine mock --db data/processed/xiangqi_sifu.db --report data/processed/simple_report.md
```

After editable install with Pikafish:

```bash
xiangqi-sifu analyze data/examples/simple_game.txt \
  --engine engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon \
  --db data/processed/xiangqi_sifu.db \
  --report data/processed/pikafish_report.md
```

With deterministic Phase 2 explanation output for local testing:

```bash
xiangqi-sifu analyze data/examples/simple_game.txt \
  --engine engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon \
  --db data/processed/xiangqi_sifu.db \
  --report data/processed/pikafish_report.md \
  --explain mock
```

With local Xiangqi-R1 inference:

```bash
xiangqi-sifu analyze data/examples/simple_game.txt \
  --engine engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon \
  --db data/processed/xiangqi_sifu.db \
  --report data/processed/xiangqi_r1_report.md \
  --explain xiangqi-r1 \
  --xiangqi-r1-model /path/to/base-model \
  --xiangqi-r1-lora /path/to/xiangqi-r1-lora
```

The official Xiangqi-R1 repository currently shows a Transformers + PEFT LoRA loading pattern with placeholder model paths. This project keeps those heavyweight dependencies optional and lazy-loaded; unit tests do not require Xiangqi-R1 or GPU libraries.

## LoRA Training Framework

The Phase 1.5 framework uses `Qwen/Qwen3.5-2B` as the default base model and writes supervised fine-tuning records to `data/training/explanations/*.jsonl`. The default corpus sources are:

```text
data/raw/WXF-41743games.pgns
data/raw/dpxq-99813games.pgns
```

Review the workflow in:

```text
docs/lora_training.md
```

The current MVP adapter has been trained on the initial 450-record slice with a 50-record validation set. This proves the Phase 1.5 training/export/inference path, but the targets are still conservative and templated; larger or final training runs should use a more diverse human-reviewed dataset.

After generating or providing a training JSONL, dry-run the trainer without starting training:

```bash
PYTHONPATH=src python3 scripts/train_lora.py \
  --config config/lora_qwen35_2b.json \
  --dataset data/training/explanations/train.jsonl \
  --dry-run
```

Evaluate the current validation split:

```bash
PYTHONPATH=src python3 scripts/evaluate_explanation_benchmark.py \
  --dataset data/training/explanations/validation.jsonl \
  --output data/training/explanations/benchmark.json
```

Actual training requires the explicit `--yes-start-training` flag. Use `--max-steps 1` for a bounded smoke run before a full job. On the current 450-record slice, the local MacBook-friendly run used `max_length=512` and 2 epochs because all records are under 512 tokens.

After training, export the adapter manifest and model card:

```bash
PYTHONPATH=src python3 scripts/export_lora_adapter.py \
  --adapter-dir models/xiangqi-sifu-qwen35-2b-lora \
  --base-model models/base/Qwen3.5-2B \
  --training-records 450 \
  --validation-records 50
```

The current exported local adapter path is:

```text
models/xiangqi-sifu-qwen35-2b-lora
```

Run the Streamlit UI:

```bash
PYTHONPATH=src streamlit run frontend/streamlit_app.py
```

The app lets you upload or paste one ICCS/PGN-like game, choose `mock` or a Pikafish binary path, set analysis depth or movetime, optionally generate mock or local LoRA explanations, store the result in SQLite, and review the move list, evaluation timeline, mistake table, verified explanations, and Markdown report.

## Workflow

1. Parse one game with `SimpleMoveParser` or `PgnParser`.
2. Normalize moves to ICCS plus UCI coordinate strings.
3. Generate FEN positions by applying coordinate moves.
4. Analyze every position with an engine adapter.
5. Compare eval before and after each move.
6. Flag inaccuracies, mistakes, and blunders from configurable thresholds.
7. Build explanation samples from FEN, played move, best move, PV(best), PV(played), and eval loss.
8. Optionally ask an explanation provider to explain why the engine move is better.
9. Verify explanation candidates with conservative support checks.
10. Store game, positions, moves, evaluations, mistakes, and verified explanations in SQLite.
11. Render a Markdown report with metadata, move list, eval timeline, mistake table, and optional verified explanations.

## Bulk Game Parsing

The raw `.pgns` database files store many games in one text file. Games are separated by:

```text
[Game "Chinese Chess"]
```

Parse each source into one structured JSONL record per game:

```bash
PYTHONPATH=src python3 scripts/import_games.py \
  --source data/raw/WXF-41743games.pgns \
  --output-dir data/processed/wxf_41743games

PYTHONPATH=src python3 scripts/import_games.py \
  --source data/raw/dpxq-99813games.pgns \
  --output-dir data/processed/dpxq_99813games
```

Outputs:

```text
data/processed/wxf_41743games/games.jsonl
data/processed/wxf_41743games/manifest.json
data/processed/dpxq_99813games/games.jsonl
data/processed/dpxq_99813games/manifest.json
```

## Phase 3A Knowledge Base

Phase 3A builds an opening/position explorer backend from normalized game JSONL. It stores position occurrence counts, move frequencies, result statistics, and representative source games.

The current local full public knowledge database is:

```text
data/processed/xiangqi_sifu_knowledge.db
141,511 indexed games
6,942,448 unique positions
7,078,454 unique position/move choices
```

Build a bounded smoke database:

```bash
PYTHONPATH=src python3 scripts/build_knowledge_base.py \
  data/processed/wxf_41743games/games.jsonl \
  data/processed/dpxq_99813games/games.jsonl \
  --db data/processed/xiangqi_sifu_knowledge.db \
  --corpus-name public \
  --max-games 1000
```

Build the full current public corpus after both JSONL files exist:

```bash
PYTHONPATH=src python3 scripts/build_knowledge_base.py \
  data/processed/wxf_41743games/games.jsonl \
  data/processed/dpxq_99813games/games.jsonl \
  --db data/processed/xiangqi_sifu_knowledge.db \
  --corpus-name public
```

Query the starting position:

```bash
PYTHONPATH=src python3 scripts/query_knowledge_base.py \
  --db data/processed/xiangqi_sifu_knowledge.db \
  --limit 10 \
  --example-limit 5
```

Each JSONL row contains `game_id`, metadata, players, result, starting FEN, move count, and normalized moves with ICCS plus UCI coordinates. Generated processed data is ignored by git because it is large and reproducible from the source file.

## Thresholds

Default centipawn-loss thresholds:

```text
inaccuracy: >= 80 cp
mistake:    >= 150 cp
blunder:    >= 300 cp
```

Moves are not flagged when the engine best move matches the played move.

## Completed

- [x] Run 1 parser abstraction.
- [x] Run 1 simple move-list parser.
- [x] Run 1 PGN-like ICCS parser.
- [x] Run 1 FEN board parser and coordinate move application.
- [x] Run 1 mocked engine analysis flow.
- [x] Run 1 mistake detector.
- [x] Run 1 Markdown report generator.
- [x] Run 1 SQLite schema and repository.
- [x] Run 1 CLI command with `--engine mock`.
- [x] Unit tests for parser, FEN, mocked engine flow, mistake detection, report generation, and database storage.
- [x] Run 2 real Pikafish UCI subprocess wrapper.
- [x] Run 2 CLI support for `--engine /path/to/pikafish`.
- [x] Run 2 score, mate, best move, and principal variation parsing.
- [x] Run 2 fake-UCI process tests so CI does not require Pikafish.
- [x] Run 3 Streamlit upload/review UI.
- [x] Run 3 move list, evaluation timeline, mistake table, and report display.
- [x] Run 3 frontend orchestration tests without requiring Streamlit in unit tests.
- [x] Bulk parser for `WXF-41743games.pgns` into per-game JSONL records.
- [x] Phase 2 explanation sample builder.
- [x] Phase 2 Xiangqi-R1-style prompt builder.
- [x] Phase 2 optional explanation provider interface.
- [x] Phase 2 local Xiangqi-R1 lazy adapter for base-model plus LoRA paths.
- [x] Phase 2 conservative explanation verifier.
- [x] Phase 2 report section for verified explanations.
- [x] Phase 2 verified explanation storage in SQLite.
- [x] Phase 2 Streamlit controls for mock/local LoRA explanations.
- [x] Phase 1.5 Qwen/Qwen3.5-2B LoRA training config.
- [x] Phase 1.5 explanation SFT JSONL builder.
- [x] Phase 1.5 guarded LoRA training launcher with dry-run mode.
- [x] Phase 1.5 local Qwen/Qwen3.5-2B LoRA adapter trained on the 450-record MVP slice.
- [x] Phase 1.5 adapter manifest and model card exported for Phase 2.
- [x] Phase 3A position/move knowledge-base schema and repository.
- [x] Phase 3A build/query scripts for opening explorer backend.
- [x] Phase 3A mixed-source sample build from WXF and dpxq processed games.
- [x] Phase 3A full WXF+dpxq public knowledge database build.

## To Do

- [ ] Later: Add XQF/XML parsers.
- [ ] Phase 1.5: Expand beyond the 450-record MVP slice with more diverse human-reviewed explanations.
- [ ] Phase 2: Add a human-rated explanation quality benchmark.
- [ ] Phase 3B: Connect analyzed user mistakes to the knowledge base for recurring-pattern reports.
- [ ] Later: Add deeper tactical/theme verification beyond simple text support checks.

## Current Limitations

- FEN generation applies moves but does not validate full Xiangqi legality.
- Only one-game-at-a-time analysis is in scope.
- The full public knowledge database is a generated local artifact; rebuild it from `data/raw` if it is deleted or moved.
- Real Xiangqi-R1 inference is optional and requires local model resources outside the default install.
- Explanation verification is conservative and does not yet prove tactical claims such as material wins or mating attacks.
