import functools
import itertools as it
import logging
from pathlib import Path
from typing import Callable, Iterable, NamedTuple, NoReturn, cast

import more_itertools as mit
import numpy as np
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


class Position(NamedTuple):
    y: int
    x: int


def get_lines(filename: Path) -> Iterable[list[Position]]:
    for line in get_stripped_lines(filename):
        segments = line.split(" -> ")
        splits = (segment.split(",") for segment in segments)
        yield [Position(y=int(y), x=int(x)) for x, y in splits]


def get_board(
    starting_point: Position, lines: list[list[Position]]
) -> tuple[npt.NDArray[np.uint8], Position]:
    def get_points() -> Iterable[Position]:
        return it.chain([starting_point], it.chain.from_iterable(lines))

    min_x, max_x = mit.minmax(map(lambda point: point.x, get_points()))
    min_y, max_y = mit.minmax(map(lambda point: point.y, get_points()))

    width = max_x - min_x + 1
    height = max_y - min_y + 1

    board = np.zeros((height, width), dtype=np.uint8)

    def scale_point(point: Position) -> Position:
        return Position(y=point.y - min_y, x=point.x - min_x)

    scaled_lines: Iterable[Iterable[Position]] = map(
        cast(
            Callable[[Iterable[Position]], Iterable[Position]],
            functools.partial(map, scale_point),
        ),
        lines,
    )

    for line in scaled_lines:
        for start_point, end_point in mit.sliding_window(line, 2):
            lower_x, upper_x = mit.minmax((start_point.x, end_point.x))
            lower_y, upper_y = mit.minmax((start_point.y, end_point.y))
            board[lower_y : upper_y + 1, lower_x : upper_x + 1] = 1

    scaled_starting_point = scale_point(starting_point)
    return board, scaled_starting_point


def get_next_positions(position: Position) -> Iterable[Position]:
    yield Position(y=position.y + 1, x=position.x)
    yield Position(y=position.y + 1, x=position.x - 1)
    yield Position(y=position.y + 1, x=position.x + 1)


class SandOutOfBoundsException(Exception):
    def __init__(self, units: int):
        self.units = units


class StartPointBlockedException(Exception):
    def __init__(self, units: int):
        self.units = units


def simulate(board: npt.NDArray[np.uint8], starting_point: Position) -> NoReturn:
    height, width = board.shape

    def is_out_of_bounds(position: Position) -> bool:
        return (
            position.x < 0
            or position.x >= width
            or position.y < 0
            or position.y >= height
        )

    units = 0
    while True:
        # new grain of sand
        current = starting_point
        if board[current]:
            # starting point is blocked, simulation is over
            raise StartPointBlockedException(units)
        while True:
            for position in get_next_positions(current):
                if is_out_of_bounds(position):
                    # sand fell out of the map, step simulation
                    raise SandOutOfBoundsException(units)
                elif not board[position]:
                    # position is empty, can move
                    current = position
                    break
                else:
                    # position in occupied, can't move there, try another position
                    continue
            else:
                # node of the positions were empty, sand will rest here
                board[current] = 2
                units += 1
                break


@wrap_main
def main(filename: Path) -> str:
    lines = list(get_lines(filename))
    starting_point = Position(y=0, x=500)
    board, scaled_starting_point = get_board(starting_point, lines)
    try:
        simulate(board, scaled_starting_point)
    except SandOutOfBoundsException as e:
        units_of_sand = e.units
        return str(units_of_sand)
    else:
        raise RuntimeError("Simulation should have ended with an exception")


if __name__ == "__main__":
    setup_logging()
    main()
