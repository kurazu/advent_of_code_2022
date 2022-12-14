import io
import logging
from pathlib import Path

import numpy as np
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import Position, SandOutOfBoundsException, StartPointBlockedException
from .task_1 import get_board as original_get_board
from .task_1 import get_lines, simulate

logger = logging.getLogger(__name__)


def get_board(
    starting_point: Position, lines: list[list[Position]]
) -> tuple[npt.NDArray[np.uint8], Position]:
    original_board, original_starting_point = original_get_board(starting_point, lines)
    original_height, original_width = original_board.shape
    new_height = original_height + 2
    new_width = original_width + 2 * original_height
    new_board = np.zeros((new_height, new_width), dtype=np.uint8)
    new_board[
        0:original_height, original_height : original_height + original_width
    ] = original_board
    # fill last row with 1s
    new_board[-1, :] = 1
    return new_board, Position(
        y=original_starting_point.y, x=original_starting_point.x + original_height
    )


def visualize_board(board: npt.NDArray[np.uint8]) -> str:
    markers: dict[int, str] = {0: ".", 1: "#", 2: "o"}
    return "\n".join("".join(map(lambda v: markers[v], row)) for row in board)


@wrap_main
def main(filename: Path) -> str:
    lines = list(get_lines(filename))
    starting_point = Position(y=0, x=500)
    board, scaled_starting_point = get_board(starting_point, lines)
    print(visualize_board(board))
    try:
        simulate(board, scaled_starting_point)
    except SandOutOfBoundsException as ex:
        raise AssertionError() from ex
    except StartPointBlockedException as ex:
        units_of_sand = ex.units
        print(visualize_board(board))
        return str(units_of_sand)
    else:
        raise AssertionError("Expected StartPointBlockedException")


if __name__ == "__main__":
    setup_logging()
    main()
