# Xiangqi-Sifu Usage

This file keeps the common local commands for corpus parsing, knowledge-base
building, and position lookup.

## Parse Large `.pgns` Files

Raw `.pgns` files contain many games in one text file. The parser splits them
by:

```text
[Game "Chinese Chess"]
```

Parse WXF:

```bash
PYTHONPATH=src .venv/bin/python scripts/import_games.py \
  --source data/raw/WXF-41743games.pgns \
  --output-dir data/processed/wxf_41743games
```

Parse dpxq:

```bash
PYTHONPATH=src .venv/bin/python scripts/import_games.py \
  --source data/raw/dpxq-99813games.pgns \
  --output-dir data/processed/dpxq_99813games
```

Expected outputs:

```text
data/processed/wxf_41743games/games.jsonl
data/processed/wxf_41743games/manifest.json
data/processed/dpxq_99813games/games.jsonl
data/processed/dpxq_99813games/manifest.json
```

## Build Opening / Position Database

Build a small smoke-test database first:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_knowledge_base.py \
  data/processed/wxf_41743games/games.jsonl \
  data/processed/dpxq_99813games/games.jsonl \
  --db data/processed/xiangqi_sifu_knowledge_smoke.db \
  --corpus-name public \
  --max-games 1000
```

Build the full public knowledge database:

```bash
PYTHONPATH=src .venv/bin/python scripts/build_knowledge_base.py \
  data/processed/wxf_41743games/games.jsonl \
  data/processed/dpxq_99813games/games.jsonl \
  --db data/processed/xiangqi_sifu_knowledge.db \
  --corpus-name public
```

Current full local database:

```text
data/processed/xiangqi_sifu_knowledge.db
141,511 indexed games
6,942,448 unique positions
7,078,454 unique position/move choices
```

## Query A FEN

Query the starting position:

```bash
PYTHONPATH=src .venv/bin/python scripts/query_knowledge_base.py \
  --db data/processed/xiangqi_sifu_knowledge.db \
  --limit 10 \
  --example-limit 5
```

Query a specific FEN:

```bash
PYTHONPATH=src .venv/bin/python scripts/query_knowledge_base.py \
  --db data/processed/xiangqi_sifu_knowledge.db \
  --fen "YOUR_FEN_HERE" \
  --limit 10 \
  --example-limit 5
```

Query representative games for a specific move from that FEN:

```bash
PYTHONPATH=src .venv/bin/python scripts/query_knowledge_base.py \
  --db data/processed/xiangqi_sifu_knowledge.db \
  --fen "YOUR_FEN_HERE" \
  --move h2e2 \
  --limit 5 \
  --example-limit 5
```

If `--fen` is omitted, the query script uses the standard starting Xiangqi FEN.

## Data Format Notes

- `.pgns`: raw source text with many games concatenated together.
- `games.jsonl`: one normalized game per line, suitable for reproducible imports
  and training-data generation.
- `xiangqi_sifu_knowledge.db`: SQLite database optimized for position lookup,
  move frequency, result statistics, and representative source-game queries.

## Phase 3.5 Board Vision

The current Phase 3.5 MVP supports two deterministic input paths:

- verified board-label JSON
- raw `.png` / `.jpg` screenshots with a manual board rectangle and template
  manifest

Convert a labelled board observation to FEN:

```bash
PYTHONPATH=src .venv/bin/python scripts/screenshot_to_fen.py \
  --labels data/vision/samples/starting_position_labels.json
```

Infer a move from before/after labelled board observations:

```bash
PYTHONPATH=src .venv/bin/python scripts/compare_screenshots.py \
  --before-labels data/vision/samples/starting_position_labels.json \
  --after-labels data/vision/samples/after_h2e2_labels.json
```

Convert a raw screenshot to FEN with templates:

```bash
PYTHONPATH=src .venv/bin/python scripts/screenshot_to_fen.py \
  --image path/to/board.png \
  --templates path/to/templates \
  --board-rect 10,10,160,180 \
  --active-color w
```

Infer a move from before/after raw screenshots with templates:

```bash
PYTHONPATH=src .venv/bin/python scripts/compare_screenshots.py \
  --before-image path/to/before.png \
  --after-image path/to/after.png \
  --templates path/to/templates \
  --board-rect 10,10,160,180 \
  --before-active-color w \
  --after-active-color b
```

Label files use Xiangqi coordinates as keys and FEN piece letters as values:

```json
{
  "active_color": "w",
  "pieces": {
    "e0": "K",
    "e9": "k"
  }
}
```

Uppercase pieces are Red, lowercase pieces are Black.

Template directories must contain `manifest.json`:

```json
{
  "templates": {
    "K": "red_king.png",
    "k": "black_king.png"
  }
}
```

The manifest should include every piece letter expected in the screenshot.

## Side Project: Pikafish Mate Finder

Find a Pikafish-reported forced mate line from a board screenshot:

```bash
PYTHONPATH=. .venv/bin/python \
  side_projects/pikafish_mate_finder/scripts/find_mate.py \
  --image path/to/board.png \
  --templates path/to/templates \
  --board-rect 10,10,160,180 \
  --engine engines/pikafish-2026-01-02/MacOS/pikafish-apple-silicon \
  --depth 12 \
  --output data/processed/mate_report.json \
  --markdown-output data/processed/mate_report.md
```

The side project only claims a forced mate when Pikafish returns `score mate`.
Centipawn scores are reported as search evaluations, not forced mate proof.
