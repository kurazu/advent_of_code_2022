import logging
from collections import deque
from pathlib import Path

import numpy as np
import tqdm
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import (
    WIDTH,
    find_top_index,
    get_jet,
    get_rocks,
    get_starting_board,
    simulate_step,
)

logger = logging.getLogger(__name__)


def trim_board(board: list[npt.NDArray[np.bool_]]) -> int:
    logger.debug("Trimming board")
    # try a background-filling algorithm at the top of the board
    # in order to verify how much of the board is still needed
    visited: set[tuple[int, int]] = set()
    to_visit: deque[tuple[int, int]] = deque()
    to_visit.append((len(board) - 1, WIDTH // 2))
    while to_visit:
        current = to_visit.popleft()
        row, col = current

        left_col = col - 1
        left = row, left_col
        if left_col >= 0 and not board[row][left_col] and left not in visited:
            to_visit.append(left)

        right_col = col + 1
        right = row, right_col
        if right_col < WIDTH and not board[row][right_col] and right not in visited:
            to_visit.append(right)

        bottom_row = row - 1
        bottom = bottom_row, col
        if not board[bottom_row][col] and bottom not in visited:
            to_visit.append(bottom)

        visited.add(current)

    last_row_to_keep = min(row for row, _ in visited) - 1
    logger.debug("Last row to keep: %d", last_row_to_keep)
    for _ in range(last_row_to_keep):
        board.pop(0)
    return last_row_to_keep


@wrap_main
def main(filename: Path) -> str:
    jet = get_jet(filename)
    rocks = get_rocks()
    steps = 1000000000000
    board = get_starting_board()
    trim_every = 1000
    trimmed_lines = 0
    for step in tqdm.trange(steps):
        simulate_step(board, next(rocks), jet)
        if step % trim_every == 0:
            trimmed_lines += trim_board(board)
    return str(find_top_index(board) + trimmed_lines)


if __name__ == "__main__":
    setup_logging(logging.INFO)
    main()
