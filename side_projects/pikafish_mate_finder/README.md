# Pikafish Mate Finder

Standalone side project for finding Pikafish-reported forced mate lines from a
Xiangqi board screenshot.

This project is intentionally separate from the main `xiangqi_sifu` package so
it can be moved out later. It uses the same design ideas as Phase 3.5 Board
Vision, but keeps its own screenshot-to-FEN and UCI code.

## What It Does

```text
board screenshot
    ↓
template-based piece recognition
    ↓
FEN
    ↓
Pikafish UCI search
    ↓
forced mate report if score mate is found
```

The tool only claims a forced mate when Pikafish returns `score mate N`.
If Pikafish returns only a centipawn score, the report says no forced mate was
found at the current search setting.

## Requirements

- Python 3.11+
- `Pillow`
- `numpy`
- A local Pikafish UCI binary
- A board screenshot in `.png` or `.jpg`
- A template directory with `manifest.json`

From the repo root:

```bash
pip install -e ".[vision]"
```

## Template Manifest

Template filenames are mapped by FEN piece letter:

```json
{
  "templates": {
    "K": "red_king.png",
    "k": "black_king.png",
    "R": "red_rook.png",
    "r": "black_rook.png"
  }
}
```

The manifest should include every piece type expected in the screenshot.
Uppercase pieces are Red; lowercase pieces are Black.

## Usage

From the repo root:

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

`--board-rect` is `x,y,width,height`, where the rectangle spans the board grid
from the top-left intersection to the bottom-right intersection.

## Output

The JSON report includes:

```text
fen
forced_mate_found
mate_score
cp_score
best_move
pv
message
image
vision_confidence
piece_count
```

## Current Limitations

- Board rectangle is manual.
- Recognition is template-based, not general OCR.
- The result depends on screenshot quality, templates, search depth, and
  Pikafish settings.
- A centipawn advantage is not treated as a forced mate.
