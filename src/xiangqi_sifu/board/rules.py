from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from xiangqi_sifu.board.fen import FILES, FenBoard
from xiangqi_sifu.board.move import normalize_move

Color = Literal["w", "b"]
Winner = Literal["red", "black"]


class IllegalMoveError(ValueError):
    pass


@dataclass(frozen=True)
class BoardState:
    board: tuple[tuple[str | None, ...], ...]
    active_color: Color
    castling: str = "-"
    en_passant: str = "-"
    halfmove_clock: int = 0
    fullmove_number: int = 1

    @classmethod
    def from_fen(cls, fen: str) -> "BoardState":
        parsed = FenBoard.from_fen(fen)
        if parsed.active_color not in {"w", "b"}:
            raise ValueError(f"Unsupported active color: {parsed.active_color!r}")
        return cls(
            board=parsed.board,
            active_color=parsed.active_color,
            castling=parsed.castling,
            en_passant=parsed.en_passant,
            halfmove_clock=parsed.halfmove_clock,
            fullmove_number=parsed.fullmove_number,
        )

    def to_fen(self) -> str:
        return FenBoard(
            board=self.board,
            active_color=self.active_color,
            castling=self.castling,
            en_passant=self.en_passant,
            halfmove_clock=self.halfmove_clock,
            fullmove_number=self.fullmove_number,
        ).to_fen()

    def piece_at(self, square: str) -> str | None:
        file_index, rank = _square_to_point(square)
        return self.board[9 - rank][file_index]


@dataclass(frozen=True)
class PositionStatus:
    kind: Literal[
        "ongoing",
        "check",
        "checkmate",
        "stalemate",
        "draw_repetition",
        "draw_no_progress",
    ]
    winner: Winner | None = None

    @property
    def terminal(self) -> bool:
        return self.kind in {
            "checkmate",
            "stalemate",
            "draw_repetition",
            "draw_no_progress",
        }


def legal_moves(state: BoardState) -> tuple[str, ...]:
    moves: list[str] = []
    for move in _pseudo_legal_moves(state, state.active_color):
        next_state = _apply_unchecked(state, move)
        if not is_in_check(next_state, state.active_color):
            moves.append(move)
    return tuple(sorted(moves))


def apply_legal_move(state: BoardState, move_uci: str) -> BoardState:
    move = normalize_move(move_uci).uci
    if move not in legal_moves(state):
        raise IllegalMoveError(f"Illegal move for current position: {move}")
    return _apply_unchecked(state, move)


def is_in_check(state: BoardState, color: str) -> bool:
    normalized = _normalize_color(color)
    king = "K" if normalized == "w" else "k"
    king_square = _find_piece(state, king)
    if king_square is None:
        return True
    opponent: Color = "b" if normalized == "w" else "w"
    return any(move[2:] == king_square for move in _pseudo_legal_moves(state, opponent))


def position_status(state: BoardState, *, repetitions: int = 1) -> PositionStatus:
    if repetitions >= 3:
        return PositionStatus("draw_repetition")
    if state.halfmove_clock >= 120:
        return PositionStatus("draw_no_progress")

    active_king = "K" if state.active_color == "w" else "k"
    if _find_piece(state, active_king) is None:
        return PositionStatus("checkmate", _winner_for_other_side(state.active_color))

    moves = legal_moves(state)
    checked = is_in_check(state, state.active_color)
    if not moves:
        return PositionStatus(
            "checkmate" if checked else "stalemate",
            _winner_for_other_side(state.active_color),
        )
    return PositionStatus("check" if checked else "ongoing")


def _pseudo_legal_moves(state: BoardState, color: Color) -> tuple[str, ...]:
    moves: list[str] = []
    for rank in range(10):
        for file_index in range(9):
            piece = _piece_at(state, file_index, rank)
            if piece is None or _piece_color(piece) != color:
                continue
            from_square = _point_to_square(file_index, rank)
            kind = piece.lower()
            if kind == "r":
                destinations = _rook_destinations(state, file_index, rank, color)
            elif kind == "c":
                destinations = _cannon_destinations(state, file_index, rank, color)
            elif kind == "n":
                destinations = _horse_destinations(state, file_index, rank, color)
            elif kind == "b":
                destinations = _elephant_destinations(state, file_index, rank, color)
            elif kind == "a":
                destinations = _advisor_destinations(state, file_index, rank, color)
            elif kind == "k":
                destinations = _general_destinations(state, file_index, rank, color)
            elif kind == "p":
                destinations = _soldier_destinations(state, file_index, rank, color)
            else:
                destinations = ()
            moves.extend(from_square + _point_to_square(*point) for point in destinations)
    return tuple(moves)


def _rook_destinations(
    state: BoardState, file_index: int, rank: int, color: Color
) -> tuple[tuple[int, int], ...]:
    destinations: list[tuple[int, int]] = []
    for file_delta, rank_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        next_file, next_rank = file_index + file_delta, rank + rank_delta
        while _inside(next_file, next_rank):
            piece = _piece_at(state, next_file, next_rank)
            if piece is None:
                destinations.append((next_file, next_rank))
            else:
                if _piece_color(piece) != color:
                    destinations.append((next_file, next_rank))
                break
            next_file += file_delta
            next_rank += rank_delta
    return tuple(destinations)


def _cannon_destinations(
    state: BoardState, file_index: int, rank: int, color: Color
) -> tuple[tuple[int, int], ...]:
    destinations: list[tuple[int, int]] = []
    for file_delta, rank_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        next_file, next_rank = file_index + file_delta, rank + rank_delta
        found_screen = False
        while _inside(next_file, next_rank):
            piece = _piece_at(state, next_file, next_rank)
            if not found_screen:
                if piece is None:
                    destinations.append((next_file, next_rank))
                else:
                    found_screen = True
            elif piece is not None:
                if _piece_color(piece) != color:
                    destinations.append((next_file, next_rank))
                break
            next_file += file_delta
            next_rank += rank_delta
    return tuple(destinations)


def _horse_destinations(
    state: BoardState, file_index: int, rank: int, color: Color
) -> tuple[tuple[int, int], ...]:
    patterns = (
        (2, 1, 1, 0),
        (2, -1, 1, 0),
        (-2, 1, -1, 0),
        (-2, -1, -1, 0),
        (1, 2, 0, 1),
        (-1, 2, 0, 1),
        (1, -2, 0, -1),
        (-1, -2, 0, -1),
    )
    destinations: list[tuple[int, int]] = []
    for file_delta, rank_delta, leg_file, leg_rank in patterns:
        target = (file_index + file_delta, rank + rank_delta)
        leg = (file_index + leg_file, rank + leg_rank)
        if _inside(*target) and _piece_at(state, *leg) is None:
            _append_if_available(destinations, state, target, color)
    return tuple(destinations)


def _elephant_destinations(
    state: BoardState, file_index: int, rank: int, color: Color
) -> tuple[tuple[int, int], ...]:
    destinations: list[tuple[int, int]] = []
    for file_delta, rank_delta in ((2, 2), (2, -2), (-2, 2), (-2, -2)):
        target = (file_index + file_delta, rank + rank_delta)
        eye = (file_index + file_delta // 2, rank + rank_delta // 2)
        if not _inside(*target) or _piece_at(state, *eye) is not None:
            continue
        if color == "w" and target[1] > 4:
            continue
        if color == "b" and target[1] < 5:
            continue
        _append_if_available(destinations, state, target, color)
    return tuple(destinations)


def _advisor_destinations(
    state: BoardState, file_index: int, rank: int, color: Color
) -> tuple[tuple[int, int], ...]:
    destinations: list[tuple[int, int]] = []
    for file_delta, rank_delta in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        target = (file_index + file_delta, rank + rank_delta)
        if _inside(*target) and _in_palace(*target, color):
            _append_if_available(destinations, state, target, color)
    return tuple(destinations)


def _general_destinations(
    state: BoardState, file_index: int, rank: int, color: Color
) -> tuple[tuple[int, int], ...]:
    destinations: list[tuple[int, int]] = []
    for file_delta, rank_delta in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        target = (file_index + file_delta, rank + rank_delta)
        if _inside(*target) and _in_palace(*target, color):
            _append_if_available(destinations, state, target, color)

    enemy_general = "k" if color == "w" else "K"
    step = 1 if color == "w" else -1
    next_rank = rank + step
    while _inside(file_index, next_rank):
        piece = _piece_at(state, file_index, next_rank)
        if piece is not None:
            if piece == enemy_general:
                destinations.append((file_index, next_rank))
            break
        next_rank += step
    return tuple(destinations)


def _soldier_destinations(
    state: BoardState, file_index: int, rank: int, color: Color
) -> tuple[tuple[int, int], ...]:
    forward = 1 if color == "w" else -1
    candidates = [(file_index, rank + forward)]
    crossed_river = rank >= 5 if color == "w" else rank <= 4
    if crossed_river:
        candidates.extend(((file_index - 1, rank), (file_index + 1, rank)))

    destinations: list[tuple[int, int]] = []
    for target in candidates:
        if _inside(*target):
            _append_if_available(destinations, state, target, color)
    return tuple(destinations)


def _apply_unchecked(state: BoardState, move_uci: str) -> BoardState:
    move = normalize_move(move_uci)
    from_file, from_rank = _square_to_point(move.from_square)
    to_file, to_rank = _square_to_point(move.to_square)
    moving_piece = _piece_at(state, from_file, from_rank)
    captured_piece = _piece_at(state, to_file, to_rank)
    if moving_piece is None:
        raise IllegalMoveError(f"No piece on {move.from_square}")

    rows = [list(row) for row in state.board]
    rows[9 - from_rank][from_file] = None
    rows[9 - to_rank][to_file] = moving_piece
    resets_clock = moving_piece.lower() == "p" or captured_piece is not None
    return BoardState(
        board=tuple(tuple(row) for row in rows),
        active_color="b" if state.active_color == "w" else "w",
        castling=state.castling,
        en_passant=state.en_passant,
        halfmove_clock=0 if resets_clock else state.halfmove_clock + 1,
        fullmove_number=state.fullmove_number + (1 if state.active_color == "b" else 0),
    )


def _append_if_available(
    destinations: list[tuple[int, int]],
    state: BoardState,
    target: tuple[int, int],
    color: Color,
) -> None:
    piece = _piece_at(state, *target)
    if piece is None or _piece_color(piece) != color:
        destinations.append(target)


def _find_piece(state: BoardState, target: str) -> str | None:
    for rank in range(10):
        for file_index in range(9):
            if _piece_at(state, file_index, rank) == target:
                return _point_to_square(file_index, rank)
    return None


def _piece_at(state: BoardState, file_index: int, rank: int) -> str | None:
    return state.board[9 - rank][file_index]


def _piece_color(piece: str) -> Color:
    return "w" if piece.isupper() else "b"


def _in_palace(file_index: int, rank: int, color: Color) -> bool:
    if file_index not in {3, 4, 5}:
        return False
    return rank in ({0, 1, 2} if color == "w" else {7, 8, 9})


def _inside(file_index: int, rank: int) -> bool:
    return 0 <= file_index < 9 and 0 <= rank < 10


def _square_to_point(square: str) -> tuple[int, int]:
    if len(square) != 2 or square[0] not in FILES or square[1] not in "0123456789":
        raise ValueError(f"Invalid Xiangqi coordinate: {square!r}")
    return FILES.index(square[0]), int(square[1])


def _point_to_square(file_index: int, rank: int) -> str:
    return f"{FILES[file_index]}{rank}"


def _normalize_color(color: str) -> Color:
    if color in {"w", "red"}:
        return "w"
    if color in {"b", "black"}:
        return "b"
    raise ValueError(f"Unsupported Xiangqi color: {color!r}")


def _winner_for_other_side(active_color: Color) -> Winner:
    return "black" if active_color == "w" else "red"
