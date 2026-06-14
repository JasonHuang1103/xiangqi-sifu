from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from side_projects.pikafish_mate_finder.mate_finder.mate_search import MateSearchResult


def result_to_dict(
    result: MateSearchResult,
    *,
    image: str,
    confidence: float,
    piece_count: int,
) -> dict:
    data = asdict(result)
    data["pv"] = list(result.pv)
    data["image"] = image
    data["vision_confidence"] = confidence
    data["piece_count"] = piece_count
    return data


def write_json(path: str | Path, data: dict) -> None:
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: str | Path, data: dict) -> None:
    lines = [
        "# Pikafish Forced Mate Report",
        "",
        f"- Image: `{data['image']}`",
        f"- FEN: `{data['fen']}`",
        f"- Forced mate found: `{data['forced_mate_found']}`",
        f"- Mate score: `{data['mate_score']}`",
        f"- Centipawn score: `{data['cp_score']}`",
        f"- Best move: `{data['best_move']}`",
        f"- PV: `{' '.join(data['pv'])}`",
        "",
        data["message"],
        "",
    ]
    Path(path).write_text("\n".join(lines), encoding="utf-8")
