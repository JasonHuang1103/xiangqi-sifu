from pathlib import Path

from xiangqi_sifu.database.repository import AnalysisRepository


def main() -> int:
    AnalysisRepository(Path("data/processed/xiangqi_sifu.db"))
    print("Initialized data/processed/xiangqi_sifu.db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
