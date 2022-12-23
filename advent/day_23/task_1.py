import logging
import operator
from pathlib import Path
from typing import Iterable, NamedTuple

import more_itertools as mit
import numpy as np
from numpy import typing as npt

from ..cli_utils import wrap_main
from ..io_utils import get_stripped_lines
from ..logs import setup_logging

logger = logging.getLogger(__name__)


class Point(NamedTuple):
    y: int
    x: int


def read_board(filename: Path) -> Iterable[Point]:
    for row_idx, line in enumerate(get_stripped_lines(filename)):
        for col_idx, c in enumerate(line):
            if c == "#":
                yield Point(y=row_idx, x=col_idx)


def simulate(elves: set[Point]) -> set[Point]:
    return elves


@wrap_main
def main(filename: Path) -> str:
    elves = set(read_board(filename))
    for _ in range(10):
        elves = simulate(elves)
    min_y, max_y = mit.minmax(map(operator.attrgetter("y"), elves))
    min_x, max_x = mit.minmax(map(operator.attrgetter("x"), elves))
    area = (max_x - min_x + 1) * (max_y - min_y + 1)
    count = area - len(elves)
    return str(count)


if __name__ == "__main__":
    setup_logging()
    main()
