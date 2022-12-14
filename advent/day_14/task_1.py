import functools
import itertools as it
import logging
from pathlib import Path
from typing import Iterable, NamedTuple

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
) -> npt.NDArray[np.uint8]:
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
        functools.partial(map, scale_point), lines
    )

    for line in scaled_lines:
        for start_point, end_point in mit.sliding_window(line, 2):
            lower_x, upper_x = mit.minmax((start_point.x, end_point.x))
            lower_y, upper_y = mit.minmax((start_point.y, end_point.y))
            board[lower_y : upper_y + 1, lower_x : upper_x + 1] = 1

    breakpoint()


@wrap_main
def main(filename: Path) -> str:
    lines = list(get_lines(filename))
    starting_point = Position(y=0, x=500)
    board = get_board(starting_point, lines)

    breakpoint()
    return ""


if __name__ == "__main__":
    setup_logging()
    main()
