from pathlib import Path


def get_data_path(day: int, filename: str) -> Path:
    base_path = Path(__file__).parent.parent / "data"
    return base_path / f"day{day:02d}" / filename
