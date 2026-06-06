from __future__ import annotations

import re
from dataclasses import dataclass


ICCS_RE = re.compile(r"^([A-I])([0-9])-([A-I])([0-9])$")
UCI_RE = re.compile(r"^([a-i])([0-9])([a-i])([0-9])$")


@dataclass(frozen=True)
class Move:
    iccs: str
    uci: str
    from_square: str
    to_square: str


def normalize_move(token: str) -> Move:
    cleaned = token.strip()
    iccs_match = ICCS_RE.match(cleaned.upper())
    if iccs_match:
        from_square = f"{iccs_match.group(1).lower()}{iccs_match.group(2)}"
        to_square = f"{iccs_match.group(3).lower()}{iccs_match.group(4)}"
        return Move(
            iccs=f"{iccs_match.group(1)}{iccs_match.group(2)}-{iccs_match.group(3)}{iccs_match.group(4)}",
            uci=f"{from_square}{to_square}",
            from_square=from_square,
            to_square=to_square,
        )

    uci_match = UCI_RE.match(cleaned.lower())
    if uci_match:
        from_square = f"{uci_match.group(1)}{uci_match.group(2)}"
        to_square = f"{uci_match.group(3)}{uci_match.group(4)}"
        return Move(
            iccs=f"{uci_match.group(1).upper()}{uci_match.group(2)}-{uci_match.group(3).upper()}{uci_match.group(4)}",
            uci=f"{from_square}{to_square}",
            from_square=from_square,
            to_square=to_square,
        )

    raise ValueError(f"Unsupported move token: {token!r}")


def uci_to_iccs(move: str) -> str:
    return normalize_move(move).iccs
