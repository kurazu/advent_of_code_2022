import enum
import logging
import operator
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import numpy as np
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


class Point(NamedTuple):
    y: int
    x: int


CHAR_TO_VELOCITY: dict[str, Point] = {
    ">": Point(y=0, x=1),
    "<": Point(y=0, x=-1),
    "^": Point(y=-1, x=0),
    "v": Point(y=1, x=0),
}


@dataclass
class Blizzard:
    initial_position: Point
    velocity: Point


@dataclass
class Board:
    height: int
    width: int
    start_point: Point
    end_point: Point
    blizzards: list[Blizzard]


def read_board(filename: Path) -> Board:
    blizzards: list[Blizzard] = []
    trimmed_lines = iter(
        map(
            operator.itemgetter(slice(1, -1)),
            get_stripped_lines(filename),
        )
    )
    first_line = next(trimmed_lines)
    assert first_line.startswith(".#")
    width = len(first_line)
    start_point = Point(y=-1, x=0)
    end_point: Point
    row = 0
    for line in trimmed_lines:
        assert len(line) == width
        if line.startswith("#"):
            assert line.endswith(".")
            end_point = Point(y=row, x=len(line) - 1)
            break
        for col, char in enumerate(line):
            if char == ".":
                continue
            initial_position = Point(y=row, x=col)
            velocity = CHAR_TO_VELOCITY[char]
            blizzards.append(
                Blizzard(
                    initial_position=initial_position,
                    velocity=velocity,
                )
            )
        row += 1
    return Board(
        height=row,
        width=width,
        start_point=start_point,
        end_point=end_point,
        blizzards=blizzards,
    )


@wrap_main
def main(filename: Path) -> str:
    board = read_board(filename)
    breakpoint()
    return ""


if __name__ == "__main__":
    setup_logging()
    main()
