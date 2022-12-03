from pathlib import Path
from typing import Iterable


def get_data_path(day: int, filename: str) -> Path:
    base_path = Path(__file__).parent.parent / "data"
    return base_path / f"day{day:02d}" / filename


def get_stripped_lines(filename: Path) -> Iterable[str]:
    with filename.open() as f:
        for line in f:
            line = line.strip()
            if line:
                yield line
