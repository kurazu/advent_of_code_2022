import enum
import io
import itertools as it
import logging
from pathlib import Path
from typing import Iterator

import tqdm

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging


class Direction(str, enum.Enum):
    LEFT = "<"
    RIGHT = ">"


logger = logging.getLogger(__name__)

ROCKS: list[list[int]] = [
    [int("000111100", 2)],
    [int("000010000", 2), int("000111000", 2), int("000010000", 2)],
    [int("000001000", 2), int("000001000", 2), int("000111000", 2)],
    [
        int("000100000", 2),
        int("000100000", 2),
        int("000100000", 2),
        int("000100000", 2),
    ],
    [int("000110000", 2), int("000110000", 2)],
]

WIDTH = 7
FLOOR = int("111111111", 2)
TUNNEL = int("100000001", 2)

MASK = int("011111110", 2)


def find_top_index(board: list[int]) -> int:
    idx = len(board) - 1
    for row in board[::-1]:
        if row & MASK:
            return idx
        idx -= 1
    raise AssertionError()


def _visualize_board(board: list[int]) -> str:
    buf = io.StringIO()
    for row in board[::-1]:
        bits = bin(row)[2:].rjust(7, "0").replace("0", ".").replace("1", "#")
        buf.write(bits)
        buf.write("\n")
    return buf.getvalue()


def visualize_board(board: list[int]) -> None:
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Board:\n%s", _visualize_board(board))


def clashes(
    board: list[int],
    rock: list[int],
    top: int,
) -> bool:
    for idx, row in enumerate(rock):
        if board[top - idx] & row:
            return True
    return False


def materialize_rock(board: list[int], rock: list[int], top: int) -> None:
    for idx, row in enumerate(rock):
        board[top - idx] |= row


# TODO add cache
def move_rock(rock: list[int], direction: Direction) -> list[int]:
    if direction == Direction.LEFT:
        return [row << 1 for row in rock]
    else:
        assert direction == Direction.RIGHT
        return [row >> 1 for row in rock]


def simulate_step(
    board: list[int],
    rock: list[int],
    jet: Iterator[Direction],
) -> None:
    logger.debug("Simulating step of rock %s", rock)
    rock_height = len(rock)
    # spawn new rock
    current_top_idx = find_top_index(board)
    logger.debug("Current top index: %s", current_top_idx)
    bottom_spawn_idx = current_top_idx + 3
    logger.debug("Bottom spawn index: %s", bottom_spawn_idx)
    top_spawn_idx = bottom_spawn_idx + rock_height
    logger.debug("Needed spawn top index: %s", top_spawn_idx)
    # intitial spawn positions
    top = top_spawn_idx
    # expand board if neecessary
    while len(board) <= top_spawn_idx:
        logger.debug("Adding new row to board")
        board.append(TUNNEL)
    # visualize_board(board)

    while True:
        direction = next(jet)
        moved_rock = move_rock(rock, direction)
        if clashes(board, moved_rock, top):
            logger.debug("Jet stream cannot move rock")
        else:
            logger.debug("Jet stream moves rock %s", direction.name)
            rock = moved_rock

        if clashes(board, rock, top - 1):
            logger.debug("Rock cannot fall anymore")
            break
        else:
            logger.debug("Rock falls")
            top -= 1

    materialize_rock(board, rock, top)


@wrap_main
def main(filename: Path) -> str:
    jet = get_jet(filename)
    rocks = get_rocks()
    steps = 2022
    board = get_starting_board()
    for _ in tqdm.trange(steps):
        simulate_step(board, next(rocks), jet)
        visualize_board(board)
    logger.info("Board after %s steps:\n%s", steps, _visualize_board(board))
    return str(find_top_index(board))


def get_starting_board() -> list[int]:
    return [FLOOR]


def get_rocks() -> Iterator[list[int]]:
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
