import logging
from pathlib import Path

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import find_path, parse_board

logger = logging.getLogger(__name__)


@wrap_main
def main(filename: Path) -> str:
    board = parse_board(filename)
    cost = find_path(
        board.tiles,
        start_position=board.end_position,
        can_climb_callback=(
            lambda current_elevation, neighbor_elevation: (
                neighbor_elevation == current_elevation - 1
            )
            or (neighbor_elevation >= current_elevation)
        ),
        early_stopping_callback=(
            lambda neighbor_position, neighbor_elevation: neighbor_elevation == 0
        ),
    )
    return str(cost)


if __name__ == "__main__":
    setup_logging()
    main()
