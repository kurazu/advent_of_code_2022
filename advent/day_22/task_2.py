import enum
import logging
from pathlib import Path
from typing import NamedTuple

import numpy as np
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..logs import setup_logging
from .task_1 import Direction, Position, find_starting_point, hash_position, read_data

logger = logging.getLogger(__name__)


class Board(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"


class Transform(str, enum.Enum):
    MIRROR = "M"
    KEEP = "K"
    SWAP = "S"
    SWAP_MIRROR = "SM"


class Transition(NamedTuple):
    target: Board
    new_direction: Direction
    x: Transform
    y: Transform


TRANSITIONS: dict[Board, dict[Direction, Transition]] = {
    Board.A: {
        Direction.UP: Transition(
            Board.E, Direction.DOWN, x=Transform.MIRROR, y=Transform.KEEP
        ),
        Direction.RIGHT: Transition(
            Board.D, Direction.LEFT, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.DOWN: Transition(
            Board.B, Direction.DOWN, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.LEFT: Transition(
            Board.F, Direction.DOWN, x=Transform.SWAP, y=Transform.SWAP
        ),
    },
    Board.B: {
        Direction.UP: Transition(
            Board.A, Direction.UP, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.RIGHT: Transition(
            Board.D, Direction.DOWN, x=Transform.SWAP, y=Transform.SWAP_MIRROR
        ),
        Direction.DOWN: Transition(
            Board.C, Direction.DOWN, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.LEFT: Transition(
            Board.F, Direction.LEFT, x=Transform.MIRROR, y=Transform.KEEP
        ),
    },
    Board.C: {
        Direction.UP: Transition(
            Board.B, Direction.UP, x=Transform.KEEP, y=Transform.MIRROR
        ),
        Direction.RIGHT: Transition(
            Board.D, Direction.RIGHT, x=Transform.MIRROR, y=Transform.KEEP
        ),
        Direction.DOWN: Transition(
            Board.E, Direction.UP, x=Transform.MIRROR, y=Transform.KEEP
        ),
        Direction.LEFT: Transition(
            Board.F, Direction.UP, x=Transform.SWAP_MIRROR, y=Transform.SWAP_MIRROR
        ),
    },
}
# numoy array for storing a single string character
SUPER_TILES: list[list[Board | None]] = [
    [None, None, Board.A, None],
    [Board.E, Board.F, Board.B, None],
    [None, None, Board.C, Board.D],
]


class MiniBoard(NamedTuple):
    tiles: npt.NDArray[np.uint8]
    original_indices: npt.NDArray[np.int16]


def get_superboard(
    board: npt.NDArray[np.uint8], super_tiles: list[list[Board | None]]
) -> dict[Board, MiniBoard]:
    result: dict[Board, MiniBoard] = {}
    height, width = board.shape
    original_indices = np.full((height, width, 2), -1, dtype=np.int16)
    for y in range(height):
        for x in range(width):
            original_indices[y, x] = (y, x)
    super_tiles_array = np.array(super_tiles, dtype=object)
    sup_height, sup_width = super_tiles_array.shape
    block_size = width // sup_width
    logger.debug("Block size %d", block_size)
    for super_y in range(sup_height):
        for super_x in range(sup_width):
            super_tile = super_tiles_array[super_y, super_x]
            if super_tile is None:
                continue
            assert isinstance(super_tile, Board)
            tile = board[
                super_y * block_size : (super_y + 1) * block_size,
                super_x * block_size : (super_x + 1) * block_size,
            ]
            indices = original_indices[
                super_y * block_size : (super_y + 1) * block_size,
                super_x * block_size : (super_x + 1) * block_size,
            ]
            result[super_tile] = MiniBoard(tile, indices)
    return result


def recover_point(
    superboard: dict[Board, MiniBoard], board: Board, point: Position
) -> Position:
    miniboard = superboard[board]
    original_y, original_x = miniboard.original_indices[point]
    return Position(y=original_y, x=original_x)


@wrap_main
def main(filename: Path) -> str:
    logger.debug("Reading data")
    board, instructions = read_data(filename)
    superboard = get_superboard(board, SUPER_TILES)
    del board
    logger.debug("Looking for starting point")
    start_board = Board.A
    start_point = find_starting_point(superboard[start_board].tiles)
    logger.debug("Starting point found %r", start_point)
    start_direction = Direction.RIGHT

    end_board, end_point, end_direction = start_board, start_point, start_direction
    logger.debug(
        "End board=%s, point=%r, direction=%s", end_board, end_point, end_direction
    )
    recovered_point = recover_point(superboard, end_board, end_point)
    logger.debug("Recovered point %r", recovered_point)
    return str(hash_position(end_point, end_direction))


if __name__ == "__main__":
    setup_logging()
    main()
