import logging
from pathlib import Path

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import PositionInTime, find_min_distance, read_board

logger = logging.getLogger(__name__)


@wrap_main
def main(filename: Path) -> str:
    board = read_board(filename)
    end_point = find_min_distance(
        board,
        start_point=PositionInTime(0, board.north_exit),
        end_position=board.south_exit,
    )
    logger.info("Crosses the exit at %s", end_point)
    end_point = find_min_distance(
        board, start_point=end_point, end_position=board.north_exit
    )
    logger.info("Crosses the exit at %s", end_point)
    end_point = find_min_distance(
        board, start_point=end_point, end_position=board.south_exit
    )
    logger.info("Crosses the exit at %s", end_point)
    return str(end_point.time)


if __name__ == "__main__":
    setup_logging(logging.INFO)
    main()
