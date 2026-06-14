from __future__ import annotations

from dataclasses import dataclass

FILES = "abcdefghi"
RANKS_TOP_TO_BOTTOM = tuple(range(9, -1, -1))


@dataclass(frozen=True)
class GridPoint:
    square: str
    file_index: int
    rank: int
    x: float
    y: float


@dataclass(frozen=True)
class BoardRectangle:
    x: float
    y: float
    width: float
    height: float

    @classmethod
    def parse(cls, value: str) -> "BoardRectangle":
        parts = [part.strip() for part in value.split(",")]
        if len(parts) != 4:
            raise ValueError("Board rectangle must use x,y,width,height format")
        x, y, width, height = (float(part) for part in parts)
        return cls(x=x, y=y, width=width, height=height)

    def grid_points(self) -> list[GridPoint]:
        file_step = self.width / 8
        rank_step = self.height / 9
        points: list[GridPoint] = []
        for row_index, rank in enumerate(RANKS_TOP_TO_BOTTOM):
            for file_index, file_name in enumerate(FILES):
                points.append(
                    GridPoint(
                        square=f"{file_name}{rank}",
                        file_index=file_index,
                        rank=rank,
                        x=self.x + file_step * file_index,
                        y=self.y + rank_step * row_index,
                    )
                )
        return points
