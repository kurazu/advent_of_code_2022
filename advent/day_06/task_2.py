from pathlib import Path

from ..cli_utils import wrap_main
from .task_1 import find_position


@wrap_main
def main(filename: Path) -> str:
    with filename.open() as f:
        text = f.read().strip()
    position = find_position(text, window_size=14)
    return str(position)


if __name__ == "__main__":
    main()
