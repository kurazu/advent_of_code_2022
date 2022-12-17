import enum
import io
import itertools as it
import logging
from pathlib import Path
from typing import Iterator

import numpy as np
import tqdm
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging


class Direction(str, enum.Enum):
    LEFT = "<"
    RIGHT = ">"


logger = logging.getLogger(__name__)

ROCKS: list[npt.NDArray[np.bool_]] = [
    np.array([[1, 1, 1, 1]], dtype=np.bool_),
    np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=np.bool_),
    np.array([[0, 0, 1], [0, 0, 1], [1, 1, 1]], dtype=np.bool_),
    np.array([[1], [1], [1], [1]], dtype=np.bool_),
    np.array([[1, 1], [1, 1]], dtype=np.bool_),
]

WIDTH = 7
FLOOR = np.array([1] * WIDTH, dtype=np.bool_)
TUNNEL = np.array([0] * WIDTH, dtype=np.bool_)


def find_top_index(board: list[npt.NDArray[np.bool_]]) -> int:
    idx = len(board) - 1
    for row in board[::-1]:
        if row.any():
            return idx
        idx -= 1
    raise AssertionError()


def _visualize_board(board: list[npt.NDArray[np.bool_]]) -> str:
    buf = io.StringIO()
    for row in board[::-1]:
        buf.write("".join("#" if cell else "." for cell in row))
        buf.write("\n")
    return buf.getvalue()


def visualize_board(board: list[npt.NDArray[np.bool_]]) -> None:
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Board:\n%s", _visualize_board(board))


def clashes(
    board: list[npt.NDArray[np.bool_]],
    rock: npt.NDArray[np.bool_],
    top: int,
    left: int,
) -> bool:
    rock_height, rock_width = rock.shape
    if left < 0:
        logger.debug("Rock clashes with left wall")
        return True
    if left + rock_width > WIDTH:
        logger.debug("Rock clashes with right wall")
        return True
    for idx, row in enumerate(rock):
        if (board[top - idx][left : left + rock_width] & row).any():
            logger.debug("Rock clashes with other rock")
            return True
    logger.debug("Rock does not clash")
    return False


def materialize_rock(
    board: list[npt.NDArray[np.bool_]], rock: npt.NDArray[np.bool_], top: int, left: int
) -> None:
    rock_height, rock_width = rock.shape
    for idx, row in enumerate(rock):
        board[top - idx][left : left + rock_width] |= row


DIRECTION_TO_OFFSET = {
    Direction.LEFT: -1,
    Direction.RIGHT: 1,
}


def simulate_step(
    board: list[npt.NDArray[np.bool_]],
    rock: npt.NDArray[np.bool_],
    jet: Iterator[Direction],
) -> None:
    logger.debug("Simulating step of rock %s", rock)
    rock_height, rock_width = rock.shape
    # spawn new rock
    current_top_idx = find_top_index(board)
    logger.debug("Current top index: %s", current_top_idx)
    bottom_spawn_idx = current_top_idx + 3
    logger.debug("Bottom spawn index: %s", bottom_spawn_idx)
    top_spawn_idx = bottom_spawn_idx + rock_height
    logger.debug("Needed spawn top index: %s", top_spawn_idx)
    # intitial spawn positions
    top = top_spawn_idx
    left = 2
    # expand board if neecessary
    while len(board) <= top_spawn_idx:
        logger.debug("Adding new row to board")
        board.append(np.copy(TUNNEL))
    # visualize_board(board)

    while True:
        direction = next(jet)
        offset = DIRECTION_TO_OFFSET[direction]
        if clashes(board, rock, top, left + offset):
            logger.debug("Jet stream cannot move rock")
        else:
            logger.debug("Jet stream moves rock %s", direction.name)
            left += offset

        if clashes(board, rock, top - 1, left):
            logger.debug("Rock cannot fall anymore")
            break
        else:
            logger.debug("Rock falls")
            top -= 1

    materialize_rock(board, rock, top, left)
    visualize_board(board)


@wrap_main
def main(filename: Path) -> str:
    jet = get_jet(filename)
    rocks = get_rocks()
    steps = 2022
    board = get_starting_board()
    for _ in tqdm.trange(steps):
        simulate_step(board, next(rocks), jet)
    logger.info("Board after %s steps:\n%s", steps, _visualize_board(board))
    return str(find_top_index(board))


def get_starting_board() -> list[npt.NDArray[np.bool_]]:
    board: list[npt.NDArray[np.bool_]] = [FLOOR]
    return board


def get_rocks() -> Iterator[npt.NDArray[np.bool_]]:
    rocks = it.cycle(ROCKS)
    return rocks


def get_jet(filename: Path) -> Iterator[Direction]:
    (jet_pattern,) = get_stripped_lines(filename)
    directions = list(map(Direction, jet_pattern))
    jet = it.cycle(directions)
    return jet


if __name__ == "__main__":
    setup_logging(logging.INFO)
    main()
